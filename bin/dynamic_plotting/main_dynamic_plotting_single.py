#!/usr/bin/env python3
import argparse
import logging
import os
import sys
from pathlib import Path
import pandas as pd
import shutil
from src.utils.sample_class import SingleSample, Parameters
from src.utils.simulated_sample_class import (
    SimulatedSingleSample,
    SimulatedPairedPreSample,
    SimulatedPairedPostSample,
    SimulatedPairedClass,
    _classify_csvs,
    load_simulated_samples
)
from src.utils.output_manager import OutputManager
from src.utils.styling import StylingManager
from src.pages.home_page_single import HomePageGenerator
from src.pages.info_page import InfoPageGenerator
from src.pages.sample_summary_page_single import SampleSummaryGeneratorSingle
from src.pages.sample_chromosome_single import ChromosomePageGeneratorSingle

def setup_logging(log_file):
    """Set up logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

def create_sample_objects(sample_types_file, parameters_obj):
    """Create SingleSample objects from the sample types CSV file"""
    samples = []
    try:
        df = pd.read_csv(sample_types_file)
        for _, row in df.iterrows():
            sample = SingleSample(
                sample_id=row['sample_id'],
                sample_type=row['type'],
                pre_sample=row['pre_sample'],
                pre_sex=row['pre_sex'],
                call_rate=row['call_rate'],
                call_rate_filt=row['call_rate_filt'],
                LRR_stdev=row['LRR_stdev'],
                parameters=parameters_obj
            )
            samples.append(sample)
        return samples
    except Exception as e:
        logging.error(f"Error reading sample types file: {str(e)}")
        sys.exit(1)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate dynamic plots for single CNV analysis")
    p.add_argument("--samples_dir", required=True, help="Directory containing sample data folders")
    p.add_argument("--sample_types", required=True, help="CSV with sample metadata")
    p.add_argument("--log_file", default="dynamic_plotting_single.log", help="Log file name")
    p.add_argument("--logo", required=True, help="Path to logo image")
    p.add_argument("--simulated_data_dir", default='./simulated_data',
                   help='Directory containing simulated data')
    p.add_argument("--output_dir", required=True, help="Output directory for reports")
    p.add_argument("--parameters", required=True, help="Analysis parameters file")
    p.add_argument("--app_name", default="index", help="Name for the main HTML application file (default: index)")
    p.add_argument("--email_helmholtz", default="", help="Helmholtz institution email")
    p.add_argument("--email_analyst", default="", help="Analyst email (optional)")
    p.add_argument("--name_analyst", default="", help="Analyst name (optional)")
    return p.parse_args()

def main() -> None:
    args = parse_args()
    
    # Load parameters first
    parameters = Parameters(args.parameters)
    
    # Set up logging
    setup_logging(args.log_file)
    logging.info("Starting dynamic plotting for single samples")
    
    # Verify inputs exist
    if not os.path.isdir(args.samples_dir):
        logging.error(f"Samples directory not found: {args.samples_dir}")
        sys.exit(1)
        
    if not os.path.isfile(args.sample_types):
        logging.error(f"Sample types file not found: {args.sample_types}")
        sys.exit(1)
        
    if not os.path.isdir(args.logo):
        logging.error(f"Logo directory not found: {args.logo}")
        sys.exit(1)
        
    if not os.path.exists(args.simulated_data_dir):
        sys.exit(f"simulated_data_dir not found → {args.simulated_data_dir}")
    
    # Then create samples with parameters
    real_samples = create_sample_objects(args.sample_types, parameters)
    
    # Initialize output manager with REAL SAMPLES ONLY
    output_manager = OutputManager(args.output_dir, app_name=args.app_name)
    sample_names = [s.pre_sample for s in real_samples]  # Only real samples
    directory_structure = output_manager.create_directory_structure(sample_names, args.logo)
    logging.info("Created output directory structure:\n" + str(directory_structure))
    
    # Initialize styling manager and create styling components
    styling_manager = StylingManager(
        output_manager, 
        app_name=args.app_name,
        email_helmholtz=args.email_helmholtz,
        email_analyst=args.email_analyst,
        name_analyst=args.name_analyst
    )
    styling_manager.create_all_components()
    logging.info("Created styling components")
    
    # Load data for each sample
    for sample in real_samples:
        logging.info(f"Loading data for sample: {sample.pre_sample}")
        sample.load_data(args.samples_dir)
    
    # Generate home page
    try:
        logging.info("Generating home page...")
        home_page_generator = HomePageGenerator(real_samples, output_manager)
        html_content = home_page_generator.generate()
        output_path = os.path.join(args.output_dir, output_manager.get_home_page_name())
        home_page_generator.save(output_path)
        logging.info(f"Successfully generated home page: {output_manager.get_home_page_name()}")
    except Exception as e:
        logging.error(f"Error generating home page: {str(e)}")
        sys.exit(1)
    
    # Create a summary file in the output directory
    summary_file = os.path.join(args.output_dir, "processing_summary.txt")
    with open(summary_file, 'w') as f:
        f.write("Processing Summary\n")
        f.write("================\n\n")
        f.write(f"Total samples processed: {len(real_samples)}\n")
        for sample in real_samples:
            f.write(f"\nSample: {sample.pre_sample}\n")
            f.write(f"Type: {sample.sample_type}\n")
            f.write(f"Sex: {sample.pre_sex}\n")
            f.write(f"Call Rate: {sample.call_rate:.2f}\n")
            f.write(f"Filtered Call Rate: {sample.call_rate_filt:.2f}\n")
            f.write(f"LRR Standard Deviation: {sample.LRR_stdev:.2f}\n")
            f.write(f"Total CNVs: {sample.total_cnvs}\n")
    logging.info("Processing complete")


    single_simulated_objs, paired_simulated_objs = load_simulated_samples(args.simulated_data_dir)

    info_generator = InfoPageGenerator(output_manager, single_simulated_objs, paired_simulated_objs)
    info_generator.save()
    logging.info("Created documentation components with simulated data")

    # Remove simulated samples from any other processing
    # Keep only real samples in these loops:
    for sample in real_samples:
        summary_generator = SampleSummaryGeneratorSingle(sample, output_manager)
        summary_generator.save()
        
        chrom_generator = ChromosomePageGeneratorSingle(sample, output_manager)
        chrom_generator.save_chromosome_pages()

    # After generating all pages
    logging.info("Final directory structure:\n%s", output_manager.dir_structure.detailed_str())

if __name__ == "__main__":
    main()
