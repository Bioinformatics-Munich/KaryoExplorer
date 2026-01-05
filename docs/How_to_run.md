# How to Run the Digital Karyotyping Pipeline

This guide provides step-by-step instructions for setting up and running the Digital Karyotyping pipeline on computing clusters.

## Prerequisites

- **Nextflow** (version 24.10.4 or later)
- **Conda** or **Singularity** for environment management
- **Java** (version 11 or later)
- **Computing cluster access** (required for optimal performance)

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
Sample	Reference
FOK0001	FOK0001BE00M32    # Paired mode: compare sample vs reference
FOK0002	FOK0002BE00M32    # Paired mode
FOK0067 None              # Single mode: analyze FOK0067 standalone (Option with None)
FOK0084 FOK0084           # Single mode: same sample name as reference (Option with including 
same sample name as reference)
```

**Analysis Modes:**
- **Paired Mode**: Compare post-treatment sample with pre-treatment reference
- **Single Mode**: Analyze sample independently (use "None" or same sample name in Reference column)


## Pipeline Setup

### 1. Create Project Directory

```bash
mkdir my_project_ID  # e.g., P25001
cd my_project_ID
```

### 2. Clone Repository

```bash
git clone <repository-url>
cd pipeline_digital_karyotyping
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
project_ID: 'YOUR_PROJECT_ID'
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

### SLURM Cluster Execution (Recommended)

The pipeline is optimized for SLURM-based cluster execution with parallelized resource management and job scheduling.

**Step 1: Prepare SLURM Submission Script**

```bash
cp templates/submit.sbatch .
```

**Step 2: Customize SLURM Parameters**

Edit `submit.sbatch` to match your cluster configuration:

```bash
#!/bin/bash
#SBATCH -o Karyoplayground.log
#SBATCH -e Karyoplayground.err
#SBATCH --job-name=Karyoplayground
#SBATCH --mem=8G                    
#SBATCH -t 06:00:00                 
#SBATCH --partition=cpu_p
#SBATCH --qos=cpu_normal
#SBATCH --nodes=1
#SBATCH --ntasks=1
```

**Step 3: Submit Job**

```bash
sbatch submit.sbatch
```

**Key Features of SLURM Execution:**
- **Automatic project ID detection** from directory structure
- **Optimized scratch directory management** (`/lustre/scratch/users/${USER}/${PROJECT_ID}`)
- **Conda environment caching** for faster subsequent runs
- **Logging** with SLURM separate stdout/stderr files
- **Resource cleanup** after completion

### Local Execution (Optional)

For testing or small datasets, you can run the pipeline locally:

```bash
export NXF_VER=24.10.4
export NXF_CONDA_CACHEDIR=/path/to/conda/cache

nextflow run main.nf \
    -params-file params.yaml \
    --outdir results \
    -profile normal \
    -with-conda \
    -resume
```

**Note**: Local execution is not recommended for production runs due to resource limitations.

## Environment Variables

Key environment variables (automatically set in SLURM template):

- **`NXF_VER`**: Nextflow version (e.g., "24.10.4")
- **`NXF_CONDA_CACHEDIR`**: Directory for conda environments
- **`NXF_WORK`**: Scratch directory for temporary files
- **`NXF_SINGULARITY_CACHEDIR`**: Directory for Singularity images
- **`TMPDIR`**: Temporary directory for processing


## Monitoring and Troubleshooting

### Monitor Job Progress

```bash
# Check SLURM job status
squeue -u $USER

# View real-time logs
tail -f Karyoplayground.log
tail -f .nextflow.log

# Check pipeline status
nextflow log
```

### Resume Failed Runs

```bash
# Resume from last successful checkpoint
sbatch submit.sbatch  # SLURM will automatically resume with -resume flag
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

### 5. Scratch Directory Cleanup
- **Issue**: Scratch directory not cleaned after job completion
- **Solution**: The SLURM template includes automatic cleanup (`rm -rf /lustre/scratch/users/${USER}/${PROJECT_ID}`)

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
├── pipeline_digital_karyotyping/              # Pipeline directory (cloned repository)
│   ├── main.nf                                # Main Nextflow workflow
│   ├── nextflow.config                        # Pipeline configuration
│   ├── params.yaml                            # Project-specific parameters (copied from template)
│   ├── submit.sbatch                          # Project-specific SLURM script (copied from template)
│   ├── sample_sheet.xls                       # Sample pairing file (generated by preprocessing)
│   ├── templates/                             # Template files
│   │   ├── params.yaml                        # Parameter template
│   │   └── submit.sbatch                      # SLURM submission template
│   ├── preprocessing/                         # Preprocessing tools
│   │   ├── preprocessing_run.sh               # Sample validation script
│   │   ├── preprocessing_config.yaml          # Preprocessing configuration
│   │   ├── preprocessing_report_*.txt         # Generated validation reports
│   │   └── sample_name_corrections_*.csv      # Generated correction suggestions (if required)
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
│       └── Changelog.md                       # Version history
└── results/                                   # Output directory (created during pipeline execution)
    ├── README.html                            # Auto-generated results documentation (based on Outputs.md)
    ├── 0.0_information/                       # Pipeline metadata and logs
    ├── 1.0_quality_control/                   # Quality control results
    ├── 2.0_preprocess/                        # Data preprocessing outputs
    ├── 3.0_sample_annotation/                 # Sample annotations
    ├── 4.0_roh_loh_analysis/                  # ROH/LOH analysis results
    ├── 5.0_<app_name>_preprocessing/          # Visualization data preparation (app_name: configurable)
    ├── 5.1_<app_name>_unpaired/               # Interactive unpaired sample results
    └── 5.2_<app_name>_paired/                 # Interactive paired sample results
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
- **submit.sbatch**: SLURM submission script customized for the HPC cluster environment
 

## Output Directory Structure

The pipeline generates a well-organized output directory with the following structure:

```
results/
├── README.html                              # This documentation file
├── 0.0_information/                         # Pipeline metadata and logs
│   ├── 0.1_pipeline_logs/                   # Process-specific log files
│   │   ├── 5.1_<app_name>_unpaired_logs/    # Unpaired analysis logs
│   │   └── 5.2_<app_name>_paired_logs/      # Paired analysis logs
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
├── 5.0_<app_name>_preprocessing/            # Data preparation for visualization (configurable)
├── 5.1_<app_name>_unpaired/                 # Interactive unpaired sample results (configurable)
└── 5.2_<app_name>_paired/                   # Interactive paired sample results (configurable)
```

---


## Pipeline Customization Options

The pipeline offers several customization options to personalize the output and branding for your organization.

### Application Naming and Branding

Customize the application name and output folder structure by editing `nextflow.config`:

```groovy
params {
  app_name = 'KaryoPlayground'  // Default: 'KaryoPlayground'
}
```

**Impact:**
- The application name appears in the **HTML page title** (e.g., `KaryoPlayground.html`)
- **Output folder names** are dynamically generated:
  - `5.0_<app_name>_preprocessing/`
  - `5.1_<app_name>_unpaired/`
  - `5.2_<app_name>_paired/`
- Application name is displayed in the **footer** of all HTML pages

**Example:**
```groovy
app_name = 'MyCustomAnalyzer'
```
This generates folders: `5.0_MyCustomAnalyzer_preprocessing/`, `5.1_MyCustomAnalyzer_unpaired/`, etc.

### Contact Information Customization

Add institutional and analyst contact information to the footer of all generated HTML pages:

```groovy
params {
  email_helmholtz = 'bioinformatics-core@helmholtz-munich.de'  // Institution email (required)
  email_analyst   = ''  // Analyst email (optional)
  name_analyst    = ''  // Analyst name (optional)
}
```

**Examples:**

**With full analyst information:**
```groovy
email_helmholtz = 'bioinformatics-core@helmholtz-munich.de'
email_analyst   = 'jane.smith@example.com'
name_analyst    = 'Dr. Jane Smith'
```

**With only institutional email:**
```groovy
email_helmholtz = 'bioinformatics-core@helmholtz-munich.de'
email_analyst   = ''
name_analyst    = ''
```

**Footer Display:**
- Helmholtz email appears with a clickable envelope icon
- If analyst name is provided: "Analysis done by: [Name] (email)"
- Analyst information helps recipients contact the person who performed the analysis

### Logo Customization

Customize the logos displayed in the interactive web application:

1. **Navigate to the assets directory**: `pipeline_digital_karyotyping/assets/logo/`
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

## Best Practices

1. **Always use preprocessing tools** to validate sample names before pipeline execution
2. **Use absolute paths** in configuration files to avoid path resolution issues
3. **Monitor resource usage** and adjust SLURM parameters accordingly
4. **Keep conda cache directory** on fast storage with sufficient space
5. **Review validation reports** carefully before applying corrections