# Digital Karyotyping Pipeline - Output Guide

## Overview

This pipeline detects Copy Number Variations (CNVs) and Runs of Homozygosity (ROH) using Illumina arrays. It is a Nextflow DSL2 implementation of the Digital Karyotyping pipeline originally developed at MPI (Prof. Binder).

**Purpose**: Detect de novo copy number abnormalities arising in cultured cell lines to determine differences between cell lines and their starting material. This genomic screening for chromosomal abnormalities serves as quality control to establish and maintain stem cell lines.

**Original repository**: https://gitlab.mpcdf.mpg.de/luciat/cnv_detection

---

## Analysis Modes

The pipeline supports two analysis modes:

- **Single Mode**: Analyzes individual samples to identify CNV and ROH patterns within each sample
- **Paired Mode**: Compares POST samples against PRE reference samples to identify differential CNV and ROH patterns between conditions

**Naming Convention**: For paired workflows, outputs use `PRE_POST` naming format (e.g., `PRE_Sample1_POST_Sample2`).

---

## Output Directory Structure

The pipeline generates a well-organized output directory with the following structure:

```
results/
├── README.html                              # This documentation file
├── 0.0_information/                         # Pipeline metadata and logs
│   ├── 0.1_pipeline_logs/                   # Process-specific log files
│   │   ├── 5.1_<app_name>_single_logs/
│   │   └── 5.2_<app_name>_paired_logs/
│   ├── 0.2_versions/                        # Software version information
│   │   ├── bcftools.version.txt
│   │   ├── plink.version.txt
│   │   └── vcftools.version.txt
│   └── 0.3_reports/                         # Pipeline parameter reports
│       ├── pipeline_parameters.json
│       └── parameter_report.md
├── 1.0_quality_control/                     # Quality control results
│   ├── 1.1_QC_results/                      # QC metrics and tables
│   ├── 1.2_single_matching/                 # Single sample genotype matching
│   ├── 1.3_paired_matching/                 # Paired sample genotype matching
│   └── 1.4_IBD_Analysis/                    # Identity by descent analysis
├── 2.0_preprocess/                          # Data preprocessing
│   ├── 2.1_manifest_reference/              # Manifest reference alleles
│   ├── 2.2_plink/                           # PLINK format conversion
│   ├── 2.3_plink_corrected/                 # Reference allele corrected VCF
│   └── 2.4_preprocess_vcf/                  # BAF/LRR annotated VCF
├── 3.0_sample_annotation/                   # Sample metadata and annotations
├── 4.0_roh_loh_analysis/                    # Runs of Homozygosity & Loss of Heterozygosity
│   ├── 4.1_roh_loh_single/                  # Single sample ROH/LOH analysis
│   └── 4.2_roh_loh_paired/                  # Paired sample ROH/LOH analysis
├── 5.0_<app_name>_preprocessing/            # Data preparation for visualization
├── 5.1_<app_name>_single/                 # Interactive single sample results
└── 5.2_<app_name>_paired/                   # Interactive paired sample results
```

---

## Quick Start - Your Main Results

**Looking for your analysis results? Start here!**

The pipeline generates comprehensive outputs organized across multiple directories, but the **main interactive results** you'll want to access are:

### For Single Sample Analysis:
Navigate to **`5.1_<app_name>_single/`** and open `<app_name>.html` in your web browser (Chrome recommended).

**What you'll find:**

- Interactive visualization of all your single sample CNV and ROH results in one place

- Chromosome-by-chromosome exploration with interactive plots

- Sample quality metrics and summary statistics

- All analysis results combined into an easy-to-navigate interface

### For Paired Sample Analysis:
Navigate to **`5.2_<app_name>_paired/`** and open `<app_name>.html` in your web browser (Chrome recommended).

**What you'll find:**

- Side-by-side comparison of PRE vs POST samples

- Differential CNV and ROH analysis showing changes between conditions

- Interactive paired sample visualizations

- All paired analysis results in one comprehensive interface

> **Tip**: These interactive HTML applications contain all your pipeline results in a user-friendly format.


> **⚠️ Important**: Keep the HTML file in the same directory as the `samples/` and `components/` folders for proper functionality.

---

## Detailed Output Description

### 0.0_information - Pipeline Metadata

Contains all pipeline execution information, logs, and software versions.

#### 0.1_pipeline_logs
- **Purpose**: Process-specific log files for debugging and tracking
- **Subdirectories**:
  - `5.1_<app_name>_single_logs/`: Logs from single sample visualization
  - `5.2_<app_name>_paired_logs/`: Logs from paired sample visualization

#### 0.2_versions
- **Purpose**: Software version tracking for reproducibility
- **Files**:
  - `bcftools.version.txt`: BCFtools version used
  - `plink.version.txt`: PLINK version used
  - `vcftools.version.txt`: VCFtools version used

#### 0.3_reports
- **Purpose**: Pipeline configuration and parameter documentation
- **Files**:
  - `pipeline_parameters.json`: All pipeline parameters in JSON format
  - `parameter_report.md`: Human-readable parameter summary in Markdown

---

### 1.0_quality_control - QC Metrics

Quality control analysis and filtering results. See the [original manual](https://gitlab.mpcdf.mpg.de/luciat/cnv_detection/-/blob/master/pipeline_description/Genotyping_Data_QC.pdf) for details on SNP filtering methodology.

#### 1.1_QC_results
- **Key Files**:
  - `Samples_Table_filt_QC.tsv`: Call rates per sample before/after filtering and LRR standard deviations
  - `GT_comp.tsv`: Matrix of all genotype correlations
  - `plot_CR_samples.pdf/png`: Call rate visualization plots
  - `BAF_table.txt`, `LRR_table.txt`: B-allele frequency and Log R Ratio tables

> **Note**: LRR standard deviations > 0.3 may indicate increased variability and potential sample quality issues.

#### 1.2_single_matching
- **Purpose**: Genotype matching results for single samples
- **Key Files**:
  - `GT_samples_comp.tsv`: Genotype correlation matrix for single samples
  - `hm_GT.pdf/png`: Heatmap visualization of genotype matches
  - `annotation_file_GTmatch.csv`: Genotype matching annotations

#### 1.3_paired_matching
- **Purpose**: Genotype matching results for paired samples
- **Key Files**:
  - `GT_samples_comp.tsv`: Genotype correlation matrix for paired samples
  - `hm_GT.pdf/png`: Heatmap visualization of genotype matches
  - `annotation_file_GTmatch.csv`: Genotype matching annotations

#### 1.4_IBD_Analysis
- **Purpose**: Identity by descent analysis results
- **Key Files**:
  - `paired_sample_with_pi_hat.csv`: PI_HAT values for paired samples (relatedness coefficient)
  - `sample_types_single_w_QC.csv`: Single sample metadata with QC metrics

---

### 2.0_preprocess - Data Preprocessing

All preprocessing steps from raw genotype data to annotated VCF files.

#### 2.1_manifest_reference
- **Purpose**: Manifest reference alleles extraction
- **Files**: `*.ref` files containing reference allele information per SNP

#### 2.2_plink
- **Purpose**: PLINK format conversion from array data
- **Key Files**:
  - `plink.vcf`: Converted VCF file
  - `plink.log`: Conversion log
  - `plink.nosex`: Sample sex information

#### 2.3_plink_corrected
- **Purpose**: Reference allele correction using manifest data
- **Files**: `plink_corrected.vcf` - VCF with corrected reference alleles

#### 2.4_preprocess_vcf
- **Purpose**: BAF and LRR annotation of VCF
- **Key Files**:
  - `data_BAF_LRR.vcf`: VCF annotated with B-allele frequency and Log R Ratio
  - `SNPs_QC.txt`: List of QC-passed SNPs (chromosome, position, ID)

---

### 3.0_sample_annotation

Sample annotation files including metadata, sex determination, and sample relationships.

**Key Files**:
- `*.tsv`: Sample annotation tables with metadata
- Sample type classifications and relationships

---

### 4.0_roh_loh_analysis - Runs of Homozygosity & Loss of Heterozygosity

ROH and LOH detection using bcftools algorithm, with overlap analysis between CNV and ROH regions.

#### 4.1_roh_loh_single
- **Purpose**: ROH/LOH analysis for individual samples
- **Structure**:
  - `{SAMPLE_NAME}/bcftools_algorithm/`: ROH detection results
  - `{SAMPLE_NAME}/overlap/`: Combined CNV-ROH analysis
- **Key Files**:
  - `*_roh.bed`: ROH regions in BED format
  - `*_cn_with_length.bed`: Copy number regions with length
  - `*_union_merged_with_length.bed`: Merged CNV and ROH regions
  - Summary tables and statistics

#### 4.2_roh_loh_paired
- **Purpose**: Differential ROH/LOH analysis for paired samples
- **Structure**: Similar to single mode with PRE, POST, and differential analysis
- **Key Files**:
  - Pre-sample ROH results
  - Post-sample ROH results
  - Differential analysis showing changes between PRE and POST

---

### 5.0_<app_name>_preprocessing

Standardized data collection and formatting for interactive visualization.

**Purpose**: Collects all analysis results and standardizes them as CSV files for the interactive visualization tool.

**Structure**:

- `single/{SAMPLE_NAME}/processed/`: Single sample processed data

- `paired/{PRE_POST_ID}/processed/`: Paired sample processed data

**Single Sample Files**:

- `single_baf_lrr_data_*.csv`: BAF and LRR data points

- `single_cn_bed_*.csv`: Copy number regions in BED format

- `single_cn_probabilities_data_*.csv`: Copy number probability distributions

- `single_cn_summary_data_*.csv`: Copy number summary statistics

- `single_cnv_chromosomes_*.csv`: CNV data organized by chromosome

- `single_cnv_detection_filtered_*.csv`: Filtered CNV detection results

- `single_roh_bed_*.csv`: ROH regions in BED format

- `single_union_bed_*.csv`: Combined CNV and ROH regions

**Paired Sample Files**:

- `combined_cn_bed_*.csv`: Combined copy number data (PRE + POST)

- `combined_cnv_chromosomes_*.csv`: Combined CNV by chromosome

- `combined_cnv_detection_filtered_*.csv`: Combined filtered CNV results

- `combined_roh_bed_*.csv`: Combined ROH data

- `combined_union_bed_*.csv`: Combined CNV and ROH regions

- `pre_*` files: Individual PRE sample data

- `post_*` files: Individual POST sample data


---

### 5.1_<app_name>_single - Interactive single Sample Results

**This is your main result for single sample analysis!**

**Purpose**: Interactive HTML-based visualization for exploring CNV and ROH patterns in individual samples.

**How to Access**:
1. Open `<app_name>.html` in a web browser (Chrome recommended)
2. Click the **ℹ** (info) icon for detailed usage instructions
3. Navigate through samples and chromosomes using the interactive interface

**Key Features**:

- Chromosome-specific visualizations with interactive plots

- CNV and ROH region exploration

- Sample summary pages with quality metrics

- Karyotype overview plots

- Downloadable data tables


> **⚠️ Important**: The HTML file must remain in the same directory as `samples/` and `components/` folders to function properly.

---

### 5.2_<app_name>_paired - Interactive Paired Sample Results

**This is your main result for paired sample analysis!**

**Purpose**: Interactive HTML-based visualization for exploring differential CNV and ROH patterns between PRE and POST samples.

**How to Access**:
1. Open `<app_name>.html` in a web browser (Chrome recommended)
2. Click the **ℹ** (info) icon for detailed usage instructions
3. Explore differential patterns between sample pairs

**Key Features**:

- Side-by-side PRE/POST comparison

- Differential CNV detection (gains/losses between conditions)

- Differential ROH analysis

- Interactive chromosome-level visualizations

- Pair summary statistics and quality metrics


> **⚠️ Important**: The HTML file must remain in the same directory as `samples/` and `components/` folders to function properly.

---

## Table Headers Reference

### CNV Detection Tables

| Column | Description |
|--------|-------------|
| `Chr` | Chromosome number |
| `Start` | Start position (genomic coordinates) |
| `End` | End position (genomic coordinates) |
| `CN_post` | Copy number in POST sample |
| `CN_pre` | Copy number in PRE sample |
| `QS` | Quality score ([Danecek et al.](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0155014)) |
| `nSites_post` | Number of SNP markers in POST sample |
| `nHets_post` | Number of heterozygous markers in POST sample |
| `nSites_pre` | Number of SNP markers in PRE sample |
| `nHets_pre` | Number of heterozygous markers in PRE sample |
| `Len` | Length of region in base pairs (End - Start) |
| `pre` | PRE sample name |
| `post` | POST sample name |
| `type` | Event type: Deletion or Duplication |

---

## Analysis Workflow Summary

### Single Mode Workflow
1. Quality Control (`1.0_quality_control/`)
2. Data Preprocessing (`2.0_preprocess/`)
3. Sample Annotation (`3.0_sample_annotation/`)
4. ROH/LOH Analysis (`4.0_roh_loh_analysis/4.1_roh_loh_single/`)
5. Data Preparation (`5.0_<app_name>_preprocessing/`)
6. **Interactive Results** (`5.1_<app_name>_single/`)

### Paired Mode Workflow
1. Quality Control (`1.0_quality_control/`)
2. Data Preprocessing (`2.0_preprocess/`)
3. Sample Annotation (`3.0_sample_annotation/`)
4. ROH/LOH Analysis (`4.0_roh_loh_analysis/4.2_roh_loh_paired/`)
5. Data Preparation (`5.0_<app_name>_preprocessing/`)
6. **Interactive Results** (`5.2_<app_name>_paired/`)

---

## Usage Tips

### Accessing Results
- **Quick Start**: Open the main `README.html` (this file) for an overview, then navigate to `5.1_<app_name>_single/` or `5.2_<app_name>_paired/` for interactive results
- **Browser Compatibility**: Chrome is recommended for best performance
- **File Integrity**: Do not move HTML files outside their directories; they depend on relative paths to `components/` and `samples/` folders

### Data Analysis
- All output files are tab-delimited or CSV format for easy import into R, Python, or Excel
- Interactive plots allow zooming, panning, and detailed inspection of specific regions
- Summary statistics are available in both the interactive interface and as downloadable tables

### Version Control
- All software versions are logged in `0.0_information/0.2_versions/`
- Pipeline parameters are documented in `0.0_information/0.3_reports/`
- This ensures full reproducibility of results

 

## References

1. Danecek P, et al. (2016) [BCFtools/RoH: a hidden Markov model approach for detecting autozygosity from next-generation sequencing data](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0155014). PLoS ONE 11(4): e0155014.

2. Original CNV Detection Pipeline: https://gitlab.mpcdf.mpg.de/luciat/cnv_detection

---

**Pipeline Version**: 2.0  
**Last Updated**: 2025
