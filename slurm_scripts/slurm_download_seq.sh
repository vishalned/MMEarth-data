#!/bin/bash
#SBATCH --job-name=data-download

#SBATCH --tasks=1
#SBATCH --cpus-per-task=4
#SBATCH --time=8-00:00:00
# PATH TO SAVE SLURM LOGS
#SBATCH --output=/home/qbk152/vishal/slurm_logs/slurm-%A_%a_%x.out
# TOTAL MEMORY PER NODE
#SBATCH --mem=4G 
#SBATCH --exclude=hendrixgpu01fl,hendrixgpu02fl,hendrixgpu07fl,hendrixgpu08fl,hendrixgpu03fl,hendrixgpu04fl

echo "SLURM_JOB_NODELIST: $SLURM_JOB_NODELIST"



python /home/qbk152/vishal/global-lr/main_download.py start_from=4518 end_at=7500
