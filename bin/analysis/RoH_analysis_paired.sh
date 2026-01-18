#!/usr/bin/env bash
set -euo pipefail

VCF="$1"
PRE="$2"
POST="$3"
WEIGHT_LRR="${4:-""}"

OUTDIR="${PRE}_${POST}"

# 1) Make output directories
mkdir -p "${OUTDIR}/cnv" "${OUTDIR}/roh"

# 2) Run bcftools cnv with `PRE` as reference and `POST` as the analyzed sample
# Build command with optional -l parameter
CNV_CMD="bcftools cnv -s $POST -c $PRE"
if [ -n "$WEIGHT_LRR" ]; then
    CNV_CMD="$CNV_CMD -l $WEIGHT_LRR"
fi
CNV_CMD="$CNV_CMD -o ${OUTDIR}/cnv/ $VCF"

eval "$CNV_CMD"

# 3) Run bcftools roh for PRE
bcftools roh \
    -G30 --AF-dflt 0.4 \
    -s "$PRE" \
    -o "${OUTDIR}/roh/roh_pre.txt" \
    "$VCF"

# 4) Run bcftools roh for POST
bcftools roh \
    -G30 --AF-dflt 0.4 \
    -s "$POST" \
    -o "${OUTDIR}/roh/roh_post.txt" \
    "$VCF"

# 5) Create a differential ROH file comparing PRE vs. POST
#    For example, lines unique to POST vs. PRE and vice versa.
#
#    This AWK script:
#      - Reads roh_pre.txt and caches each line (keyed by fields 1-4)
#      - Reads roh_post.txt, caches each line similarly
#      - Finally, any line in pre but not in post is "LOST_IN_POST",
#      - any line in post but not in pre is "NEW_IN_POST"

# Replace the existing awk script with this improved version:
awk '
BEGIN {
    OFS="\t"
    print "Status", "Chromosome", "Start", "End", "Quality", "Original_Line"
}

# Process PRE file
NR==FNR && /^RG/ {
    key = $3 ":" $4 "-" $5  # chr:start-end
    pre_intervals[key] = $0
    next
}

# Process POST file
NR>FNR && /^RG/ {
    chr=$3
    start=$4
    end=$5
    quality=$8
    key = chr ":" start "-" end
    
    if (key in pre_intervals) {
        # Present in both - mark as unchanged
        print "UNCHANGED", chr, start, end, quality, $0
        delete pre_intervals[key]
    } else {
        # New in POST
        print "NEW_IN_POST", chr, start, end, quality, $0
    }
}

END {
    # Remaining PRE intervals are lost
    for (key in pre_intervals) {
        split(pre_intervals[key], fields, "\t")
        print "LOST_IN_POST", fields[3], fields[4], fields[5], fields[8], pre_intervals[key]
    }
}' "${OUTDIR}/roh/roh_pre.txt" "${OUTDIR}/roh/roh_post.txt" > "${OUTDIR}/roh/roh_diff.txt"