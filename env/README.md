# Environment Configurations

Conda environment specifications for the KaryoExplorer pipeline.

## Quick Setup Environment

### karyoexplorer.yaml

A minimal environment containing only the essential tools needed to run the pipeline (Nextflow and Java). All other dependencies are automatically managed by Nextflow during pipeline execution.

**Create the environment:**
```bash
conda env create -f env/karyoexplorer.yaml
conda activate karyoexplorer
```

**Includes:**
- Nextflow ≥ 24.10.0 (workflow management)
- OpenJDK ≥ 11 (Java runtime for Nextflow)
- Conda ≥ 23.0 (environment management)

**What happens when you run the pipeline:**
When you execute `nextflow run main.nf -profile conda`, Nextflow automatically creates and manages all required modular environments based on the specifications below.

## Modular Environments (Automatically Managed)

These environments are automatically created by Nextflow during pipeline execution. You don't need to create them manually.

```
env/
├── karyoexplorer.yaml  # Quick setup (Nextflow + Java)
├── bokeh.yaml          # Interactive visualization (auto-created by pipeline)
├── ibd.yaml            # Identity-by-descent analysis (auto-created by pipeline)
├── pandoc.yaml         # Document conversion (auto-created by pipeline)
├── preproc.yaml        # Data preprocessing (auto-created by pipeline)
└── renv.yaml           # R statistical computing (auto-created by pipeline)
```

**Note:** Manual creation of modular environments is only needed for standalone script execution or troubleshooting specific components.
