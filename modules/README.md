# Nextflow Modules

Modular Nextflow processes organized by analysis type for reusability and maintainability.

## Directory Structure

```
modules/
└── local/                        # Pipeline-specific modules
    ├── analysis/                 # Specialized genomic analyses
    │   ├── ibd.nf                # Identity-by-descent analysis
    │   ├── loh.nf                # Loss of heterozygosity detection
    │   └── roh.nf                # Runs of homozygosity analysis
    ├── cnv/                      # Copy number variation analysis
    │   ├── cnv_core.nf           # Core CNV detection algorithms
    │   └── cnv_summary.nf        # CNV result summarization
    ├── dynamic_plotting/         # Interactive web application
    │   ├── dynamic_plotting_data_preprocessing.nf  # Data prep for visualization
    │   └── dynamic_plotting.nf   # Web app generation
    ├── genotyping/               # Genotype analysis and matching
    │   └── genotype_matching.nf  # Sample comparison and pairing
    ├── input/                    # Data input and preprocessing
    │   ├── manifest.nf           # Manifest file processing
    │   └── vcf.nf                # VCF file creation and annotation
    ├── plotting/                 # Static visualization
    │   └── cnv_plots.nf          # CNV and LRR-BAF plotting
    ├── qc/                       # Quality control
    │   └── quality_control.nf    # Data filtering and QC metrics
    └── reporting/                # Report generation
        └── reports.nf            # Parameter reports and documentation
```
