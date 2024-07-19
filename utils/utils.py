import time
import geojson
import logging
import ee
import os
import glob
import config.ee_init
import json


def read_geojson(path):
    '''
    Reads the geojson file
    '''
    with open(path) as f:
        gj = geojson.load(f)
    return gj

def merge_dicts(in_path, out_path = 'data/data_100k_130_tile_info.json'):
    '''
    Merges the dictionaries from the tile_info json files.
    '''

    # reading all the tile json files
    tile_info_dict = {}
    for tile_name in glob.glob(f'{in_path}/tile_info_*'):
        tmp = read_geojson(tile_name)
        tile_info_dict = tmp | tile_info_dict

    # writing the merged dictionary to a file
    print(len(tile_info_dict))
    with open(out_path, 'w') as f:
        geojson.dump(tile_info_dict, f)

    # remove the individual tile_info files
    # for tile_name in glob.glob('data/tile_info/tile_info_*'):
    #     os.remove(tile_name)

def create_missing_tiles_geojson():
    '''
    Creates the missing tiles geojson file.
    '''

    missing_tiles_csv = 'data/missing_tiles_1M.csv'
    tile_geojson = '/home/qbk152/vishal/global-lr/tile_polygons/uni_biomes_only/tiles_1M_130.geojson'

    geojson = {
        'type': 'FeatureCollection',
        'features': []
    }

    # reading the tile geojson file
    gj = read_geojson(tile_geojson)
    features = gj['features']

    # reading the missing tiles csv file
    for line in open(missing_tiles_csv):
        line = line.strip()
        line = line.split(',')
        tile_name = line[0]
        print('Processing tile: ', tile_name)

        # finding the tile in the tile geojson file
        for feature in features:
            if feature['properties']['tile_id'] == tile_name:
                geojson['features'].append(feature)
                break

    # writing the geojson file
    print('Total missing tiles: ', len(geojson['features']))
    with open('data/missing_tiles_1M.geojson', 'w') as f:
        json.dump(geojson, f)


        



def update_tile_info(tile, ee_set_, tile_info = None):
    '''
    Updates the tile information in the geojson file.
    '''

    if tile_info is not None:
        # this implies that there already exists a tile_info file, and we need to read the information from that file and update it with the new information which for now is only the bands
        id = ee_set_.id
        existing_bands = tile_info['BANDS']
        new_bands = ee_set_.img_bands
        bands = existing_bands | new_bands
        tile_info['BANDS'] = bands

        # # HARDCODED: adding the era5 data to the tile_info
        # if len(ee_set_.era5_data) > 0:
        #     tile_info['era5'] = ee_set_.era5_data
        return tile_info
    else:
        return_dict = {}
        return_dict['S2_DATE'] = ee_set_.s2_date
        # return_dict['S2_IMAGEID'] = ee_set_.s2_imageid
        return_dict['S2_type'] = ee_set_.s2_type
        return_dict['CRS'] = ee_set_.crs
        return_dict['lat'] = ee_set_.lat
        return_dict['lon'] = ee_set_.lon
        return_dict['biome'] = ee_set_.biome
        return_dict['eco_region'] = ee_set_.eco_region
        return_dict['NO_DATA'] = ee_set_.no_data
        return_dict['BANDS'] = ee_set_.img_bands
        if len(ee_set_.era5_data) > 0:
            return_dict['era5'] = ee_set_.era5_data
        return return_dict



def get_points_filter(roi, buffer_size=0):
    pnt_roi = roi.buffer(buffer_size, ee.ErrorMargin(1)).bounds()
    coord_list = ee.List(pnt_roi.coordinates().get(0))
    b_left = ee.Geometry.Point(coord_list.get(0))
    b_right = ee.Geometry.Point(coord_list.get(1))
    t_right = ee.Geometry.Point(coord_list.get(2))
    t_left = ee.Geometry.Point(coord_list.get(3))

    points_filter = ee.Filter.And(
        ee.Filter.geometry(b_right),
        ee.Filter.geometry(t_left)
    )

    return points_filter


def get_ee_task_list():
    '''
    Gets the list of all the tasks in the EE project.
    '''
    tasks = []
    task_list = ee.data.getTaskList()
    for task in task_list:
        if task['state'] in ['RUNNING', 'READY']:
            tasks.append(task['id'])
    return tasks


def read_txt(path):
    '''
    Reads the txt file and returns a list of the lines in the file.
    '''
    string_list = []
    with open(path, 'r') as f:
        for line in f:
            string_list.append(line.strip())
    return string_list

def write_json(path, data):
    '''
    Writes the data to the json file.
    '''
    with open(path, 'w') as f:
        json.dump(data, f)

def read_json(path):
    '''
    Reads the json file and returns the data.
    '''
    with open(path, 'r') as f:
        data = json.load(f)
    return data


if __name__ == '__main__':
    merge_dicts('/home/qbk152/vishal/global-lr/data/data_300k_130_tile_info.json')
    # create_missing_tiles_geojson()