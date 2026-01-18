import os
import argparse
import json
import numpy as np
import pandas as pd
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# --------------------------------------------------------
# Chromosome reference data
# --------------------------------------------------------
CHROMOSOME_INFO = {
    "1":  {"length": 248956422, "centromere": 125000000},
    "2":  {"length": 242193529, "centromere": 93300000},
    "3":  {"length": 198295559, "centromere": 91000000},
    "4":  {"length": 190214555, "centromere": 50000000},
    "5":  {"length": 181538259, "centromere": 48800000},
    "6":  {"length": 170805979, "centromere": 60500000},
    "7":  {"length": 159345973, "centromere": 60100000},
    "8":  {"length": 145138636, "centromere": 45200000},
    "9":  {"length": 138394717, "centromere": 43000000},
    "10": {"length": 133797422, "centromere": 39800000},
    "11": {"length": 135086622, "centromere": 53400000},
    "12": {"length": 133275309, "centromere": 35500000},
    "13": {"length": 114364328, "centromere": 17500000},
    "14": {"length": 107043718, "centromere": 17200000},
    "15": {"length": 101991189, "centromere": 19000000},
    "16": {"length": 90338345,  "centromere": 36800000},
    "17": {"length": 83257441,  "centromere": 25100000},
    "18": {"length": 80373285,  "centromere": 18500000},
    "19": {"length": 58617616,  "centromere": 28600000},
    "20": {"length": 64444167,  "centromere": 27500000},
    "21": {"length": 46709983,  "centromere": 13200000},
    "22": {"length": 50818468,  "centromere": 14700000},
    "X":  {"length": 156040895, "centromere": 60000000},
    "Y":  {"length": 57227415,  "centromere": 11000000},
}

# --------------------------------------------------------
# Default CNV Type to Chromosome Mapping - Simplified version with only basic types
# --------------------------------------------------------
DEFAULT_CNV_MAPPING = {
    # Simple mapping with only deletion, duplication, normal, and cn_loh types
    "1": ["deletion"],
    "2": ["deletion"],
    "3": ["deletion"],
    "4": ["normal"],
    "5": ["normal"],
    "6": ["normal"],
    "7": ["cn_loh"],
    "8": ["duplication"],
    "9": ["duplication"],
    "10": ["duplication"],
    "11": ["duplication"],
    "12": ["duplication"],
    "13": ["deletion"],
    "14": ["deletion"],
    "15": ["duplication"],
    "16": ["deletion"],
    "17": ["duplication"],
    "18": ["normal"],
    "19": ["deletion", "duplication", "cn_loh"],  # Showcase with all three types
    "20": ["deletion"],
    "21": ["duplication"],
    "22": ["cn_loh"],
    "X": ["normal"],
    "Y": ["normal"]
}

# --------------------------------------------------------
# Illumina cnvPartition parameters for various genotypes
# --------------------------------------------------------
ILLUMINA_GENOTYPE_PARAMS = {
    # CNV type: [(genotype, LRR_mean, LRR_sd, BAF_mean, BAF_sd, weight), ...]
    "0": [("DD", -5.0, 2.0, None, None, 1.0)],  # Double deletion
    "1": [("A", -0.45, 0.18, 0.0, 0.03, 0.5),   # Deletion of one allele
          ("B", -0.45, 0.18, 1.0, 0.03, 0.5)],
    "2": [("AA", 0.0, 0.18, 0.0, 0.03, 0.25),   # Normal - homozygous A
          ("AB", 0.0, 0.18, 0.5, 0.03, 0.5),    # Normal - heterozygous
          ("BB", 0.0, 0.18, 1.0, 0.03, 0.25)],  # Normal - homozygous B
    "3": [("AAA", 0.3, 0.18, 0.0, 0.03, 0.25),  # Duplication - AAA
          ("AAB", 0.3, 0.18, 1/3, 0.03, 0.25),  # Duplication - AAB
          ("ABB", 0.3, 0.18, 2/3, 0.03, 0.25),  # Duplication - ABB
          ("BBB", 0.3, 0.18, 1.0, 0.03, 0.25)], # Duplication - BBB
    "4": [("AAAA", 0.75, 0.18, 0.0, 0.03, 0.25),   # 4 copies - AAAA
          ("AAAB", 0.75, 0.18, 0.25, 0.03, 0.25),  # 4 copies - AAAB
          ("ABBB", 0.75, 0.18, 0.75, 0.03, 0.25),  # 4 copies - ABBB
          ("BBBB", 0.75, 0.18, 1.0, 0.03, 0.25)]   # 4 copies - BBBB
}

# --------------------------------------------------------
# Helper functions to generate segments and SNP data
# --------------------------------------------------------
def generate_controlled_segments(chromosomes, region_counts, size_range, genome_sizes, cnv_mapping=None):
    """Generate segments with controlled CNV type placement based on chromosome mapping, avoiding centromeres.
    For normal segments, ensure they span the entire chromosome length."""
    segments = {chrom: [] for chrom in chromosomes}
    
    # Use default mapping if none provided
    if cnv_mapping is None:
        cnv_mapping = DEFAULT_CNV_MAPPING
    
    for chrom in chromosomes:
        used = []
        max_len = genome_sizes[chrom]
        max_seg = min(size_range[1], max_len // 4)
        min_seg = min(size_range[0], max_len // 10)
        
        # Get centromere position
        if chrom in CHROMOSOME_INFO:
            centromere_pos = CHROMOSOME_INFO[chrom]["centromere"]
            # Define centromere buffer zone (10Mb around centromere position)
            centromere_start = max(1, centromere_pos - 5_000_000)
            centromere_end = min(max_len, centromere_pos + 5_000_000)
        else:
            # Default for unknown chromosomes
            centromere_start = max_len // 2 - 5_000_000
            centromere_end = max_len // 2 + 5_000_000
        
        # Determine which CNV types can be placed on this chromosome
        allowed_cnv_types = cnv_mapping.get(chrom, ["deletion", "duplication", "cn_loh"])
        
        # Always allow normal regions on all chromosomes
        if "normal" not in allowed_cnv_types:
            allowed_cnv_types.append("normal")
        
        # First, create the normal segments that span the entire chromosome
        # Create p-arm normal segment
        if centromere_start > 1:
            segments[chrom].append((1, centromere_start - 1, "normal"))
            used.append((1, centromere_start - 1, "normal"))
        
        # Create q-arm normal segment
        if centromere_end < max_len:
            segments[chrom].append((centromere_end + 1, max_len, "normal"))
            used.append((centromere_end + 1, max_len, "normal"))
        
        # Calculate counts for each allowed non-normal type
        non_normal_types = [t for t in allowed_cnv_types if t != "normal"]
        if non_normal_types:
            # Special handling for chromosome 19 to ensure all types are placed
            if chrom == "19" and len(non_normal_types) > 1:
                # Ensure at least one of each type for chromosome 19
                chrom_counts = {cnv_type: 1 for cnv_type in non_normal_types}
                
                # Set larger segments for better visualization
                min_seg = max(min_seg, 10_000_000)  # Ensure segments are at least 10Mb
                max_seg = max(max_seg, 20_000_000)  # Allow segments up to 20Mb
            else:
                # Calculate total non-normal regions to place
                non_normal_total = sum(region_counts.get(t, 1) for t in ["deletion", "duplication", "cn_loh"])
                
                # Distribute evenly among allowed types
                per_type_count = max(1, non_normal_total // len(non_normal_types))
                
                # Create a dictionary of counts for this chromosome
                chrom_counts = {}
                for cnv_type in non_normal_types:
                    chrom_counts[cnv_type] = per_type_count
        else:
            # If only normal regions are allowed
            chrom_counts = {}
        
        # Place non-normal segments according to allowed types and counts
        for region_type, count in chrom_counts.items():
            for _ in range(count):
                seg_len = np.random.randint(min_seg, max_seg + 1)
                for attempt in range(5000):
                    # Randomly choose p-arm or q-arm placement to avoid centromere
                    if np.random.random() < 0.5 and centromere_start > min_seg + 1:
                        # p-arm placement
                        start = np.random.randint(1, centromere_start - seg_len)
                    else:
                        # q-arm placement
                        start = np.random.randint(centromere_end, max_len - seg_len)
                    
                    end = start + seg_len
                    
                    # Check for overlap with existing non-normal segments
                    if not any(start <= u_end and end >= u_start for u_start, u_end, u_type in used if u_type != "normal"):
                        used.append((start, end, region_type))
                        segments[chrom].append((start, end, region_type))
                        
                        # Update the normal segments to account for this non-normal segment
                        updated_normal_segments = []
                        for norm_start, norm_end, norm_type in [s for s in segments[chrom] if s[2] == "normal"]:
                            # If this normal segment overlaps with the new non-normal segment
                            if start <= norm_end and end >= norm_start:
                                # Create up to two new normal segments (before and after)
                                if norm_start < start:
                                    updated_normal_segments.append((norm_start, start - 1, "normal"))
                                if norm_end > end:
                                    updated_normal_segments.append((end + 1, norm_end, "normal"))
                            else:
                                # This normal segment is not affected
                                updated_normal_segments.append((norm_start, norm_end, "normal"))
                        
                        # Replace normal segments with updated ones
                        segments[chrom] = [s for s in segments[chrom] if s[2] != "normal"] + updated_normal_segments
                        break
                else:
                    # Fallback if we couldn't place after many attempts
                    if np.random.random() < 0.5 and centromere_start > min_seg + 1:
                        start = np.random.randint(1, centromere_start - min_seg)
                    else:
                        start = np.random.randint(centromere_end, max_len - min_seg)
                    
                    end = start + min_seg
                    used.append((start, end, region_type))
                    segments[chrom].append((start, end, region_type))
                    
                    # Update normal segments here too
                    updated_normal_segments = []
                    for norm_start, norm_end, norm_type in [s for s in segments[chrom] if s[2] == "normal"]:
                        if start <= norm_end and end >= norm_start:
                            if norm_start < start:
                                updated_normal_segments.append((norm_start, start - 1, "normal"))
                            if norm_end > end:
                                updated_normal_segments.append((end + 1, norm_end, "normal"))
                        else:
                            updated_normal_segments.append((norm_start, norm_end, "normal"))
                    
                    segments[chrom] = [s for s in segments[chrom] if s[2] != "normal"] + updated_normal_segments
                    logging.warning(f"Fallback placement for {chrom} {region_type}")
    
    # Log segment counts for debugging
    for chrom in chromosomes:
        normal_segments = [s for s in segments[chrom] if s[2] == "normal"]
        non_normal_segments = [s for s in segments[chrom] if s[2] != "normal"]
        logging.info(f"Chromosome {chrom}: {len(normal_segments)} normal segments, {len(non_normal_segments)} non-normal segments")
        
        # Check coverage
        normal_bases = sum(end - start + 1 for start, end, _ in normal_segments)
        non_normal_bases = sum(end - start + 1 for start, end, _ in non_normal_segments)
        centromere_size = CHROMOSOME_INFO[chrom]["centromere"] + 10_000_000 if chrom in CHROMOSOME_INFO else 10_000_000
        expected_total = genome_sizes[chrom] - centromere_size
        actual_total = normal_bases + non_normal_bases
        coverage_pct = (actual_total / genome_sizes[chrom]) * 100
        logging.info(f"Chromosome {chrom} coverage: {coverage_pct:.2f}% ({actual_total:,} bp of {genome_sizes[chrom]:,} bp)")
    
    return segments

def generate_realistic_positions(chrom, total_snps):
    """Generate realistic SNP positions that span the entire chromosome length, avoiding centromeres."""
    if chrom in CHROMOSOME_INFO:
        chrom_length = CHROMOSOME_INFO[chrom]["length"]
        centromere_pos = CHROMOSOME_INFO[chrom]["centromere"]
        # Define centromere buffer zone (15Mb around centromere position)
        centromere_start = max(1, centromere_pos - 7_500_000)
        centromere_end = min(chrom_length, centromere_pos + 7_500_000)
    else:
        chrom_length = 100000000  # Default fallback value
        centromere_start = 45000000  # Approximate default for unknown chromosomes
        centromere_end = 55000000
        logging.warning(f"Using default chromosome length for unknown chromosome {chrom}")
    
    # First generate more positions than needed because we'll filter some out
    extra_factor = 1.3  # Generate 30% more positions to account for filtering
    total_to_generate = int(total_snps * extra_factor)
    
    # Create initial uniform distribution
    uniform_positions = np.sort(np.random.randint(1, chrom_length, size=total_to_generate))
    
    # Filter out positions in centromeric region
    uniform_positions = uniform_positions[
        ~((uniform_positions >= centromere_start) & (uniform_positions <= centromere_end))
    ]
    
    # Apply some clustering to create more realistic patterns
    clustered_positions = []
    for i, pos in enumerate(uniform_positions):
        # Add some local clustering
        if np.random.random() < 0.3:  # 30% chance of creating a small cluster
            cluster_size = np.random.randint(2, 6)
            cluster_spread = np.random.randint(100, 5000)
            for j in range(cluster_size):
                cluster_pos = pos + np.random.randint(-cluster_spread, cluster_spread)
                # Only add if in valid range and not in centromere
                if (1 <= cluster_pos <= chrom_length and 
                    not (centromere_start <= cluster_pos <= centromere_end)):
                    clustered_positions.append(cluster_pos)
        else:
            clustered_positions.append(pos)
    
    # Take the requested number of SNPs
    if len(clustered_positions) >= total_snps:
        positions = np.sort(np.random.choice(clustered_positions, size=total_snps, replace=False))
    else:
        # If we don't have enough positions after filtering, use what we have
        logging.warning(f"Only generated {len(clustered_positions)} SNPs for chromosome {chrom} after filtering")
        positions = np.sort(clustered_positions)
    
    return positions

def generate_baf_lrr_values(region_type, n_snps):
    """Generate realistic BAF and LRR values based on region type using Illumina cnvPartition parameters.
    Creates variations within basic types based on Illumina parameter specifications."""
    # Parse region type to determine the CN state
    if region_type == 'normal':
        # Normal regions (CN=2)
        cn = "2"
        # Standard normal distribution using all genotypes (AA, AB, BB)
        genotype_models = ILLUMINA_GENOTYPE_PARAMS[cn]
        
    elif region_type == 'deletion':
        # Deletion (CN=1)
        cn = "1"
        
        # Special case for chromosome 19 - create variation in deletion types
        # For other chromosomes, use the standard mix of A and B deletions
        if np.random.random() < 0.5:  # Randomly select A or B predominant deletions 
            # Create a variation with predominant A genotype (BAF near 0)
            genotype_models = [
                ("A", -0.45, 0.18, 0.0, 0.03, 0.9),   # 90% A genotype
                ("B", -0.45, 0.18, 1.0, 0.03, 0.1)    # 10% B genotype
            ]
        else:
            # Create a variation with predominant B genotype (BAF near 1)
            genotype_models = [
                ("A", -0.45, 0.18, 0.0, 0.03, 0.1),   # 10% A genotype
                ("B", -0.45, 0.18, 1.0, 0.03, 0.9)    # 90% B genotype
            ]
        
    elif region_type == 'duplication':
        # Duplication (CN=3)
        cn = "3"
        
        # Special case for chromosome 19 - create variation in duplication types
        # For other chromosomes, use the standard mix of all duplication genotypes
        variant_type = np.random.randint(0, 4)  # Randomly select one of 4 duplication patterns
        
        if variant_type == 0:
            # Create a variation with predominantly AAA genotype (BAF near 0)
            genotype_models = [
                ("AAA", 0.3, 0.18, 0.0, 0.03, 0.85),   # 85% AAA genotype
                ("AAB", 0.3, 0.18, 1/3, 0.03, 0.05),   # 5% AAB genotype
                ("ABB", 0.3, 0.18, 2/3, 0.03, 0.05),   # 5% ABB genotype
                ("BBB", 0.3, 0.18, 1.0, 0.03, 0.05)    # 5% BBB genotype
            ]
        elif variant_type == 1:
            # Create a variation with predominantly AAB genotype (BAF near 1/3)
            genotype_models = [
                ("AAA", 0.3, 0.18, 0.0, 0.03, 0.05),   # 5% AAA genotype
                ("AAB", 0.3, 0.18, 1/3, 0.03, 0.85),   # 85% AAB genotype
                ("ABB", 0.3, 0.18, 2/3, 0.03, 0.05),   # 5% ABB genotype
                ("BBB", 0.3, 0.18, 1.0, 0.03, 0.05)    # 5% BBB genotype
            ]
        elif variant_type == 2:
            # Create a variation with predominantly ABB genotype (BAF near 2/3)
            genotype_models = [
                ("AAA", 0.3, 0.18, 0.0, 0.03, 0.05),   # 5% AAA genotype
                ("AAB", 0.3, 0.18, 1/3, 0.03, 0.05),   # 5% AAB genotype
                ("ABB", 0.3, 0.18, 2/3, 0.03, 0.85),   # 85% ABB genotype
                ("BBB", 0.3, 0.18, 1.0, 0.03, 0.05)    # 5% BBB genotype
            ]
        else:
            # Create a variation with predominantly BBB genotype (BAF near 1)
            genotype_models = [
                ("AAA", 0.3, 0.18, 0.0, 0.03, 0.05),   # 5% AAA genotype
                ("AAB", 0.3, 0.18, 1/3, 0.03, 0.05),   # 5% AAB genotype
                ("ABB", 0.3, 0.18, 2/3, 0.03, 0.05),   # 5% ABB genotype
                ("BBB", 0.3, 0.18, 1.0, 0.03, 0.85)    # 85% BBB genotype
            ]
        
    elif region_type == 'cn_loh':
        # Copy-neutral LOH (CN=2, but only homozygous genotypes)
        cn = "2"
        # Create a special case for cn_loh with only homozygous genotypes
        genotype_models = [
            ("AA", 0.0, 0.18, 0.0, 0.03, 0.5),  # 50% AA genotype
            ("BB", 0.0, 0.18, 1.0, 0.03, 0.5)   # 50% BB genotype
        ]
        
    else:
        # Fallback for unknown region types
        cn = "2"  # Default to normal
        genotype_models = ILLUMINA_GENOTYPE_PARAMS[cn]
    
    # Initialize arrays
    baf_values = np.zeros(n_snps)
    lrr_values = np.zeros(n_snps)
    
    # For each SNP, randomly select a genotype according to the weights
    genotypes = [model[0] for model in genotype_models]
    weights = [model[5] for model in genotype_models]
    selected_genotypes = np.random.choice(range(len(genotypes)), size=n_snps, p=weights)
    
    # For each SNP, generate BAF and LRR values based on the selected genotype
    for i in range(n_snps):
        genotype_idx = selected_genotypes[i]
        _, lrr_mean, lrr_sd, baf_mean, baf_sd, _ = genotype_models[genotype_idx]
        
        # Generate LRR value
        lrr_values[i] = np.random.normal(lrr_mean, lrr_sd)
        
        # Generate BAF value
        if baf_mean is None:  # Special case for homozygous deletion
            # For homozygous deletions, BAF is a uniform distribution between 0 and 1
            baf_values[i] = np.random.uniform(0, 1)
        else:
            baf_values[i] = np.random.normal(baf_mean, baf_sd)
    
    # Clip BAF values to [0, 1]
    baf_values = np.clip(baf_values, 0, 1)
    
    return baf_values, lrr_values

def generate_continuous_snp_data(chromosomes, segments, genome_sizes, average_snps_per_mb=200):
    """Generate continuous SNP data that spans entire chromosomes."""
    all_snps = []
    
    for chrom in chromosomes:
        # Calculate total SNPs based on chromosome length and desired density
        chrom_length_mb = genome_sizes[chrom] / 1000000
        total_snps = int(chrom_length_mb * average_snps_per_mb)
        
        # Generate positions that span the entire chromosome
        positions = generate_realistic_positions(chrom, total_snps)
        
        # Create default normal values for the entire chromosome
        baf_values = np.zeros(len(positions))
        lrr_values = np.zeros(len(positions))
        cn_values = np.full(len(positions), 2)  # Default CN=2 (normal)
        p_cn = np.zeros((len(positions), 5))  # Now including CN=0 and CN=4
        
        # Set default probabilities for normal regions
        for i in range(len(positions)):
            p_cn[i, 2] = 0.9  # 90% probability of CN=2
            p_cn[i, 0] = 0.02  # Small probability for other values
            p_cn[i, 1] = 0.03  # CN=1
            p_cn[i, 3] = 0.03  # CN=3
            p_cn[i, 4] = 0.02  # CN=4
        
        # Generate default normal BAF and LRR
        default_baf, default_lrr = generate_baf_lrr_values('normal', len(positions))
        baf_values = default_baf
        lrr_values = default_lrr
        
        # Overlay segment-specific values
        chrom_segments = segments.get(chrom, [])
        for start, end, region_type in chrom_segments:
            # Find SNPs within this segment
            segment_indices = np.where((positions >= start) & (positions <= end))[0]
            
            if len(segment_indices) > 0:
                # Generate segment-specific BAF and LRR values
                segment_baf, segment_lrr = generate_baf_lrr_values(region_type, len(segment_indices))
                
                # Apply to the segment indices
                baf_values[segment_indices] = segment_baf
                lrr_values[segment_indices] = segment_lrr
                
                # Update CN values and probabilities based on region type
                if region_type == 'deletion':
                    # Deletion (CN=1)
                    cn_values[segment_indices] = 1
                    for i in segment_indices:
                        p_cn[i] = [0.05, 0.9, 0.03, 0.01, 0.01]  # High prob for CN=1
                
                elif region_type == 'normal':
                    # Normal region (CN=2)
                    cn_values[segment_indices] = 2
                    for i in segment_indices:
                        p_cn[i] = [0.02, 0.03, 0.9, 0.03, 0.02]  # High prob for CN=2
                
                elif region_type == 'duplication':
                    # Duplication (CN=3)
                    cn_values[segment_indices] = 3
                    for i in segment_indices:
                        p_cn[i] = [0.01, 0.01, 0.03, 0.9, 0.05]  # High prob for CN=3
                
                elif region_type == 'cn_loh':
                    # Copy-neutral LOH - keeps CN=2 but with only homozygous genotypes
                    cn_values[segment_indices] = 2
                    for i in segment_indices:
                        p_cn[i] = [0.01, 0.01, 0.95, 0.02, 0.01]  # Very high prob for CN=2
        
        # Create DataFrame for this chromosome
        df = pd.DataFrame({
            'Chromosome': chrom,
            'Position': positions,
            'BAF': baf_values,
            'LRR': lrr_values,
            'CN': cn_values,
            'P(CN0)': p_cn[:,0], 
            'P(CN1)': p_cn[:,1],
            'P(CN2)': p_cn[:,2], 
            'P(CN3)': p_cn[:,3],
            'P(CN4)': p_cn[:,4]
        })
        
        all_snps.append(df)
    
    # Combine all chromosomes
    return pd.concat(all_snps, ignore_index=True).sort_values(['Chromosome', 'Position'])

# --------------------------------------------------------
# Single sample simulation
# --------------------------------------------------------
def simulate_single(sample_name, params, outdir=None, prefix='single', use_subdir=True):
    base_dir = outdir or params['output_dir']
    if use_subdir:
        sample_dir = os.path.join(base_dir, f"{prefix}_{sample_name}")
    else:
        sample_dir = base_dir
    os.makedirs(sample_dir, exist_ok=True)

    chroms = params['chromosomes'] + ['X']
    if params.get('gender','female')=='male':
        chroms.append('Y')

    # Use controlled segment generation with CNV mapping
    segments = generate_controlled_segments(
        chroms, 
        params['region_counts'],
        params['segment_size_range'], 
        params['genome_sizes'],
        params.get('cnv_mapping')
    )
    
    # Use the new continuous SNP data generator
    snp_df = generate_continuous_snp_data(chroms, segments, params['genome_sizes'])

    # write pre/post SNP files
    baf_lrr = snp_df[['Chromosome','Position','BAF','LRR']]
    
    # Handle probability columns - now there's a P(CN4) column too
    if 'P(CN4)' in snp_df.columns:
        probs = snp_df[['Chromosome','Position','CN','P(CN0)','P(CN1)','P(CN2)','P(CN3)','P(CN4)']]
    else:
        # For backward compatibility
        probs = snp_df[['Chromosome','Position','CN','P(CN0)','P(CN1)','P(CN2)','P(CN3)']]
        
    baf_lrr.to_csv(os.path.join(sample_dir, f"{prefix}_baf_lrr_data_{sample_name}.csv"), index=False)
    probs.to_csv(os.path.join(sample_dir, f"{prefix}_cn_probabilities_data_{sample_name}.csv"), index=False)

    # summary and beds
    summary, cn_bed, roh_bed, union_bed, cnv_chrom, det_filtered = ([] for _ in range(6))
    for chrom, segs in segments.items():
        for start, end, rtype in segs:
            sub = snp_df[(snp_df.Chromosome==chrom)&(snp_df.Position.between(start,end))]
            nSites = len(sub)
            nHETs = ((sub.BAF.between(0.3,0.7))).sum()
            cn_mode = int(sub.CN.mode()[0]) if nSites>0 else 2
            qual = round(np.random.uniform(10,30),1)
            # Always add to summary regardless of CN state
            summary.append({'Region':'RG','Chromosome':chrom,'Start':start,'End':end,
                            'CopyNumber':cn_mode,'Quality':qual,'nSites':nSites,'nHETs':nHETs,'Sample':sample_name})
            # Only add to cn_bed and det_filtered if it's not normal
            if cn_mode!=2:
                cn_bed.append({'Chromosome':chrom,'Start':start,'End':end,'Length':end-start+1})
                det_filtered.append({'Chromosome':chrom,'Start':start,'End':end,
                                     'CN':cn_mode,'QS':qual,'nSites':nSites,'nHets':nHETs,
                                     'Length':end-start+1,'Type':rtype.capitalize(),'Sample':sample_name})
            if rtype=='cn_loh':
                roh_bed.append({'Chromosome':chrom,'Start':start,'End':end,'Length':end-start+1})
            if rtype!='normal':
                union_bed.append({'Chromosome':chrom,'Start':start,'End':end,'Length':end-start+1})
            # Include deletion, duplication, and cn_loh
            if rtype in ['deletion', 'duplication', 'cn_loh'] or cn_mode != 2:
                cnv_chrom.append({'Chromosome':chrom,'Start':start,'End':end,
                                  'CN':cn_mode,'QS':qual,'nSites':nSites,'nHets':nHETs,
                                  'Len':end-start+1,'type':rtype.capitalize(),'sample_name':sample_name})
    pd.DataFrame(summary).to_csv(os.path.join(sample_dir,f"{prefix}_cn_summary_data_{sample_name}.csv"),index=False)
    pd.DataFrame(cn_bed).to_csv(os.path.join(sample_dir,f"{prefix}_cn_bed_{sample_name}.csv"),index=False)
    pd.DataFrame(roh_bed).to_csv(os.path.join(sample_dir,f"{prefix}_roh_bed_{sample_name}.csv"),index=False)
    pd.DataFrame(union_bed).to_csv(os.path.join(sample_dir,f"{prefix}_union_bed_{sample_name}.csv"),index=False)
    pd.DataFrame(cnv_chrom).to_csv(os.path.join(sample_dir,f"{prefix}_cnv_chromosomes_{sample_name}.csv"),index=False)
    pd.DataFrame(det_filtered).to_csv(os.path.join(sample_dir,f"{prefix}_cnv_detection_filtered_{sample_name}.csv"),index=False)
    return segments, snp_df

# --------------------------------------------------------
# Paired sample simulation
# --------------------------------------------------------
def simulate_paired(sample_pre, sample_post, params):
    pair_id = f"PRE_{sample_pre}_POST_{sample_post}"
    base = os.path.join(params['output_dir'], pair_id)
    os.makedirs(base, exist_ok=True)

    # Generate individual pre/post files WITH PAIR ID
    simulate_single(pair_id, params, outdir=base, prefix='pre', use_subdir=False)
    simulate_single(pair_id, params, outdir=base, prefix='post', use_subdir=False)

    # Generate combined files
    chroms = params['chromosomes'] + ['X']
    if params.get('gender','female')=='male':
        chroms.append('Y')
    
    # Use controlled segment generation with CNV mapping
    segments = generate_controlled_segments(
        chroms, 
        params['region_counts'],
        params['segment_size_range'], 
        params['genome_sizes'],
        params.get('cnv_mapping')
    )
    
    # Create pre/post DataFrames using continuous generator
    pre_df = generate_continuous_snp_data(chroms, segments, params['genome_sizes'])
    post_df = generate_continuous_snp_data(chroms, segments, params['genome_sizes'])
    
    # Save pre/post dataframes with pair ID
    pre_df[['Chromosome','Position','BAF','LRR']].to_csv(
        os.path.join(base, f"pre_baf_lrr_data_{pair_id}.csv"), index=False)
    post_df[['Chromosome','Position','BAF','LRR']].to_csv(
        os.path.join(base, f"post_baf_lrr_data_{pair_id}.csv"), index=False)
    
    # Handle probability columns - now there's a P(CN4) column too
    if 'P(CN4)' in pre_df.columns:
        pre_df[['Chromosome','Position','CN','P(CN0)','P(CN1)','P(CN2)','P(CN3)','P(CN4)']].to_csv(
            os.path.join(base, f"pre_cn_probabilities_data_{pair_id}.csv"), index=False)
        post_df[['Chromosome','Position','CN','P(CN0)','P(CN1)','P(CN2)','P(CN3)','P(CN4)']].to_csv(
            os.path.join(base, f"post_cn_probabilities_data_{pair_id}.csv"), index=False)
    else:
        # For backward compatibility
        pre_df[['Chromosome','Position','CN','P(CN0)','P(CN1)','P(CN2)','P(CN3)']].to_csv(
            os.path.join(base, f"pre_cn_probabilities_data_{pair_id}.csv"), index=False)
        post_df[['Chromosome','Position','CN','P(CN0)','P(CN1)','P(CN2)','P(CN3)']].to_csv(
            os.path.join(base, f"post_cn_probabilities_data_{pair_id}.csv"), index=False)

    # Build combined files with pair ID
    combined_cn_bed, combined_cnv_chrom, combined_det = [], [], []
    combined_roh, combined_union = [], []
    
    # New list for combined summary that includes all segments
    combined_summary = []
    
    for chrom, segs in segments.items():
        for start, end, rtype in segs:
            sub_pre = pre_df[(pre_df.Chromosome==chrom)&(pre_df.Position.between(start,end))]
            sub_post = post_df[(post_df.Chromosome==chrom)&(post_df.Position.between(start,end))]
            pre_cn = int(sub_pre.CN.mode()[0]) if len(sub_pre) > 0 else 2
            post_cn = int(sub_post.CN.mode()[0]) if len(sub_post) > 0 else 2
            qs = round(np.random.uniform(10,30),1)
            pre_n = len(sub_pre)
            post_n = len(sub_post)
            pre_h = sub_pre.BAF.between(0.3,0.7).sum() if len(sub_pre) > 0 else 0
            post_h = sub_post.BAF.between(0.3,0.7).sum() if len(sub_post) > 0 else 0
            length = end-start+1
            
            # Add all segments to the combined summary regardless of type
            combined_summary.append({
                'Region': 'RG',
                'Chromosome': chrom,
                'Start': start,
                'End': end,
                'CopyNumber_pre': pre_cn,
                'CopyNumber_post': post_cn,
                'Quality': qs,
                'nSites_pre': pre_n,
                'nHETs_pre': pre_h,
                'nSites_post': post_n,
                'nHETs_post': post_h,
                'Length': length,
                'Sample': pair_id
            })
            
            if pre_cn!=2 or post_cn!=2:
                combined_cn_bed.append({'Chromosome':chrom,'Start':start,'End':end,'Length':length})
            # Include deletion, duplication, and cn_loh
            if rtype in ['deletion', 'duplication', 'cn_loh'] or pre_cn != 2 or post_cn != 2:
                combined_cnv_chrom.append({'Region':'RG','Chromosome':chrom,'Start':start,'End':end,
                                            'CN_post':post_cn,'CN_pre':pre_cn,'QS':qs,
                                            'nSites_post':post_n,'nHets_post':post_h,
                                            'nSites_pre':pre_n,'nHets_pre':pre_h,
                                            'Delta_CN':post_cn-pre_cn,'Length':length})
            if pre_cn!=2 or post_cn!=2:
                combined_det.append({'Chromosome':chrom,'Start':start,'End':end,
                                      'CN_post':post_cn,'CN_pre':pre_cn,'QualityScore':qs,
                                      'PostSites':post_n,'PostHets':post_h,
                                      'PreSites':pre_n,'PreHets':pre_h,'Length':length,
                                      'PreSample':sample_pre,'PostSample':sample_post,
                                      'Type':rtype.capitalize()})
            if rtype=='cn_loh':
                combined_roh.append({'Chromosome':chrom,'Start':start,'End':end,'Length':length})
            if rtype!='normal':
                combined_union.append({'Chromosome':chrom,'Start':start,'End':end,'Length':length})
    
    # Save combined summary file
    pd.DataFrame(combined_summary).to_csv(
        os.path.join(base, f"combined_cn_summary_data_{pair_id}.csv"), index=False)
        
    # Save combined files with pair_id
    pd.DataFrame(combined_cn_bed).to_csv(
        os.path.join(base, f"combined_cn_bed_{pair_id}.csv"), index=False)
    pd.DataFrame(combined_cnv_chrom).to_csv(
        os.path.join(base, f"combined_cnv_chromosomes_{pair_id}.csv"), index=False)
    pd.DataFrame(combined_det).to_csv(
        os.path.join(base, f"combined_cnv_detection_filtered_{pair_id}.csv"), index=False)
    pd.DataFrame(combined_roh).to_csv(
        os.path.join(base, f"combined_roh_bed_{pair_id}.csv"), index=False)
    pd.DataFrame(combined_union).to_csv(
        os.path.join(base, f"combined_union_bed_{pair_id}.csv"), index=False)

    # Update log file naming
    log_file = os.path.join(base, f'{pair_id}_preprocess_log.txt')
    with open(log_file,'w') as lg:
        lg.write(f"Paired simulation run: {datetime.now()}\n")
        lg.write(f"Pre-sample: {sample_pre}, Post-sample: {sample_post}\n")
        lg.write(json.dumps(params, indent=2))
    logging.info(f"Paired data generated in {base}")

# --------------------------------------------------------
# Main entrypoint
# --------------------------------------------------------
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Simulate CNV data')
    parser.add_argument('--mode', choices=['single','paired'], default='single',
                        help='Mode: single sample or paired samples')
    parser.add_argument('--sample1', dest='sample1',
                        help='Name for single sample (or PRE sample if paired)')
    parser.add_argument('--sample2', dest='sample2',
                        help='Name for POST sample in paired mode')
    parser.add_argument('--params', help='JSON file of parameters')
    parser.add_argument('--outdir', help='Output directory')
    args = parser.parse_args()

    # Default simulation parameters
    default_params = {
        'output_dir': 'simulated_data',
        'chromosomes': [str(i) for i in range(1,23)],
        'genome_sizes': {**{str(i): CHROMOSOME_INFO[str(i)]["length"] for i in range(1,23)}, 
                          'X': CHROMOSOME_INFO["X"]["length"], 
                          'Y': CHROMOSOME_INFO["Y"]["length"]},
        'gender': 'female',
        'region_counts': {'normal': 3, 'deletion': 1, 'duplication': 1, 'cn_loh': 1},  # Added cn_loh back
        'segment_size_range': (500_000, 5_000_000),
        'snps_per_segment': 200,
        'cnv_mapping': DEFAULT_CNV_MAPPING,  # Using the simplified mapping
    }

    # Override with user parameters file
    if args.params:
        with open(args.params) as pf:
            default_params.update(json.load(pf))
    # Override output directory
    if args.outdir:
        default_params['output_dir'] = args.outdir

    # Set fixed random seed for reproducibility
    np.random.seed(42)

    # Dispatch modes
    if args.mode == 'single':
        if not args.sample1:
            parser.error('Sample name required in single mode. Use --sample1.')
        simulate_single(args.sample1, default_params)
    else:
        if not args.sample1 or not args.sample2:
            parser.error('Both --sample1 and --sample2 required in paired mode.')
        simulate_paired(args.sample1, args.sample2, default_params)
