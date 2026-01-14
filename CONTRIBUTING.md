# Contributing to KaryoExplorer

Thank you for your interest in contributing to KaryoExplorer! We welcome contributions from the community.

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue on GitHub with:
- A clear, descriptive title
- Detailed description of the problem
- Steps to reproduce the issue
- Your environment details:
  - Nextflow version (`nextflow -version`)
  - Execution profile (conda/docker/singularity)
  - Operating system
- Error messages and relevant log files
- Minimal reproducible example if possible

### Suggesting Enhancements

We welcome feature requests! Please open an issue describing:
- The use case and motivation
- Proposed solution or approach
- Expected behavior
- Alternative approaches you've considered
- Any relevant examples from other tools

### Pull Requests

1. **Fork the repository** and create your branch from `main`
   ```bash
   git clone https://github.com/YOUR_USERNAME/KaryoExplorer.git
   cd KaryoExplorer
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow the existing code style
   - Add comments for complex logic
   - Update documentation if needed

3. **Test your changes**
   - Run the demo dataset to ensure the pipeline still works
   - Test with different execution profiles if possible
   - Verify that existing functionality is not broken

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add feature: brief description"
   ```

5. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Open a Pull Request**
   - Provide a clear description of the changes
   - Reference any related issues
   - Describe how you tested the changes

## Development Guidelines

### Code Style

- **Nextflow processes**: Follow Nextflow DSL2 best practices
- **Python scripts**: Follow PEP 8 style guidelines
- **R scripts**: Follow tidyverse style guide
- **Documentation**: Use clear, concise language

### Commit Messages

- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit first line to 72 characters
- Reference issues and pull requests when relevant

### Documentation

When adding new features:
- Update relevant documentation in `docs/`
- Add usage examples
- Update the README if the feature affects user-facing functionality
- Document any new parameters in `docs/How_to_run.md`

### Testing

- Test with the demo dataset
- Verify compatibility with different execution profiles (conda, docker, singularity)
- Check that output files are generated correctly
- Validate interactive HTML reports still function

## Project Structure

```
KaryoExplorer/
├── main.nf                 # Main Nextflow pipeline
├── nextflow.config         # Configuration file
├── nextflow_schema.json    # Pipeline schema
├── LICENSE                 # MIT License
├── README.md               # Main documentation
├── CONTRIBUTING.md         # Contribution guidelines
├── CODE_OF_CONDUCT.md      # Community standards
│
├── modules/                # Nextflow DSL2 modules
│   └── local/              # Local module definitions
│       ├── analysis/       # Analysis modules
│       ├── cnv/            # CNV detection modules
│       ├── dynamic_plotting/ # Visualization modules
│       ├── genotyping/     # Genotyping modules
│       ├── input/          # Input processing modules
│       ├── plotting/       # Static plotting modules
│       ├── qc/             # Quality control modules
│       └── reporting/      # Report generation modules
│
├── subworkflows/           # Nextflow subworkflows
│   ├── analysis.nf         # Analysis subworkflow
│   ├── cnv_analysis.nf     # CNV analysis subworkflow
│   ├── genotype_analysis.nf # Genotype analysis subworkflow
│   ├── input_preparation.nf # Input preparation subworkflow
│   ├── quality_control.nf  # QC subworkflow
│   ├── reporting.nf        # Reporting subworkflow
│   └── visualization.nf    # Visualization subworkflow
│
├── workflows/              # Main workflow definitions
│   └── digital_karyotyping.nf # Main workflow
│
├── bin/                    # Scripts used by the pipeline
│   ├── analysis/           # Analysis scripts (Python, R, Bash)
│   ├── cnv/                # CNV analysis scripts (R)
│   ├── dynamic_plotting/   # Interactive visualization (Python)
│   ├── functions/          # Utility functions (R)
│   ├── genotyping/         # Genotyping scripts (R)
│   ├── plotting/           # Static plotting scripts (R)
│   └── qc/                 # Quality control scripts (R)
│
├── conf/                   # Configuration profiles
│   ├── base.config         # Base configuration
│   ├── docker.config       # Docker profile
│   └── slurm.config        # SLURM cluster profile
│
├── env/                    # Conda environment files
│   ├── karyoexplorer.yaml  # Main environment (Nextflow + Java)
│   ├── bokeh.yaml          # Visualization environment
│   ├── ibd.yaml            # IBD analysis environment
│   ├── pandoc.yaml         # Documentation environment
│   ├── preproc.yaml        # Preprocessing environment
│   └── renv.yaml           # R environment
│
├── templates/              # Configuration templates
│   └── params.yaml         # Parameter template
│
├── docs/                   # Documentation
│   ├── How_to_run.md       # Installation and usage guide
│   ├── Outputs.md          # Output documentation
│   └── illumina_demo_dataset_guide.pdf # Demo tutorial
│
├── datasets/               # Demo datasets and references
│   ├── demo/               # Illumina demo data
│   └── PAR/                # Pseudoautosomal region coordinates
│
└── assets/                 # Images and static files
    ├── figures/            # Documentation figures
    └── logo/               # Project logos
```

## Questions?

If you have questions about contributing, feel free to:
- Open an issue for discussion
- Contact the development team at cf-bios@helmholtz-munich.de

## Code of Conduct

Please note that this project is released with a Code of Conduct. By participating in this project you agree to abide by its terms.

## Recognition

Contributors will be acknowledged in the project documentation and release notes.

Thank you for contributing to KaryoExplorer!

