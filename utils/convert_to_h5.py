'''
A python script to do the pre-processing and convert the data to h5 format. It will then be ready to be used by the dataloader for training.
'''


import argparse
import os
import h5py
import numpy as np
import json
import tifffile as tiff




MODALITIES = {
            'sentinel2': {'dtype': 'uint16', 'n_bands': 13, 'bands': ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8A', 'B8', 'B9', 'B10', 'B11', 'B12']},
            'sentinel2_cloudmask': {'dtype': 'uint16', 'n_bands': 1, 'bands': ['QA60']},
            'sentinel2_cloudprod': {'dtype': 'uint16', 'n_bands': 1, 'bands': ['MSK_CLDPRB']},
            'sentinel2_scl': {'dtype': 'uint8', 'n_bands': 1, 'bands': ['SCL']},
            'sentinel1': {'dtype': 'float32', 'n_bands': 8, 'bands': ['asc_VV', 'asc_VH', 'asc_HH', 'asc_HV', 'desc_VV', 'desc_VH', 'desc_HH', 'desc_HV']},
            'aster': {'dtype': 'int16', 'n_bands': 2, 'bands': ['elevation', 'slope']},
            'era5': {'dtype': 'float32', 'n_bands': 12, 'bands': ['prev_month_avg_temp', 'prev_month_min_temp', 'prev_month_max_temp', 'prev_month_total_precip', 'curr_month_avg_temp', 'curr_month_min_temp', 'curr_month_max_temp', 'curr_month_total_precip', 'year_avg_temp', 'year_min_temp', 'year_max_temp', 'year_total_precip']},
            'dynamic_world': {'dtype': 'uint8', 'n_bands': 1, 'bands': ['landcover']},
            'canopy_height_eth': {'dtype': 'int8', 'n_bands': 2, 'bands': ['height', 'std']},
            'lat': {'dtype': 'float32', 'n_bands': 2, 'bands': ['sin', 'cos']},
            'lon': {'dtype': 'float32', 'n_bands': 2, 'bands': ['sin', 'cos']},
            'biome': {'dtype': 'uint8', 'n_bands': 1},
            'eco_region': {'dtype': 'uint16', 'n_bands': 1},
            'month': {'dtype': 'float32', 'n_bands': 2, 'bands': ['sin', 'cos']},
            'esa_worldcover':{ 'dtype': 'uint8', 'n_bands': 1, 'bands': ['map']}
}

sentinel2_bands = [
    'B1',
    'B2',
    'B3',
    'B4',
    'B5',
    'B6',
    'B7',
    'B8A',
    'B8',
    'B9',
    'B10',
    'B11',
    'B12',
]

# MODALITIES_IN_IMAGE = [
#     'sentinel2',
#     'sentinel1_asc',
#     'sentinel1_desc',
#     'aster',
#     'dynamic_world',
#     'canopy_height_eth',
#     'esa_worldcover'

# ]

variables = {}
remove = []



def read_data(tile_id, tile_info, data_dir, img_size, exisiting_datasets=None):
    tile_info_bands = tile_info['BANDS']
    type = tile_info['S2_type']
    try:
        data = tiff.imread(os.path.join(data_dir, tile_id + '.tif'))
    except:
        return None
    return_data_dict = {}
    count = 0 # this represents the count of the bands, we use this since all the bands are stacked in the same order
    
    # creating a center crop of size img_size
    start_x = (data.shape[0] - img_size) // 2
    start_y = (data.shape[1] - img_size) // 2
    if len(data.shape) == 2:
        data = np.expand_dims(data, axis=2)
    data = data[start_x:start_x + img_size, start_y:start_y + img_size, :]
    for modality, modality_info in MODALITIES.items():
        if exisiting_datasets is not None and modality not in exisiting_datasets:
            continue

        
        ### SENTINEL 2 ###
        if modality == 'sentinel2':
            placeholder = np.zeros((13, img_size, img_size), dtype='uint16')
            count += len(tile_info_bands['sentinel2']) - 3 if type == 'l2a' else len(tile_info_bands['sentinel2']) - 1
            for i, band in enumerate(sentinel2_bands):
                if band in tile_info_bands['sentinel2']:
                    placeholder[i] = np.expand_dims(data[:, :, tile_info_bands['sentinel2'].index(band)], 2).transpose(2, 0, 1)
            return_data_dict['sentinel2'] = placeholder

        if modality == 'sentinel2_cloudmask':
            if 'QA60' in tile_info_bands['sentinel2']:
                return_data_dict['sentinel2_cloudmask'] = np.expand_dims(data[:, :, tile_info_bands['sentinel2'].index('QA60')], 2).transpose(2, 0, 1)
                count += 1
            else:
                return_data_dict['sentinel2_cloudmask'] = np.ones((1, img_size, img_size), dtype='uint16') * 65535

        if modality == 'sentinel2_cloudprod':
            
            if 'MSK_CLDPRB' in tile_info_bands['sentinel2']:
                count += 1
                return_data_dict['sentinel2_cloudprod'] = np.expand_dims(data[:, :, tile_info_bands['sentinel2'].index('MSK_CLDPRB')], 2).transpose(2, 0, 1)
            else:
                return_data_dict['sentinel2_cloudprod'] = np.ones((1, img_size, img_size), dtype='uint16') * 65535


        if modality == 'sentinel2_scl':
            if 'SCL' in tile_info_bands['sentinel2']:
                count += 1
                return_data_dict['sentinel2_scl'] = np.expand_dims(data[:, :, tile_info_bands['sentinel2'].index('SCL')], 2).transpose(2, 0, 1)
            else:
                return_data_dict['sentinel2_scl'] = np.ones((1, img_size, img_size), dtype='uint8') * 255



        ### SENTINEL 1 ###
        if modality == 'sentinel1':
            bands_map = {'VV': 0, 'VH': 1, 'HH': 2, 'HV': 3}
            orbit_map = {'asc': 0, 'desc': 4}
            tmp = np.ones((8, img_size, img_size), dtype='float32') * float('-inf')
            for orbit in ['asc', 'desc']:
                if tile_info_bands[f'sentinel1_{orbit}'] is not None:
                    bands_img = tile_info_bands[f'sentinel1_{orbit}']
                    count += len(bands_img)
                    for i, band in enumerate(bands_img):
                        tmp[orbit_map[orbit] + bands_map[band]] = data[:, :, count - len(bands_img) + i]

            return_data_dict['sentinel1'] = tmp

        ### ASTER ###
        if modality == 'aster':
            count += len(tile_info_bands['aster'])
            return_data_dict['aster'] = data[:, :, count - len(tile_info_bands['aster']):count].transpose(2, 0, 1)

        ### ERA5 ###
        if modality == 'era5':

            era_data = tile_info['era5']
            
            return_data_dict['era5'] = np.stack([era_data['month1'] + era_data['month2'] + era_data['year']], axis=0).astype('float32')

        ### DYNAMIC WORLD ###
        if modality == 'dynamic_world':
            try:
                count += len(tile_info_bands['dynamic_world'])
                return_data_dict['dynamic_world'] = np.expand_dims(data[:, :, count - len(tile_info_bands['dynamic_world'])], axis = 0)
            except Exception as e:
                print('dynamic_world not found')
                return_data_dict['dynamic_world'] = np.zeros((1, img_size, img_size), dtype='uint8')
            

        ### CANOPY HEIGHT ###
        if modality == 'canopy_height_eth':
            count += len(tile_info_bands['canopy_height_eth']) 
            tmp = data[:, :, count - len(tile_info_bands['canopy_height_eth']):count].transpose(2, 0, 1)
            if tmp.shape[0] == 0:
                return_data_dict['canopy_height_eth'] = np.ones((2, img_size, img_size), dtype='int8') * 255
            else:
                return_data_dict['canopy_height_eth'] = data[:, :, count - len(tile_info_bands['canopy_height_eth']):count].transpose(2, 0, 1)
   


        ### LATITUDE ###
        if modality == 'lat':
            return_data_dict['lat'] = np.stack([np.sin(np.deg2rad(tile_info['lat'])), np.cos(np.deg2rad(tile_info['lat']))], axis=0).astype('float32')


        ### LONGITUDE ###
        if modality == 'lon':
            return_data_dict['lon'] = np.stack([np.sin(np.deg2rad(tile_info['lon'])), np.cos(np.deg2rad(tile_info['lon']))], axis=0).astype('float32')
        
        ### BIOME ###
        if modality == 'biome':
            biome = tile_info['biome']
            one_hot = np.zeros(14)
            one_hot[biome] = 1
            return_data_dict['biome'] = one_hot.astype('uint8')

        ### ECO-REGION ###
        if modality == 'eco_region':
            eco_region = tile_info['eco_region']
            one_hot = np.zeros(846)
            one_hot[eco_region] = 1
            return_data_dict['eco_region'] = one_hot.astype('uint16')

        ### MONTH ###
        if modality == 'month':
            month = tile_info['S2_DATE'].split('-')[1]
            month = int(month)
            return_data_dict['month'] = np.stack([np.sin(2 * np.pi * month / 12), np.cos(2 * np.pi * month / 12)], axis=0).astype('float32')

        ## ESA WORLD COVER ###
        if modality == 'esa_worldcover':
            try:
                count += len(tile_info_bands['esa_worldcover'])
                return_data_dict['esa_worldcover'] = np.expand_dims(data[:, :, count - len(tile_info_bands['esa_worldcover'])], axis = 0)

            except Exception as e:
                print('esa_worldcover not found')
                print('exception: ',e)
                exit()
                return_data_dict['esa_worldcover'] = np.ones((1, img_size, img_size), dtype='uint8') * 255

    return return_data_dict


def main(args):

    mode = args.mode
    print('Mode: ', mode)
    if mode == 'create':
        data_dir = args.data_dir
        data_dir = os.path.join(data_dir, 'merged')
        img_size = args.image_size

        # we first check if the output file already exists, if it does, we delete it
        if os.path.exists(args.output_file): 
            os.remove(args.output_file) 

        hdf5_file = h5py.File(args.output_file, 'a')
        
        num_tiles = len(os.listdir(data_dir))

        tile_info = json.load(open(args.tile_info, 'r'))


        # we calculate the real number of tiles by verifying how many tiles
        # have number of bands equal to the sum of the bands in the tile_info.json file

        num_tiles = 0
        for i, tile_id in enumerate(tile_info):
            count_t = 0
            for b in ['sentinel2', 'sentinel1_asc', 'sentinel1_desc', 'aster', 'dynamic_world', 'canopy_height_eth', 'esa_worldcover']:
                if b in tile_info[tile_id]['BANDS']:
                    count_t += len(tile_info[tile_id]['BANDS'][b]) if tile_info[tile_id]['BANDS'][b] is not None else 0

            try:
                data = tiff.imread(os.path.join(data_dir, tile_id + '.tif'))
            except:
                # sometimes the data is not downloaded, so we skip it
                continue
            if data.shape[-1] == count_t:
                num_tiles += 1
            else:
                #  we store the lat lon in a csv file to check the tiles that have not been downloaded
                print('Tile shape mismatch: ', tile_id)
                lat, lon = tile_info[tile_id]['lat'], tile_info[tile_id]['lon']
                # with open(args.missing_tiles, 'a') as f:
                #     f.write(f'{tile_id},{lat},{lon}\n')

        # num_tiles = len(tile_info)
        print('Number of tiles: ', num_tiles)
        print('Number of entries in tile_info: ', len(tile_info))
        print('Number of tiles skipped due to mismatch: ', len(tile_info) - num_tiles)
        # exit()

        

        # creating a dataset for each modality
        for modality, modality_info in MODALITIES.items():
            if modality == 'lat' or modality == 'lon' or modality == 'month':
                variables[modality] = hdf5_file.create_dataset(modality, shape=(num_tiles, 2), dtype=modality_info['dtype'], compression='gzip', chunks=(1, 2))
            elif modality == 'biome':
                variables[modality] = hdf5_file.create_dataset(modality, shape=(num_tiles, 14), dtype=modality_info['dtype'], compression='gzip', chunks=(1, 14))
            elif modality == 'eco_region':
                variables[modality] = hdf5_file.create_dataset(modality, shape=(num_tiles, 846), dtype=modality_info['dtype'], compression='gzip', chunks=(1, 846))
            elif modality == 'era5':
                variables[modality] = hdf5_file.create_dataset(modality, shape=(num_tiles, modality_info['n_bands']), dtype=modality_info['dtype'], compression='gzip', chunks=(1, modality_info['n_bands']))
            else:
                variables[modality] = hdf5_file.create_dataset(modality, shape=(num_tiles, modality_info['n_bands'], img_size, img_size), dtype=modality_info['dtype'], compression='gzip', chunks=(1, modality_info['n_bands'], img_size, img_size))
        

        # create a new meta data with tile_id and s2 type which is either l2a or l1c
        metadata_dt = np.dtype([('tile_id', 'S100'), ('S2_type', 'S10')]) # string of length 100
        ds_metadata = hdf5_file.create_dataset('metadata', shape=(num_tiles,), dtype=metadata_dt, compression='gzip', chunks=(1,))

        # metadata_dt = np.dtype([('tile_id', 'S100')]) # string of length 100
        # ds_metadata = hdf5_file.create_dataset('metadata', shape=(num_tiles,), dtype=metadata_dt, compression='gzip', chunks=(1,))

        j = 0
        count_s = 0
        for i, tile_id in enumerate(tile_info):

            print(f'Processing tile {i}/{num_tiles}, {tile_id}')
            count_t = 0

            for b in ['sentinel2', 'sentinel1_asc', 'sentinel1_desc', 'aster', 'dynamic_world', 'canopy_height_eth', 'esa_worldcover']:
                if b in tile_info[tile_id]['BANDS']:
                    count_t += len(tile_info[tile_id]['BANDS'][b]) if tile_info[tile_id]['BANDS'][b] is not None else 0

            try:
                data = tiff.imread(os.path.join(data_dir, tile_id + '.tif'))
            except:
                print('Skipping tile: ', tile_id)
                continue

            if data.shape[-1] != count_t:
                print('mismatch')
                count_s += 1
                continue


            data_ = read_data(tile_id, tile_info[tile_id], data_dir, img_size)
            if data_ is None:
                print('Skipping tile: ', tile_id)
                continue
            for modality, _ in MODALITIES.items():
                try:
                    variables[modality][j] = data_[modality]
                except Exception as e:
                    print('Error in modality: ', modality)
                    print(e)
                    exit() 
            # breakpoint()        
            # ds_metadata[j] = tile_id
            ds_metadata[j] = (tile_id, tile_info[tile_id]['S2_type'])
            j += 1
            # exit() ## testing
        hdf5_file.close()
        print('Done!')
        print('number of tiles: ', num_tiles)

        print('Number of tiles skipped due to mismatch: ', count_s)
    else:
        # we are now merging 2 h5 files
        if os.path.exists(args.output_file): 
            print('Output file already exists. ')
        
        img_size = args.image_size

        file1 = h5py.File(args.path1, 'r')
        file2 = h5py.File(args.path2, 'r')
        tile_info1 = json.load(open(args.path1_tile_info, 'r'))
        tile_info2 = json.load(open(args.path2_tile_info, 'r'))

        size = len(file1['metadata']) + len(file2['metadata'])

        hdf5_file = h5py.File(args.output_path, 'a')

        # creating a dataset for each modality
        for modality, modality_info in MODALITIES.items():
            if modality == 'lat' or modality == 'lon' or modality == 'month':
                variables[modality] = hdf5_file.create_dataset(modality, shape=(size, 2), dtype=modality_info['dtype'])
            elif modality == 'biome':
                variables[modality] = hdf5_file.create_dataset(modality, shape=(size, 14), dtype=modality_info['dtype'])
            elif modality == 'eco_region':
                variables[modality] = hdf5_file.create_dataset(modality, shape=(size, 846), dtype=modality_info['dtype'])
            elif modality == 'era5':
                variables[modality] = hdf5_file.create_dataset(modality, shape=(size, modality_info['n_bands']), dtype=modality_info['dtype'])
            else:
                variables[modality] = hdf5_file.create_dataset(modality, shape=(size, modality_info['n_bands'], img_size, img_size), dtype=modality_info['dtype'])

        metadata_dt = np.dtype([('tile_id', 'S100')]) # string of length 100
        ds_metadata = hdf5_file.create_dataset('metadata', shape=(size,), dtype=metadata_dt)

        j = 0
        for i in range(len(file1['metadata'])):
            print(f'Processing tile {i}/{len(file1["metadata"])}')
            # we append the data from the first file, and then the data from the second file
            for modality, _ in MODALITIES.items():
                variables[modality][j] = file1[modality][i]
            ds_metadata[j] = file1['metadata'][i]
            j += 1

        for i in range(len(file2['metadata'])):
            print(f'Processing tile {i}/{len(file2["metadata"])}')
            # we append the data from the first file, and then the data from the second file
            for modality, _ in MODALITIES.items():
                variables[modality][j] = file2[modality][i]
            ds_metadata[j] = file2['metadata'][i]
            j += 1

        hdf5_file.close()
        print('Done!')

        # we also need to merge the tile_info files
        tile_info = {}
        for i in range(len(file1['metadata'])):
            tile = file1['metadata'][i][0].decode('utf-8')
            tile_info[tile] = tile_info1[tile]
        for i in range(len(file2['metadata'])):
            tile = file2['metadata'][i][0].decode('utf-8')
            tile_info[tile] = tile_info2[tile]
        with open(args.output_path.split('.')[0] + '_tile_info.json', 'w') as f:
            json.dump(tile_info, f)
        print('number of tiles: ', size)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert the data to h5 format')
    parser.add_argument('--mode', type=str, required=True, help='append or create', choices= ['merge', 'create'])
    
    # args for create mode
    # required args
    parser.add_argument('--data_dir', type=str, default='', help='path to the data directory')
    # optional args
    parser.add_argument('--tile_info', type=str, default='', help='path to the tile info json file')  
    parser.add_argument('--output_file', type=str, default='', help='path to the output h5 file')
    parser.add_argument('--missing_tiles', type=str, default='', help='path to the csv file containing the missing tiles')
    parser.add_argument('--image_size', type=int, default=128, help='size of the image')


    # args for merge mode
    # required args
    parser.add_argument('--data_dir1', type=str, default='', help='path to the first folder')
    parser.add_argument('--data_dir2', type=str, default='', help='path to the first folder')
    parser.add_argument('--output_path', type=str, help='path to the output h5 file')
    # optional args
    parser.add_argument('--path1', type=str, default='', help='path to the first h5 file')
    parser.add_argument('--path1_tile_info', type=str, default='', help='path to the tile info json file for the first h5 file')
    parser.add_argument('--path2', type=str, default='', help='path to the second h5 file')
    parser.add_argument('--path2_tile_info', type=str, default='', help='path to the tile info json file for the second h5 file')
    

    args = parser.parse_args()
    if args.mode == 'merge':
        assert args.output_path != '', 'Please provide the output path'
        assert args.data_dir1 != '', 'Please provide the path to the first folder'
        assert args.data_dir2 != '', 'Please provide the path to the second folder'

        name1 = args.data_dir1.split('/')[-1] if args.data_dir1[-1] != '/' else args.data_dir1.split('/')[-2]
        name2 = args.data_dir2.split('/')[-1] if args.data_dir2[-1] != '/' else args.data_dir2.split('/')[-2]
        if args.path1 == '':
            args.path1 = os.path.join(args.data_dir1, name1 + '.h5')
        if args.path1_tile_info == '':
            args.path1_tile_info = os.path.join(args.data_dir1, name1 + '_tile_info.json')
        if args.path2 == '':
            args.path2 = os.path.join(args.data_dir2, name2 + '.h5')
        if args.path2_tile_info == '':
            args.path2_tile_info = os.path.join(args.data_dir2, name2 + '_tile_info.json')
    
    if args.mode == 'create':
        assert args.data_dir != '', 'Please provide the path to the data directory'
        name = args.data_dir.split('/')[-1] if args.data_dir[-1] != '/' else args.data_dir.split('/')[-2]
        if args.tile_info == '':
            args.tile_info = os.path.join(args.data_dir, name + '_tile_info.json')
        if args.output_file == '':
            args.output_file = os.path.join(args.data_dir, name + '.h5')
        if args.missing_tiles == '':
            args.missing_tiles = os.path.join(args.data_dir, name + 'missing_tiles.csv')
        


    main(args)