#!/bin/bash

# URLs of the files to download
file_urls=(
    "https://sid.erda.dk/share_redirect/ChL1BoVEyH/data_1M_v001_band_stats.json"
    "https://sid.erda.dk/share_redirect/ChL1BoVEyH/data_1M_v001_tile_info.json"
    "https://sid.erda.dk/share_redirect/ChL1BoVEyH/data_1M_v001_splits.json"
    "https://sid.erda.dk/share_redirect/ChL1BoVEyH/data_1M_v001.h5"
    "https://sid.erda.dk/share_redirect/ChL1BoVEyH/LICENSE-data"
)

# Destination folder to save the downloaded files
destination_folder="./data_1M_v001/"

# Create the destination folder if it doesn't exist
mkdir -p "$destination_folder"

# Loop through each URL and download the corresponding file
for url in "${file_urls[@]}"; do
    # Extract filename from URL
    filename=$(basename "$url")
    # Download the file using curl
    curl -o "${destination_folder}${filename}" "$url"
    # Check if the download was successful
    if [ $? -eq 0 ]; then
        echo "File '${filename}' downloaded successfully."
    else
        echo "Failed to download the file '${filename}'."
    fi
done

