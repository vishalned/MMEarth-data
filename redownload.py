import json
import os
import glob
import argparse


# set the following values based on the slurm script. 
# num_of_tiles =  1300000
# num_of_jobs = 40
# num_tiles_per_job = 33000
# tile_info_path = 'data/tile_info/*.json'

def main(args):
    # num_tiles_per_job = num_of_tiles // num_of_jobs
    num_of_tiles = args.num_of_tiles
    num_of_jobs = args.num_of_jobs
    num_tiles_per_job = args.num_tiles_per_job
    tile_info_path = args.tile_info_path


    tile_info_files = glob.glob(tile_info_path) 

    start = []
    stop = []
    total_files = 0

    for i in range(num_tiles_per_job, num_of_tiles+1, num_tiles_per_job):
        files = []
        for f in tile_info_files:
            # get all the files with the last number equal to i. This gets all the files
            # processed in that job or in subsequent redownloads
            if (f.split('.')[0].split('_')[-1] == str(i)):
                files.append(f)

        # read each file and append the count
        count = 0
        for f in files:
            print(f)
            count += len(json.load(open(f, 'r')).keys())
        print(f"Number of tiles processed: {count}")
        start.append(i-num_tiles_per_job + count)
        stop.append(i)
        total_files += num_tiles_per_job - count

        # print(i + count - 1, i - 1)cl
        


        # break
    for i in range(len(start)):
        print(f"Job {i} : {start[i]} to {stop[i]}")

    print(f"Total number of files to download: {total_files}")

    # write the start and stop to a file
    with open('start_stop_redownload.txt', 'w') as f:
        for i in range(len(start)):
            f.write(f"{start[i]} {stop[i]}\n")



if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--num_of_tiles', type=int, help='total number of tiles already downloaded', default=1300000)
    parser.add_argument('--num_of_jobs', type=int, help='total number of parallel slurm jobs when downloading the full tiles', default=40)
    parser.add_argument('--num_tiles_per_job', type=int, help='total number of tiles processed per job', default=33000)
    parser.add_argument('--tile_info_path', type=str, help='path to the tile_info files', default='data/tile_info/*.json', required=True)

    args = parser.parse_args()

    main(args)

    




