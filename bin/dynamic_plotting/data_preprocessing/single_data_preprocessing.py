#!/usr/bin/env python3
import sys
import logging
import pandas as pd
from pathlib import Path
import argparse

class DataParser:
    def __init__(self):
        self.parser = argparse.ArgumentParser(description='Dynamic Plotting Data Preprocessor')
        self._add_arguments()
        
    def _add_arguments(self):
        self.parser.add_argument('--sex', type=str, required=True)
        self.parser.add_argument('--pre', type=str, required=True)
        self.parser.add_argument('--post', type=str)
        self.parser.add_argument('--summary_tab', type=Path, required=True)
        self.parser.add_argument('--dat_tab', type=Path, required=True)
        self.parser.add_argument('--cn_tab', type=Path, required=True)
        self.parser.add_argument('--cnv_detection', type=Path, required=True)
        self.parser.add_argument('--cnv_table', type=Path, required=True)
        self.parser.add_argument('--union_bed', type=Path, required=True)
        self.parser.add_argument('--roh_bed', type=Path, required=True)
        self.parser.add_argument('--cn_bed', type=Path, required=True)
        self.parser.add_argument('--sample_types', type=Path, required=True)
        self.parser.add_argument('--output_dir', type=Path, required=True)
        
    def parse_args(self):
        args = self.parser.parse_args()
        args.output_dir.mkdir(parents=True, exist_ok=True)
        return args

class DataLoader:
    def __init__(self, args):
        self.args = args
        self.sex = self._get_sample_sex()
        self.logger = logging.getLogger(__name__)
        
    def _get_sample_sex(self):
        """Extract sex from sample_types.csv"""
        sample_df = pd.read_csv(self.args.sample_types)
        sample_row = sample_df[sample_df['pre_sample'] == self.args.pre]
        if sample_row.empty:
            raise ValueError(f"Sample {self.args.pre} not found in sample_types.csv")
        return sample_row['pre_sex'].values[0]
    
    def _map_chromosome(self, chr_value):
        """Convert chromosome numbers to X/Y based on standard numbering"""
        try:
            chr_num = int(chr_value)
            if chr_num == 23:
                return 'X'
            elif chr_num == 24:
                return 'Y'
            return str(chr_num)
        except ValueError:
            return str(chr_value)
    
    def _load_table(self, path, columns, chr_cols):
        """Generic table loader with chromosome mapping"""
        self.logger.info(f"Loading {path.name}")
        df = pd.read_csv(path, sep='\t', comment='#')
        
        # Normalize existing column names
        df.columns = df.columns.str.replace('chr', 'Chromosome', case=False)
        
        # Handle column names
        if len(df.columns) == len(columns):
            df.columns = columns
        else:
            self.logger.warning(f"Column count mismatch in {path.name}. Using header: {df.columns.tolist()}")
        
        # Process chromosome columns
        for col in chr_cols:
            if col in df.columns:
                df[col] = df[col].apply(self._map_chromosome)
            else:
                self.logger.warning(f"Chromosome column {col} not found in {path.name}")
        
        return df

    def load_summary(self):
        return self._load_table(
            self.args.summary_tab,
            columns=['Region', 'Chromosome', 'Start', 'End', 'CopyNumber', 'Quality', 'nSites', 'nHETs'],
            chr_cols=['Chromosome']
        )
    
    def load_dat(self):
        return self._load_table(
            self.args.dat_tab,
            columns=['Chromosome', 'Position', 'BAF', 'LRR'],
            chr_cols=['Chromosome']
        )
    
    def load_cn(self):
        return self._load_table(
            self.args.cn_tab,
            columns=['Chromosome', 'Position', 'CN', 'P_CN0', 'P_CN1', 'P_CN2', 'P_CN3'],
            chr_cols=['Chromosome']
        )
    
    def load_cnv_detection(self):
        return self._load_table(
            self.args.cnv_detection,
            columns=['Chromosome', 'Start', 'End', 'CN', 'QS', 'nSites', 'nHets', 'Length', 'Type', 'Sample'],
            chr_cols=['Chromosome']
        )
    
    def load_cnv_table(self):
        return self._load_table(
            self.args.cnv_table,
            columns=['Sample', 'Chromosome', 'CN_200kb', 'CN_1Mb', 'CN_Type', 'CNVs'],
            chr_cols=['Chromosome']
        )
    
    def load_bed(self, path):
        """Load BED file with chromosome mapping"""
        import os
        # Handle empty BED files gracefully
        if os.path.getsize(path) == 0:
            return pd.DataFrame(columns=['Chromosome', 'Start', 'End', 'Length'])
        
        df = pd.read_csv(path, sep='\t', header=None)
        df.columns = ['Chromosome', 'Start', 'End', 'Length'][:len(df.columns)]
        df['Chromosome'] = df['Chromosome'].apply(self._map_chromosome)
        return df
    
    def _log_file_head(self, path, num_lines=8):
        """Read and return first N lines of a file"""
        try:
            with open(path, 'r') as f:
                return [next(f).strip() for _ in range(num_lines)]
        except:
            return ["File not found or has fewer lines than requested"]

    def load_all(self):
        """Load and process all data files with logging"""
        log_content = []
        
        # Log raw file headers
        log_content.append("=== RAW FILE HEADERS ===")
        files = [
            ('Summary', self.args.summary_tab),
            ('Dat', self.args.dat_tab),
            ('CN', self.args.cn_tab),
            ('CNV Detection', self.args.cnv_detection),
            ('CNV Table', self.args.cnv_table),
            ('Union BED', self.args.union_bed),
            ('ROH BED', self.args.roh_bed),
            ('CN BED', self.args.cn_bed)
        ]
        
        for name, path in files:
            log_content.append(f"\n{name} File: {path.name}")
            log_content.extend(self._log_file_head(path))
        
        # Process data
        processed_data = {
            'single_cn_summary_data': self.load_summary(),
            'single_baf_lrr_data': self.load_dat(),
            'single_cn_probabilities_data': self.load_cn(),
            'single_cnv_detection_filtered': self.load_cnv_detection(),
            'single_cnv_chromosomes': self.load_cnv_table(),
            'single_union_bed': self.load_bed(self.args.union_bed),
            'single_roh_bed': self.load_bed(self.args.roh_bed),
            'single_cn_bed': self.load_bed(self.args.cn_bed)
        }
        
        # Log processed data samples
        log_content.append("\n\n=== PROCESSED DATA SAMPLES ===")
        for name, df in processed_data.items():
            log_content.append(f"\n{name.capitalize()} Data (first 5 rows):")
            log_content.append(df.head(5).to_string(index=False))
        
        # Write log file
        log_path = self.args.output_dir / "single_preprocess_log.txt"
        with open(log_path, 'w') as f:
            f.write("\n".join(log_content))
        
        return processed_data

def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    try:
        parser = DataParser()
        args = parser.parse_args()
        loader = DataLoader(args)
        processed_data = loader.load_all()
        
        # Save processed CSVs WITH HEADERS
        for name, df in processed_data.items():
            output_path = args.output_dir / f"{name}_{args.pre}.csv"
            df.to_csv(
                output_path, 
                index=False, 
                header=True,
                float_format='%.6f'
            )
            logging.info(f"Saved {output_path}")
            
        logging.info("Processing completed successfully")
        
    except Exception as e:
        logging.error(f"Processing failed: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()