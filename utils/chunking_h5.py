# take an existing h5 file, and create a new one with the same data but by using chunks.

import h5py
import numpy as np
import os
import argparse


def create_h5_file_with_chunks(h5_file_path = '', chunk_size = 1):
    """
    Create a new h5 file with the same data as the original file, but with the specified chunk size.
    :param h5_file_path: path to the original h5 file.
    :param chunk_size: chunk size to use.
    :return: None
    """
    # open the original file
    h5 = h5py.File(h5_file_path, 'r')
    keys = list(h5.keys())
    # create a new file
    name = h5_file_path.split('/')[-1][:-3]
    new_h5_file_path = os.path.join(os.path.dirname(h5_file_path), name + '_chunked_gzip.h5')
    print(new_h5_file_path)
    if os.path.exists(new_h5_file_path):
        os.remove(new_h5_file_path)
        
    new_h5 = h5py.File(new_h5_file_path, 'w')
    # the dataset is too big to load into memory, so we will iterate over the keys
    meta = h5['metadata']
    num_samples = meta.shape[0]
    for key in keys:
        print('creating dataset for key: ', key)
        shape = h5[key].shape
        tmp = new_h5.create_dataset(key, shape = h5[key].shape, dtype = h5[key].dtype, chunks = (chunk_size, *shape[1:]), compression = 'gzip')

        # iterate over the samples
        for i in range(num_samples):
            if i % 1000 == 0:
                print(key, i)
            # get the sample
            sample = h5[key][i]
            # write the sample to the new file
            tmp[i] = sample

        


    # close the files
    h5.close()
    new_h5.close()


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--h5_file_path', type=str, help='path to the h5 file', required=True)
    parser.add_argument('--chunk_size', type=int, help='chunk size to use', default=1)
    args = parser.parse_args()

    create_h5_file_with_chunks(h5_file_path = args.h5_file_path, chunk_size = args.chunk_size)