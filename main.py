#!/usr/bin/env python3
"""
ECMWF Data Downloader

A CLI tool for downloading meteorological forecast data from ECMWF Data Store.
Supports various forecast models and data formats.
"""

import asyncio
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from urllib.parse import urljoin, urlparse

import aiohttp
import httpx
import pandas as pd
import typer
from pydantic import BaseModel, field_validator
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

app = typer.Typer(
    name="ecmwf-downloader",
    help="Download ECMWF meteorological forecast data",
    rich_markup_mode="rich"
)
console = Console()

# Configuration
ECMWF_BASE_URL = "https://data.ecmwf.int/forecasts/"
DEFAULT_OUTPUT_DIR = Path("./ecmwf_data")
VALID_DATE_FORMAT = "%Y%m%d"


class DownloadConfig(BaseModel):
    """Configuration for ECMWF data downloads."""
    base_url: str = ECMWF_BASE_URL
    output_dir: Path = DEFAULT_OUTPUT_DIR
    max_concurrent_downloads: int = 5
    timeout_seconds: int = 300
    chunk_size: int = 8192
    
    @field_validator('output_dir', mode='before')
    @classmethod
    def validate_output_dir(cls, v):
        if isinstance(v, str):
            v = Path(v)
        v.mkdir(parents=True, exist_ok=True)
        return v


class ECMWFDownloader:
    """Main class for downloading ECMWF data."""
    
    def __init__(self, config: DownloadConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def get_available_dates(self, days_back: int = 7) -> List[str]:
        """Get list of available forecast dates."""
        dates = []
        base_date = datetime.now()
        
        for i in range(days_back):
            date = base_date - timedelta(days=i)
            dates.append(date.strftime(VALID_DATE_FORMAT))
        
        return dates
    
    def validate_date_format(self, date_str: str) -> bool:
        """Validate date format (YYYYMMDD)."""
        try:
            datetime.strptime(date_str, VALID_DATE_FORMAT)
            return True
        except ValueError:
            return False
    
    async def list_available_files(self, date: str, 
                                   forecast_time: str = "12z", 
                                   model: str = "ifs", 
                                   resolution: str = "0p25", 
                                   data_type: str = "oper") -> List[Dict[str, Any]]:
        """List available files for a given date and parameters."""
        if not self.validate_date_format(date):
            raise ValueError(f"Invalid date format: {date}. Expected YYYYMMDD.")
        
        # Build the full URL path
        url = urljoin(self.config.base_url, f"{date}/{forecast_time}/{model}/{resolution}/{data_type}/")
        
        try:
            async with self.session.get(url) as response:
                if response.status == 404:
                    console.print(f"[yellow]No data available for: {date}/{forecast_time}/{model}/{resolution}/{data_type}[/yellow]")
                    return []
                
                response.raise_for_status()
                content = await response.text()
                
                # Parse directory listing for actual files
                files = self._parse_data_files(content, date, forecast_time, model, resolution, data_type)
                return files
                
        except aiohttp.ClientError as e:
            console.print(f"[red]Error accessing {url}: {e}[/red]")
            return []
    
    def _parse_data_files(self, html_content: str, date: str, forecast_time: str, 
                         model: str, resolution: str, data_type: str) -> List[Dict[str, Any]]:
        """Parse HTML directory listing to extract actual data files."""
        files = []
        
        # Updated regex to match the actual ECMWF file structure
        # Pattern: <a href="filename.ext">filename.ext</a>       date time    size    id
        file_pattern = r'<a href="([^"]+\.(?:grib2?|index|nc))"[^>]*>([^<]+)</a>\s+(\d{2}-\d{2}-\d{4}\s+\d{2}:\d{2})\s+(\d+)\s+(\d+)'
        matches = re.findall(file_pattern, html_content, re.IGNORECASE)
        
        base_url = f"{self.config.base_url}{date}/{forecast_time}/{model}/{resolution}/{data_type}/"
        
        for href, filename, date_time, size, file_id in matches:
            # Extract forecast hour from filename (e.g., "20250617120000-0h-oper-fc.grib2")
            hour_match = re.search(r'-(\d+)h-', filename)
            forecast_hour = hour_match.group(1) if hour_match else "unknown"
            
            file_info = {
                'filename': filename.strip(),
                'url': urljoin(base_url, href),
                'date': date,
                'forecast_time': forecast_time,
                'model': model,
                'resolution': resolution,
                'data_type': data_type,
                'forecast_hour': forecast_hour,
                'size': self._format_file_size(int(size)),
                'raw_size': int(size),
                'type': self._get_file_type(filename),
                'modified': date_time
            }
            files.append(file_info)
        
        return files
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
    
    def _get_file_type(self, filename: str) -> str:
        """Determine file type based on extension."""
        if filename.endswith('.grib') or filename.endswith('.grib2'):
            return 'GRIB'
        elif filename.endswith('.nc') or filename.endswith('.netcdf'):
            return 'NetCDF'
        elif filename.endswith('.idx'):
            return 'Index'
        else:
            return 'Unknown'
    
    async def download_file(self, file_info: Dict[str, Any], progress: Progress, task_id: Any) -> bool:
        """Download a single file with progress tracking."""
        url = file_info['url']
        filename = file_info['filename']
        output_path = self.config.output_dir / file_info['date'] / filename
        
        # Create date-specific directory
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            async with self.session.get(url) as response:
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                if total_size > 0:
                    progress.update(task_id, total=total_size)
                
                with open(output_path, 'wb') as f:
                    downloaded = 0
                    async for chunk in response.content.iter_chunked(self.config.chunk_size):
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress.update(task_id, completed=downloaded)
                
                console.print(f"[green]✓[/green] Downloaded: {filename}")
                return True
                
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to download {filename}: {e}")
            if output_path.exists():
                output_path.unlink()  # Remove partial file
            return False
    
    async def download_files(self, files: List[Dict[str, Any]], max_concurrent: Optional[int] = None) -> Dict[str, int]:
        """Download multiple files concurrently."""
        if not files:
            return {'success': 0, 'failed': 0}
        
        max_concurrent = max_concurrent or self.config.max_concurrent_downloads
        semaphore = asyncio.Semaphore(max_concurrent)
        
        results = {'success': 0, 'failed': 0}
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            
            async def download_with_progress(file_info):
                async with semaphore:
                    task_id = progress.add_task(f"Downloading {file_info['filename']}", total=None)
                    success = await self.download_file(file_info, progress, task_id)
                    progress.remove_task(task_id)
                    return success
            
            tasks = [download_with_progress(file_info) for file_info in files]
            download_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in download_results:
                if isinstance(result, bool) and result:
                    results['success'] += 1
                else:
                    results['failed'] += 1
        
        return results
    
    async def list_available_configurations(self, date: str) -> Dict[str, List[str]]:
        """List available forecast configurations for a date."""
        if not self.validate_date_format(date):
            raise ValueError(f"Invalid date format: {date}. Expected YYYYMMDD.")
        
        configurations = {
            'forecast_times': [],
            'models': [],
            'resolutions': [],
            'data_types': []
        }
        
        # Get forecast times (12z, 18z, etc.)
        date_url = urljoin(self.config.base_url, f"{date}/")
        try:
            async with self.session.get(date_url) as response:
                if response.status == 200:
                    content = await response.text()
                    time_pattern = r'<a href="([^"]+z)/"[^>]*>([^<]+z)/</a>'
                    time_matches = re.findall(time_pattern, content, re.IGNORECASE)
                    # Extract just the time part (e.g., "12z" from "/forecasts/20250617/12z")
                    configurations['forecast_times'] = [match[0].split('/')[-1] for match in time_matches if match[0].endswith('z')]
        except:
            pass
        
        # Check common configurations
        common_configs = [
            ('12z', 'ifs', ['0p25', '0p4'], ['oper', 'enfo', 'waef', 'wave']),
            ('18z', 'ifs', ['0p25', '0p4'], ['oper', 'enfo', 'waef', 'wave']),
            ('18z', 'aifs-single', ['0p25'], ['oper']),
        ]
        
        for forecast_time, model, resolutions, data_types in common_configs:
            if forecast_time in configurations['forecast_times'] or not configurations['forecast_times']:
                if model not in configurations['models']:
                    configurations['models'].append(model)
                for res in resolutions:
                    if res not in configurations['resolutions']:
                        configurations['resolutions'].append(res)
                for dt in data_types:
                    if dt not in configurations['data_types']:
                        configurations['data_types'].append(dt)
        
        return configurations


def display_files_table(files: List[Dict[str, Any]]):
    """Display available files in a formatted table."""
    if not files:
        console.print("[yellow]No files found.[/yellow]")
        return
    
    table = Table(title="Available ECMWF Files")
    table.add_column("Filename", style="cyan", no_wrap=True)
    table.add_column("Type", style="magenta")
    table.add_column("Forecast", style="blue")
    table.add_column("Model", style="green")
    table.add_column("Resolution", style="yellow")
    table.add_column("Size", style="red")
    
    for file_info in files:
        forecast_info = f"{file_info.get('forecast_time', 'N/A')} +{file_info.get('forecast_hour', '?')}h"
        table.add_row(
            file_info['filename'],
            file_info['type'],
            forecast_info,
            file_info.get('model', 'N/A'),
            file_info.get('resolution', 'N/A'),
            file_info['size']
        )
    
    console.print(table)


@app.command()
def list_dates(
    days_back: int = typer.Option(7, "--days", "-d", help="Number of days back to show")
):
    """List available forecast dates."""
    config = DownloadConfig()
    downloader = ECMWFDownloader(config)
    
    dates = downloader.get_available_dates(days_back)
    
    console.print(f"\n[bold]Available forecast dates (last {days_back} days):[/bold]")
    for date in dates:
        formatted_date = datetime.strptime(date, VALID_DATE_FORMAT).strftime("%Y-%m-%d (%A)")
        console.print(f"  • {date} ({formatted_date})")


@app.command()
def list_files(
    date: str = typer.Argument(..., help="Forecast date (YYYYMMDD format)"),
    forecast_time: str = typer.Option("12z", "--time", "-t", help="Forecast time (12z, 18z, etc.)"),
    model: str = typer.Option("ifs", "--model", "-m", help="Model (ifs, aifs-single)"),
    resolution: str = typer.Option("0p25", "--resolution", "-r", help="Resolution (0p25, 0p4)"),
    data_type: str = typer.Option("oper", "--type", help="Data type (oper, enfo, waef, wave)"),
    output_dir: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory")
):
    """List available files for a specific forecast date and configuration."""
    config = DownloadConfig()
    if output_dir:
        config.output_dir = output_dir
    
    async def _list_files():
        async with ECMWFDownloader(config) as downloader:
            files = await downloader.list_available_files(date, forecast_time, model, resolution, data_type)
            display_files_table(files)
            
            if files:
                console.print(f"\n[dim]Found {len(files)} files for {date}/{forecast_time}/{model}/{resolution}/{data_type}[/dim]")
    
    asyncio.run(_list_files())


@app.command()
def list_config(
    date: str = typer.Argument(..., help="Forecast date (YYYYMMDD format)")
):
    """List available forecast configurations for a specific date."""
    config = DownloadConfig()
    
    async def _list_config():
        async with ECMWFDownloader(config) as downloader:
            configurations = await downloader.list_available_configurations(date)
            
            console.print(f"\n[bold]Available configurations for {date}:[/bold]")
            
            for config_type, values in configurations.items():
                if values:
                    formatted_name = config_type.replace('_', ' ').title()
                    value_str = ", ".join(values)
                    console.print(f"  [cyan]{formatted_name}:[/cyan] {value_str}")
                else:
                    formatted_name = config_type.replace('_', ' ').title()
                    console.print(f"  [dim]{formatted_name}: No data available[/dim]")
    
    asyncio.run(_list_config())


@app.command()
def download(
    date: str = typer.Argument(..., help="Forecast date (YYYYMMDD format)"),
    forecast_time: str = typer.Option("12z", "--time", "-t", help="Forecast time (12z, 18z, etc.)"),
    model: str = typer.Option("ifs", "--model", "-m", help="Model (ifs, aifs-single)"),
    resolution: str = typer.Option("0p25", "--resolution", "-r", help="Resolution (0p25, 0p4)"),
    data_type: str = typer.Option("oper", "--type", help="Data type (oper, enfo, waef, wave)"),
    pattern: Optional[str] = typer.Option(None, "--pattern", "-p", help="File pattern to match (regex)"),
    output_dir: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory"),
    max_concurrent: int = typer.Option(5, "--concurrent", "-c", help="Max concurrent downloads"),
    timeout: int = typer.Option(300, "--timeout", help="Timeout in seconds"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be downloaded without downloading")
):
    """Download ECMWF forecast data for a specific date and configuration."""
    config = DownloadConfig(max_concurrent_downloads=max_concurrent, timeout_seconds=timeout)
    if output_dir:
        config.output_dir = output_dir
    
    async def _download():
        async with ECMWFDownloader(config) as downloader:
            console.print(f"[bold]Fetching file list for {date}/{forecast_time}/{model}/{resolution}/{data_type}...[/bold]")
            files = await downloader.list_available_files(date, forecast_time, model, resolution, data_type)
            
            if not files:
                console.print(f"[yellow]No files found for: {date}/{forecast_time}/{model}/{resolution}/{data_type}[/yellow]")
                console.print("[dim]Try using 'list-config' to see available configurations.[/dim]")
                return
            
            # Filter files by pattern if provided
            if pattern:
                regex = re.compile(pattern, re.IGNORECASE)
                files = [f for f in files if regex.search(f['filename'])]
                console.print(f"[dim]Filtered to {len(files)} files matching pattern: {pattern}[/dim]")
            
            if not files:
                console.print("[yellow]No files match the specified pattern.[/yellow]")
                return
            
            display_files_table(files)
            
            if dry_run:
                console.print(f"\n[yellow]Dry run: Would download {len(files)} files to {config.output_dir}[/yellow]")
                return
            
            # Confirm download
            if not typer.confirm(f"\nDownload {len(files)} files to {config.output_dir}?"):
                console.print("[yellow]Download cancelled.[/yellow]")
                return
            
            console.print(f"\n[bold]Starting download of {len(files)} files...[/bold]")
            results = await downloader.download_files(files, max_concurrent)
            
            console.print(f"\n[bold]Download completed![/bold]")
            console.print(f"[green]✓ Success: {results['success']} files[/green]")
            if results['failed'] > 0:
                console.print(f"[red]✗ Failed: {results['failed']} files[/red]")
    
    asyncio.run(_download())


@app.command()
def bulk_download(
    start_date: str = typer.Argument(..., help="Start date (YYYYMMDD format)"),
    end_date: str = typer.Argument(..., help="End date (YYYYMMDD format)"),
    pattern: Optional[str] = typer.Option(None, "--pattern", "-p", help="File pattern to match (regex)"),
    output_dir: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory"),
    max_concurrent: int = typer.Option(3, "--concurrent", "-c", help="Max concurrent downloads"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be downloaded without downloading")
):
    """Download ECMWF data for a date range."""
    config = DownloadConfig(max_concurrent_downloads=max_concurrent)
    if output_dir:
        config.output_dir = output_dir
    
    # Validate date range
    try:
        start_dt = datetime.strptime(start_date, VALID_DATE_FORMAT)
        end_dt = datetime.strptime(end_date, VALID_DATE_FORMAT)
        if start_dt > end_dt:
            console.print("[red]Error: Start date must be before end date.[/red]")
            raise typer.Exit(1)
    except ValueError:
        console.print("[red]Error: Invalid date format. Use YYYYMMDD.[/red]")
        raise typer.Exit(1)
    
    # Generate date range
    date_range = []
    current_date = start_dt
    while current_date <= end_dt:
        date_range.append(current_date.strftime(VALID_DATE_FORMAT))
        current_date += timedelta(days=1)
    
    console.print(f"[bold]Processing {len(date_range)} dates from {start_date} to {end_date}[/bold]")
    
    async def _bulk_download():
        total_files = 0
        total_success = 0
        total_failed = 0
        
        async with ECMWFDownloader(config) as downloader:
            for date in date_range:
                console.print(f"\n[bold cyan]Processing date: {date}[/bold cyan]")
                files = await downloader.list_available_files(date)
                
                if pattern:
                    regex = re.compile(pattern, re.IGNORECASE)
                    files = [f for f in files if regex.search(f['filename'])]
                
                if not files:
                    console.print(f"[yellow]No files found for {date}[/yellow]")
                    continue
                
                total_files += len(files)
                console.print(f"Found {len(files)} files for {date}")
                
                if dry_run:
                    display_files_table(files[:5])  # Show first 5 files
                    if len(files) > 5:
                        console.print(f"[dim]... and {len(files) - 5} more files[/dim]")
                    continue
                
                results = await downloader.download_files(files, max_concurrent)
                total_success += results['success']
                total_failed += results['failed']
        
        console.print(f"\n[bold]Bulk download summary:[/bold]")
        console.print(f"Total files processed: {total_files}")
        if not dry_run:
            console.print(f"[green]✓ Successfully downloaded: {total_success}[/green]")
            if total_failed > 0:
                console.print(f"[red]✗ Failed downloads: {total_failed}[/red]")
        else:
            console.print(f"[yellow]Dry run: Would download {total_files} files[/yellow]")
    
    asyncio.run(_bulk_download())


@app.command()
def config(
    show: bool = typer.Option(False, "--show", help="Show current configuration"),
    base_url: Optional[str] = typer.Option(None, "--base-url", help="Set base URL"),
    output_dir: Optional[Path] = typer.Option(None, "--output-dir", help="Set default output directory"),
    timeout: Optional[int] = typer.Option(None, "--timeout", help="Set default timeout"),
    concurrent: Optional[int] = typer.Option(None, "--concurrent", help="Set default concurrent downloads")
):
    """Configure ECMWF downloader settings."""
    config_file = Path.home() / ".ecmwf_downloader_config.json"
    
    if show:
        if config_file.exists():
            import json
            with open(config_file) as f:
                config_data = json.load(f)
            console.print("[bold]Current configuration:[/bold]")
            for key, value in config_data.items():
                console.print(f"  {key}: {value}")
        else:
            console.print("[yellow]No configuration file found. Using defaults.[/yellow]")
        return
    
    # Update configuration
    config_data = {}
    if config_file.exists():
        import json
        with open(config_file) as f:
            config_data = json.load(f)
    
    if base_url:
        config_data['base_url'] = base_url
    if output_dir:
        config_data['output_dir'] = str(output_dir)
    if timeout:
        config_data['timeout_seconds'] = timeout
    if concurrent:
        config_data['max_concurrent_downloads'] = concurrent
    
    if config_data:
        import json
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
        console.print(f"[green]Configuration saved to {config_file}[/green]")
    else:
        console.print("[yellow]No configuration changes specified.[/yellow]")


def main():
    """Entry point for the CLI application."""
    app()


if __name__ == "__main__":
    main()
