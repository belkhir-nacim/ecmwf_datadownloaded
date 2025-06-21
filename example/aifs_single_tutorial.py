#!/usr/bin/env python3
"""
AIFS-Single Download Tutorial

This tutorial demonstrates how to download the most recent files from the AIFS-Single 
(Artificial Intelligence Forecasting System) dataset using the ECMWF Data Downloader.

AIFS-Single is ECMWF's new AI-based weather forecasting model that provides 
high-resolution global weather predictions.
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add the parent directory to Python path to import main module
sys.path.append(str(Path(__file__).parent.parent))

from main import ECMWFDownloader, DownloadConfig, console


async def find_most_recent_aifs_data():
    """Find the most recent available AIFS-Single data."""
    config = DownloadConfig(
        output_dir=Path("./tutorial_downloads/aifs_single"),
        max_concurrent_downloads=3,
        timeout_seconds=300
    )
    
    async with ECMWFDownloader(config) as downloader:
        console.print("[bold blue]🔍 Searching for most recent AIFS-Single data...[/bold blue]")
        
        # Check the last 5 days for available data
        for days_back in range(5):
            date = (datetime.now() - timedelta(days=days_back)).strftime("%Y%m%d")
            console.print(f"[dim]Checking date: {date}[/dim]")
            
            # Try different forecast times (12z is typically available first)
            for forecast_time in ["12z", "00z"]:
                files = await downloader.list_available_files(
                    date=date,
                    forecast_time=forecast_time,
                    model="aifs-single",  # This is the AI model
                    resolution="0p25",    # 0.25 degree resolution (~25km)
                    data_type="oper"      # Operational forecast
                )
                
                if files:
                    console.print(f"[green]✓ Found {len(files)} files for {date} {forecast_time}[/green]")
                    return date, forecast_time, files
                else:
                    console.print(f"[dim]No files found for {date} {forecast_time}[/dim]")
        
        console.print("[red]❌ No recent AIFS-Single data found in the last 5 days[/red]")
        return None, None, []


async def download_specific_forecast_hours(date: str, forecast_time: str, files: list, 
                                          forecast_hours: list = None):
    """Download files for specific forecast hours."""
    if forecast_hours is None:
        forecast_hours = ["0", "6", "12", "24", "48"]  # Common forecast hours
    
    config = DownloadConfig(
        output_dir=Path("./tutorial_downloads/aifs_single"),
        max_concurrent_downloads=3,
        timeout_seconds=300
    )
    
    # Filter files by forecast hours
    selected_files = []
    for file_info in files:
        if file_info['forecast_hour'] in forecast_hours:
            selected_files.append(file_info)
    
    if not selected_files:
        console.print(f"[yellow]No files found for forecast hours: {forecast_hours}[/yellow]")
        return
    
    console.print(f"[blue]📥 Downloading {len(selected_files)} files for forecast hours: {', '.join(forecast_hours)}[/blue]")
    
    async with ECMWFDownloader(config) as downloader:
        results = await downloader.download_files(selected_files)
        
        if results['success'] > 0:
            console.print(f"[green]✅ Successfully downloaded {results['success']} files[/green]")
            console.print(f"[dim]Files saved to: {config.output_dir / date}[/dim]")
        
        if results['failed'] > 0:
            console.print(f"[red]❌ Failed to download {results['failed']} files[/red]")


async def download_latest_surface_analysis():
    """Download the latest surface analysis (0-hour forecast) from AIFS-Single."""
    console.print("[bold green]🌍 Downloading Latest AIFS-Single Surface Analysis[/bold green]")
    
    date, forecast_time, files = await find_most_recent_aifs_data()
    
    if not files:
        return
    
    # Filter for 0-hour forecast (current analysis)
    surface_files = [f for f in files if f['forecast_hour'] == '0']
    
    if surface_files:
        console.print(f"[blue]Found {len(surface_files)} surface analysis files[/blue]")
        await download_specific_forecast_hours(date, forecast_time, surface_files, ["0"])
    else:
        console.print("[yellow]No surface analysis files (0-hour forecast) found[/yellow]")


async def download_short_range_forecast():
    """Download short-range forecast (0-48 hours) from AIFS-Single."""
    console.print("[bold green]🌤️  Downloading AIFS-Single Short-Range Forecast[/bold green]")
    
    date, forecast_time, files = await find_most_recent_aifs_data()
    
    if not files:
        return
    
    # Download forecasts for 0, 6, 12, 24, and 48 hours
    forecast_hours = ["0", "6", "12", "24", "48"]
    await download_specific_forecast_hours(date, forecast_time, files, forecast_hours)


async def show_available_files_info():
    """Display information about available AIFS-Single files."""
    console.print("[bold blue]📊 AIFS-Single File Information[/bold blue]")
    
    date, forecast_time, files = await find_most_recent_aifs_data()
    
    if not files:
        return
    
    # Group files by forecast hour
    forecast_hours = {}
    total_size = 0
    
    for file_info in files:
        hour = file_info['forecast_hour']
        if hour not in forecast_hours:
            forecast_hours[hour] = []
        forecast_hours[hour].append(file_info)
        total_size += file_info['raw_size']
    
    console.print(f"\n[green]📅 Date: {date} {forecast_time}[/green]")
    console.print(f"[green]🤖 Model: AIFS-Single (AI Forecasting System)[/green]")
    console.print(f"[green]🌐 Resolution: 0.25° (~25km)[/green]")
    console.print(f"[green]📦 Total files: {len(files)}[/green]")
    console.print(f"[green]💾 Total size: {_format_file_size(total_size)}[/green]")
    
    console.print("\n[bold]Available forecast hours:[/bold]")
    for hour in sorted(forecast_hours.keys(), key=lambda x: int(x) if x.isdigit() else 999):
        file_count = len(forecast_hours[hour])
        hour_size = sum(f['raw_size'] for f in forecast_hours[hour])
        console.print(f"  {hour}h: {file_count} files ({_format_file_size(hour_size)})")


def _format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


async def main():
    """Main tutorial function."""
    console.print("[bold magenta]🚀 AIFS-Single Download Tutorial[/bold magenta]")
    console.print("[dim]AIFS-Single is ECMWF's AI-based global weather forecasting model[/dim]\n")
    
    # Show menu options
    console.print("[bold]Available options:[/bold]")
    console.print("1. Show available files information")
    console.print("2. Download latest surface analysis (0-hour forecast)")
    console.print("3. Download short-range forecast (0-48 hours)")
    console.print("4. Run all examples")
    
    try:
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            await show_available_files_info()
        elif choice == "2":
            await download_latest_surface_analysis()
        elif choice == "3":
            await download_short_range_forecast()
        elif choice == "4":
            await show_available_files_info()
            await download_latest_surface_analysis()
            await download_short_range_forecast()
        else:
            console.print("[red]Invalid choice. Please run the script again.[/red]")
            return
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Tutorial interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"[red]An error occurred: {e}[/red]")


if __name__ == "__main__":
    # Run the tutorial
    asyncio.run(main()) 