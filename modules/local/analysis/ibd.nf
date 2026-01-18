nextflow.enable.dsl=2

/*
========================================================================================
    SPECIALIZED ANALYSIS: IDENTITY BY DESCENT (IBD)
========================================================================================
    IBD analysis and sample type classification
----------------------------------------------------------------------------------------
*/

process IBD_ANALYSIS {
    
    tag "IBD analysis for paired samples"
    label 'process_medium'

    // publishDir "${params.outdir}/3.1_QC", mode: 'copy', overwrite: true

    conda "${baseDir}/env/ibd.yaml"

    input:
        path gsplink
        path paired_sample_types

    output:
        path "ibd_results.genome", emit: ibd_results
        path "paired_sample_with_pi_hat.csv", emit: pi_hat_results

    when:
        gsplink && paired_sample_types

    script:
        """
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Starting IBD analysis"
        
        # Run PLINK IBD analysis
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Running PLINK IBD calculation"
        plink --ped `ls $gsplink/*.ped` --map `ls $gsplink/*.map` --genome --out ibd_results
        
        # Check if results were generated
        if [[ ! -f "ibd_results.genome" ]]; then
            echo "ERROR: IBD analysis failed - no results generated"
            exit 1
        fi
        
        # Merge the genome results with paired samples CSV
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Merging IBD results with paired samples"
        ${projectDir}/bin/analysis/analyze_ibd.py ibd_results.genome "${paired_sample_types}"
        
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: IBD analysis completed"
        echo "Analyzed \$(wc -l < ibd_results.genome) sample pairs"
        """
}

process SAMPLE_TYPES_SINGLE {
    
    tag "Classifying single sample types"
    label 'process_low'

    // publishDir "${params.outdir}/4_samples", mode: 'copy', overwrite: true

    conda "${baseDir}/env/preproc.yaml"

    input:
        path samples_manifest
        path samples_table_qc

    output:
        path "sample_types_single.csv", emit: sample_csv_single
        path "sample_types_single_w_QC.csv", emit: sample_csv_single_w_QC

    when:
        samples_manifest && samples_table_qc

    script:
        """
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Starting single sample type classification"
        
        # 1) Generate the base sample_types_single.csv
        echo "sample_id,type,pre_sample,pre_sex,post_sample,post_sex" > sample_types_single.csv

        awk -F'\\t' '
        BEGIN {
            OFS = ","
        }
        # First pass: Build sex lookup from lines that start with M or F
        {
            if (\$1 ~ /^[FM]\$/ && \$2 != "") {
                if (\$2 != "None") sex[\$2] = \$1
                if (\$3 != "" && \$3 != "None") sex[\$3] = \$1
            }
        }

        # Skip header lines
        \$1 == "sex" { next }

        # Second pass: output single samples (where \$3 == "None")
        \$3 == "None" {
            pre_sample = \$2
            printf "%s,single,%s,%s,NA,NA\\n", pre_sample, pre_sample, sex[pre_sample]
        }
        ' ${samples_manifest} >> sample_types_single.csv

        # 2) Merge QC columns, dropping post_sample/post_sex
        python -c '
import pandas as pd

df_st = pd.read_csv("sample_types_single.csv")
df_qc = pd.read_csv("${samples_table_qc}", sep="\\t")

# Merge on sample_id (left) and sample_ID (right)
df_merged = pd.merge(
    df_st,
    df_qc[["sample_ID", "call_rate", "call_rate_filt", "LRR_stdev"]],
    left_on="sample_id",
    right_on="sample_ID",
    how="left"
)

# Drop columns we no longer want
df_merged.drop(columns=["sample_ID", "post_sample", "post_sex"], inplace=True)

# Write final merged CSV
df_merged.to_csv("sample_types_single_w_QC.csv", index=False)
'
        
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Single sample classification completed"
        echo "Classified \$(tail -n +2 sample_types_single.csv | wc -l) single samples"
        """
}

process SAMPLE_TYPES_PAIRED {
    
    tag "Classifying paired sample types"
    label 'process_low'

    // publishDir "${params.outdir}/4_samples", mode: 'copy', overwrite: true

    conda "${baseDir}/env/preproc.yaml"

    input:
        path samples_manifest

    output:
        path "sample_types_paired.csv", emit: sample_csv_paired

    when:
        samples_manifest

    script:
        """
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Starting paired sample type classification"
        
        echo "sample_id,type,pre_sample,pre_sex,post_sample,post_sex" > sample_types_paired.csv

        awk -F'\\t' '
        BEGIN {
            OFS = ","
        }
        # First pass: Build sex lookup
        {
            if (\$1 ~ /^[FM]\$/ && \$2 != "") {
                if (\$2 != "None") sex[\$2] = \$1
                if (\$3 != "" && \$3 != "None") sex[\$3] = \$1
            }
        }

        # Skip header lines
        \$1 == "sex" { next }

        # Second pass: output paired samples
        \$3 != "None" {
            pre_sample = \$2
            post_sample = \$3
            pre_sex = (pre_sample in sex) ? sex[pre_sample] : "NA"
            post_sex = (post_sample in sex) ? sex[post_sample] : "NA"
            printf "%s,paired,%s,%s,%s,%s\\n", pre_sample, pre_sample, pre_sex, post_sample, post_sex
        }
        ' ${samples_manifest} >> sample_types_paired.csv
        
        echo "[\$(date '+%Y-%m-%d %H:%M:%S')] INFO: Paired sample classification completed"
        echo "Classified \$(tail -n +2 sample_types_paired.csv | wc -l) paired samples"
        """
}
