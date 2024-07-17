#!/bin/bash
#SBATCH --job-name=geojson-download

#SBATCH --tasks=1
#SBATCH --cpus-per-task=4
#SBATCH --time=2-00:00:00
# PATH TO SAVE SLURM LOGS
#SBATCH --output=/home/qbk152/vishal/slurm_logs/tiles-download-%A_%a_%x.out
# TOTAL MEMORY PER NODE
#SBATCH --mem=4G 
#SBATCH --exclude=hendrixgpu01fl,hendrixgpu02fl,hendrixgpu07fl,hendrixgpu08fl,hendrixgpu03fl,hendrixgpu04fl
echo "SLURM_JOB_NODELIST: $SLURM_JOB_NODELIST"



python -u /home/qbk152/vishal/MMEarth-data/create_tiles_polygon.py\
        tiles_geojson_path='/projects/dereeco/data/global-lr/geojson_files/tiles_1M_v001.geojson' \
        num_of_images=1500000 \
        tile_size=1300 \
        uniform_type=0 \



