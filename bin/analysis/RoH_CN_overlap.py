#!/usr/bin/env python3

import argparse
import os
import pandas as pd

def analyze_overlaps(df_roh, df_cn, df_union):
    """Perform detailed analysis of overlaps between ROH and CN regions"""
    results = {}
    
    # Basic statistics
    results['total_roh_regions'] = len(df_roh) if df_roh is not None else 0
    results['total_cn_regions'] = len(df_cn) if df_cn is not None else 0
    results['total_union_regions'] = len(df_union) if df_union is not None else 0
    
    # Length statistics
    results['mean_roh_length'] = df_roh.iloc[:, -1].mean() if df_roh is not None and len(df_roh) > 0 else 0
    results['mean_cn_length'] = df_cn.iloc[:, -1].mean() if df_cn is not None and len(df_cn) > 0 else 0
    results['mean_union_length'] = df_union.iloc[:, -1].mean() if df_union is not None and len(df_union) > 0 else 0
    
    return results

def analyze_cnloh_specific_overlaps(args):
    """Enhanced cnLoH-specific overlap analysis"""
    results = {}
    
    # Check if CN-specific BED files exist for detailed analysis
    cn_deletions_file = args.cn_with_len.replace('.bed', '').replace('_cn_with_length', '_cn_deletions') + '.bed'
    cn_normal_file = args.cn_with_len.replace('.bed', '').replace('_cn_with_length', '_cn_normal') + '.bed'
    
    # If detailed CN files exist, perform stratified analysis
    if os.path.exists(cn_deletions_file) and os.path.exists(cn_normal_file):
        results['detailed_analysis'] = True
        
        # Load CN stratified data
        df_cn_del = pd.read_csv(cn_deletions_file, sep="\t", header=None) if os.path.getsize(cn_deletions_file) > 0 else pd.DataFrame()
        df_cn_norm = pd.read_csv(cn_normal_file, sep="\t", header=None) if os.path.getsize(cn_normal_file) > 0 else pd.DataFrame()
        
        results['cn_deletions_count'] = len(df_cn_del)
        results['cn_normal_count'] = len(df_cn_norm)
        
        # Add length columns if missing
        if not df_cn_del.empty and df_cn_del.shape[1] == 3:
            df_cn_del[3] = df_cn_del.iloc[:, 2] - df_cn_del.iloc[:, 1]
        if not df_cn_norm.empty and df_cn_norm.shape[1] == 3:
            df_cn_norm[3] = df_cn_norm.iloc[:, 2] - df_cn_norm.iloc[:, 1]
            
        results['total_cn_del_length'] = df_cn_del.iloc[:, -1].sum() if not df_cn_del.empty else 0
        results['total_cn_norm_length'] = df_cn_norm.iloc[:, -1].sum() if not df_cn_norm.empty else 0
        results['mean_cn_del_length'] = df_cn_del.iloc[:, -1].mean() if not df_cn_del.empty else 0
        results['mean_cn_norm_length'] = df_cn_norm.iloc[:, -1].mean() if not df_cn_norm.empty else 0
        
    else:
        results['detailed_analysis'] = False
        results['cn_deletions_count'] = 0
        results['cn_normal_count'] = 0
        results['total_cn_del_length'] = 0
        results['total_cn_norm_length'] = 0
        results['mean_cn_del_length'] = 0
        results['mean_cn_norm_length'] = 0
    
    return results

def main():
    parser = argparse.ArgumentParser(
        description="Compute coverage stats for ROH/CN overlaps and union with cnLoH-specific analysis."
    )
    parser.add_argument("--roh_with_len", required=True, help="ROH intervals with length column")
    parser.add_argument("--cn_with_len", required=True, help="CN intervals with length column")
    parser.add_argument("--roh_perspective", required=True, help="Overlap from ROH perspective")
    parser.add_argument("--cn_perspective", required=True, help="Overlap from CN perspective")
    parser.add_argument("--union_with_len", required=True, help="Union of ROH+CN with length")
    parser.add_argument("--sample", required=True, help="Sample ID")
    parser.add_argument("--output_dir", required=True, help="Output directory for analysis files")
    parser.add_argument("--log", required=True, help="Output log file for stats")
    args = parser.parse_args()

    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)

    # Load data files
    df_roh = pd.read_csv(args.roh_with_len, sep="\t", header=None) if os.path.getsize(args.roh_with_len) > 0 else None
    df_cn = pd.read_csv(args.cn_with_len, sep="\t", header=None) if os.path.getsize(args.cn_with_len) > 0 else None
    df_union = pd.read_csv(args.union_with_len, sep="\t", header=None) if os.path.getsize(args.union_with_len) > 0 else None
    
    # Perform basic analysis
    analysis_results = analyze_overlaps(df_roh, df_cn, df_union)
    
    # Perform cnLoH-specific analysis
    cnloh_results = analyze_cnloh_specific_overlaps(args)
    
    # Generate report
    lines = []
    lines.append(f"=== Enhanced Overlap Analysis for Sample: {args.sample} ===\n")
    
    # Basic statistics
    lines.append("=== Basic Statistics ===")
    lines.append(f"Total ROH regions: {analysis_results['total_roh_regions']}")
    lines.append(f"Total CN regions: {analysis_results['total_cn_regions']}")
    lines.append(f"Total union regions: {analysis_results['total_union_regions']}\n")
    
    # Length statistics
    lines.append("=== Length Statistics ===")
    lines.append(f"Mean ROH length: {analysis_results['mean_roh_length']:.2f}")
    lines.append(f"Mean CN length: {analysis_results['mean_cn_length']:.2f}")
    lines.append(f"Mean union length: {analysis_results['mean_union_length']:.2f}\n")
    
    # cnLoH-specific statistics
    if cnloh_results['detailed_analysis']:
        lines.append("=== cnLoH-Specific Analysis ===")
        lines.append(f"CN < 2 regions (known LoH): {cnloh_results['cn_deletions_count']}")
        lines.append(f"CN = 2 regions (candidate cnLoH): {cnloh_results['cn_normal_count']}")
        lines.append(f"Mean deletion length: {cnloh_results['mean_cn_del_length']:.2f} bp")
        lines.append(f"Mean normal CN length: {cnloh_results['mean_cn_norm_length']:.2f} bp")
        lines.append(f"Total deletion coverage: {cnloh_results['total_cn_del_length']:,} bp")
        lines.append(f"Total normal CN coverage: {cnloh_results['total_cn_norm_length']:,} bp\n")
    
    # Calculate bidirectional overlaps
    total_roh_length = df_roh.iloc[:, -1].sum() if df_roh is not None else 0
    total_cn_length = df_cn.iloc[:, -1].sum() if df_cn is not None else 0
    
    if os.path.getsize(args.roh_perspective) > 0:
        df_roh_intersect = pd.read_csv(args.roh_perspective, sep="\t", header=None)
        overlap_from_roh = df_roh_intersect.iloc[:, -1].sum()
        pct_roh_covered = (overlap_from_roh / total_roh_length * 100) if total_roh_length > 0 else 0
        lines.append("=== Bidirectional Overlap Analysis ===")
        lines.append(f"ROH regions overlapped by CN: {pct_roh_covered:.2f}%")
        lines.append(f"ROH overlap length: {overlap_from_roh:,} bp of {total_roh_length:,} bp total")
    
    if os.path.getsize(args.cn_perspective) > 0:
        df_cn_intersect = pd.read_csv(args.cn_perspective, sep="\t", header=None)
        overlap_from_cn = df_cn_intersect.iloc[:, -1].sum()
        pct_cn_covered = (overlap_from_cn / total_cn_length * 100) if total_cn_length > 0 else 0
        lines.append(f"CN regions overlapped by ROH: {pct_cn_covered:.2f}%")
        lines.append(f"CN overlap length: {overlap_from_cn:,} bp of {total_cn_length:,} bp total\n")
    
    # cnLoH interpretation
    lines.append("=== cnLoH Detection Interpretation ===")
    if cnloh_results['detailed_analysis']:
        lines.append("Analysis includes both known LoH (CN<2) and candidate cnLoH (CN=2) regions.")
        if cnloh_results['cn_normal_count'] > 0:
            lines.append(f"Potential cnLoH events: CN=2 regions ({cnloh_results['cn_normal_count']}) overlapping with ROH")
            lines.append("These represent copy-neutral Loss of Heterozygosity candidates.")
        else:
            lines.append("No CN=2 regions detected - limited cnLoH detection capability.")
        if cnloh_results['cn_deletions_count'] > 0:
            lines.append(f"Known LoH events: CN<2 regions ({cnloh_results['cn_deletions_count']}) overlapping with ROH")
        lines.append("Recommendation: Focus on CN=2 + ROH overlaps for cnLoH validation.")
    else:
        lines.append("Standard analysis performed. For enhanced cnLoH detection,")
        lines.append("ensure CN=2 regions are included in the analysis pipeline.")
    
    # Write report
    with open(args.log, "w") as f:
        f.write("\n".join(lines))
    
    # Generate enhanced summary statistics
    summary_stats = pd.DataFrame({
        'metric': ['total_regions', 'mean_length', 'total_length'],
        'roh': [
            analysis_results['total_roh_regions'],
            analysis_results['mean_roh_length'],
            total_roh_length
        ],
        'cn_all': [
            analysis_results['total_cn_regions'],
            analysis_results['mean_cn_length'],
            total_cn_length
        ],
        'union': [
            analysis_results['total_union_regions'],
            analysis_results['mean_union_length'],
            df_union.iloc[:, -1].sum() if df_union is not None else 0
        ]
    })
    
    # Add cnLoH-specific metrics if available
    if cnloh_results['detailed_analysis']:
        cnloh_stats = pd.DataFrame({
            'metric': ['cn_deletions', 'cn_normal', 'del_length', 'norm_length'],
            'count_or_length': [
                cnloh_results['cn_deletions_count'],
                cnloh_results['cn_normal_count'], 
                cnloh_results['total_cn_del_length'],
                cnloh_results['total_cn_norm_length']
            ]
        })
        cnloh_stats.to_csv(os.path.join(args.output_dir, f"{args.sample}_cnloh_stats.txt"),
                          sep='\t', index=False)
    
    # Save summary statistics
    summary_stats.to_csv(os.path.join(args.output_dir, f"{args.sample}_summary_stats.txt"), 
                        sep='\t', index=False)

    # Print to stdout for Nextflow logging
    print("\n".join(lines))

if __name__ == "__main__":
    main()