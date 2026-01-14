# How to Run the Digital Karyotyping Pipeline

This guide provides step-by-step instructions for setting up and running the Digital Karyotyping pipeline on computing clusters.

## Prerequisites

### System Requirements

 Minimum: 4 CPU cores, 16 GB RAM, 50 GB storage

#### Software Dependencies
- **Nextflow** ≥ 24.10.0 ([installation guide](https://www.nextflow.io/docs/latest/getstarted.html))
- **Java** ≥ 11 (required by Nextflow)
- **Container/Environment Manager** (choose one):
  - Docker ≥ 20.10 (recommended for local execution)
  - Conda/Mamba (for HPC clusters)
  - Apptainer (for HPC clusters)

### Supported Platforms


- **HPC Clusters** - Compatible with SLURM, PBS, SGE, LSF, and other resource managers

- **Linux** (x86_64) 

- **Windows** (x86_64)

- **macOS** (Apple Silicon) - Supported via Docker with x86_64 emulation   

> **Note for Apple Silicon Users (M1/M2/M3):**  
> The pipeline uses Docker with `linux/amd64` platform emulation for compatibility with bioinformatics tools. Nextflow Wave automatically builds and caches containers. Successfully tested with demo dataset on MacBook Pro M1 with 16GB RAM using the `docker` profile.


### Quick Setup

**Conda Environment Setup**
```bash
# 1. Clone the repository
git clone https://github.com/Bioinformatics-Munich/KaryoExplorer.git
cd KaryoExplorer

# 2. Create environment with Nextflow and Java
conda env create -f env/karyoexplorer.yaml
conda activate karyoexplorer

# 3. Test installation
nextflow run main.nf --help
```
## Data Preparation

### 1. GenomeStudio Export

Export the following files from GenomeStudio:

- **Full Data Table**: `Full_Data_Table.txt`
- **Samples Table**: `Samples_Table.txt` 
- **SNP Table**: `SNP_Table.txt`
- **PLINK files**: Export as PLINK format (`.ped` and `.map` files)

### 2. Sample Pairing File Generation

The pipeline supports two analysis modes defined in a sample pairing file:

#### Sample Reference Table Format

```tsv
Sample          Reference
iPSC_clone1     Donor_material1    # Paired: compare iPSC_clone1 vs Donor_material1
iPSC_clone2     Donor_material2    # Paired: compare iPSC_clone2 vs Donor_material2
iPSC_clone1     iPSC_clone1        # Single: analyze iPSC_clone1 independently
iPSC_clone2     iPSC_clone2        # Single: analyze iPSC_clone2 independently
Donor_material1 Donor_material1    # Single: analyze Donor_material1 independently
Donor_material2 Donor_material2    # Single: analyze Donor_material2 independently
```


**Analysis Types:**
- **Paired Analysis**: Detects differential copy number changes between sample and reference (e.g., somatic variants in clones vs donor)
- **Single Analysis**: Identifies absolute copy number variants in individual samples based on expected base copy number. For further details, please see bcftools cnv detection algorithm. 

**Important Requirements:**
- **Tab-separated format**: Use tabs (not spaces) between Sample and Reference columns
- **Header required**: First line must contain `Sample` and `Reference` column headers
- **Paired analysis**: Sample name differs from Reference name (e.g., `iPSC_clone1` vs `Donor_material1`)
- **Single analysis**: Sample name matches Reference name (e.g., `iPSC_clone1` vs `iPSC_clone1`)
- **Complete coverage**: All samples used in paired analysis must also be included as single analysis entries

## Pipeline Setup

### 1. Create Project Directory

```bash
mkdir my_project
cd my_project
```

### 2. Clone Repository

```bash
git clone https://github.com/Bioinformatics-Munich/KaryoExplorer.git
cd KaryoExplorer
```

### 3. Configure Parameters

Copy and customize the parameter template:

```bash
cp templates/params.yaml params.yaml
```

Edit `params.yaml` with your project-specific paths:

```yaml
# Reference Genome (choose GRCh37 or GRCh38)
PAR: /path/to/PAR_Coord_GRCh38.txt
fasta: /path/to/Homo_sapiens.GRCh38.dna.primary_assembly.fa

# Project Information
project_ID: 'YOUR_PROJECT'
responsible_person: 'Name_of_the_requester'

# Input Files
samples_refs: /path/to/sample_sheet.xls
manifest: /path/to/GSA-MD-48v4-0_Manifest.csv
fullTable: /path/to/Full_Data_Table.txt
samplesTable: /path/to/Samples_Table.txt
snpTable: /path/to/SNP_Table.txt
gsplink: /path/to/PLINK_files_directory
```

## Running the Pipeline

### HPC Cluster Execution (Recommended)

The pipeline is optimized for HPC cluster execution with parallelized resource management and job scheduling. It is compatible with various resource managers including SLURM, PBS, SGE, and LSF.

**Step 1: Prepare Submission Script**

Create a submission script based on your HPC cluster's resource manager and requirements. The script should:
- Set appropriate resource limits (memory, time, CPUs)
- Define environment variables for Nextflow
- Execute the pipeline with the desired profile
- Include cleanup commands for temporary files

**Step 2: Configure Nextflow Execution**

Your submission script should execute Nextflow with appropriate parameters:

```bash
nextflow run main.nf \
    -params-file params.yaml \
    --outdir results \
    -profile <your_profile> \
    -resume
```

Available profiles:
- `docker` - For Docker-based execution
- `conda` - For Conda environment management
- `slurm` - For SLURM clusters with specific configurations
- Custom profiles can be defined in `nextflow.config`

**Step 3: Submit Job**

Submit your job using the appropriate command for your resource manager (e.g., `sbatch`, `qsub`, `bsub`).

### Local Execution (Optional)

For testing or small datasets, you can run the pipeline locally:

```bash
nextflow run main.nf \
    -params-file params.yaml \
    --outdir results \
    -profile docker \
    -resume
```

## Environment Variables

Key environment variables (recommended to be set in your HPC submission script for optimal execution):

- **`NXF_VER`**: Nextflow version (e.g., "24.10.4")
- **`NXF_CONDA_CACHEDIR`**: Directory for conda environments
- **`NXF_WORK`**: Scratch directory for temporary files
- **`NXF_SINGULARITY_CACHEDIR`**: Directory for Singularity/Apptainer images (if using containers)
- **`TMPDIR`**: Temporary directory for processing


## Monitoring and Troubleshooting

### Monitor Job Progress

```bash
# Check job status (adjust command for your resource manager)

# SLURM:
squeue -u $USER
# PBS:
qstat -u $USER
# SGE:
qstat -u $USER
# LSF:
bjobs -u $USER

# View real-time logs
tail -f KaryoExplorer.log
tail -f .nextflow.log

# Check pipeline status
nextflow log
```

### Resume Failed Runs

```bash
# Resume from last successful checkpoint
# Submit your job again - Nextflow will automatically resume with -resume flag
# The specific command depends on your resource manager (sbatch, qsub, bsub, etc.)
```

## Common Issues and Solutions

### 1. Sample Name Validation
- **Issue**: Sample names contain invalid characters
- **Solution**: Use preprocessing tools to identify and correct naming issues

### 2. File Path Problems
- **Issue**: Relative paths causing file not found errors
- **Solution**: Use absolute paths in `params.yaml`

### 3. Conda Environment Issues
- **Issue**: Conda cache directory full or inaccessible
- **Solution**: Ensure sufficient space in `NXF_CONDA_CACHEDIR` or you have correct ACL permissions to the directory. 

### 4. Scratch Directory Cleanup
- **Issue**: Scratch directory not cleaned after job completion
- **Solution**: Add cleanup commands to your submission script to remove temporary files after pipeline completion

## Input Structure

The following directory structure shows the recommended organization of input files, pipeline components, and output directories:

```
my_project_ID/                                 # Main project directory (e.g., P25001)
├── data/                                      # Input data directory
│   ├── GenomeStudio_exports/                  # GenomeStudio exported files
│   │   ├── Full_Data_Table.txt                # Complete SNP data with LRR/BAF values
│   │   ├── Samples_Table.txt                  # Sample metadata and QC metrics
│   │   └── SNP_Table.txt                      # SNP annotation information
│   ├── PLINK_files/                           # PLINK format files
│   │   ├── PLINK_280825_1054.ped              # Genotype data in PLINK format
│   │   └── PLINK_280825_1054.map              # SNP map file
│   ├── manifest/                              # Illumina array manifest
│   │   └── GSA-MD-48v4-0_20098041_B2.csv      # Array manifest file (CSV format)
│   └── reference_genome/                      # Reference genome files
│       ├── Homo_sapiens.GRCh38.dna.primary_assembly.fa     # Reference FASTA
│       └── Homo_sapiens.GRCh38.dna.primary_assembly.fa.fai # FASTA index
├── KaryoExplorer/                             # Pipeline directory (cloned repository)
│   ├── main.nf                                # Main Nextflow workflow
│   ├── nextflow.config                        # Pipeline configuration
│   ├── params.yaml                            # Project-specific parameters (copied from template)
│   ├── sample_sheet.xls                       # Sample pairing file
│   ├── templates/                             # Template files
│   │   └── params.yaml                        # Parameter template
│   ├── logs/                                  # Execution logs (created during run)
│   │   └── nextflow/                          # Nextflow-specific logs
│   │       ├── report.html                    # Execution report
│   │       ├── trace.txt                      # Process trace
│   │       └── timeline.html                  # Execution timeline
│   ├── modules/                               # Nextflow modules
│   ├── subworkflows/                          # Nextflow subworkflows
│   ├── bin/                                   # Analysis scripts and tools
│   ├── env/                                   # Conda environment files
│   ├── conf/                                  # Configuration files
│   ├── datasets/                              # Reference datasets
│   │   └── PAR/PAR_Coord_GRCh38.txt           # Pseudoautosomal region files
│   └── docs/                                  # Documentation
│       ├── How_to_run.md                      # This file
│       ├── Outputs.md                         # Output documentation
└── results/                                   # Output directory (created during pipeline execution)
    ├── README.html                            # Auto-generated results documentation (based on Outputs.md)
    ├── 0.0_information/                       # Pipeline metadata and logs
    ├── 1.0_quality_control/                   # Quality control results
    ├── 2.0_preprocess/                        # Data preprocessing outputs
    ├── 3.0_sample_annotation/                 # Sample annotations
    ├── 4.0_roh_loh_analysis/                  # ROH/LOH analysis results
    ├── 5.0_KaryoExplorer_preprocessing/       # Visualization data preparation (app_name: configurable)
    ├── 5.1_KaryoExplorer_single/              # Interactive single sample results
    └── 5.2_KaryoExplorer_paired/              # Interactive paired sample results
```

### Key Input File Requirements

**Essential Files:**
- **GenomeStudio Exports**: Full Data Table, Samples Table, SNP Table (`.txt` format)
- **PLINK Files**: Genotype data in PLINK format (`.ped` and `.map` files)
- **Array Manifest**: Illumina manifest file in CSV format
- **Reference Genome**: FASTA file with index for chosen genome build (GRCh37/GRCh38)
- **Sample Pairing File**: Excel file (xls) defining analysis mode for each sample (generated by preprocessing tools)

**Configuration Files:**
- **params.yaml**: Project-specific parameter file with all input/output paths
 

## Output Directory Structure

The pipeline generates a well-organized output directory with the following structure:

```
results/
├── README.html                              # This documentation file
├── 0.0_information/                         # Pipeline metadata and logs
│   ├── 0.1_pipeline_logs/                   # Process-specific log files
│   │   ├── 5.1_KaryoExplorer_single_logs/      # single analysis logs
│   │   └── 5.2_KaryoExplorer_paired_logs/      # Paired analysis logs
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
├── 5.0_KaryoExplorer_preprocessing/            # Data preparation for visualization (configurable)
├── 5.1_KaryoExplorer_single/                   # Interactive single sample results (configurable)
└── 5.2_KaryoExplorer_paired/                   # Interactive paired sample results (configurable)
```

---


## Pipeline Customization Options

The pipeline offers several customization options to personalize the output and branding for your organization.

### Contact Information Customization

Add institutional and analyst contact information to the footer of all generated HTML pages:

```groovy
params {
  email_helmholtz = 'example@institution.de'  // Institution email (required)
  email_analyst   = ''  // Analyst email (optional)
  name_analyst    = ''  // Analyst name (optional)
}
```

**Examples:**

**With full analyst information:**
```groovy
email_helmholtz = 'example@institution.de'
email_analyst   = 'jane.smith@example.com'
name_analyst    = 'Dr. Jane Smith'
```

**With only institutional email:**
```groovy
email_helmholtz = 'example@institution.de'
email_analyst   = ''
name_analyst    = ''
```

**Footer Display:**
- If analyst name is provided: "Analysis done by: [Name] (email)"
- Analyst information helps recipients contact the person who performed the analysis

### Logo Customization

Customize the logos displayed in the interactive web application:

1. **Navigate to the assets directory**: `assets/logo/`
2. **Replace the existing logo files** with your custom logos:
   - `left_icon.png` - Left side logo/icon (typically institutional logo)
   - `right_icon.png` - Right side logo/icon (typically project logo)
3. **Maintain the same file names** and PNG format for proper integration

**Requirements:**
- File format: PNG
- Recommended dimensions: 100x100 pixels or similar square format
- Keep original filenames for automatic recognition

### Results Documentation Customization

Customize the documentation provided to end users in their results folder:

1. **Edit the source file**: `docs/Outputs.md`
2. **Add project-specific information**, modify descriptions, or include additional guidance
3. **The pipeline automatically generates** `README.html` in the results directory based on this file

**Benefits:**
- Provide project-specific context to result recipients
- Include institutional branding and contact information  
- Add custom analysis guidelines or interpretation notes
- Maintain consistent documentation across projects 


For detailed output descriptions, see [Outputs.md](Outputs.md).
