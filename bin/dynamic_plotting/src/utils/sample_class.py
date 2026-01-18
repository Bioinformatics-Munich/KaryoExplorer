import pandas as pd
import os
import glob    
import logging

class Parameters:
    def __init__(self, parameters_file):
        self.parameters_file = parameters_file
        self.project_ID = None   
        self.responsible_person = None   
        self.reference_genome = None
        self.data = {}  #  
        
        
        # Parse reference genome from parameters file
        self._parse_parameters()
    
    def _parse_parameters(self):
        """Parse parameters from JSON file"""
        import json
        with open(self.parameters_file) as f:
            self.data = json.load(f)  # Store entire JSON data
            self.reference_genome = self.data['reference_genome']['detected']
            
            # Load project information if available
            if 'project_info' in self.data:
                self.project_ID = self.data['project_info'].get('project_ID', 'Unknown')
                self.responsible_person = self.data['project_info'].get('responsible_person', 'Unknown')
            else:
                # Fallback to default values if not in JSON
                self.project_ID = "Project_ID"
                self.responsible_person = "Responsible_Person"

class SingleSample:
    def __init__(self, sample_id, sample_type, pre_sample, pre_sex, call_rate, call_rate_filt, LRR_stdev, parameters):
        self.sample_id = sample_id
        self.sample_type = sample_type
        self.pre_sample = pre_sample
        self.pre_sex = pre_sex
        self.call_rate = call_rate
        self.call_rate_filt = call_rate_filt
        self.LRR_stdev = LRR_stdev
        self.parameters = parameters
        
        # Data attributes to be loaded later
        self.baf_lrr_data = None
        self.cn_probabilities_data = None
        self.cn_summary_data = None
        self.cnv_detection_filtered = None
        self.cnv_chromosomes = None
        self.union_bed = None
        self.roh_bed = None
        self.cn_bed = None
        self.total_cnvs = 0  # Initialize total_cnvs attribute
        self.available_chromosomes = None  # Add this line

    def load_data(self, samples_dir: str):
        """Load all CSV files for this sample from the samples directory"""
        sample_dir = os.path.join(samples_dir, self.pre_sample)
        
        # Define file patterns
        file_patterns = {
            'baf_lrr_data': f'single_baf_lrr_data_{self.pre_sample}.csv',
            'cn_probabilities_data': f'single_cn_probabilities_data_{self.pre_sample}.csv',
            'cn_summary_data': f'single_cn_summary_data_{self.pre_sample}.csv',
            'cnv_detection_filtered': f'single_cnv_detection_filtered_{self.pre_sample}.csv',
            'cnv_chromosomes': f'single_cnv_chromosomes_{self.pre_sample}.csv',
            'union_bed': f'single_union_bed_{self.pre_sample}.csv',
            'roh_bed': f'single_roh_bed_{self.pre_sample}.csv',
            'cn_bed': f'single_cn_bed_{self.pre_sample}.csv'
        }
        
        # Load each file if it exists
        for attr, filename in file_patterns.items():
            file_path = os.path.join(sample_dir, filename)
            if os.path.exists(file_path):
                try:
                    data = pd.read_csv(file_path, dtype={'Chromosome': str}, low_memory=False)
                    setattr(self, attr, data)
                    
                    if attr == 'baf_lrr_data' and data is not None:
                        # Get unique chromosomes and sort naturally
                        chromosomes = data['Chromosome'].unique().tolist()
                        # Updated sorting: numeric first (1-22), then X/Y
                        chromosomes.sort(key=lambda x: (
                            not x.isdigit(),  # False comes first (digits)
                            int(x) if x.isdigit() else float('inf'),  # Sort numbers numerically
                            x  # For non-digits (X/Y), sort alphabetically
                        ))
                        self.available_chromosomes = chromosomes
                    
                    # Existing CNV count code
                    if attr == 'cnv_detection_filtered' and data is not None:
                        self.total_cnvs = len(data)
                        
                        # Calculate significant CNVs (p < 0.05)
                        if 'QS' in data.columns:
                            # Convert QS to p-value: p = 10^(-QS/10)
                            data['p_value'] = data['QS'].apply(lambda qs: 10**(-qs/10))
                            self.significant_cnvs = len(data[data['p_value'] < 0.05])
                        else:
                            self.significant_cnvs = 0
                except Exception as e:
                    print(f"Error loading {filename}: {str(e)}")
                    setattr(self, attr, None)
            else:
                print(f"Warning: File not found: {file_path}")
                setattr(self, attr, None)

        # Add LRR and CNV statistics
        self.lrr_stats = {}
        self.chromosome_stats = {}
        
        if self.baf_lrr_data is not None:
            # Calculate chromosome-specific LRR stats
            for chrom in self.available_chromosomes:
                chrom_data = self.baf_lrr_data[self.baf_lrr_data['Chromosome'] == chrom]
                self.lrr_stats[chrom] = {
                    'mean': chrom_data['LRR'].mean(),
                    'median': chrom_data['LRR'].median(),
                    'std': chrom_data['LRR'].std()
                }

        if self.cnv_detection_filtered is not None:
            # Calculate chromosome-specific CNV stats using Type column
            for chrom in self.available_chromosomes:
                chrom_cnvs = self.cnv_detection_filtered[self.cnv_detection_filtered['Chromosome'] == chrom]
                self.chromosome_stats[chrom] = {
                    'total_cnvs': len(chrom_cnvs),
                    'duplications': len(chrom_cnvs[chrom_cnvs['Type'].str.contains('Duplication', case=False)]),
                    'deletions': len(chrom_cnvs[chrom_cnvs['Type'].str.contains('Deletion', case=False)])
                }

        print(f"Available chromosomes for {self.sample_id}: {self.available_chromosomes}")

    def _calculate_cnv_stats(self):
        """Calculate CNV statistics while preserving original data"""
        stats = {}
        if self.cnv_detection_filtered is not None and self.available_chromosomes:
            # Handle different column names for single vs paired
            cn_column = 'CN' if 'CN' in self.cnv_detection_filtered.columns else 'CopyNumber'
            
            for chrom in self.available_chromosomes:
                chrom_data = self.cnv_detection_filtered[self.cnv_detection_filtered['Chromosome'] == chrom]
                stats[chrom] = {
                    'duplications': len(chrom_data[chrom_data[cn_column] > 2]),
                    'deletions': len(chrom_data[chrom_data[cn_column] < 2])
                }
        return stats

    def __str__(self):
        return f"SingleSample(sample_id={self.sample_id}, pre_sample={self.pre_sample}, type={self.sample_type}, total_cnvs={self.total_cnvs})"

    def __repr__(self):
        return self.__str__()
    
    
    
    
    
    
# ────────────────────────────────────────────────────────────────────────────────
# NEW CLASSES – directory‑aware loaders
# ────────────────────────────────────────────────────────────────────────────────
class PreSample(SingleSample):
    """SingleSample acting as *pre* in ≥1 pairs – loads files named 'pre_*' and their
    single–bed companions (`pre_union_bed_single`, `pre_roh_bed_single`)."""

    def __init__(self, sample_id, pre_sample, **kwargs):
        super().__init__(
            sample_id=sample_id,
            sample_type='pre',
            pre_sample=pre_sample,
            pre_sex=kwargs.get('pre_sex', 'Unknown'),
            call_rate=kwargs.get('call_rate', 0),
            call_rate_filt=kwargs.get('call_rate_filt', 0),
            LRR_stdev=kwargs.get('LRR_stdev', 0),
            parameters=kwargs.get('parameters', None)
        )
        self.available_chromosomes = []
        self.significant_cnvs = 0  # Initialize significant_cnvs
        
    def load_data(self, samples_dir: str) -> None:
        import glob, os, pandas as pd, logging

        pair_dirs = glob.glob(os.path.join(samples_dir, f"PRE_{self.pre_sample}_POST_*"))
        if not pair_dirs:
            logging.warning("No PRE‑directories found for %s", self.pre_sample)
            return

        patterns = {
            # per‑locus data
            "baf_lrr_data":         f"pre_baf_lrr_data_PRE_{self.pre_sample}_POST_*.csv",
            "cn_probabilities_data":f"pre_cn_probabilities_data_PRE_{self.pre_sample}_POST_*.csv",
            "cn_summary_data":      f"pre_cn_summary_data_PRE_{self.pre_sample}_POST_*.csv",
            # single BEDs
            "union_bed":            f"pre_union_bed_single_PRE_{self.pre_sample}_POST_*.csv",
            "roh_bed":              f"pre_roh_bed_single_PRE_{self.pre_sample}_POST_*.csv",
            "cn_bed":               f"pre_cn_bed_single_PRE_{self.pre_sample}_POST_*.csv"
        }

        for attr, glob_pat in patterns.items():
            for d in pair_dirs:                       # first match wins
                matches = glob.glob(os.path.join(d, glob_pat))
                if matches:
                    try:
                        setattr(self, attr, pd.read_csv(matches[0], dtype={"Chromosome": str}))
                    except Exception as e:
                        logging.error("Error loading %s: %s", matches[0], e)
                    break

        # total CNVs from summary
        if self.cn_summary_data is not None:
            self.total_cnvs = len(self.cn_summary_data)
            
            # Calculate significant CNVs (p < 0.05)
            if 'Quality' in self.cn_summary_data.columns:
                # Convert Quality to p-value: p = 10^(-Quality/10)
                pre_qual_data = self.cn_summary_data['Quality'].apply(lambda q: 10**(-q/10))
                self.significant_cnvs = len(pre_qual_data[pre_qual_data < 0.05])

        # Extract chromosomes from BAF/LRR data
        if self.baf_lrr_data is not None:
            self.available_chromosomes = sorted(
                self.baf_lrr_data['Chromosome'].unique(),
                key=lambda x: (
                    not x.isdigit(),          # Numeric first (False comes first)
                    int(x) if x.isdigit() else float('inf'),  # Sort numbers numerically
                    x                         # Alphabetical for non-digits (X/Y)
                )
            )

        if self.baf_lrr_data is None:
            print("BAF/LRR data missing - cannot determine chromosomes!")

    def __str__(self):
        return f"PreSample({self.sample_id}, CNVs={self.total_cnvs})"


class PostSample(SingleSample):
    """SingleSample acting as *post* – loads `post_*` and the *_single BEDs."""

    def __init__(self, sample_id, pre_sample, **kwargs):
        super().__init__(
            sample_id=sample_id,
            sample_type='post',
            pre_sample=pre_sample,
            pre_sex=kwargs.get('pre_sex', 'Unknown'),
            call_rate=kwargs.get('call_rate', 0),
            call_rate_filt=kwargs.get('call_rate_filt', 0),
            LRR_stdev=kwargs.get('LRR_stdev', 0),
            parameters=kwargs.get('parameters', None)
        )
        self.available_chromosomes = []
        self.significant_cnvs = 0  # Initialize significant_cnvs
        
    def load_data(self, samples_dir: str) -> None:
        import glob, os, pandas as pd, logging

        pair_dirs = glob.glob(os.path.join(samples_dir, f"PRE_*_POST_{self.pre_sample}"))
        if not pair_dirs:
            logging.warning("No POST‑directories found for %s", self.pre_sample)
            return

        patterns = {
            "baf_lrr_data":         f"post_baf_lrr_data_PRE_*_POST_{self.pre_sample}.csv",
            "cn_probabilities_data":f"post_cn_probabilities_data_PRE_*_POST_{self.pre_sample}.csv",
            "cn_summary_data":      f"post_cn_summary_data_PRE_*_POST_{self.pre_sample}.csv",
            "union_bed":            f"post_union_bed_single_PRE_*_POST_{self.pre_sample}.csv",
            "roh_bed":              f"post_roh_bed_single_PRE_*_POST_{self.pre_sample}.csv",
            "cn_bed":               f"post_cn_bed_single_PRE_*_POST_{self.pre_sample}.csv"
        }

        for attr, glob_pat in patterns.items():
            for d in pair_dirs:
                matches = glob.glob(os.path.join(d, glob_pat))
                if matches:
                    try:
                        setattr(self, attr, pd.read_csv(matches[0], dtype={"Chromosome": str}))
                    except Exception as e:
                        logging.error("Error loading %s: %s", matches[0], e)
                    break

        if self.cn_summary_data is not None:
            self.total_cnvs = len(self.cn_summary_data)
            
            # Calculate significant CNVs (p < 0.05)
            if 'Quality' in self.cn_summary_data.columns:
                # Convert Quality to p-value: p = 10^(-Quality/10)
                post_qual_data = self.cn_summary_data['Quality'].apply(lambda q: 10**(-q/10))
                self.significant_cnvs = len(post_qual_data[post_qual_data < 0.05])

        # Extract chromosomes from BAF/LRR data
        if self.baf_lrr_data is not None:
            self.available_chromosomes = sorted(
                self.baf_lrr_data['Chromosome'].unique(),
                key=lambda x: (
                    not x.isdigit(),          # Numeric first (False comes first)
                    int(x) if x.isdigit() else float('inf'),  # Sort numbers numerically
                    x                         # Alphabetical for non-digits (X/Y)
                )
            )

        if self.baf_lrr_data is None:
            print("BAF/LRR data missing - cannot determine chromosomes!")

    def __str__(self):
        return f"PostSample({self.sample_id}, CNVs={self.total_cnvs})"

class PairedClass:
    """
    Combines a PreSample and a PostSample.

    Directory name  : PRE_<pre>_POST_<post>
    Pair‑level files : combined_*  inside that directory
    """

    def __init__(self, pre: PreSample, post: PostSample, sample_type: str, PI_HAT: float):
        self.pre = pre
        self.post = post
        self.sample_type = sample_type
        self.PI_HAT = float(PI_HAT)

        self.pair_id = f"PRE_{pre.pre_sample}_POST_{post.pre_sample}"

        # pair‑level data
        self.cnv_chromosomes = None
        self.cnv_detection_filtered = None
        self.union_bed = None
        self.roh_bed = None
        self.cn_bed = None
        self.total_cnvs = 0
        self.significant_cnvs = 0  # Initialize significant CNVs count
        self.available_chromosomes = post.available_chromosomes  # Direct reference

    # ---------------------------------------------------------------- loaders
    def load_data(self, samples_dir: str) -> None:
        pair_dir = os.path.join(samples_dir, self.pair_id)
        patt = {
            "cnv_chromosomes": f"combined_cnv_chromosomes_{self.pair_id}.csv",
            "cnv_detection_filtered": f"combined_cnv_detection_filtered_{self.pair_id}.csv",
            "union_bed": f"combined_union_bed_{self.pair_id}.csv",
            "roh_bed": f"combined_roh_bed_{self.pair_id}.csv",
            "cn_bed": f"combined_cn_bed_{self.pair_id}.csv"
        }

        for attr, fname in patt.items():
            fpath = os.path.join(pair_dir, fname)
            if os.path.exists(fpath):
                try:
                    setattr(self, attr, pd.read_csv(fpath, dtype={"Chromosome": str}))
                except Exception as e:
                    logging.error("Error loading %s: %s", fpath, e)

        # Add CNV count calculation
        if self.cnv_detection_filtered is not None:
            self.total_cnvs = len(self.cnv_detection_filtered)
            
            # Calculate significant CNVs (p < 0.05)
            if 'QualityScore' in self.cnv_detection_filtered.columns:
                # Convert QualityScore to p-value: p = 10^(-QualityScore/10)
                self.cnv_detection_filtered['p_value'] = self.cnv_detection_filtered['QualityScore'].apply(
                    lambda q: 10**(-q/10))
                self.significant_cnvs = len(self.cnv_detection_filtered[self.cnv_detection_filtered['p_value'] < 0.05])
        else:
            self.total_cnvs = 0
            self.significant_cnvs = 0
            logging.warning(f"No CNV detection data found for {self.pair_id}")

        # Add pair-level statistics
        self.lrr_stats = {}
        self.chromosome_stats = {}

        if self.post.baf_lrr_data is not None:
            # Calculate chromosome-specific LRR stats from post sample
            for chrom in self.post.available_chromosomes:
                chrom_data = self.post.baf_lrr_data[self.post.baf_lrr_data['Chromosome'] == chrom]
                self.lrr_stats[chrom] = {
                    'mean': chrom_data['LRR'].mean(),
                    'median': chrom_data['LRR'].median(),
                    'std': chrom_data['LRR'].std()
                }

        if self.cnv_detection_filtered is not None:
            # Calculate pair-level chromosome-specific CNV stats using Type column
            for chrom in self.post.available_chromosomes:
                chrom_cnvs = self.cnv_detection_filtered[self.cnv_detection_filtered['Chromosome'] == chrom]
                self.chromosome_stats[chrom] = {
                    'total_cnvs': len(chrom_cnvs),
                    'duplications': len(chrom_cnvs[chrom_cnvs['Type'].str.contains('Duplication', case=False)]),
                    'deletions': len(chrom_cnvs[chrom_cnvs['Type'].str.contains('Deletion', case=False)])
                }

    def _calculate_pair_cnv_stats(self):
        """Calculate pair-level CNV statistics while preserving original data"""
        stats = {}
        if self.cnv_detection_filtered is not None and self.post.available_chromosomes:
            # Use CN_post for paired analysis
            cn_column = 'CN_post' if 'CN_post' in self.cnv_detection_filtered.columns else 'Copy_Number'
            
            for chrom in self.post.available_chromosomes:
                chrom_data = self.cnv_detection_filtered[self.cnv_detection_filtered['Chromosome'] == chrom]
                stats[chrom] = {
                    'duplications': len(chrom_data[chrom_data[cn_column] > 2]),
                    'deletions': len(chrom_data[chrom_data[cn_column] < 2])
                }
        return stats

    # ---------------------------------------------------------------- repr
    def __str__(self):
        return (
            f"PairedClass({self.pair_id}, PI_HAT={self.PI_HAT:.4f}, "
            f"pre={self.pre.sample_id}, post={self.post.sample_id})"
        )

    __repr__ = __str__
    
    
    
    
    