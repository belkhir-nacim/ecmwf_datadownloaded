#!/bin/bash

# AIFS-Single CLI Examples
# This script demonstrates how to use the ECMWF Data Downloader CLI
# to download AIFS-Single (AI forecasting) data

set -e  # Exit on any error

echo "🚀 AIFS-Single CLI Examples"
echo "=================================="
echo ""

# Get today's date in YYYYMMDD format
TODAY=$(date +%Y%m%d)
YESTERDAY=$(date -d "yesterday" +%Y%m%d)

echo "📅 Using dates:"
echo "  Today: $TODAY"
echo "  Yesterday: $YESTERDAY"
echo ""

# Navigate to the parent directory where main.py is located
cd "$(dirname "$0")/.."

echo "1️⃣  Listing available AIFS-Single files for today..."
echo "Command: python main.py list-files $TODAY --model aifs-single --time 12z"
echo ""

python main.py list-files "$TODAY" --model aifs-single --time 12z || {
    echo "⚠️  No data found for today, trying yesterday..."
    python main.py list-files "$YESTERDAY" --model aifs-single --time 12z || {
        echo "❌ No AIFS-Single data found for recent dates"
        echo "💡 AIFS-Single is a newer model - data may not always be available"
        echo ""
    }
}

echo ""
echo "2️⃣  Checking what configurations are available..."
echo "Command: python main.py list-config $TODAY"
echo ""

python main.py list-config "$TODAY" || {
    echo "⚠️  Trying yesterday..."
    python main.py list-config "$YESTERDAY" || {
        echo "❌ No configuration data found"
    }
}

echo ""
echo "3️⃣  Dry run - Show what would be downloaded (no actual download)..."
echo "Command: python main.py download $TODAY --model aifs-single --dry-run --pattern '.*-[0-6]h-.*'"
echo ""

python main.py download "$TODAY" --model aifs-single --dry-run --pattern '.*-[0-6]h-.*' || {
    echo "⚠️  Trying yesterday..."
    python main.py download "$YESTERDAY" --model aifs-single --dry-run --pattern '.*-[0-6]h-.*' || {
        echo "❌ No data available for dry run"
    }
}

echo ""
echo "4️⃣  Download surface analysis only (0-hour forecast)..."
echo "Command: python main.py download $TODAY --model aifs-single --pattern '.*-0h-.*' --output ./example_downloads/surface"
echo ""

read -p "🤔 Do you want to download the surface analysis? (y/N): " -r
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python main.py download "$TODAY" --model aifs-single --pattern '.*-0h-.*' --output ./example_downloads/surface || {
        echo "⚠️  Trying yesterday..."
        python main.py download "$YESTERDAY" --model aifs-single --pattern '.*-0h-.*' --output ./example_downloads/surface || {
            echo "❌ Download failed - no data available"
        }
    }
else
    echo "⏭️  Skipping download"
fi

echo ""
echo "5️⃣  Advanced: Download short-range forecast with custom settings..."
echo "Command: python main.py download $TODAY --model aifs-single --pattern '.*-[0-9]h-.*' --concurrent 3 --output ./example_downloads/forecast --timeout 180"
echo ""

read -p "🤔 Do you want to download short-range forecasts? (y/N): " -r
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "⚠️  This will download multiple large files..."
    python main.py download "$TODAY" --model aifs-single --pattern '.*-[0-9]h-.*' --concurrent 3 --output ./example_downloads/forecast --timeout 180 || {
        echo "⚠️  Trying yesterday..."
        python main.py download "$YESTERDAY" --model aifs-single --pattern '.*-[0-9]h-.*' --concurrent 3 --output ./example_downloads/forecast --timeout 180 || {
            echo "❌ Download failed - no data available"
        }
    }
else
    echo "⏭️  Skipping download"
fi

echo ""
echo "6️⃣  Bulk download for date range (careful - can be large!)..."
echo "This example shows how to download data for multiple days"
echo ""

# Calculate a 3-day range ending yesterday
START_DATE=$(date -d "3 days ago" +%Y%m%d)
END_DATE="$YESTERDAY"

echo "Command: python main.py bulk-download $START_DATE $END_DATE --pattern '.*aifs.*-0h-.*' --dry-run"
echo "Date range: $START_DATE to $END_DATE (surface analysis only)"
echo ""

read -p "🤔 Do you want to see what bulk download would get? (y/N): " -r
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python main.py bulk-download "$START_DATE" "$END_DATE" --pattern '.*aifs.*-0h-.*' --dry-run || {
        echo "❌ Bulk download preview failed"
    }
else
    echo "⏭️  Skipping bulk download preview"
fi

echo ""
echo "✅ CLI Examples Complete!"
echo ""
echo "📚 Additional Commands:"
echo "  • Get help: python main.py --help"
echo "  • Command-specific help: python main.py download --help"
echo "  • List available dates: python main.py list-dates --days 14"
echo "  • Check configuration: python main.py config --show"
echo ""
echo "💡 Tips:"
echo "  • Always do a dry run first with --dry-run"
echo "  • Use patterns to filter specific files (e.g., --pattern '.*-[0-6]h-.*' for 0-6 hour forecasts)"
echo "  • Monitor disk space - GRIB2 files can be 100-500 MB each"
echo "  • AIFS-Single data may not be available for all dates (it's a newer model)"
echo ""
echo "📁 Downloaded files (if any) are in:"
echo "  • ./example_downloads/surface/ (surface analysis)"
echo "  • ./example_downloads/forecast/ (multi-hour forecasts)" 