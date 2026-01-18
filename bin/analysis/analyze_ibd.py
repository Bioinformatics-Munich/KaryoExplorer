#!/usr/bin/env python3

import sys
import os
import pandas as pd

def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <ibd_results.genome> <paired_samples.csv>")
        sys.exit(1)

    ibd_file = sys.argv[1]
    paired_csv = sys.argv[2]

    # Validate inputs
    if not os.path.isfile(ibd_file):
        print(f"Error: IBD file '{ibd_file}' does not exist.")
        sys.exit(1)
    if not os.path.isfile(paired_csv):
        print(f"Error: Paired CSV '{paired_csv}' does not exist.")
        sys.exit(1)

    # Initialize logging
    log_file_path = "ibd_results.log"
    with open(log_file_path, "a") as log_file:
        log_file.write("\n=== IBD Analysis Log Start ===\n")
        log_file.write(f"IBD file: {ibd_file}\n")
        log_file.write(f"Paired CSV: {paired_csv}\n")

    # Load paired samples data
    df_pairs = pd.read_csv(paired_csv)
    
    # Load PLINK IBD results with updated pandas syntax
    ibd_cols = [
        "FID1", "IID1", "FID2", "IID2", "RT", "EZ", "Z0", 
        "Z1", "Z2", "PI_HAT", "PHE", "DST", "PPC", "RATIO"
    ]
    ibd_df = pd.read_csv(
        ibd_file, 
        sep='\s+',  # Updated from delim_whitespace=True
        names=ibd_cols, 
        comment='#',  # Handle possible comment lines
        header=0
    )

    # Merge results in both directions
    merged1 = pd.merge(
        df_pairs,
        ibd_df[['IID1','IID2','PI_HAT']],
        left_on=['pre_sample','post_sample'],
        right_on=['IID1','IID2'],
        how='left'
    )
    merged2 = pd.merge(
        df_pairs,
        ibd_df[['IID1','IID2','PI_HAT']],
        left_on=['pre_sample','post_sample'],
        right_on=['IID2','IID1'],
        how='left'
    )

    # Combine results
    final_df = df_pairs.copy()
    final_df["PI_HAT"] = merged1["PI_HAT"].combine_first(merged2["PI_HAT"])
    
    # Handle PLINK's Y chromosome warning explicitly
    y_warning_handled = """
    Note: PLINK's warning about 'Nonmissing nonmale Y chromosome genotype(s)' 
    is expected when analyzing samples with Y chromosome data. This does not 
    affect IBD calculations but means Y chromosome genotypes from non-male 
    samples were treated as missing.
    """

    # Generate results
    low_count = final_df[final_df["PI_HAT"] < 0.9].shape[0]
    high_count = final_df[final_df["PI_HAT"] >= 0.9].shape[0]
    out_file = "paired_sample_with_pi_hat.csv"
    final_df.to_csv(out_file, index=False)

    # Update logging
    with open(log_file_path, "a") as log_file:
        log_file.write(y_warning_handled)
        log_file.write(f"\nPairs with PI_HAT < 0.9: {low_count}")
        log_file.write(f"\nPairs with PI_HAT >= 0.9: {high_count}")
        log_file.write(f"\nResults saved to: {out_file} (CSV format)")
        log_file.write("\n=== IBD Analysis Log End ===\n\n")

    # Console output
    print(y_warning_handled)
    print(f"Number of paired samples with PI_HAT < 0.9: {low_count}")
    print(f"Number of paired samples with PI_HAT >= 0.9: {high_count}")
    print(f"Full table saved to: {out_file} (CSV format)")

if __name__ == "__main__":
    main()