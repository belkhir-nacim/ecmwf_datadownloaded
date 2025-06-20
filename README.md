# ECMWF Data Downloader

A powerful CLI tool for downloading ECMWF meteorological forecast data with concurrent downloads, progress tracking, and rich terminal output.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Features

- 🚀 **Fast concurrent downloads** with configurable parallelism
- 📊 **Real-time progress tracking** with beautiful terminal output
- 🗓️ **Date range downloads** for bulk data acquisition
- 🔍 **Pattern matching** to filter specific files
- ⚙️ **Configurable settings** with persistent configuration
- 🛡️ **Robust error handling** with retry mechanisms
- 📁 **Organized output** with date-based directory structure
- 🌐 **Multiple data formats** support (GRIB, NetCDF, Index files)

## Installation

### Using uv (Recommended)

```bash
# Install from PyPI (when published)
uv tool install ecmwf-datadownloaded

# Or install from source
uv tool install git+https://github.com/yourusername/ecmwf-datadownloaded
```

### Using pip

```bash
pip install ecmwf-datadownloaded
```

### Development Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/ecmwf-datadownloaded
cd ecmwf-datadownloaded

# Install with uv
uv sync --all-extras

# Or with pip
pip install -e ".[dev]"
```

## Quick Start

### List Available Dates

```bash
# Show available forecast dates for the last 7 days
ecmwf-download list-dates

# Show last 14 days
ecmwf-download list-dates --days 14
```

### List Available Files

```bash
# List all files for a specific date
ecmwf-download list-files 20250620

# List files with custom output directory
ecmwf-download list-files 20250620 --output ./my_data
```

### Download Data

```bash
# Download all files for a specific date
ecmwf-download download 20250620

# Download with pattern matching (only GRIB files)
ecmwf-download download 20250620 --pattern "*.grib"

# Download with custom settings
ecmwf-download download 20250620 \
  --output ./weather_data \
  --concurrent 10 \
  --timeout 600
```

### Bulk Downloads

```bash
# Download data for a date range
ecmwf-download bulk-download 20250618 20250620

# Bulk download with pattern filtering
ecmwf-download bulk-download 20250618 20250620 \
  --pattern ".*00.*grib" \
  --concurrent 5

# Dry run to see what would be downloaded
ecmwf-download bulk-download 20250618 20250620 --dry-run
```

## Command Reference

### Global Options

- `--help` - Show help message
- `--version` - Show version information

### Commands

#### `list-dates`
List available forecast dates.

```bash
ecmwf-download list-dates [OPTIONS]
```

**Options:**
- `--days`, `-d` INTEGER - Number of days back to show (default: 7)

#### `list-files`
List available files for a specific forecast date.

```bash
ecmwf-download list-files DATE [OPTIONS]
```

**Arguments:**
- `DATE` - Forecast date in YYYYMMDD format

**Options:**
- `--output`, `-o` PATH - Output directory

#### `download`
Download ECMWF forecast data for a specific date.

```bash
ecmwf-download download DATE [OPTIONS]
```

**Arguments:**
- `DATE` - Forecast date in YYYYMMDD format

**Options:**
- `--pattern`, `-p` TEXT - File pattern to match (regex)
- `--output`, `-o` PATH - Output directory
- `--concurrent`, `-c` INTEGER - Max concurrent downloads (default: 5)
- `--timeout`, `-t` INTEGER - Timeout in seconds (default: 300)
- `--dry-run` - Show what would be downloaded without downloading

#### `bulk-download`
Download ECMWF data for a date range.

```bash
ecmwf-download bulk-download START_DATE END_DATE [OPTIONS]
```

**Arguments:**
- `START_DATE` - Start date in YYYYMMDD format
- `END_DATE` - End date in YYYYMMDD format

**Options:**
- `--pattern`, `-p` TEXT - File pattern to match (regex)
- `--output`, `-o` PATH - Output directory
- `--concurrent`, `-c` INTEGER - Max concurrent downloads (default: 3)
- `--dry-run` - Show what would be downloaded without downloading

#### `config`
Configure ECMWF downloader settings.

```bash
ecmwf-download config [OPTIONS]
```

**Options:**
- `--show` - Show current configuration
- `--base-url` TEXT - Set base URL
- `--output-dir` PATH - Set default output directory
- `--timeout` INTEGER - Set default timeout
- `--concurrent` INTEGER - Set default concurrent downloads

## Configuration

The tool supports persistent configuration through a JSON file stored at `~/.ecmwf_downloader_config.json`.

### View Current Configuration

```bash
ecmwf-download config --show
```

### Set Configuration

```bash
# Set default output directory
ecmwf-download config --output-dir ./ecmwf_data

# Set default timeout
ecmwf-download config --timeout 600

# Set default concurrent downloads
ecmwf-download config --concurrent 8
```

## Data Organization

Downloaded files are organized in the following structure:

```
output_directory/
├── 20250618/
│   ├── file1.grib
│   ├── file2.grib
│   └── index.idx
├── 20250619/
│   ├── file1.grib
│   ├── file2.grib
│   └── index.idx
└── 20250620/
    ├── file1.grib
    ├── file2.grib
    └── index.idx
```

## File Types Supported

- **GRIB/GRIB2** (`.grib`, `.grib2`) - Binary meteorological data format
- **NetCDF** (`.nc`, `.netcdf`) - Network Common Data Form
- **Index** (`.idx`) - Index files for data access
- **Other formats** - Automatically detected

## Pattern Matching Examples

Use regular expressions to filter files:

```bash
# Download only GRIB files
--pattern ".*\.grib$"

# Download files containing "00" (00Z forecasts)
--pattern ".*00.*"

# Download temperature data
--pattern ".*[Tt]emp.*"

# Download multiple patterns (temp OR wind)
--pattern ".*(temp|wind).*"
```

## Performance Tips

1. **Concurrent Downloads**: Adjust `--concurrent` based on your network capacity
2. **Timeout Settings**: Increase timeout for large files or slow connections
3. **Pattern Filtering**: Use specific patterns to avoid downloading unnecessary files
4. **Dry Run**: Always test with `--dry-run` first for bulk downloads

## Error Handling

The tool includes robust error handling:

- **Network errors**: Automatic retry with exponential backoff
- **Partial downloads**: Automatic cleanup of incomplete files
- **Invalid dates**: Clear error messages for date format issues
- **Missing files**: Graceful handling when data is not available

## Examples

### Download Recent Forecast Data

```bash
# Get yesterday's forecast
ecmwf-download download $(date -d "1 day ago" +%Y%m%d)

# Download last 3 days of GRIB files
ecmwf-download bulk-download \
  $(date -d "3 days ago" +%Y%m%d) \
  $(date -d "1 day ago" +%Y%m%d) \
  --pattern ".*\.grib$"
```

### Download Specific Model Data

```bash
# Download only 00Z runs
ecmwf-download download 20250620 --pattern ".*00.*"

# Download high-resolution data
ecmwf-download download 20250620 --pattern ".*hres.*"
```

### Automated Downloads

```bash
#!/bin/bash
# Daily download script

DATE=$(date +%Y%m%d)
OUTPUT_DIR="/data/ecmwf"

ecmwf-download download $DATE \
  --output $OUTPUT_DIR \
  --pattern ".*\.grib$" \
  --concurrent 8
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Commit your changes (`git commit -am 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Development

### Setup Development Environment

```bash
# Clone and setup
git clone https://github.com/yourusername/ecmwf-datadownloaded
cd ecmwf-datadownloaded
uv sync --all-extras

# Run tests
uv run pytest

# Format code
uv run black .
uv run ruff check --fix .

# Type checking
uv run mypy .
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=main

# Run specific test
uv run pytest tests/test_downloader.py
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [ECMWF](https://www.ecmwf.int/) for providing free access to meteorological data
- [Typer](https://typer.tiangolo.com/) for the excellent CLI framework
- [Rich](https://rich.readthedocs.io/) for beautiful terminal output
- [aiohttp](https://docs.aiohttp.org/) for async HTTP capabilities

## Support

- 📖 [Documentation](https://github.com/yourusername/ecmwf-datadownloaded#readme)
- 🐛 [Issue Tracker](https://github.com/yourusername/ecmwf-datadownloaded/issues)
- 💬 [Discussions](https://github.com/yourusername/ecmwf-datadownloaded/discussions)

---

**Disclaimer**: This tool is not officially affiliated with ECMWF. Please respect ECMWF's data usage policies and terms of service.
