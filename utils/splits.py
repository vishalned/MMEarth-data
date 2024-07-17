# a file that has functions to create the train, val, and test splits from a h5 file. 
# we only create a new file, with indices of the train, val, and test splits.


import h5py
import numpy as np
import os
import json

# data_path = "/home/qbk152/vishal/global-lr/data/data_100k_130.h5"
# tile_info = "/home/qbk152/vishal/global-lr/data/data_100k_130_tile_info.json"
# store_path = "/home/qbk152/vishal/global-lr/data/data_100k_130_splits.json"


def create_splits(data_folder = '', tile_info = '', store_path = '', train_split=1.0, val_split=0.0, test_split=0):

    if data_folder == '':
        raise ValueError("Please provide the path to the data folder")
    name = data_folder.split('/')[-1] if data_folder[-1] != '/' else data_folder.split('/')[-2]
    data_path = os.path.join(data_folder, name + '.h5') 
    tile_info = os.path.join(data_folder, name + '_tile_info.json') if tile_info == '' else tile_info
    store_path = os.path.join(data_folder, name + '_splits.json') if store_path == '' else store_path
    

    # read the tile info
    with open(tile_info, 'r') as f:
        tile_info = json.load(f)

    # read the h5 file
    f = h5py.File(data_path, 'r')

    meta = f['metadata']
    bands = list(i for i in f.keys() if i != 'metadata')
    print(bands)


    print("number of images: ", len(meta))

    # create the splits
    num_images = len(meta)
    num_train = int(train_split * num_images)
    num_val = int(val_split * num_images)
    num_test = num_images - num_train - num_val

    # create the indices
    indices = np.arange(num_images)
    np.random.shuffle(indices)

    train_indices = indices[:num_train]
    val_indices = indices[num_train:num_train + num_val]
    test_indices = indices[num_train + num_val:]


    # create the splits
    splits = {
        'train': train_indices.tolist(),
        'val': val_indices.tolist(),
        'test': test_indices.tolist()
    }

    # store the splits in a json file
    with open(store_path, 'w') as f:
        json.dump(splits, f)


    # # create the splits
    # train_split = {}
    # val_split = {}
    # test_split = {}

    # for band in bands:
    #     print('creating splits for band: ', band)
    #     data = f[band]
    #     train_split[band] = data[train_indices]
    #     val_split[band] = data[val_indices]
    #     test_split[band] = data[test_indices]

    # # create the metadata splits
    # train_meta = meta[train_indices]
    # val_meta = meta[val_indices]
    # test_meta = meta[test_indices]

    # # create the output file
    # f_out = h5py.File(store_path, 'w')

    # # write the metadata
    # train_meta_out = f_out.create_dataset('train_metadata', data=train_meta)
    # val_meta_out = f_out.create_dataset('val_metadata', data=val_meta)
    # test_meta_out = f_out.create_dataset('test_metadata', data=test_meta)

    # # write the data
    # for band in bands:
    #     print('writing band: ', band)
    #     train_out = f_out.create_dataset('train_' + band, data=train_split[band])
    #     val_out = f_out.create_dataset('val_' + band, data=val_split[band])
    #     test_out = f_out.create_dataset('test_' + band, data=test_split[band])

    # # close the files
    # f.close()
    # f_out.close()


if __name__ == '__main__':
    create_splits(data_path, tile_info, store_path) 