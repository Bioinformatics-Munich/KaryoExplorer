import pandas as pd
import os
import glob
import logging
from typing import Tuple, List
import os, glob, logging
from typing import List, Tuple


# ---------------------------------------------------------------- 
    # Simulated Sample Classes
 # ---------------------------------------------------------------- 
 
 
 
 
class SimulatedSingleSample:
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
        
        # Add metrics dictionary
        self.metrics = {
            'id': sample_id,
            'dir': f"single_{sample_id}",
            'total_chromosomes': 0,
            'total_cnvs': 0,
            'data_points': 0,
            'total_roh': 0
        }

    def load_data(self, samples_dir: str):
        """Load all CSV files for this sample from the samples directory"""
        sample_dir = samples_dir
        
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

        # Update metrics after loading data
        self._update_metrics()

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

    def _update_metrics(self):
        """Update metrics with current data state"""
        self.metrics.update({
            'total_chromosomes': len(self.available_chromosomes) if self.available_chromosomes else 0,
            'total_cnvs': self.total_cnvs,
            'data_points': len(self.baf_lrr_data) if self.baf_lrr_data is not None else 0,
            'total_roh': len(self.roh_bed) if self.roh_bed is not None else 0
        })
    
    
    
    
    
    
# ────────────────────────────────────────────────────────────────────────────────
# NEW CLASSES – directory‑aware loaders
# ────────────────────────────────────────────────────────────────────────────────
class SimulatedPairedPreSample(SimulatedSingleSample):
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
        
    def load_data(self, samples_dir: str) -> None:
        sample_dir = samples_dir
        
        # Modified patterns to use full pair_id from directory name
        patterns = {
            "baf_lrr_data": f"pre_baf_lrr_data_*.csv",
            "cn_probabilities_data": f"pre_cn_probabilities_data_*.csv",
            "cn_summary_data": f"pre_cn_summary_data_*.csv",
            "union_bed": f"pre_union_bed_*.csv",
            "roh_bed": f"pre_roh_bed_*.csv",
            "cn_bed": f"pre_cn_bed_*.csv"
        }

        for attr, pattern in patterns.items():
            matches = glob.glob(os.path.join(sample_dir, pattern))
            if matches:
                try:  # Take first match and verify pair_id consistency
                    valid = [m for m in matches if self.pre_sample in os.path.basename(m)]
                    if valid:
                        setattr(self, attr, pd.read_csv(valid[0], dtype={"Chromosome": str}))
                except Exception as e:
                    logging.error("Error loading %s: %s", matches[0], e)

        # total CNVs from summary
        if self.cn_summary_data is not None:
            self.total_cnvs = len(self.cn_summary_data)

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


class SimulatedPairedPostSample(SimulatedSingleSample):
    """SingleSample acting as *post* – loads `post_*` and the *_single BEDs."""

    def __init__(self, sample_id, post_sample, **kwargs):
        super().__init__(
            sample_id=sample_id,
            sample_type='post',
            pre_sample=post_sample,  # Store in pre_sample for base class compatibility
            pre_sex=kwargs.get('pre_sex', 'Unknown'),
            call_rate=kwargs.get('call_rate', 0),
            call_rate_filt=kwargs.get('call_rate_filt', 0),
            LRR_stdev=kwargs.get('LRR_stdev', 0),
            parameters=kwargs.get('parameters', None)
        )
        # Add explicit post_sample reference
        self.post_sample = post_sample  
        self.available_chromosomes = []
        
    def load_data(self, samples_dir: str) -> None:
        sample_dir = samples_dir
        
        patterns = {
            "baf_lrr_data": f"post_baf_lrr_data_*.csv",
            "cn_probabilities_data": f"post_cn_probabilities_data_*.csv",
            "cn_summary_data": f"post_cn_summary_data_*.csv",
            "union_bed": f"post_union_bed_*.csv",
            "roh_bed": f"post_roh_bed_*.csv",
            "cn_bed": f"post_cn_bed_*.csv"
        }

        for attr, pattern in patterns.items():
            matches = glob.glob(os.path.join(sample_dir, pattern))
            if matches:
                try:
                    # Use the stored post_sample reference
                    valid = [m for m in matches if self.post_sample in os.path.basename(m)]
                    if valid:
                        setattr(self, attr, pd.read_csv(valid[0], dtype={"Chromosome": str}))
                except Exception as e:
                    logging.error("Error loading %s: %s", matches[0], e)

        if self.cn_summary_data is not None:
            self.total_cnvs = len(self.cn_summary_data)

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

class SimulatedPairedClass:
    """
    Combines a PreSample and a PostSample.

    Directory name  : PRE_<pre>_POST_<post>
    Pair‑level files : combined_*  inside that directory
    """

    def __init__(
        self,
        pre: "SimulatedPairedPreSample",
        post: "SimulatedPairedPostSample",
        sample_type: str,
        PI_HAT: float,
        pair_id: str  # Add pair_id parameter
    ):
        self.pre = pre
        self.post = post
        self.sample_type = sample_type
        self.PI_HAT = float(PI_HAT)
        self.pair_id = pair_id  # Use provided pair_id instead of generating

        # pair‑level data
        self.cnv_chromosomes = None
        self.cnv_detection_filtered = None
        self.union_bed = None
        self.roh_bed = None
        self.cn_bed = None
        self.total_cnvs = 0
        self.available_chromosomes = post.available_chromosomes 
        
        # Add combined metrics
        self.combined_metrics = {
            'pair_id': self.pair_id,
            'dir': f"paired_{pre.pre_sample}_{post.pre_sample}",
            'pre': pre.pre_sample,
            'post': post.pre_sample,
            'shared_cnvs': 0,
            'discordant_cnvs': 0,
            'combined_data_points': 0,
            'total_cnvs': 0
        }

    # ---------------------------------------------------------------- loaders
    def load_data(self, samples_dir: str) -> None:

        self.pre.load_data(samples_dir)
        self.post.load_data(samples_dir)

        pair_dir = os.path.join(samples_dir, self.pair_id)
        patt = {
            "cnv_chromosomes":       f"combined_cnv_chromosomes_{self.pair_id}.csv",
            "cnv_detection_filtered":f"combined_cnv_detection_filtered_{self.pair_id}.csv",
            "union_bed":             f"combined_union_bed_{self.pair_id}.csv",
            "roh_bed":               f"combined_roh_bed_{self.pair_id}.csv",
            "cn_bed":                f"combined_cn_bed_{self.pair_id}.csv",
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
        else:
            self.total_cnvs = 0
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

        # Update metrics after loading data
        self._update_combined_metrics()

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

    def _update_combined_metrics(self):
        """Update combined metrics for paired analysis"""
        if self.cnv_detection_filtered is not None:
            shared = len(self.cnv_detection_filtered[
                self.cnv_detection_filtered['Type'] == 'Shared'
            ])
            discordant = len(self.cnv_detection_filtered[
                self.cnv_detection_filtered['Type'] == 'Discordant'
            ])
            
        self.combined_metrics.update({
            'shared_cnvs': shared if self.cnv_detection_filtered is not None else 0,
            'discordant_cnvs': discordant if self.cnv_detection_filtered is not None else 0,
            'combined_data_points': (
                len(self.pre.baf_lrr_data) + len(self.post.baf_lrr_data)
            ) if (self.pre.baf_lrr_data is not None and 
                  self.post.baf_lrr_data is not None) else 0,
            'total_cnvs': self.total_cnvs
        })

    # ---------------------------------------------------------------- repr
    def __str__(self):
        return (
            f"PairedClass({self.pair_id}, PI_HAT={self.PI_HAT:.4f}, "
            f"pre={self.pre.sample_id}, post={self.post.sample_id})"
        )

    __repr__ = __str__
    
    
    
# ────────────────────────────────────────────────────────────────────────────
# helper ─ collect csv paths in one folder
# ────────────────────────────────────────────────────────────────────────────
def _classify_csvs(dir_path: str) -> tuple[list[str], list[str], list[str], list[str]]:
    """
    Return four lists with full paths to *.csv, grouped by filename prefix.
    """
    single, pre, post, combined = [], [], [], []
    for fp in glob.glob(os.path.join(dir_path, "*.csv")):
        name = os.path.basename(fp)
        # Match base prefixes while allowing pair_id suffixes
        if name.startswith("single_"):   
            single.append(fp)
        elif name.startswith("pre_"):     
            pre.append(fp)
        elif name.startswith("post_"):    
            post.append(fp)
        elif name.startswith("combined_"):
            combined.append(fp)
    
    print(f"Classified in {dir_path}:")
    print(f"Single ({len(single)}): {[os.path.basename(p) for p in single]}")
    print(f"Pre ({len(pre)}): {[os.path.basename(p) for p in pre]}")
    print(f"Post ({len(post)}): {[os.path.basename(p) for p in post]}")
    print(f"Combined ({len(combined)}): {[os.path.basename(p) for p in combined]}")
    
    return single, pre, post, combined


# ────────────────────────────────────────────────────────────────────────────
# main loader
# ────────────────────────────────────────────────────────────────────────────
def load_simulated_samples(
    sim_root: str
) -> Tuple[List[SimulatedSingleSample], List[SimulatedPairedClass]]:
    """
    Walk `sim_root` and create fully-populated
      • SimulatedSingleSample  objects for  single_* directories
      • SimulatedPairedClass   objects for  paired_* directories
    Additionally exposes the four filename lists you requested.
    """
    singles: List[SimulatedSingleSample] = []
    pairs:   List[SimulatedPairedClass]  = []

    # These four variables can be imported / returned if you need them outside
    single_object_data_list:            list[str] = []
    paired_pre_object_data_list:        list[str] = []
    paired_post_object_data_list:       list[str] = []
    paired_combined_object_data_list:   list[str] = []

    print(f"Single: {single_object_data_list}")
    print(f"Pre: {paired_pre_object_data_list}")
    print(f"Post: {paired_post_object_data_list}")
    print(f"Combined: {paired_combined_object_data_list}")
    
    

    for entry in os.listdir(sim_root):
        dir_path = os.path.join(sim_root, entry)
        if not os.path.isdir(dir_path):
            continue

        # ────────────── SINGLE ───────────────────────────────────────
        if entry.startswith("single_"):
            sample_id = entry[len("single_"):]          # "Sample_1"
            # collect csvs for *this* folder
            single_csvs, _, _, _ = _classify_csvs(dir_path)
            single_object_data_list.extend(single_csvs)

            # build the object (existing API)
            single = SimulatedSingleSample(
                sample_id      = sample_id,
                sample_type    = "single",
                pre_sample     = sample_id,
                pre_sex        = "NA",
                call_rate      = 0,
                call_rate_filt = 0,
                LRR_stdev      = 0,
                parameters     = {},
            )
            single.load_data(dir_path)
            singles.append(single)
            logging.info("Loaded single simulation: %s  (%d csv)",
                         sample_id, len(single_csvs))

        # ────────────── PAIRED ───────────────────────────────────────
        elif entry.startswith("PRE_") and "_POST_" in entry:
            pair_dir = os.path.join(sim_root, entry)
            
            # Extract full pair ID from directory name
            pair_id = entry  
            try:
                # Parse individual sample names for object creation
                pre_sample = pair_id.split("PRE_")[1].split("_POST_")[0]
                post_sample = pair_id.split("_POST_")[1]
            except IndexError:
                logging.error(f"Invalid paired directory format: {pair_id}")
                continue

            # Classify CSV files first to verify detection
            _, pre_csvs, post_csvs, comb_csvs = _classify_csvs(pair_dir)

            # Create samples with directory-derived IDs but full pair context
            pre = SimulatedPairedPreSample(
                sample_id=f"pre_{pair_id}",
                pre_sample=pair_id  # Store full pair ID for file matching
            )
            
            post = SimulatedPairedPostSample(
                sample_id=f"post_{pair_id}",
                post_sample=pair_id
            )

            # Load data using the actual directory path
            pre.load_data(pair_dir)
            post.load_data(pair_dir)

            # Create pair with explicit pair_id
            pair = SimulatedPairedClass(
                pre=pre,
                post=post,
                sample_type="paired",
                PI_HAT=1.0,
                pair_id=pair_id  # Pass directory name as pair_id
            )
            pairs.append(pair)
            logging.info(f"Loaded paired: {pre_sample} ↔ {post_sample}")
            logging.debug(f"Pre CSVs: {[os.path.basename(p) for p in pre_csvs]}")
            logging.debug(f"Post CSVs: {[os.path.basename(p) for p in post_csvs]}")

        # ignore everything else silently
        else:
            logging.debug("Ignoring directory: %s", entry)

    # If you need the four lists elsewhere just return them too, e.g.
    # return singles, pairs, single_object_data_list, \
    #        paired_pre_object_data_list, paired_post_object_data_list, \
    #        paired_combined_object_data_list
    return singles, pairs