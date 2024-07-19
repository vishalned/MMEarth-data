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
        area_biome = json.load(open(cfg.aree_biome_path))
        area_eco = json.load(open(cfg.area_eco_path))

    # getting the list of biomes
    biome_names = json.load(open(cfg.biome_names_path))
    
    tile_id_count = 0 # we use a simple number to keep track of the tile_id. This is just a number that is incremented by 1 for each tile

    tiles_list = []
    failed_eco_regions = []
    biomes = list(biome_names.keys())[0:-1] # skipping the last one because it is rock and ice

    # biome loop
    for j, biome in enumerate(biomes): 
        print(f'Biome {j+1}/14: {biome}')
        if cfg.uniform_type == 1 or cfg.uniform_type == 0:
            print('Number of images per biome: ', NUM_IMAGES_PER_BIOME)
        print('Number of eco-regions: ', len(biome_names[biome]))

        # eco region loop
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
                num_while_loops = 0 # a variable to keep track of the number of while loops we have done
                while num_of_tiles > 0:
                    
                    tiles_to_export = min(num_of_tiles, 5000)

                    print('Tiles to export inside the while loop: ', tiles_to_export)


                    single_region = eco_region.filter(ee.Filter.eq('ECO_NAME', eco_region_name))
                    
                    # the following 2 lines is just to generate a number based on a string. This ensure that the number is the same for the same string. 
                    # we mod it by 10^5 to keep it small.
                    coord_string = f"{i}{eco_region_name}{tiles_to_export}{num_while_loops}" 
                    seed = int(hashlib.sha256(coord_string.encode('utf-8')).hexdigest(), 16) % 10**5 
                    
                    # adding a line to make the seed new as compared to the previous one
                    # seed += 42
                    random_points = ee.FeatureCollection.randomPoints(single_region, tiles_to_export, seed)

                    tiles = random_points.map(lambda point: point.buffer(cfg.tile_size / 2).bounds())
                    tile_features = tiles.getInfo()['features']

                    for idx in range(len(tile_features)):
                        tile_features[idx]['properties'] = {
                            'tile_id': f"{tile_id_count}",
                            'biome': biome,
                            'eco_region': eco_region_name,
                            
                        }
                        tiles_list.append(tile_features[idx])
                        tile_id_count += 1 # incrementing the tile_id
                    
                    # shuffling the tiles_list
                    random.shuffle(tiles_list)
                    geojson_collection = {
                        'type': 'FeatureCollection',
                        'features': tiles_list
                    }

                    with open(cfg.tiles_geojson_path, 'w') as f:
                        json.dump(geojson_collection, f)

                    num_of_tiles -= tiles_to_export
                    num_while_loops += 1
                    
            except ee.ee_exception.EEException as e:
                print('Could not get this eco-region. Skipping...')
                print(e)
                failed_eco_regions.append(eco_region_name)
                continue


    with open(cfg.failed_eco_regions_path, 'w') as f:
        f.write('\n'.join(failed_eco_regions))

if __name__ == '__main__':
    main()

