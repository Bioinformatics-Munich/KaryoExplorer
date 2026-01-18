# Workflows

Main workflow orchestration for the KaryoExplorer pipeline.

## Directory Structure

```
workflows/
└── digital_karyotyping.nf  # Primary workflow coordinating all analysis steps
```

## Overview

The main workflow (`DK`) orchestrates the complete digital karyotyping analysis including:
- Quality control and data preprocessing
- CNV detection and analysis
- Genotype matching and sample pairing
- ROH/LOH analysis
- Interactive visualization generation
