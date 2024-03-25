'''
File that has code to read the resolve ecoregions geojson file and extract the biome names and eco-regions. 
It also writes the biome names to a json file.
'''

import geojson
from tqdm import tqdm
import json

def read_geojson(filename):
    with open(filename) as f:
        gj = geojson.load(f)
    return gj

def get_biome_data():
    path = "../datasets/RESOLVE_ecoregions.geojson"
    gj = read_geojson(path)

    data = gj['features'][0]['properties']

    # getting all the biome names, and the list of eco_regions
    print('List of keys: ', data.keys())

    biome_names = {}

    eco_count = 0
    for i in tqdm(range(len(gj['features']))):
        if gj['features'][i]['properties']['BIOME_NAME'] not in biome_names.keys():
            biome_names[gj['features'][i]['properties']['BIOME_NAME']] = []

        biome_names[gj['features'][i]['properties']['BIOME_NAME']].append([gj['features'][i]['properties']['ECO_NAME'], gj['features'][i]['properties']['REALM']])
        eco_count += 1

    print('Total number of biomes', len(biome_names.keys()))
    print('Total number of eco-regions', eco_count)
    # writing the biome names to a json file
    import json
    
    with open('stats/biome_names.json', 'w') as fp:
        json.dump(biome_names, fp)



if __name__ == '__main__':
    import os
    os.makedirs('stats', exist_ok=True)
    get_biome_data()
