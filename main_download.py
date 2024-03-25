'''
The main function to download all the data from GEE

'''


import os
import config.ee_init 
import ee
import numpy as np
import geojson
import hydra
from omegaconf import DictConfig, OmegaConf

from ee_utils.ee_data import ee_set
from utils.utils import read_geojson, update_tile_info
import logging
import h5py
import time
import warnings
import json
warnings.filterwarnings("ignore")




@hydra.main(config_path='config', config_name='config_data')
def main(cfg: DictConfig) -> None:
    print(OmegaConf.to_yaml(cfg))


    # setting up the logger. Logs both to the console and to a file inside outputs/ date/ time. This is created by hydra
    numeric_level = getattr(logging, cfg.log.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % cfg.log)
    logging.basicConfig(
                        # filename='log.txt', # comment this line if you want to log to console only
                        level=numeric_level, 
                        format='%(levelname)s : %(message)s',
                        filemode='w'
        )

    # reading the geojson file
    gj = read_geojson(cfg.tiles_path)
    datasets = cfg.datasets
    cfg.update_geojson = True

    # if sentinel2 is in the datasets, then we need to update the geojson file to include the date of the image, crs, and other details.
    # if it is not present, this means that we are downloading other datasets, and hence need to use the geojson data instead of updating
    cfg.update_geojson = 'sentinel2' in datasets
    cfg.read_tile_info = not 'sentinel2' in datasets # if we are downloading things other than s2, we need to read the tile information from the geojson. 

    tile_info_dict = {}
    if cfg.read_tile_info:
        logging.info('Reading tile information from geojson. Please note that any errors with the tiles.geojson, implies that you did not download Sentinel 2 yet. Please download Sentinel 2 first. ')
        tile_info = json.load(open(cfg.tile_info_path, 'r'))
    else:
        tile_info = None

    i = cfg.start_from
    end = min(cfg.end_at, len(gj['features']))
    
    start = time.time()

    while i < end:
        start_ = time.time()
        logging.info(f'####################### Processing tile [{i}/{len(gj["features"])}] #######################')
        tile = gj['features'][i]
        id = tile['properties']['tile_id']
        if cfg.read_tile_info and id not in tile_info.keys():
            # this is not in tile info, hence the s2 has not been downloaded yet. so we skip this tile
            logging.info(f"Tile {id} not in tile_info. Skipping")
            i += 1
            continue
        # creating the ee_set object, the function calls are inside the constructor, hence it will automatically download the data
        if cfg.read_tile_info:
            ee_set_ = ee_set(tile, cfg, tile_info=tile_info[id])
        else:
            ee_set_ = ee_set(tile, cfg) 
        logging.debug(f"Time taken for 1 tile: {time.time() - start_}")
        if cfg.update_geojson and not ee_set_.no_data:
            tile_info_dict[id] = update_tile_info(tile, ee_set_, tile_info[id] if tile_info is not None else None)
            os.makedirs(f"./data/tile_info", exist_ok=True)
            with open(f"./data/tile_info/tile_info_{cfg.start_from}_{cfg.end_at}.json", 'w') as f:
                geojson.dump(tile_info_dict, f)
        elif ee_set_.no_data:
            logging.info(f"no sentinel2 data for this tile. Skipping")
            gj['features'].pop(i)
            i -= 1



        i += 1
        # break # we only want to download one tile for now
    logging.info(f"TOTAL TIME TAKEN: {time.time() - start}")
    logging.info(f"AVG TIME TAKEN: {(time.time() - start)/(end - cfg.start_from)}")

if __name__ == "__main__":
    main()


