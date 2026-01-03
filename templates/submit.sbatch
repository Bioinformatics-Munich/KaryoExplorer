#!/bin/bash 
#SBATCH -o KaryoExplorer.log
#SBATCH -e KaryoExplorer.err
#SBATCH --job-name=KaryoExplorer
#SBATCH --mem=16G                    
#SBATCH -t 06:00:00                 
#SBATCH --partition=<partition_name>
#SBATCH --qos=<qos_name>
#SBATCH --nodes=1
#SBATCH --ntasks=1


set -eo pipefail

# for info
echo "Script started at $(date)"
echo "Submitted from directory: $(pwd)"
PROJECT_ID=$(pwd | grep -oP "P2[4-9]000/\K[^/]+")
printf "PROJECT_ID: $PROJECT_ID\n"

####################################################################################

# Set environment variables
export NXF_VER=24.10.4
export NXF_HOME="${HOME}/.nextflow"
export NXF_WORK="<scratch_directory_path>/${USER}/${PROJECT_ID}"
export NXF_CONDA_CACHEDIR="<conda_cache_directory_path>"
export TMPDIR=$NXF_WORK/tmp
export LOGS_DIR=$(pwd)/logs
export NXF_LOG_FILE=$(pwd)/.nextflow.log d
mkdir -p $TMPDIR
mkdir -p $LOGS_DIR
umask 0002

export NXF_SINGULARITY_CACHEDIR="<singularity_images_directory_path>"
export TMPDIR=$NXF_WORK/tmp
mkdir -p $TMPDIR
umask 0002


cd $(pwd) && \
nextflow run main.nf \
    -params-file params.yaml \
    -profile normal\
    --samples_refs $(pwd)/sample_sheet.xls \
    --outdir $(pwd)/../results \
    -with-conda \
    -resume \
    -with-report ${LOGS_DIR}/nextflow/report.html \
    -with-trace ${LOGS_DIR}/nextflow/trace.txt \
    -with-timeline ${LOGS_DIR}/nextflow/timeline.html && rm -rf <scratch_directory_path>/${USER}/${PROJECT_ID}

