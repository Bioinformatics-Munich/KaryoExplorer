# Subworkflows

Logical groupings of related processes for pipeline organization and modularity.

## Directory Structure

```
subworkflows/
├── analysis.nf           # IBD, LOH, and ROH analysis coordination
├── cnv_analysis.nf       # Copy number variation detection workflow
├── genotype_analysis.nf  # Genotype matching and comparison
├── input_preparation.nf  # Data preprocessing and file conversion
├── quality_control.nf    # QC filtering and validation
├── reporting.nf          # Report and documentation generation
└── visualization.nf      # Static and interactive plot generation
```
