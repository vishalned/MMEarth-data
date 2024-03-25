'''
A script to view the contents of the h5 file.
'''


import h5py
import matplotlib.pyplot as plt
import numpy as np
import random
import os
import json
from matplotlib.colors import ListedColormap, BoundaryNorm



h5_path = '/projects/dereeco/data/global-lr/data_1M_130_new/data_1M_130_new.h5'
tile_info_path = '/home/qbk152/vishal/global-lr/data/data_1M_130_new/data_1M_130_new_tile_info.json'
save_dir = '/home/qbk152/vishal/global-lr/data/visualizations/130'
splits_path = '/home/qbk152/vishal/global-lr/data/data_1M_130_new/data_1M_130_new_splits.json'

# display_num = 20 # number of tiles to display
# display_id = 'tsmbfsngfsf_29'
display_id = 'mfwsnsasfmf_485'


save_tif = False



def save_img(path, img, cmap = None, norm = None):
    if cmap is None:
        plt.imshow(img)
    else:
        if norm is None:
            plt.imshow(img, cmap=cmap)
        else:
            plt.imshow(img, cmap=cmap, norm=norm)
    plt.axis('off')
    plt.savefig(path, bbox_inches='tight', pad_inches=0)
    plt.close()



def view_h5(h5_path):

    hdf5_file = h5py.File(h5_path, 'r')
    print('h5 KEYS: ', hdf5_file.keys())
    splits = json.load(open(splits_path, 'r'))
    meta = hdf5_file['metadata']    

    num_tiles = len(meta)
   
    if display_id is not None:
        for i in range(num_tiles):
            tile_id = meta[i][0].decode('utf-8')
            if tile_id == display_id:
                dir = os.path.join(save_dir, tile_id)
                os.makedirs(dir, exist_ok=True)
                for key in hdf5_file.keys():
                    # if len(hdf5_file[key].shape) != 4:
                    #     continue
                    # print('Key: ', key)
                    img = hdf5_file[key][i]
                    write_img(img, key, dir)
    else:
    # choose a random tile           
        for j in range(display_num):
            i = random.randint(0, num_tiles - 1)
            tile_id = meta[i][0].decode('utf-8')
            print('Tile ID: ', tile_id)

            train = splits['train']
            val = splits['val']
            test = splits['test']

            if i in train:
                print('Train, idx: ', i)
            elif i in val:
                print('Val, idx: ', i)
            elif i in test:
                print('Test, idx: ', i)
            

            if not save_tif:
                dir = os.path.join(save_dir, tile_id)
                os.makedirs(dir, exist_ok=True)
                for key in hdf5_file.keys():
                    # we only want to visualize sentinel2 for now TESTING PURPOSES
                    # if key != 'sentinel2':
                    #     continue
                    if len(hdf5_file[key].shape) != 4:
                        continue
                    # print('Key: ', key)
                    img = hdf5_file[key][i]
                    write_img(img, key, dir)                

def write_img(img, key, dir):
    if key == 'sentinel2':
        img = img[[3, 2, 1], :, :]/10000
        clip_val = 0.2
        img = np.clip(img, 0, clip_val)
        img = img/clip_val

        img = img.transpose(1, 2, 0)

        # plt.imsave(os.path.join(dir, 'sentinel2.png'), img)
        save_img(os.path.join(dir, 's2.png'), img)

    elif key == 'sentinel1':
        bands_map = {'VV': 0, 'VH': 1, 'HH': 2, 'HV': 3}
        orbit_map = {'asc': 0, 'desc': 4}
        # write each band separately
        for band, band_idx in bands_map.items():
            for orbit, orbit_idx in orbit_map.items():
                img_ = img[orbit_idx + band_idx, :, :]
                # print(np.min(img_), np.max(img_))
                img_ = (np.clip(img_, -30, 0) + 30) / 30
                # print(np.min(img_), np.max(img_))
                # plt.imsave(os.path.join(dir, 's1_' + band + '_' + orbit + '.png'), img_)
                save_img(os.path.join(dir, 's1_' + band + '_' + orbit + '.png'), img_)

    elif key == 'aster':
        # write elevation and slope
        img_ = img[0, :, :]
        # plt.imsave(os.path.join(dir, 'aster_elevation.png'), img_)
        save_img(os.path.join(dir, 'aster_elevation.png'), img_)
        img_ = img[1, :, :]
        # plt.imsave(os.path.join(dir, 'aster_slope.png'), img_)
        save_img(os.path.join(dir, 'aster_slope.png'), img_)

    elif key == 'dynamic_world':
        # write the label band
        img_ = img[0, :, :]
        colors = ['#000000', '#419bdf', '#397d49', '#88b053', '#7a87c6', '#e49635', '#dfc35a', '#c4281b', '#a59b8f', '#b39fe1']
        norm = BoundaryNorm([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], len(colors))

        cmap = ListedColormap(colors)
        # plt.imsave(os.path.join(dir, 'dynamic_world.png'), img_, cmap=cmap)
        save_img(os.path.join(dir, 'dynamic_world.png'), img_, cmap=cmap, norm=norm)


    elif key == 'canopy_height_eth':
        # write the 2 bands
        img_ = img[0, :, :]
        # plt.imsave(os.path.join(dir, 'canopy_height_height.png'), img_)
        save_img(os.path.join(dir, 'canopy_height_height.png'), img_)
        img_ = img[1, :, :]
        # plt.imsave(os.path.join(dir, 'canopy_height_std.png'), img_)
        save_img(os.path.join(dir, 'canopy_height_std.png'), img_)
    
    elif key == 'esa_worldcover':
        img_ = img[0, :, :]
        colormap = [
            '#006400',  # Tree cover - 10
            '#ffbb22',  # Shrubland - 20
            '#ffff4c',  # Grassland - 30
            '#f096ff',  # Cropland - 40
            '#fa0000',  # Built-up - 50
            '#b4b4b4',  # Bare / sparse vegetation - 60
            '#f0f0f0',  # Snow and ice - 70
            '#0064c8',  # Permanent water bodies - 80
            '#0096a0',  # Herbaceous wetland - 90
            '#00cf75',  # Mangroves - 95
            '#fae6a0'   # Moss and lichen - 100
        ]

        bounds = [10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100]
        norm = BoundaryNorm(bounds, len(colormap))

        cmap = ListedColormap(colormap)
        # plt.imsave(os.path.join(dir, 'esa_worldcover.png'), img_, cmap=cmap, norm=norm)

        save_img(os.path.join(dir, 'esa_worldcover.png'), img_, cmap=cmap, norm=norm)
    
    else:
        print(key, img)







if __name__ == '__main__':
    os.makedirs(save_dir, exist_ok=True)
    view_h5(h5_path)