
![MMEarth-logo](https://github.com/vishalned/MMEarth-data/assets/27778126/09675b82-ff9e-43be-9160-3267b948e941)





# MMEarth - Data Downloading
[![Project Website](https://img.shields.io/badge/Project%20Website-8A2BE2)](https://vishalned.github.io/mmearth)
[![Paper](https://img.shields.io/badge/arXiv-2405.02771-blue)](https://arxiv.org/abs/2405.02771)
[![Code - Models](https://img.shields.io/badge/Code%20--%20Model-darkgreen)](https://github.com/vishalned/MMEarth-train/tree/main)


This repository contains scripts to download the data presented in the paper [MMEarth: Exploring Multi-Modal Pretext Tasks For Geospatial Representation Learning](https://arxiv.org/abs/2405.02771). The scripts are used  to download large scale satellite data from different sensors and satellites (Sentinel-2, Sentinel-1, ERA5 - temperature & precipitation, Aster GDEM etc) which we call modalities. The data is downloaded from [Google Earth Engine](https://earthengine.google.com/).

## 📢 Latest Updates
:fire::fire::fire: Last Updated on 2024.11.07 :fire::fire::fire:
- Dataset is now available on [TorchGeo](https://torchgeo.readthedocs.io/en/latest/api/datasets.html).
- **Paper accepted to ECCV 2024 !!**
- Updated datasets to version v001.
    - Dataset fix: Removed duplicates and corrected ERA5 yearly statistics.
- Fixed downloading scripts.


## Table of contents
1. [Data Download](https://github.com/vishalned/MMEarth-data?tab=readme-ov-file#data-download)
2. [Data Loading](https://github.com/vishalned/MMEarth-data?tab=readme-ov-file#data-loading)
3. [Getting Started](https://github.com/vishalned/MMEarth-data?tab=readme-ov-file#getting-started)
4. [Data Stacks](https://github.com/vishalned/MMEarth-data?tab=readme-ov-file#data-stacks)
5. [Code Structure](https://github.com/vishalned/MMEarth-data?tab=readme-ov-file#code-structure)
6. [Slurm Execution](https://github.com/vishalned/MMEarth-data?tab=readme-ov-file#slurm-execution)
7. [Citation](https://github.com/vishalned/MMEarth-data?tab=readme-ov-file#citation)

## Data Download
The MMEarth data can be downloaded using the following links. To enable more easier development with Multi-Modal data, we also provide 2 more "taster" datasets along with the original MMEarth data. The license for the data is [CC BY 4.0](https://github.com/vishalned/MMEarth-data/blob/main/LICENSE-data). 

:bangbang:  **UPDATE: The new Version 001 data is ready to download.** 

| **Dataset** | **Image Size** | **Number of Tiles** | **Dataset size** | **Data Link** | **Bash Script** |
| :---: | :---: | :---: | :---: | :---: | :---: |
| MMEarth | 128x128 | 1.2M | 597GB | [download](https://sid.erda.dk/sharelink/ChL1BoVEyH) | [bash](https://github.com/vishalned/MMEarth-data/blob/main/bash_scripts/data_1M_128.sh)|
| MMEarth64 | 64x64 | 1.2M | 152GB | [download](https://sid.erda.dk/sharelink/bX5JzPuwJF) | [bash](https://github.com/vishalned/MMEarth-data/blob/main/bash_scripts/data_1M_64.sh)|
| MMEarth100k | 128x128 | 100k | 48GB | [download](https://sid.erda.dk/sharelink/CoaUojVXzu) | [bash](https://github.com/vishalned/MMEarth-data/blob/main/bash_scripts/data_100k_128.sh)|

All 3 dataset have a similar structure as below:

    .
    ├── data_1M_v001/                      # root data directory
    │   ├── data_1M_v001.h5                # h5 file containing the data
    │   ├── data_1M_v001_band_stats.json   # json file containing information about the bands present in the h5 file for each data stack
    │   ├── data_1M_v001_splits.json       # json file containing information for train, val, test splits
    │   └── data_1M_v001_tile_info.json    # json file containing additional meta information of each tile that was downloaded. 
  

## Data Loading
A sample Jupyter Notebook that shows an example to load the data using pytorch is [here](https://github.com/vishalned/MMEarth-train/blob/main/examples/data_loader_example.ipynb). Alternatively, the dataloader has also been added to [TorchGeo](https://torchgeo.readthedocs.io/en/latest/api/datasets.html).

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
- [Sentinel-2](https://developers.google.com/earth-engine/datasets/catalog/sentinel-2)
- [Sentinel-1](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S1_GRD)
- [ERA5 (Temperature and precipitation)](https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_MONTHLY_AGGR)
- [Aster GDEM (Elevation and Slope)](https://gee-community-catalog.org/projects/aster/)
- [Dynamic world (LULC)](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1)
- [Canopy Height](https://gee-community-catalog.org/projects/canopy/)
- [ESA WorldCover](https://developers.google.com/earth-engine/datasets/catalog/ESA_WorldCover_v100)

  

## Code Structure
The data downloading happens only when you have a geojson file with all the tiles you want to download. Here tiles represent ROI (or polygons) for each location that you want. Once you have the tiles, the data stacks (data for each modality) are downloaded for each tile in the geojson. The data can be downloaded by following this broad structure, and each of these points are further explained below:
* creating tiles (small ROIs sampled globally)
* download data stacks for each of the tiles
* post processing of the downloaded data
* redownload (if needed)

#### Creating Tiles
- `create_tiles_polygon.py` is the file used to create the tiles. The corresponding config is `config/config_tiles.yaml`.  For a global sample, the various sampling techniques are based on the biomes and ecoregions from the [RESOLVE ECOREGIONS](https://developers.google.com/earth-engine/datasets/catalog/RESOLVE_ECOREGIONS_2017).
- In the config you can set the size of the tile in meters along with the number of tiles to download and the sampling method (how to sample the tiles in a region).

#### Downloading Data Stacks 
- `main_download.py` is the main script to download the data. The corresponding config is `config/config_data.yaml`. The config file contains various parameter to be set regarding the different modalities, and paths. Based on the geojson file created from the above step, this file downloads the data stacks for each tile.
- The `ee_utils/ee_data.py` file contains custom functions for retrieving each modality in the data stack from GEE. It merges all these modalities into one array, and export it as a GeoTIFF file. The band information and other tile information is stored in a json file (`tile_info.json`).

#### Post Processing
- The `post_download.py` file performs 4 operations sequentially:
  - Mergining multiple `tile_info.json` files (these files are created when parallely downloading using slurm - explained more below)
  - Converting the GeoTIFFs to single hdf5 file.
  - Obtaining statistics for each band. (used for normalization purposes)
  - Computing the splits (train, val splits - only if needed).
 

#### Redownload
- `redownload.py` is the file that can be used to redownload any tiles that failed to download. Sometimes when downloading the data stacks, the script can skip tiles due to various reasons (lack of sentinel-2 reference image, network issues, GEE issues). Hence if needed, we have an option to redownload these tile. (An alternative is to just download more tiles than needed).


(**NOTE**: The files are executed by making use of SLURM. More information on this is provided in the [Slurm Execution](https://github.com/vishalned/MMEarth-data?tab=readme-ov-file#slurm-execution) section)

## Slurm Execution

<img width="815" alt="MMEarth-data" src="https://github.com/vishalned/MMEarth-data/assets/27778126/02764bda-7384-4359-bdae-01c4456239a0">


**Downloading Data Stacks:** GEE provides a function called `getDownloadUrl()` that allows you to export images as GeoTIFF files. We extend this by merging all modalities for a single location into one image, and export this as a single GeoTIFF file. To further speed up the data downloading, we make use of parallel processing using SLURM. The above figures give an idea of how this is done. The tile information (tile GeoJSON) contains location information and more about N tiles we need to download. N/40 tiles are downloaded by 40 slurm jobs (we set the max jobs as 40 since this is the maximum number of concurrent requests by the GEE API). 
  
To run the slurm parallel download, execute the following command
```sh
sbatch slurm_scripts/slurm_download_parallel.sh
```


## Citation 
Please cite our paper if you use this code or any of the provided data.

Vishal Nedungadi, Ankit Kariryaa, Stefan Oehmcke, Serge Belongie, Christian Igel, & Nico Lang (2024). MMEarth: Exploring Multi-Modal Pretext Tasks For Geospatial Representation Learning.
```
@misc{nedungadi2024mmearth,
      title={MMEarth: Exploring Multi-Modal Pretext Tasks For Geospatial Representation Learning},
      author={Vishal Nedungadi and Ankit Kariryaa and Stefan Oehmcke and Serge Belongie and Christian Igel and Nico Lang},
      year={2024},
      eprint={2405.02771},
      archivePrefix={arXiv},
      primaryClass={cs.CV}
}
```









  


