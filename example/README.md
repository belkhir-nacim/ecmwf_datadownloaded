# AIFS-Single Download Tutorial

This tutorial demonstrates how to download the most recent files from the **AIFS-Single** (Artificial Intelligence Forecasting System) dataset using the ECMWF Data Downloader.

## What is AIFS-Single?

AIFS-Single is ECMWF's cutting-edge AI-based weather forecasting model that represents a major breakthrough in numerical weather prediction. Key features:

- **🤖 AI-Powered**: Uses machine learning instead of traditional numerical methods
- **🌍 Global Coverage**: Provides worldwide weather forecasts
- **⚡ High Performance**: Significantly faster than traditional models
- **🎯 High Resolution**: 0.25° resolution (~25km grid spacing)
- **📊 Competitive Accuracy**: Matches or exceeds traditional forecasting models

## Prerequisites

Make sure you have the ECMWF Data Downloader installed and configured:

```bash
# Install dependencies
pip install -r requirements.txt

# Or using the project
pip install -e .
```

## Running the Tutorial

### Interactive Mode

Run the tutorial script directly:

```bash
cd example
python aifs_single_tutorial.py
```

This will present you with a menu:

```
🚀 AIFS-Single Download Tutorial
AIFS-Single is ECMWF's AI-based global weather forecasting model

Available options:
1. Show available files information
2. Download latest surface analysis (0-hour forecast)
3. Download short-range forecast (0-48 hours)
4. Run all examples

Enter your choice (1-4):
```

### Command Line Usage

You can also use the main CLI tool directly:

#### List available AIFS-Single files

```bash
# List files for today
python ../main.py list-files $(date +%Y%m%d) --model aifs-single

# List files for a specific date
python ../main.py list-files 20240117 --model aifs-single --time 12z
```

#### Download AIFS-Single data

```bash
# Download all files for today
python ../main.py download $(date +%Y%m%d) --model aifs-single

# Download specific forecast hours
python ../main.py download 20240117 --model aifs-single --pattern ".*-[0-9]h-.*"

# Download with custom settings
python ../main.py download $(date +%Y%m%d) \
    --model aifs-single \
    --time 12z \
    --resolution 0p25 \
    --output ./my_aifs_data \
    --concurrent 5
```

## Tutorial Examples

### 1. Show Available Files Information

This example shows you what AIFS-Single data is available without downloading anything:

- **Purpose**: Explore available data, file sizes, and forecast hours
- **Output**: Displays file information, total size, and available forecast hours
- **Duration**: ~10-30 seconds

### 2. Download Latest Surface Analysis

Downloads the current weather analysis (0-hour forecast):

- **Purpose**: Get the most recent weather conditions
- **Files**: 0-hour forecast files only
- **Size**: Typically 50-200 MB
- **Use Case**: Current weather state, model initialization

### 3. Download Short-Range Forecast

Downloads forecasts for the next 48 hours:

- **Purpose**: Get short-term weather predictions
- **Files**: 0, 6, 12, 24, and 48-hour forecasts
- **Size**: Typically 250-1000 MB
- **Use Case**: Weather planning, short-term predictions

### 4. Run All Examples

Combines all the above examples in sequence.

## File Structure

Downloaded files are organized as follows:

```
tutorial_downloads/aifs_single/
└── YYYYMMDD/                    # Date folder
    ├── YYYYMMDDHHMM00-0h-oper-fc.grib2   # Current analysis
    ├── YYYYMMDDHHMM00-6h-oper-fc.grib2   # 6-hour forecast
    ├── YYYYMMDDHHMM00-12h-oper-fc.grib2  # 12-hour forecast
    ├── YYYYMMDDHHMM00-24h-oper-fc.grib2  # 24-hour forecast
    └── YYYYMMDDHHMM00-48h-oper-fc.grib2  # 48-hour forecast
```

## Understanding the File Names

AIFS-Single files follow this naming convention:

```
YYYYMMDDHHMM00-{FH}h-oper-fc.grib2
```

Where:
- `YYYYMMDDHHMM00`: Date and time of forecast initialization
- `{FH}h`: Forecast hour (0, 6, 12, 24, 48, etc.)
- `oper`: Operational forecast (not experimental)
- `fc`: Forecast data
- `.grib2`: GRIB2 format (meteorological data format)

## Data Formats

AIFS-Single data is provided in **GRIB2** format, which is the standard for meteorological data. To work with these files, you can use:

- **Python**: `pygrib`, `xarray`, `cfgrib`
- **Command line**: `grib_ls`, `grib_get` (ECCODES tools)
- **GUI**: Panoply, NCEP GRIB2 Decoder

## Tips and Best Practices

1. **Check availability first**: Use option 1 to see what's available before downloading
2. **Start small**: Begin with surface analysis (option 2) before downloading larger datasets
3. **Monitor disk space**: AIFS-Single files can be large (100-500 MB each)
4. **Use concurrent downloads**: The tool supports multiple simultaneous downloads
5. **Regular updates**: AIFS-Single data is typically available 2-4 times per day

## Common Issues

- **No data found**: AIFS-Single is relatively new; data may not be available for all dates
- **Slow downloads**: Large files may take time; consider using fewer concurrent downloads
- **Network errors**: Temporary ECMWF server issues; try again later

## Next Steps

After downloading AIFS-Single data, you might want to:

1. **Visualize the data**: Use tools like Matplotlib, Cartopy, or specialized weather visualization software
2. **Compare with observations**: Validate the AI model's performance
3. **Analyze forecast skill**: Compare different forecast hours
4. **Extract specific variables**: Focus on temperature, precipitation, wind, etc.

## Support

For issues with this tutorial:
- Check the main project documentation
- Review the CLI help: `python ../main.py --help`
- Check ECMWF's data availability status

For AIFS-Single model questions:
- Visit [ECMWF's AIFS documentation](https://www.ecmwf.int/en/research/projects/aifs)
- Check the [ECMWF Data Store](https://data.ecmwf.int/) 