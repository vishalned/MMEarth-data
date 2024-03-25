#!/bin/bash
#SBATCH --job-name=1-mil-download

#SBATCH --array=0-39
#SBATCH --tasks=1
#SBATCH --cpus-per-task=4
#SBATCH --time=8-00:00:00
# PATH TO SAVE SLURM LOGS
#SBATCH --output=/home/qbk152/vishal/slurm_logs/slurm-%A_%a_%x.out
# TOTAL MEMORY PER NODE
#SBATCH --mem=4G 
#SBATCH --exclude=hendrixgpu01fl,hendrixgpu02fl,hendrixgpu07fl,hendrixgpu08fl,hendrixgpu03fl,hendrixgpu04fl

echo "SLURM_JOB_NODELIST: $SLURM_JOB_NODELIST"

# Read start and stop values from the file for each task ID
task_file="start_stop_redownload.txt"
line_number=$((SLURM_ARRAY_TASK_ID + 1))
start_from=$(sed -n "${line_number}p" "$task_file" | awk '{print $1}')
end_at=$(sed -n "${line_number}p" "$task_file" | awk '{print $2}')

echo "Task ID: $SLURM_ARRAY_TASK_ID, Start from: $start_from, End at: $end_at"

python /home/qbk152/vishal/global-lr/main_download.py start_from=$start_from end_at=$end_at
