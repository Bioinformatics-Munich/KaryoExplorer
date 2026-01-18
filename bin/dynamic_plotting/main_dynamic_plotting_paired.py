import argparse
import logging
import os
import sys
from datetime import datetime
from typing import List, Tuple
from collections import defaultdict
import json

import pandas as pd

from src.utils.sample_class import SingleSample, PreSample, PostSample, PairedClass, Parameters
from src.utils.output_manager import OutputManager
from src.pages.home_page_paired import HomePageGenerator
from src.pages.info_page import InfoPageGenerator
from src.utils.styling import StylingManager
from src.pages.sample_summary_page_paired import SampleSummaryGenerator
from src.pages.sample_chromosome_paired import ChromosomePageGeneratorPaired

from src.utils.simulated_sample_class import (
    SimulatedSingleSample,
    SimulatedPairedPreSample,
    SimulatedPairedPostSample,
    SimulatedPairedClass,
    _classify_csvs,
    load_simulated_samples
)


# ────────────────────────────────────────────────────────────────────────────────
# CLI
# ────────────────────────────────────────────────────────────────────────────────
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate dynamic plots for paired CNV analysis")
    p.add_argument("--samples_dir", required=True, help="Directory containing PRE_*/POST_* folders")
    p.add_argument("--sample_types_single", required=True, help="CSV with single‑sample meta data")
    p.add_argument("--sample_types_paired", required=True, help="CSV with pair definitions")
    p.add_argument("--log_file", default="dynamic_plotting_paired.log", help="Log‑file name")
    p.add_argument("--logo", required=True, help="(kept for downstream plotting)")
    p.add_argument("--simulated_data_dir", default='./simulated_data',
                    help='Directory containing simulated data')
    p.add_argument("--parameters", required=True, help="Analysis parameters file")
    p.add_argument("--output_dir", required=True, help="Folder for output plots / reports")
    p.add_argument("--app_name", default="index", help="Name for the main HTML application file (default: index)")
    p.add_argument("--email_helmholtz", default="", help="Helmholtz institution email")
    p.add_argument("--support_helmholtz", default="", help="Helmholtz support email")
    p.add_argument("--email_analyst", default="", help="Analyst email (optional)")
    p.add_argument("--name_analyst", default="", help="Analyst name (optional)")
    return p.parse_args()


# ────────────────────────────────────────────────────────────────────────────────
# logging
# ────────────────────────────────────────────────────────────────────────────────
def setup_logger(log_file: str) -> None:
    fmt = "%(asctime)s  %(levelname)-8s  %(message)s"
    dtfmt = "%Y-%m-%d %H:%M:%S"
    logging.basicConfig(filename=log_file, filemode="w", level=logging.INFO, format=fmt, datefmt=dtfmt)
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(fmt=fmt, datefmt=dtfmt))
    logging.getLogger().addHandler(console)

# ────────────────────────────────────────────────────────────────────────────────
# object creation
# ────────────────────────────────────────────────────────────────────────────────
def load_sample_objects(
    args: argparse.Namespace,
) -> Tuple[List[PreSample], List[PostSample], List[PairedClass]]:
    logging.info("Reading metadata CSVs …")
    single_df = pd.read_csv(args.sample_types_single)
    paired_df = pd.read_csv(args.sample_types_paired)

    single_lookup = {row["sample_id"]: row for _, row in single_df.iterrows()}

    # Load parameters once at the start
    with open(args.parameters) as f:
        parameters = Parameters(args.parameters)

    pre_cache: dict[str, PreSample] = {}
    post_cache: dict[str, PostSample] = {}
    pair_list: List[PairedClass] = []

    logging.info("Constructing objects …")
    for _, row in paired_df.iterrows():
        pre_id, post_id = row["pre_sample"], row["post_sample"]

        # PreSample ----------------------------------------------------------------
        if pre_id not in pre_cache:
            meta = single_lookup.get(pre_id)
            if meta is None:
                raise ValueError(f"Missing PRE sample '{pre_id}' in single CSV")

            pre_obj = PreSample(
                sample_id=meta["sample_id"],
                sample_type=meta["type"],
                pre_sample=meta["pre_sample"],
                pre_sex=meta["pre_sex"],
                call_rate=meta.get("call_rate"),
                call_rate_filt=meta.get("call_rate_filt"),
                LRR_stdev=meta.get("LRR_stdev"),
                parameters=parameters
            )
            pre_obj.load_data(args.samples_dir)
            pre_cache[pre_id] = pre_obj
            logging.info("Loaded PreSample %s (CNVs=%d)", pre_id, pre_obj.total_cnvs)

        # PostSample ---------------------------------------------------------------
        if post_id not in post_cache:
            meta = single_lookup.get(post_id)
            if meta is None:
                raise ValueError(f"Missing POST sample '{post_id}' in single CSV")

            post_obj = PostSample(
                sample_id=meta["sample_id"],
                sample_type=meta["type"],
                pre_sample=meta["pre_sample"],
                pre_sex=meta["pre_sex"],
                call_rate=meta.get("call_rate"),
                call_rate_filt=meta.get("call_rate_filt"),
                LRR_stdev=meta.get("LRR_stdev"),
                parameters=parameters
            )
            post_obj.load_data(args.samples_dir)
            post_cache[post_id] = post_obj
            logging.info("Loaded PostSample %s (CNVs=%d)", post_id, post_obj.total_cnvs)

        # PairedClass --------------------------------------------------------------
        pair_obj = PairedClass(
            pre=pre_cache[pre_id],
            post=post_cache[post_id],
            sample_type=row["type"],
            PI_HAT=row["PI_HAT"],
        )
        pair_obj.load_data(args.samples_dir)
        pair_list.append(pair_obj)
        logging.info("Created pair %-60s PI_HAT=%0.4f", pair_obj.pair_id, pair_obj.PI_HAT)

    return list(pre_cache.values()), list(post_cache.values()), pair_list


# ────────────────────────────────────────────────────────────────────────────────
# summary writer
# ────────────────────────────────────────────────────────────────────────────────
def write_processing_summary(
    out_path: str,
    pre_samples: List[PreSample],
    post_samples: List[PostSample],
    pairs: List[PairedClass],
    log_file: str,
    samples_dir: str,
) -> None:
    logging.info("Writing summary → %s", out_path)
    with open(out_path, "w") as f:
        f.write("Paired Sample Processing Summary\n")
        f.write("================================\n\n")
        f.write(f"Unique pre‑samples : {len(pre_samples)}\n")
        f.write(f"Unique post‑samples: {len(post_samples)}\n")
        f.write(f"Pairs             : {len(pairs)}\n\n")

        # Pre
        f.write("PRE‑Samples\n-----------\n")
        for s in pre_samples:
            f.write(f"{s.sample_id} | Sex {s.pre_sex} | CallRate {s.call_rate} | CNVs {s.total_cnvs}\n")
        # Post
        f.write("\nPOST‑Samples\n------------\n")
        for s in post_samples:
            f.write(f"{s.sample_id} | Sex {s.pre_sex} | CallRate {s.call_rate} | CNVs {s.total_cnvs}\n")
        # Pairs
        f.write("\nPairs\n-----\n")
        for p in pairs:
            f.write(
                f"{p.pair_id}  PI_HAT={p.PI_HAT:.4f}  "
                f"union_bed={'Yes' if p.union_bed is not None else 'No'} (shape={p.union_bed.shape if p.union_bed is not None else 'N/A'})  "
                f"roh_bed={'Yes' if p.roh_bed is not None else 'No'} (shape={p.roh_bed.shape if p.roh_bed is not None else 'N/A'})  "
                f"cnv_det={'Yes' if p.cnv_detection_filtered is not None else 'No'} "
                f"(cols={len(p.cnv_detection_filtered.columns) if p.cnv_detection_filtered is not None else 0})\n"
            )

        f.write("\nLog file : " + os.path.abspath(log_file) + "\n")
        f.write("Generated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n")
    logging.info("Summary done.")


# ────────────────────────────────────────────────────────────────────────────────
# MAIN
# ────────────────────────────────────────────────────────────────────────────────
def main() -> None:
    args = parse_args()
    
    # Load parameters first
    parameters = Parameters(args.parameters)
    
    if not os.path.exists(args.samples_dir):
        sys.exit(f"samples_dir not found → {args.samples_dir}")
    if not os.path.exists(args.simulated_data_dir):
        sys.exit(f"simulated_data_dir not found → {args.simulated_data_dir}")

    os.makedirs(args.output_dir, exist_ok=True)
    setup_logger(args.log_file)

    logging.info("🟢  CNV paired‑analysis run started")
    pre_samples, post_samples, pairs = load_sample_objects(args)
    logging.info(
        "Loaded %d PRE, %d POST, %d pairs",
        len(pre_samples),
        len(post_samples),
        len(pairs),
    )

    # Create output structure for pairs
    output_manager = OutputManager(args.output_dir, app_name=args.app_name)
    pair_ids = [p.pair_id for p in pairs]
    output_manager.create_paired_structure(pair_ids, args.logo)

    write_processing_summary(
        os.path.join(args.output_dir, "processing_summary_paired.txt"),
        pre_samples,
        post_samples,
        pairs,
        args.log_file,
        args.samples_dir,
    )

    # Initialize styling components
    styling_manager = StylingManager(
        output_manager,
        app_name=args.app_name,
        email_helmholtz=args.email_helmholtz,
        email_analyst=args.email_analyst,
        name_analyst=args.name_analyst
    )
    styling_manager.create_all_components()
    logging.info("Created styling components")
    
    logging.info("Generating home page...")
    home_page_generator = HomePageGenerator(
        pre_samples, 
        post_samples, 
        pairs, 
        output_manager,
        parameters  # Add parameters
    )
    html_path = os.path.join(args.output_dir, output_manager.get_home_page_name())
    home_page_generator.save(html_path)
    logging.info(f"Successfully generated home page: {output_manager.get_home_page_name()}")
    logging.info("Created home page")
        
    single_simulated_objs, paired_simulated_objs = load_simulated_samples(args.simulated_data_dir)
    logging.info("Loaded simulated data")
    info_generator = InfoPageGenerator(output_manager, single_simulated_objs, paired_simulated_objs, 
                                       support_email=args.support_helmholtz)
    info_generator.save()
    logging.info("Created documentation components with simulated data")
    

    logging.info("Generating paired sample summary pages...")
    for pair in pairs:
        summary_generator = SampleSummaryGenerator(pair, output_manager)
        summary_generator.save()
        
        # Add chromosome page generation
        chrom_generator = ChromosomePageGeneratorPaired(pair, output_manager)
        chrom_generator.save_chromosome_pages()

    logging.info("🏁  Run finished successfully")


if __name__ == "__main__":
    main()