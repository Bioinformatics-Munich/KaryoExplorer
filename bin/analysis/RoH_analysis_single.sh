#!/bin/bash
set -euo pipefail

VCF=$1
SAMPLE=$2
WEIGHT_LRR=${3:-""}

# Create output directories
mkdir -p "${SAMPLE}/roh" "${SAMPLE}/cnv"

# Build bcftools cnv command with optional -l parameter
CNV_CMD="bcftools cnv -s $SAMPLE"
if [ -n "$WEIGHT_LRR" ]; then
    CNV_CMD="$CNV_CMD -l $WEIGHT_LRR"
fi
CNV_CMD="$CNV_CMD -o ${SAMPLE}/cnv/ $VCF"

# Run bcftools commands - files will be created automatically with correct extensions
eval "$CNV_CMD"
bcftools roh -G30 --AF-dflt 0.4 -s ${SAMPLE} -o "${SAMPLE}/roh/roh.txt" $VCF 



