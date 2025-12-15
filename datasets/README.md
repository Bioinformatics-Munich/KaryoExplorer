# Datasets

Reference datasets and coordinate files required for genomic analysis.

## Directory Structure

```
datasets/
├── PAR/                    # Pseudoautosomal Region coordinates
│   ├── PAR_Coord_GRCh37.txt   # PAR coordinates for GRCh37/hg19 reference
│   └── PAR_Coord_GRCh38.txt   # PAR coordinates for GRCh38/hg38 reference
└── demo/                   # Illumina demo dataset (tracked via Git LFS)
    └── [demo dataset files]  # See demo/README.md for details
```

## Demo Dataset

The Illumina Global Screening Array v4.0 demo dataset is stored in `datasets/demo/` and is tracked using **Git LFS** due to its size (~1.74 GB).

### Important Notes

- **Git LFS Required**: This dataset uses Git Large File Storage (LFS). Make sure Git LFS is installed before cloning.
- **Installation**: If you haven't installed Git LFS, see the [Git LFS Setup Guide](../docs/Git_LFS_Setup.md)
- **Download**: After cloning, run `git lfs pull` to download the actual files
- **Usage**: See the [Illumina Demo Dataset Guide](../docs/illumina_demo_dataset_guide.pdf) for detailed instructions
