# MMEarth - Data Downloading
This repository contains scripts to download large scale satellite data from different sensors and satellites (sentinel-2, sentinel-1, temperature, precipitation etc) which we call modalities..

## Table of contents

## Getting Started
To get started with this repository, you can install the dependencies and packages with this command 

```sh
pip install -r requirements.txt
```

Once this is done, you need to setup gcloud and earthengine to make the code work. Follow the below steps:
- Earthengine requires the initialization of gcloud, so install gcloud by following the instructions from [here](https://cloud.google.com/sdk/docs/install).
- Setting up earthengine on your local machine: To setup earthengine on your local machine run `earthengine authenticate`.
- Setting up earthengine on a remote cluster: Many times `earthengine authenticate` doesnt directly work since you will get multiple links to click, and these links
  wouldnt work when opening them from the browser on your local machine. Hence run this command `earthengine authenticate --quiet`. Follow the instructions on your terminal
  and everything should work. An additional step is to add the project name in every file that has `earthengine.initialize(project = '$PROJECT_NAME')`.

## Data Stacks
This repository allows downloading data from various sensors. Currently the code is written to download the following sensors/modalities:
- Sentinel 2
- Sentinel 1
- ERA5 (Temperature and precipitation)
- Aster DEM (Elevation and Slope)
- Dynamic world (LULC)
- Canopy Height
  

## Code Structure
The data downloading happens only when you have a geojson file with all the tiles you want to download. Here tiles represent ROI (or polygons) for each location that you want. 
Once you have the tiles, the data stacks (data for each modality) are downloaded for each tile in the geojson. 
- `create_tiles_polygon.py` is the file used to create the tiles. The corresponding config is `config/config_tiles.yaml`. In the config you can set the size of the tile in meters along with the number of tiles to download and the sampling method (how to sample the tiles in a region). Note: the various sampling techniques are based on the biomes and ecoregions from the
  [RESOLVE ECOREGIONS](https://developers.google.com/earth-engine/datasets/catalog/RESOLVE_ECOREGIONS_2017).
- `main_download.py` is the main script to download the data. The corresponding config is `config/config_data.yaml`. The config file contains various parameter to be set regarding the different modalities, and paths. Based on the geojson file created from the above step, this file downloads the data stacks for each tile. The `ee_utils/ee_data.py` file contains functions for each modality in the data stack.
- `post_download.py` is the file that contains scripts to be executed after downloading the data stacks. This script does 3 things (optional). First it merges all the tile information (explained more below), then it converts the data stacks into a h5 file, then computes band statistics for each modalities (used for normalization purposes), and finally creates the splits.
- `redownload.py` is the file that can be used to redownload any tiles that failed to download. Sometimes when downloading the data stacks, the script can skip tiles due to various reasons (lack of sentinel-2 reference image, network issues, GEE issues). Hence if needed, we have an option to redownload these tile. (An alternative is to just download more tiles than needed).

  


