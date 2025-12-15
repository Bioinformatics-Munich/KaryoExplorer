# General
The pipeline has been simplified, bash scripts in the orginal pipeline are not used anymore, R scripts are directly called in the nf processes.

2024-11
- Added Illumina Global Screening Array v4.0 demo dataset guide
  - Step-by-step instructions for downloading and organizing demo data
  - Complete Genome Studio workflow documentation with screenshots
  - Data extraction procedures for Full Data Table, SNP Table, Samples Table, and PLINK files

2024-10
- Added detailed documentation and README files
- Improved setup and execution instructions (How_to_run.md)
- Added detailed pipeline outputs documentation (Outputs.md)

2024-09
- Repository structure refactored based on Nextflow best practices
- Improved organization and maintainability

2024-04
- cnLoH detection based on LoH and RoH approach included

2024-03
- Dynamic Reporting (KaryoPlayground) implemented
- Interactive HTML reports for CNV visualization

2024-12
- LoH-RoH Calculation included 

2024-08-09
- Copy relevant txt files to tsv in 2_QC
- Calculate LRR stdev and create tables in 2_QC
- Export GT comparision tables in 3.2_QC

2024-07-17
- Renamed relevant tables from .tab to .tsv
- Added new tables that summarize the CSVs per chromosome for single and paired analysis available from 6.2_CNV_differential and 7.2_CNV_single folders  
- Added these new tables that summarize the CSVs per chromosome for single and paired analysis to new combined tables (8_CNV_single_paired_summary/{CNVs_single_chromosomes.xls,CNVs_paired_chromosomes.xls})  

2024-07-12
- Added outputs description as html

2024-04-27
- Added summary plot and self contained html reports

2024-03-23
- Revert to orginal R script files
- Add script create_annotation_file.R
- modified create_annSample_run.R to use sampleID
- modified summary_diffCN_run.R
- modified plot_summary_cnv_function.R L170 + 172: use unlist
- modified lrr plot: fix chr24 undef
- Consistant naming in all outputs for the comparative workflow: POST_PRE
- GT_match_run.R second heatmap removed, what is the correct algo for the sample mismatch? They need to be checked now manually in the output table, check Sample_name_new column. It's assumed now that the user input is correct. Currently it's setup such that the Sample_name column which contains the PRE name is used and other samples are checked if GT match > 0.96, if there is another sample with that its labeled as mismatch  

