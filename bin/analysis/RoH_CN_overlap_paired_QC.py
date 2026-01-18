#!/usr/bin/env python3

import argparse
import pandas as pd
import numpy as np
from contextlib import redirect_stdout
import os

def main():
    parser = argparse.ArgumentParser(description='RoH-CN Overlap Analysis for Paired Samples')
    # Required arguments
    parser.add_argument('--roh', required=True, help='Input ROH differential file path')
    parser.add_argument('--cn_summary', required=True, help='CN summary file path')
    parser.add_argument('--output_dir', required=True, help='Output directory path')
    parser.add_argument('--pre_sample', required=True, help='Pre sample name')
    parser.add_argument('--post_sample', required=True, help='Post sample name')
    args = parser.parse_args()

    sample_pair = f"{args.pre_sample}_{args.post_sample}"
    
    # Set up logging and output
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)
    
    with open(f"{args.output_dir}/{sample_pair}.log.txt", 'w') as f:
        with redirect_stdout(f):
            try:
                print(f"=== Paired Analysis Report for {args.pre_sample} vs {args.post_sample} ===\n")
                print("Checking input files...")
                print(f"Found ROH differential file: {args.roh}")
                print(f"Found CN summary file: {args.cn_summary}\n")
                
                # Load and process ROH differential data
                print("\n1. ROH Differential Data Processing")
                print("----------------------------------")
                df_roh_diff = load_roh_differential(args.roh)
                
                if df_roh_diff.empty:
                    raise ValueError("ROH differential file is empty. Check input ROH files.")
                
                print("\nROH Differential Records summary:")
                print(f"Total NEW_IN_POST regions: {len(df_roh_diff[df_roh_diff['Status'] == 'NEW_IN_POST'])}")
                print(f"Total LOST_IN_POST regions: {len(df_roh_diff[df_roh_diff['Status'] == 'LOST_IN_POST'])}")
                
                # Filter by quality (P-value) only
                df_roh_diff['P_value'] = df_roh_diff['Quality'].apply(phred_to_p)
                df_roh_filtered = df_roh_diff[df_roh_diff['P_value'] < 0.05]
                
                print("\nAfter quality filtering (P < 0.05):")
                print(f"Total regions passing filter: {len(df_roh_filtered)}")
                print("Status distribution:")
                print(df_roh_filtered['Status'].value_counts())

                # Generate BED files for all statuses with quality filter
                print("\nGenerating quality-filtered BED files:")
                statuses = ['NEW_IN_POST', 'LOST_IN_POST', 'UNCHANGED']
                for status in statuses:
                    bed_path = f"{args.output_dir}/{sample_pair}.{status.lower().replace('_', '-')}.filtered.bed"
                    df_roh_filtered[df_roh_filtered['Status'] == status][['Chromosome', 'Start', 'End']]\
                        .to_csv(bed_path, sep='\t', index=False, header=False)
                    print(f"- {status}: {bed_path}")

                # Continue with overlap analysis for NEW/LOST_IN_POST only
                analysis_regions = df_roh_filtered
                
                # Load and process CN data
                print("\n2. CNV Data Processing")
                print("---------------------")
                df_summary = load_summary_tab(args.cn_summary, args.post_sample, args.pre_sample)
                
                if df_summary.empty:
                    raise ValueError("CN summary file is empty. Check CNV analysis output.")
                
                print("\nRaw CN Summary data (first 5 rows):")
                print(df_summary[['Chromosome', 'Start', 'End', 'Copy_Number_POST', 'Copy_Number_PRE', 'P_segment_CN']].head(5))
                
                print("\nInitial Copy Number Distribution:")
                print("POST CN Distribution:")
                print(df_summary['Copy_Number_POST'].value_counts().sort_index())
                print("\nPRE CN Distribution:")
                print(df_summary['Copy_Number_PRE'].value_counts().sort_index())

                # Apply filters
                initial_count = len(df_summary)
                df_summary = df_summary[df_summary['P_segment_CN'] < 0.05]
                pval_filter_count = len(df_summary)
                
                # MODIFIED: Enhanced filtering for cnLoH detection
                # Keep CN < 2 AND CN = 2 for comprehensive LoH analysis
                df_summary_loh = df_summary[(df_summary['Copy_Number_POST'] <= 2) | (df_summary['Copy_Number_PRE'] <= 2)]
                cn_filter_count = len(df_summary_loh)
                
                # Separate into categories for detailed analysis
                df_deletions = df_summary_loh[(df_summary_loh['Copy_Number_POST'] < 2) | (df_summary_loh['Copy_Number_PRE'] < 2)]
                df_normal_cn = df_summary_loh[(df_summary_loh['Copy_Number_POST'] == 2) & (df_summary_loh['Copy_Number_PRE'] == 2)]
                df_mixed = df_summary_loh[((df_summary_loh['Copy_Number_POST'] == 2) & (df_summary_loh['Copy_Number_PRE'] < 2)) |
                                         ((df_summary_loh['Copy_Number_POST'] < 2) & (df_summary_loh['Copy_Number_PRE'] == 2))]

                print(f"\nEnhanced Filtering Results for cnLoH Detection:")
                print(f"Initial count: {initial_count} segments")
                print(f"After P-value filtering (P < 0.05): {pval_filter_count} segments")
                print(f"After keeping CN ≤ 2 for LoH analysis: {cn_filter_count} segments")
                print(f"  - Deletions (CN < 2 in either sample): {len(df_deletions)} segments")
                print(f"  - Normal CN (CN = 2 in both samples): {len(df_normal_cn)} segments")
                print(f"  - Mixed CN states: {len(df_mixed)} segments")

                print("\nFiltered CN Segments for LoH analysis (first 5 rows):")
                print(df_summary_loh[['Chromosome', 'Start', 'End', 'Copy_Number_POST', 'Copy_Number_PRE', 'P_segment_CN']].head(5))
                
                print("\nFinal CN Distribution (POST sample):")
                print(df_summary_loh['Copy_Number_POST'].value_counts().sort_index())
                print("Final CN Distribution (PRE sample):")
                print(df_summary_loh['Copy_Number_PRE'].value_counts().sort_index())

                # Update df_summary to the LoH-focused dataset
                df_summary = df_summary_loh

                # Now proceed with filtered CN data
                print(f"\nTotal high-quality CN segments: {len(df_summary)}")
                
                # Add debug output
                print("\nFirst 3 ROH differential regions:")
                print(df_roh_diff.head(3))
                print("\nFirst 3 CN segments:")
                print(df_summary.head(3))
                
                # Analyze ROH and CN overlap
                print("\n3. ROH-CN Integration Analysis")
                print("-----------------------------")
                
                results = []
                
                # Process all regions regardless of status
                for status in ['NEW_IN_POST', 'LOST_IN_POST', 'UNCHANGED']:
                    status_regions = analysis_regions[analysis_regions['Status'] == status]
                    for _, roh_region in status_regions.iterrows():
                        cn_overlaps = find_cn_overlaps(roh_region, df_summary)
                        for cn_overlap in cn_overlaps:
                            event_type = classify_event(
                                cn_overlap['copy_number_post'], 
                                cn_overlap['copy_number_pre'],
                                status  # Pass actual status to classifier
                            )
                            results.append({
                                'Chromosome': roh_region['Chromosome'],
                                'Start': max(roh_region['Start'], cn_overlap['start']),
                                'End': min(roh_region['End'], cn_overlap['end']),
                                'Status': status,
                                'POST_CN': cn_overlap['copy_number_post'],
                                'PRE_CN': cn_overlap['copy_number_pre'],
                                'Event_Type': event_type
                            })
                
                # Create final results DataFrame
                df_results = pd.DataFrame(results)
                
                # Only proceed if there are results
                if not df_results.empty:
                    # Save detailed analysis with all columns
                    analysis_file = f"{args.output_dir}/{sample_pair}_detailed_analysis.txt"
                    df_results[['Chromosome', 'Start', 'End', 'Status', 'POST_CN', 'PRE_CN', 'Event_Type']]\
                        .to_csv(analysis_file, sep='\t', index=False)
                    print(f"Saved detailed analysis to {analysis_file}")

                    # Create simplified BED files
                    print("\nGenerating simplified BED files:")
                    
                    # For NEW_IN_POST regions
                    new_bed = f"{args.output_dir}/{sample_pair}.new_in_post.bed"
                    df_results[df_results['Status'] == 'NEW_IN_POST'][['Chromosome', 'Start', 'End']]\
                        .to_csv(new_bed, sep='\t', index=False, header=False)
                    print(f"- NEW_IN_POST regions: {new_bed}")
                    
                    # For LOST_IN_POST regions
                    lost_bed = f"{args.output_dir}/{sample_pair}.lost_in_post.bed"
                    df_results[df_results['Status'] == 'LOST_IN_POST'][['Chromosome', 'Start', 'End']]\
                        .to_csv(lost_bed, sep='\t', index=False, header=False)
                    print(f"- LOST_IN_POST regions: {lost_bed}")
                else:
                    print("\nNo overlapping regions found between ROH and CN data")

                # Generate comprehensive BED files
                print("\nGenerating full BED files for bedtools operations...")

                # 1. Full ROH differential BED (all regions)
                roh_full_bed = f"{args.output_dir}/{sample_pair}.full_roh.bed"
                df_roh_diff[['Chromosome', 'Start', 'End']].to_csv(
                    roh_full_bed, sep='\t', index=False, header=False
                )
                print(f"Saved {len(df_roh_diff)} ROH regions to {roh_full_bed}")

                # 2. Full CN segments BED (all regions)
                cn_full_bed = f"{args.output_dir}/{sample_pair}.full_cn.bed"
                df_summary[['Chromosome', 'Start', 'End']].to_csv(
                    cn_full_bed, sep='\t', index=False, header=False
                )
                print(f"Saved {len(df_summary)} CN segments to {cn_full_bed}")

                # Add UNCHANGED regions to full BED files
                unchanged_bed = f"{args.output_dir}/{sample_pair}.unchanged.bed"
                df_roh_diff[df_roh_diff['Status'] == 'UNCHANGED'][['Chromosome', 'Start', 'End']]\
                    .to_csv(unchanged_bed, sep='\t', index=False, header=False)
                print(f"Saved UNCHANGED regions to {unchanged_bed}")

                # Update BED generation section
                print("\nGenerating status-specific BED files:")
                statuses = ['NEW_IN_POST', 'LOST_IN_POST', 'UNCHANGED']
                for status in statuses:
                    bed_path = f"{args.output_dir}/{sample_pair}.{status.lower().replace('_', '-')}.bed"
                    df_roh_diff[df_roh_diff['Status'] == status][['Chromosome', 'Start', 'End']]\
                        .to_csv(bed_path, sep='\t', index=False, header=False)
                    print(f"- {status}: {bed_path}")

                # Filter CN segments by P-value
                df_summary_filtered = df_summary[df_summary['P_segment_CN'] < 0.05]
                print(f"\nCN segments after P-value filtering (P < 0.05): {len(df_summary_filtered)}")
                print("CN Copy Number Distribution after filtering:")
                print(df_summary_filtered['Copy_Number_POST'].value_counts().sort_index())

                # Generate filtered BED files with requested names
                print("\nGenerating filtered BED files:")
                
                # ROH data (quality filtered)
                roh_filtered_bed = f"{args.output_dir}/{sample_pair}.roh_data.bed"
                df_roh_filtered[['Chromosome', 'Start', 'End']].to_csv(
                    roh_filtered_bed, sep='\t', index=False, header=False
                )
                print(f"- ROH regions: {roh_filtered_bed} ({len(df_roh_filtered)} regions)")
                
                # CN data (quality filtered)
                cn_filtered_bed = f"{args.output_dir}/{sample_pair}.cn_data.bed"
                df_summary_filtered[['Chromosome', 'Start', 'End']].to_csv(
                    cn_filtered_bed, sep='\t', index=False, header=False
                )
                print(f"- CN segments: {cn_filtered_bed} ({len(df_summary_filtered)} segments)")

                # Remove previous BED file generations
                print("\nRemoving intermediate BED files...")
                # ... (optional cleanup code if needed)

                print("\nAnalysis completed successfully")
                
            except Exception as e:
                print(f"\nERROR: An error occurred during analysis:")
                print(f"Error message: {str(e)}")
                raise

def load_roh_differential(roh_diff_file):
    """Load ROH differential data with proper column handling."""
    try:
        data = []
        with open(roh_diff_file, 'r') as f:
            # Skip header
            next(f)
            for line in f:
                if line.startswith('#'):
                    continue
                # Split into max 5 columns, remaining is Original_Line
                parts = line.strip().split('\t', 5)
                if len(parts) < 6:
                    continue
                data.append({
                    'Status': parts[0],
                    'Chromosome': str(parts[1]),  # Force string type
                    'Start': int(parts[2]),
                    'End': int(parts[3]),
                    'Quality': float(parts[4]),
                    'Original_Line': parts[5]
                })
        
        df = pd.DataFrame(data)
        print(f"\nLoaded {len(df)} valid ROH differential regions")
        return df
    except Exception as e:
        print(f"Error loading ROH differential: {str(e)}")
        return pd.DataFrame()

def load_summary_tab(summary_file, post_sample, pre_sample):
    """
    bcftools cnv typically produces 11 columns for each region (RG).
    We'll define a fixed column list and rename the relevant copy-number columns
    to 'Copy_Number_POST' and 'Copy_Number_PRE'.
    """
    try:
        col_names = [
            "RG",
            "Chromosome",
            "Start",
            "End",
            f"Copy_number:{post_sample}",
            f"Copy_number:{pre_sample}",
            "Quality",
            "nSites_post",
            "nHETs_post",
            "nSites_pre",
            "nHETs_pre"
        ]
        # Read all lines except those starting with '#'
        df = pd.read_csv(
            summary_file,
            sep="\t",
            comment='#',
            names=col_names,
            dtype={
                "Chromosome": str,
                "Start": int,
                "End": int,
                f"Copy_number:{post_sample}": float,
                f"Copy_number:{pre_sample}": float,
                "Quality": float,
                "nSites_post": int,
                "nHETs_post": int,
                "nSites_pre": int,
                "nHets_pre": float  # or int if guaranteed
            }
        )
        
        # Rename the copy number fields for clarity
        df.rename(columns={
            f"Copy_number:{post_sample}": "Copy_Number_POST",
            f"Copy_number:{pre_sample}": "Copy_Number_PRE"
        }, inplace=True)
        
        # If needed, convert them to int
        df["Copy_Number_POST"] = df["Copy_Number_POST"].fillna(2).astype(int)
        df["Copy_Number_PRE"]  = df["Copy_Number_PRE"].fillna(2).astype(int)
        
        # Add P-value conversion
        df["P_segment_CN"] = df["Quality"].apply(phred_to_p)
        
        print(f"Loaded {len(df)} CN segments from {summary_file}")
        return df

    except Exception as e:
        print(f"CN summary loading error: {str(e)}")
        return pd.DataFrame()

def find_cn_overlaps(roh_region, df_summary):
    """Robust CN overlap detection."""
    # Use alternative column names if primary not found
    cn_post_col = 'Copy_Number_POST' if 'Copy_Number_POST' in df_summary else 'CN_POST'
    cn_pre_col = 'Copy_Number_PRE' if 'Copy_Number_PRE' in df_summary else 'CN_PRE'
    
    # Convert coordinates
    df_summary = df_summary.assign(
        Start=pd.to_numeric(df_summary['Start'], errors='coerce'),
        End=pd.to_numeric(df_summary['End'], errors='coerce')
    ).dropna(subset=['Start', 'End'])
    
    # Find overlapping segments
    mask = (
        (df_summary['Chromosome'] == roh_region['Chromosome']) &
        (df_summary['End'] >= roh_region['Start']) &
        (df_summary['Start'] <= roh_region['End'])
    )
    
    cn_segments = df_summary[mask]
    print(f"Found {len(cn_segments)} CN overlaps for ROH {roh_region['Chromosome']}:{roh_region['Start']}-{roh_region['End']}")
    
    return [{
        'start': row['Start'],
        'end': row['End'],
        'copy_number_post': row[cn_post_col],
        'copy_number_pre': row[cn_pre_col]
    } for _, row in cn_segments.iterrows()]

def classify_event(cn_post, cn_pre, roh_status):
    """Enhanced event classification for cnLoH detection."""
    if roh_status == 'NEW_IN_POST':
        if cn_post == 2 and cn_pre == 2:
            return 'cnLoH (copy-neutral Loss of Heterozygosity)'
        elif cn_post == 2 and cn_pre < 2:
            return 'Copy-number restoration with maintained LoH'
        elif cn_post < 2 and cn_pre == 2:
            return 'Copy-number loss with acquired LoH'
        elif cn_post < 2 and cn_pre < 2:
            return 'Copy-number loss with maintained LoH'
        elif cn_post > 2:
            return 'Copy-number gain with acquired LoH'
        else:
            return 'Complex copy-number change with acquired LoH'
    elif roh_status == 'LOST_IN_POST':
        if cn_post == 2 and cn_pre == 2:
            return 'Restored heterozygosity (normal CN)'
        elif cn_post == 2 and cn_pre < 2:
            return 'Copy-number restoration with gained heterozygosity'
        elif cn_post < 2 and cn_pre == 2:
            return 'Copy-number loss with maintained heterozygosity'
        elif cn_post > 2:
            return 'Copy-number gain with gained heterozygosity'
        else:
            return 'Complex copy-number change with lost LoH'
    else:  # UNCHANGED
        if cn_post != cn_pre:
            if cn_post == 2 and cn_pre == 2:
                return 'Stable LoH with normal CN (potential technical variation)'
            elif (cn_post == 2) != (cn_pre == 2):
                return 'Copy-number change with stable LoH'
            else:
                return 'Complex CN change with stable LoH'
        else:
            if cn_post == 2:
                return 'Stable cnLoH (copy-neutral)'
            elif cn_post < 2:
                return 'Stable deletion-associated LoH'
            else:
                return 'Stable amplification-associated LoH'

def phred_to_p(q_score):
    """Convert Phred quality score to p-value."""
    return 10 ** (-q_score / 10)

if __name__ == "__main__":
    main()