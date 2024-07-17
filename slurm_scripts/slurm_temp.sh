#!/bin/bash
#SBATCH --job-name=chunk

#SBATCH --tasks=1
#SBATCH --cpus-per-task=4
#SBATCH --time=2-00:00:00
# PATH TO SAVE SLURM LOGS
#SBATCH --output=/home/qbk152/vishal/slurm_logs/temp-%A_%a_%x.out
# TOTAL MEMORY PER NODE
#SBATCH --mem=32G 
#SBATCH --exclude=hendrixgpu01fl,hendrixgpu02fl,hendrixgpu07fl,hendrixgpu08fl,hendrixgpu03fl,hendrixgpu04fl

echo "SLURM_JOB_NODELIST: $SLURM_JOB_NODELIST"


# use 16G of mem when running the below code
# python -u convert_to_h5.py \
#         --mode create \
#         --data_dir /projects/dereeco/data/global-lr/data_300k_130/ \
#         --tile_info /home/qbk152/vishal/global-lr/data/data_300k_130_tile_info.json \
#         --output_file /projects/dereeco/data/global-lr/data_300k_130/data_300k_130.h5\
#         --missing_tiles /home/qbk152/vishal/global-lr/data/missing_tiles_300k.csv

# python -u utils/utils.py
# python -u /home/qbk152/vishal/global-lr/normalization.py

# python -u utils/convert_to_h5.py \
#         --mode merge \
#         --data_dir1 /projects/dereeco/data/global-lr/data_1M_130_new/ \
#         --data_dir2 /projects/dereeco/data/global-lr/data_missing_130/ \
#         --output_path /projects/dereeco/data/global-lr/data_1M_130_new/data_1M_130_new2.h5 \

python -u post_download.py \
        --data_dir  /projects/dereeco/data/global-lr/data_1M_v001/

# python -u data_exp/data_exp.py \
#         --data_dir /projects/dereeco/data/global-lr/data_1M_130_new

#python -u utils/chunking_h5.py \
 #       --h5_file_path /projects/dereeco/data/global-lr/data_1M_130_new/data_1M_130_new.h5













