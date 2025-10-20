#!/bin/bash 

#SBATCH --job-name=nef_to_jpeg 

#SBATCH --output=nef_to_jpeg_%j.out 

#SBATCH --error=nef_to_jpeg_%j.err 

#SBATCH --exclusive 

#SBATCH --partition=cpuq 

#SBATCH --time=01:00:00 

module load conda/anaconda3

conda activate nef_conversion

INPUT_FOLDER="/net/cluster1-prod-hpcnfs.aims.gov.au/3d-ltmp/EcoRRAP/data/202503/ONND/FR1/S/ECT1/1"
OUTPUT_FOLDER="/net/cluster1-prod-hpcnfs.aims.gov.au/3d-ltmp/EcoRRAP/data/202503/ONND/FR1/S/ECT1/1"

python convert_nef_to_jpeg.py "$INPUT_FOLDER" "$OUTPUT_FOLDER"
