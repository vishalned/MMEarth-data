'''
A script to create a geojson with the tiles from various ecoregions or biomes of the world based on the CONFIG file
'''

import hashlib
import ee
from datetime import datetime
import json
# Initialize Earth Engine
ee.Initialize(project = 'global-rl-2')
import hydra
from omegaconf import DictConfig, OmegaConf
import random

# def get_crs_from_s2(single_region):    
#     s2_image_collection = ee.ImageCollection("COPERNICUS/S2") 
#     img = s2_image_collection \
#         .filter(ee.Filter.calendarRange(2020, 2021, 'year')) \
#         .filter(ee.Filter.calendarRange(6, 8, 'month')) \
#         .filterBounds(single_region) \
#         .first()
#     img = img.select('B4', 'B3', 'B2').float() # we are just choosing these bands for the sake of simplicity to get the CRS
#     crs = img.projection().crs().getInfo()
#     return crs

def get_uniq_val(*args):
    # a function to get a unique id for each input string. It just takes the first letter of each word and concatenates them
    id = ""
    for i in args:
        for j in i.split():
            #check if the string is an alphabet
            if j[0].isalpha():
                id += j[0].lower()         
    return id

@hydra.main(config_path='config', config_name='config_tiles')
def main(cfg: DictConfig) -> None:
    print(OmegaConf.to_yaml(cfg))

    eco_region = ee.FeatureCollection("RESOLVE/ECOREGIONS/2017")

    NUM_IMAGES = cfg.num_of_images
    if cfg.uniform_type == 1:
        print('------- Unform across biomes --------')
        NUM_IMAGES_PER_BIOME = NUM_IMAGES // cfg.num_of_biomes
    elif cfg.uniform_type == 2:
        print('------- Unform across eco-regions --------')
    elif cfg.uniform_type == 0:
        print('------- Unform across biomes only --------')
        NUM_IMAGES_PER_BIOME = NUM_IMAGES // cfg.num_of_biomes
        area_biome = json.load(open('./stats/total_area_biome.json'))
        area_eco = json.load(open('./stats/total_area_eco_region.json'))

    # getting the list of biomes
    biome_names = json.load(open(cfg.biome_names_path))

    tiles_list = []
    failed_eco_regions = []
    biomes = list(biome_names.keys())[0:-1]
    for j, biome in enumerate(biomes): # skipping the last one because it is rock and ice
        print(f'Biome {j+1}/14: {biome}')
        if cfg.uniform_type == 1 or cfg.uniform_type == 0:
            print('Number of images per biome: ', NUM_IMAGES_PER_BIOME)
        print('Number of eco-regions: ', len(biome_names[biome]))

        for i, eco in enumerate(biome_names[biome]):
            try:
                eco_region_name, realm = eco[0], eco[1]
                print(f'Eco-region {i}/{len(biome_names[biome])}: {eco_region_name} ')
                if cfg.uniform_type == 1:
                    num_of_tiles = NUM_IMAGES_PER_BIOME // len(biome_names[biome]) 
                elif cfg.uniform_type == 2:
                    num_of_tiles = NUM_IMAGES // 846 # 846 is the total number of eco-regions in the RESOLVE ecoregions dataset
                elif cfg.uniform_type == 0:
                    num_of_tiles = int(NUM_IMAGES_PER_BIOME * (area_eco[eco_region_name] / area_biome[biome]))

                print('Number of tiles in the eco-region: ', num_of_tiles)

                # gee only allows max of 5000 features to be exported at a time. So we need to split the eco-regions into smaller batches



                while num_of_tiles > 0:
                    
                    tiles_to_export = min(num_of_tiles, 5000)

                    print('Tiles to export inside the while loop: ', tiles_to_export)


                    single_region = eco_region.filter(ee.Filter.eq('ECO_NAME', eco_region_name))
                    
                    coord_string = f"{i}{eco_region_name}{tiles_to_export}" 
                    seed = int(hashlib.sha256(coord_string.encode('utf-8')).hexdigest(), 16) % 10**5 
                    
                    # adding a line to make the seed new as compared to the previous one
                    # seed += 42
                    random_points = ee.FeatureCollection.randomPoints(single_region, tiles_to_export, seed)

                    tiles = random_points.map(lambda point: point.buffer(cfg.tile_size / 2).bounds())
                    tile_features = tiles.getInfo()['features']

                    for i in range(len(tile_features)):
                        tile_features[i]['properties'] = {
                            # 'crs': crs,
                            'tile_id': f"{get_uniq_val(biome, eco_region_name)}_{i}",
                            'biome': biome,
                            'eco_region': eco_region_name,
                            
                        }
                        tiles_list.append(tile_features[i])
                    # shuffling the tiles_list
                    random.shuffle(tiles_list)
                    geojson_collection = {
                        'type': 'FeatureCollection',
                        'features': tiles_list
                    }

                    with open(cfg.tiles_geojson_path, 'w') as f:
                        json.dump(geojson_collection, f)

                    num_of_tiles -= tiles_to_export
                    
            except ee.ee_exception.EEException as e:
                print('Could not get this eco-region. Skipping...')
                print(e)
                failed_eco_regions.append(eco_region_name)
                continue


    with open(cfg.failed_eco_regions_path, 'w') as f:
        f.write('\n'.join(failed_eco_regions))

if __name__ == '__main__':
    main()

