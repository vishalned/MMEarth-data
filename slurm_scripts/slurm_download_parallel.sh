#!/bin/bash
#SBATCH --job-name=download

#SBATCH --array=0-39
#SBATCH --tasks=1
#SBATCH --cpus-per-task=4
#SBATCH --time=20-00:00:00
# PATH TO SAVE SLURM LOGS
#SBATCH --output=/home/qbk152/vishal/slurm_logs/slurm-%A_%a_%x.out
# TOTAL MEMORY PER NODE
#SBATCH --mem=16G 
#SBATCH --exclude=hendrixgpu01fl,hendrixgpu02fl,hendrixgpu07fl,hendrixgpu08fl,hendrixgpu03fl,hendrixgpu04fl

echo "SLURM_JOB_NODELIST: $SLURM_JOB_NODELIST"


task_per_job=37500 # this number is the total number of tiles divided by the number of jobs
start_from=$((SLURM_ARRAY_TASK_ID * task_per_job))
end_at=$((start_from + task_per_job))


python /home/qbk152/vishal/MMEarth-data/main_download.py start_from=$start_from end_at=$end_at



