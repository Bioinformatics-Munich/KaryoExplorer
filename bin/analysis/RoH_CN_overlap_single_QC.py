#!/usr/bin/env python3
import argparse
import pandas as pd
import numpy as np
from contextlib import redirect_stdout
import os

def main():
    parser = argparse.ArgumentParser(description='RoH-CN Overlap Analysis')
    parser.add_argument('--roh', required=True, help='Input ROH file path')
    parser.add_argument('--cn_summary', required=True, help='CN summary file path')
    parser.add_argument('--dat', required=False, help='DAT file path (optional)')
    parser.add_argument('--cn', required=False, help='CN file path (optional)')
    parser.add_argument('--output_dir', required=True, help='Output directory path')
    parser.add_argument('--sample', required=True, help='Sample name')
    args = parser.parse_args()

    # Set up logging with wider display for pandas
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)
    
    # Create log file with sample name included
    with open(f"{args.output_dir}/{args.sample}.log.txt", 'w') as f:
        with redirect_stdout(f):
            try:
                print(f"=== Analysis Report for Sample: {args.sample} ===\n")
                
                # Verify input files exist
                print("Checking input files...")
                for file_path, file_type in [
                    (args.roh, "ROH"),
                    (args.cn_summary, "CN Summary"),
                ]:
                    if not os.path.exists(file_path):
                        print(f"ERROR: {file_type} file not found: {file_path}")
                        return
                    print(f"Found {file_type} file: {file_path}")
                
                # Check optional files
                optional_files = []
                if args.dat:
                    optional_files.append((args.dat, "DAT"))
                if args.cn:
                    optional_files.append((args.cn, "CN"))
                
                for file_path, file_type in optional_files:
                    if os.path.exists(file_path):
                        print(f"Found optional {file_type} file: {file_path}")
                    else:
                        print(f"Optional {file_type} file not found: {file_path} (will skip related analysis)")
                
                # Load and log ROH data
                print("\n1. ROH Data Loading and Processing")
                print("----------------------------------")
                print(f"Loading ROH data from: {args.roh}")
                df_rg, df_st = load_roh_data(args.roh, args.sample)
                
                print(f"ROH Regions (first 5 rows):")
                if not df_rg.empty:
                    # Convert Quality scores to P-values
                    df_rg['P_value'] = df_rg['Quality'].apply(phred_to_p)
                    
                    print("\nRG Records before filtering:")
                    cols_to_display = ["Chromosome", "Start", "End", "Length_bp", "Num_Markers", "Quality", "P_value"]
                    print(df_rg[cols_to_display].head().to_string(index=False, float_format=lambda x: '{:.2e}'.format(x) if isinstance(x, float) else str(x)))
                    print(f"\nTotal ROH regions before filtering: {len(df_rg)}")
                    print("\nROH Statistics before filtering:")
                    print(df_rg[["Length_bp", "Num_Markers", "Quality", "P_value"]].describe().to_string(float_format=lambda x: '{:.2e}'.format(x)))
                    
                    # Filter ROH regions by P-value
                    df_rg_filtered = df_rg[df_rg['P_value'] < 0.05]
                    
                    print(f"\nROH Regions after P-value filtering (P < 0.05): {len(df_rg_filtered)} regions")
                    if not df_rg_filtered.empty:
                        print("\nFiltered RG Records (first 5 rows):")
                        print(df_rg_filtered[cols_to_display].head().to_string(index=False, float_format=lambda x: '{:.2e}'.format(x) if isinstance(x, float) else str(x)))
                        print("\nROH Statistics after filtering:")
                        print(df_rg_filtered[["Length_bp", "Num_Markers", "Quality", "P_value"]].describe().to_string(float_format=lambda x: '{:.2e}'.format(x)))
                    
                    print(f"\nROH regions removed by filtering: {len(df_rg) - len(df_rg_filtered)}")
                    
                    # Update df_rg to filtered version for downstream processing
                    df_rg = df_rg_filtered
                else:
                    print("No ROH regions detected")
                
                # Handle empty ROH case
                if df_rg.empty:
                    print("\nWarning: No ROH regions detected - proceeding with empty dataset")
                    df_rg = pd.DataFrame(columns=["Chromosome", "Start", "End"])
                
                # Load and log CNV data
                print("\n2. CNV Data Loading and Processing")
                print("----------------------------------")
                print(f"Loading DAT data from: {args.dat}")
                df_dat = load_dat_data(args.dat)
                print(f"\nDAT data (first 5 rows):")
                print(df_dat.head().to_string(index=False))
                print(f"\nTotal DAT entries: {len(df_dat)}")
                print("\nDAT Summary Statistics:")
                print(df_dat[["BAF", "LRR"]].describe().to_string())
                
                print(f"\nLoading CN data from: {args.cn}")
                df_cn = load_cnv_data(args.cn)
                print(f"\nCN data (first 5 rows):")
                print(df_cn.head().to_string(index=False))
                print(f"\nTotal CN entries: {len(df_cn)}")
                print("\nCN Value Distribution:")
                print(df_cn["CN"].value_counts().sort_index().to_string())
                
                print(f"\nLoading Summary data from: {args.cn_summary}")
                df_summary = load_summary_tab(args.cn_summary)
                print(f"\nRaw Summary data (first 5 rows):")
                print(df_summary.head().to_string(index=False))
                print(f"\nTotal Summary entries: {len(df_summary)}")
                print("\nCopy Number Distribution in Summary:")
                print(df_summary["Copy_Number"].value_counts().sort_index().to_string())

                # Process and log CN summary data
                print("\n3. CN Summary Processing")
                print("------------------------")
                df_summary_updated = process_cn_summary(df_summary, args.sample)
                print("Processed Summary data with CN states (first 5 rows):")
                print(df_summary_updated[["Chromosome", "Start", "End", "Copy_Number", "CN_State", "P_segment_CN"]].head().to_string(index=False))
                print("\nCN State Distribution:")
                print(df_summary_updated["CN_State"].value_counts().to_string())
                
                # Filter and log results - MODIFIED FOR cnLoH DETECTION
                print("\n4. Filtering Results for LoH Analysis")
                print("------------------------------------")
                print(f"Initial count: {len(df_summary_updated)} segments")
                
                df_summary_filtered = df_summary_updated[df_summary_updated["P_segment_CN"] < 0.05]
                print(f"After P-value filtering (P < 0.05): {len(df_summary_filtered)} segments")
                
                # CHANGE: Keep all CNV segments for comprehensive LoH analysis
                # Split into different categories for analysis
                df_cn0_cn1 = df_summary_filtered[df_summary_filtered["Copy_Number"] < 2]  # Deletions (known LoH)
                df_cn2 = df_summary_filtered[df_summary_filtered["Copy_Number"] == 2]     # Normal CN (candidate cnLoH)
                df_cn3_plus = df_summary_filtered[df_summary_filtered["Copy_Number"] > 2] # Amplifications
                
                print(f"\nCN segment stratification:")
                print(f"  CN < 2 (deletions/known LoH): {len(df_cn0_cn1)} segments")
                print(f"  CN = 2 (normal/candidate cnLoH): {len(df_cn2)} segments") 
                print(f"  CN > 2 (amplifications): {len(df_cn3_plus)} segments")
                
                # For comprehensive analysis, combine CN<2 and CN=2 for LoH detection
                df_summary_for_loh = pd.concat([df_cn0_cn1, df_cn2], ignore_index=True)
                print(f"\nTotal segments for LoH analysis (CN ≤ 2): {len(df_summary_for_loh)} segments")
                
                if not df_summary_for_loh.empty:
                    print("\nLoH analysis segments (first 5 rows):")
                    print(df_summary_for_loh[["Chromosome", "Start", "End", "Copy_Number", "CN_State", "P_segment_CN"]].head().to_string(index=False))
                    print("\nLoH Segments Summary:")
                    print(df_summary_for_loh[["Copy_Number", "P_segment_CN"]].describe().to_string())

                # Generate BED files - UPDATED
                print("\n5. BED File Generation")
                print("---------------------")
                
                # Generate comprehensive CN BED file for LoH analysis (CN ≤ 2)
                df_cn_bed = df_summary_for_loh[["Chromosome", "Start", "End"]].copy()
                if not df_cn_bed.empty:
                    df_cn_bed["Start"] -= 1
                    print("\nComprehensive CN BED preview (CN ≤ 2, first 5 rows):")
                    print(df_cn_bed.head().to_string(index=False))
                df_cn_bed.to_csv(f"{args.output_dir}/{args.sample}.cn_data.bed", sep="\t", index=False, header=False)
                print(f"\nComprehensive CN BED file created with {len(df_cn_bed)} regions (includes CN=2 for cnLoH detection)")
                
                # Generate separate BED files by CN category for detailed analysis
                # CN < 2 (deletions/known LoH)
                df_cn_deletions = df_cn0_cn1[["Chromosome", "Start", "End"]].copy()
                if not df_cn_deletions.empty:
                    df_cn_deletions["Start"] -= 1
                df_cn_deletions.to_csv(f"{args.output_dir}/{args.sample}.cn_deletions.bed", sep="\t", index=False, header=False)
                print(f"CN deletions BED file created with {len(df_cn_deletions)} regions")
                
                # CN = 2 (candidate cnLoH)
                df_cn_normal = df_cn2[["Chromosome", "Start", "End"]].copy()
                if not df_cn_normal.empty:
                    df_cn_normal["Start"] -= 1
                df_cn_normal.to_csv(f"{args.output_dir}/{args.sample}.cn_normal.bed", sep="\t", index=False, header=False)
                print(f"CN normal (candidate cnLoH) BED file created with {len(df_cn_normal)} regions")
                
                # ROH BED (unchanged)
                df_roh_bed = df_rg[["Chromosome", "Start", "End"]].copy()
                if not df_roh_bed.empty:
                    df_roh_bed["Start"] -= 1
                    print("\nROH BED preview (first 5 rows):")
                    print(df_roh_bed.head().to_string(index=False))
                df_roh_bed.to_csv(f"{args.output_dir}/{args.sample}.roh_data.bed", sep="\t", index=False, header=False)
                print(f"\nROH BED file created with {len(df_roh_bed)} regions (after P-value filtering)")

                # Add analysis summary for cnLoH detection
                print("\n6. cnLoH Detection Summary")
                print("-------------------------")
                print("Analysis strategy for cnLoH detection:")
                print("1. CN < 2 + RoH overlap → Deletion-associated LoH")
                print("2. CN = 2 + RoH overlap → Candidate copy-neutral LoH (cnLoH)")
                print("3. CN > 2 + RoH overlap → Copy-gain with LoH")
                print(f"\nCandidate cnLoH regions available: {len(df_cn2)} CN=2 segments")
                print(f"Known LoH regions available: {len(df_cn0_cn1)} CN<2 segments")
                print(f"Total RoH regions for overlap: {len(df_rg)} segments")

                print("\nAnalysis completed successfully")
                
            except Exception as e:
                print(f"\nERROR: An error occurred during analysis:")
                print(f"Error message: {str(e)}")
                raise

def load_roh_data(roh_file, target_sample):
    """Load bcftools roh output for a specific sample."""
    rg_records = []
    st_records = []
    
    with open(roh_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            rec_type = parts[0]
            sample = parts[1]

            if sample != target_sample:
                continue

            if rec_type == "RG":
                rg_records.append({
                    "Segment_ID": f"{parts[2]}_{parts[3]}_{parts[4]}",
                    "Sample": sample,
                    "Chromosome": parts[2],
                    "Start": int(parts[3]),
                    "End": int(parts[4]),
                    "Length_bp": int(parts[5]),
                    "Num_Markers": int(parts[6]),
                    "Quality": float(parts[7])
                })
            elif rec_type == "ST":
                st_records.append({
                    "Sample": sample,
                    "Chromosome": parts[2],
                    "Position": int(parts[3]),
                    "State": int(parts[4]),
                    "Quality": float(parts[5])
                })

    return pd.DataFrame(rg_records), pd.DataFrame(st_records)

def phred_to_p(q_score):
    return 10 ** (-q_score / 10)

def load_dat_data(dat_tab_file, has_header=True):
    """Load bcftools cnv 'dat.SAMPLE.tab' containing BAF, LRR."""
    return pd.read_csv(
        dat_tab_file,
        sep="\t",
        header=0 if has_header else None,
        names=["Chromosome", "Position", "BAF", "LRR"],
        dtype={"Chromosome": str, "Position": int}
    )

def load_cnv_data(cn_tab_file, has_header=True):
    """Load CNV data from cn.<sample>.tab file."""
    df = pd.read_csv(
        cn_tab_file,
        sep="\t",
        header=0 if has_header else None,
        names=["Chromosome", "Position", "CN", "P(CN0)", "P(CN1)", "P(CN2)", "P(CN3)"],
        dtype={"Chromosome": str, "Position": int, "CN": int}
    )
    if has_header:
        df.columns = [col.split("]")[-1].strip() for col in df.columns]
    return df

def load_summary_tab(summary_file):
    """Load summary.<sample>.tab file."""
    return pd.read_csv(
        summary_file,
        sep="\t",
        header=None,
        names=["RG", "Chromosome", "Start", "End", "Copy_Number", "Quality", "nSites", "nHETs"],
        comment="#",
        dtype={"Chromosome": str, "Start": int, "End": int, "Copy_Number": int}
    )

def process_cn_summary(df_summary, sample_name):
    """Process CN summary data and classify CN states."""
    df_summary["Segment_ID"] = df_summary["Chromosome"].astype(str) + "_" + \
                              df_summary["Start"].astype(str) + "_" + \
                              df_summary["End"].astype(str)
    df_summary["Sample"] = sample_name
    
    conditions = [
        (df_summary["Copy_Number"] < 2),
        (df_summary["Copy_Number"] == 2),
        (df_summary["Copy_Number"] > 2)
    ]
    choices = ["Deletion", "Neutral", "Amplification"]
    df_summary["CN_State"] = np.select(conditions, choices, default="Unknown")
    df_summary["P_segment_CN"] = df_summary["Quality"].apply(phred_to_p)
    
    return df_summary

if __name__ == "__main__":
    main()