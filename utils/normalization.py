# this function reads the h5 file and computes the mean and std of each band 
# including the min and max, and saves it in a json file. 


import os
import json
import numpy as np
import h5py
from math import inf


NO_DATA_VAL = {
    'sentinel2': 0,
    'sentinel2_cloudmask': 65535,
    'sentinel2_cloudprod': 65535,
    'sentinel2_scl': 255,
    'sentinel1': float('-inf'),
    'aster': float('-inf'),
    'canopy_height_eth': 255,
    'dynamic_world': 0,
    'esa_worldcover': 255,
    'lat': float('-inf'),
    'lon': float('-inf'),
    'month': float('-inf'),
    'era5': float('inf')
}

# DATA_PATH = "/home/qbk152/vishal/global-lr/data/data_1M_130/data_1M_130.h5"
# TILE_INFO = "/home/qbk152/vishal/global-lr/data/data_1M_130/data_1M_130_tile_info.json"
# SUBSET_SIZE = 100000 ##### define subset size here, we only compute mean and std for a subset
# STORE_PATH = "/home/qbk152/vishal/global-lr/data/data_1M_130/data_1M_130_band_stats.json"

# DATA_PATH = "/projects/dereeco/data/global-lr/data_1M_130/data_1M_130.h5"
# TILE_INFO = "/projects/dereeco/data/global-lr/data_1M_130/data_1M_130_tile_info.json"
# SUBSET_SIZE = 100000 ##### define subset size here, we only compute mean and std for a subset
# STORE_PATH = "/projects/dereeco/data/global-lr/data_1M_130/data_1M_130_band_stats.json"



def compute_band_stats(data_folder = '', tile_info = '', store_path = ''):

    if data_folder == '':
        raise ValueError("Please provide the path to the data folder")
    
    name = data_folder.split('/')[-1]  if data_folder[-1] != '/' else data_folder.split('/')[-2]
    data_path = os.path.join(data_folder, name + '.h5')
    tile_info = os.path.join(data_folder, name + '_tile_info.json') if tile_info == '' else tile_info
    store_path = os.path.join(data_folder, name + '_band_stats.json') if store_path == '' else store_path

    # since the number of images are large, we compute the rolling mean and std

    # read the tile info
    with open(tile_info, 'r') as f:
        tile_info = json.load(f)

    # read the h5 file
    f = h5py.File(data_path, 'r')

    meta = f['metadata']
    bands = list(i for i in f.keys() if i != 'metadata')
    print(bands)


    print("number of images: ", len(meta))

    return_dict = {}
    

    

    for band in bands:
        if band in ['lat', 'lon', 'month', 'era5']:
            print('computing stats for band: ', band)
            if band == 'era5':
                num_images = np.count_nonzero(~np.isnan(f[band]), axis=0)
            else:
                num_images = len(meta)
            data = f[band]
            mean = np.nansum(data, axis=0) / num_images
            std = np.sqrt(np.nansum((data - mean)**2, axis = 0) / num_images)
            min_val = np.nanmin(data, axis=0)
            max_val = np.nanmax(data, axis=0)
            return_dict[band] = {
                'mean': list(mean.astype(float)),
                'std': list(std.astype(float)),
                'min': list(min_val.astype(float)),
                'max': list(max_val.astype(float))
            }
            print(return_dict[band])
            continue
        
        
        if band not in ['sentinel2_cloudmask', 'sentinel2_cloudprod', 'sentinel2', 'sentinel1', 'aster', 'canopy_height_eth']:
            continue
        
        
        print('computing stats for band: ', band)
        num_images = len(meta)
        
        subset_size = min(SUBSET_SIZE, num_images)
        C = f[band].shape[1]
        channel_sums = np.zeros(C, dtype=np.float64)
        channel_sums_squared = np.zeros(C, dtype=np.float64)
        count_ = np.zeros(C, dtype=np.float64)
        min_val = np.ones(C, dtype=np.float64)*float('inf')
        max_val = np.ones(C, dtype=np.float64)*float('-inf')
        max_range = 1.7e308


        inf_values = 0
        # set numpy seed
        np.random.seed(0)
        indices = np.random.randint(0, num_images, size=subset_size)

        if 'sentinel2' in band:
            channel_sums_l2a = np.zeros(C, dtype=np.float64)
            channel_sums_squared_l2a = np.zeros(C, dtype=np.float64)
            count_l2a = np.zeros(C, dtype=np.float64)
            channel_sums_l1c = np.zeros(C, dtype=np.float64)
            channel_sums_squared_l1c = np.zeros(C, dtype=np.float64)
            count_l1c = np.zeros(C, dtype=np.float64)
            min_val_l2a = np.ones(C, dtype=np.float64)*float('inf')
            max_val_l2a = np.ones(C, dtype=np.float64)*float('-inf')
            min_val_l1c = np.ones(C, dtype=np.float64)*float('inf')
            max_val_l1c = np.ones(C, dtype=np.float64)*float('-inf')
            max_range = 1.7e308

            for idx, i in enumerate(indices):
                name = meta[i][0].decode('utf-8')
                if tile_info[name]['S2_type'] == "l2a":
                    image = np.float64(f[band][i])
                    channel_sums_l2a += np.sum(image, axis=(1, 2), where=(image != NO_DATA_VAL[band]))
                    channel_sums_squared_l2a += np.sum(image**2, axis=(1, 2), where=(image != NO_DATA_VAL[band]))
                    count_l2a += np.sum(image != NO_DATA_VAL[band], axis=(1, 2))
                    tmp_img = np.where(image == NO_DATA_VAL[band], np.nan, image)
                    min_val_l2a = np.nanmin([min_val_l2a, np.nanmin(tmp_img, axis=(1, 2))], axis=0)
                    max_val_l2a = np.nanmax([max_val_l2a, np.nanmax(tmp_img, axis=(1, 2))], axis=0)



                elif tile_info[name]['S2_type'] == "l1c":
                    image = np.float64(f[band][i])
                    channel_sums_l1c += np.sum(image, axis=(1, 2), where=(image != NO_DATA_VAL[band]))
                    channel_sums_squared_l1c += np.sum(image**2, axis=(1, 2), where=(image != NO_DATA_VAL[band]))
                    count_l1c += np.sum(image != NO_DATA_VAL[band], axis=(1, 2))
                    tmp_img = np.where(image == NO_DATA_VAL[band], np.nan, image)
                    min_val_l1c = np.nanmin([min_val_l1c, np.nanmin(tmp_img, axis=(1, 2))], axis=0)
                    max_val_l1c = np.nanmax([max_val_l1c, np.nanmax(tmp_img, axis=(1, 2))], axis=0)

            mean_l2a = channel_sums_l2a/count_l2a
            std_l2a = np.sqrt((channel_sums_squared_l2a/count_l2a) - mean_l2a**2)
            mean_l1c = channel_sums_l1c/count_l1c
            std_l1c = np.sqrt((channel_sums_squared_l1c/count_l1c) - mean_l1c**2)
            return_dict[band + "_l2a"] = {
                'mean': list(mean_l2a.astype(float)),
                'std': list(std_l2a.astype(float)),
                'min': list(min_val_l2a.astype(float)),
                'max': list(max_val_l2a.astype(float))
            }
            return_dict[band + "_l1c"] = {
                'mean': list(mean_l1c.astype(float)),
                'std': list(std_l1c.astype(float)),
                'min': list(min_val_l1c.astype(float)),
                'max': list(max_val_l1c.astype(float))
            }
            print(return_dict[band + "_l2a"])
            print(return_dict[band + "_l1c"])

        else:

            for i in indices:
                
                image = np.float64(f[band][i])
                tmp = np.sum(image, axis=(1, 2), where=(image != NO_DATA_VAL[band]))
                
                channel_sums += tmp
                # if band == 'sentinel1':
                #     channel_sums_squared += np.sum(image**2, axis=(1, 2), where=(image != NO_DATA_VAL[band] or image != float('-inf')))
                # else:
                channel_sums_squared += np.sum(image**2, axis=(1, 2), where=(image != NO_DATA_VAL[band]))
                if np.any(channel_sums_squared > max_range):
                    print("channel_sums_squared: ", channel_sums_squared)
                    print("index", idx)
                    raise OverflowError("channel_sums_squared is greater than max_range")
                
                # computing min and max
                # replace all no data with nan
                tmp_img = np.where(image == NO_DATA_VAL[band], np.nan, image)
                min_val = np.nanmin([min_val, np.nanmin(tmp_img, axis=(1, 2))], axis=0)
                max_val = np.nanmax([max_val, np.nanmax(tmp_img, axis=(1, 2))], axis=0)
                count_ += np.sum(image != NO_DATA_VAL[band], axis=(1, 2))


            mean = channel_sums/count_
            std = np.sqrt((channel_sums_squared/count_) - mean**2)

            return_dict[band] = {
                'mean': list(mean.astype(float)),
                'std': list(std.astype(float)),
                'min': list(min_val.astype(float)),
                'max': list(max_val.astype(float))
            }

            print(return_dict[band])
        # exit()

    with open(store_path, 'w') as f:
        json.dump(return_dict, f)



if __name__ == "__main__":
    compute_band_stats(DATA_PATH, TILE_INFO, STORE_PATH)