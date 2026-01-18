import sys
import logging
import pandas as pd
from pathlib import Path
import argparse


class DataParser:
    """Command‑line argument helper"""

    def __init__(self):
        self.parser = argparse.ArgumentParser(
            description="Dynamic Plotting Data Preprocessor"
        )
        self._add_arguments()

    def _add_arguments(self):
        self.parser.add_argument("--sex", type=str, required=True)
        self.parser.add_argument("--pre", type=str, required=True)
        self.parser.add_argument("--post", type=str, required=True)
        self.parser.add_argument("--summary_tab_pre", type=Path, required=True)
        self.parser.add_argument("--dat_tab_pre", type=Path, required=True)
        self.parser.add_argument("--cn_tab_pre", type=Path, required=True)
        self.parser.add_argument("--summary_tab_post", type=Path, required=True)
        self.parser.add_argument("--dat_tab_post", type=Path, required=True)
        self.parser.add_argument("--cn_tab_post", type=Path, required=True)
        self.parser.add_argument("--cnv_detection_filt", type=Path, required=True)
        self.parser.add_argument("--summary_tab", type=Path, required=True)
        self.parser.add_argument("--union_bed", type=Path, required=True)
        self.parser.add_argument("--roh_bed", type=Path, required=True)
        self.parser.add_argument("--pre_union_bed", type=Path, required=True)
        self.parser.add_argument("--post_union_bed", type=Path, required=True)
        self.parser.add_argument("--pre_roh_bed", type=Path, required=True)
        self.parser.add_argument("--post_roh_bed", type=Path, required=True)
        self.parser.add_argument("--pre_cn_bed", type=Path, required=True)
        self.parser.add_argument("--post_cn_bed", type=Path, required=True)
        self.parser.add_argument("--paired_cn_bed", type=Path, required=True)
        self.parser.add_argument("--sample_types", type=Path, required=True)
        self.parser.add_argument("--output_dir", type=Path, required=True)

    def parse_args(self):
        args = self.parser.parse_args()
        args.output_dir.mkdir(parents=True, exist_ok=True)
        return args


class DataLoader:
    """All heavy lifting lives here"""

    def __init__(self, args):
        self.args = args
        self.sex = self._get_sample_sex()
        self.logger = logging.getLogger(__name__)

    # ---------- helpers ---------- #

    def _get_sample_sex(self):
        df = pd.read_csv(self.args.sample_types)
        row = df[df["pre_sample"] == self.args.pre]
        if row.empty:
            raise ValueError(f"Sample {self.args.pre} not found in sample_types.csv")
        return row["pre_sex"].iat[0]

    def _map_chromosome(self, chr_value):
        """Convert chromosome numbers to X/Y using standard numbering"""
        try:
            num = int(chr_value)
            if num == 23:
                return "X"
            if num == 24:
                return "Y"
            return str(num)
        except ValueError:
            return str(chr_value)

    def _load_table(self, path, columns, chr_cols):
        self.logger.info(f"Loading {path.name}")
        df = pd.read_csv(path, sep="\t", comment="#")

        # make header case‑insensitive and uniform
        df.columns = df.columns.str.replace("chr", "Chromosome", case=False)

        if len(df.columns) == len(columns):
            df.columns = columns
        else:
            self.logger.warning(
                f"Column count mismatch in {path.name}. Using original header."
            )

        for col in chr_cols:
            if col in df.columns:
                df[col] = df[col].apply(self._map_chromosome)
            else:
                self.logger.warning(f"Missing chromosome col {col} in {path.name}")
        return df

    # ---------- CNV helper ---------- #

    def _standardise_cnv_detection_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Rename every weird variant to the long canonical label."""
        out = df.copy()

        # CN columns first (regex)
        out.columns = (
            out.columns.str.replace(r"^CN_post.*", "CN_post", regex=True)
            .str.replace(r"^CN_pre.*", "CN_pre", regex=True)
        )

        # explicit simple renames
        renames = {
            "Chr": "Chromosome",
            "QS": "QualityScore",
            "nSites_post": "PostSites",
            "nHets_post": "PostHets",
            "nSites_pre": "PreSites",
            "nHets_pre": "PreHets",
            "Len": "Length",
            "pre": "PreSample",
            "post": "PostSample",
            "type": "Type",
        }
        out = out.rename(columns=renames, errors="ignore")

        # final column order
        final_columns = [
            "Chromosome",
            "Start",
            "End",
            "CN_post",
            "CN_pre",
            "QualityScore",
            "PostSites",
            "PostHets",
            "PreSites",
            "PreHets",
            "Length",
            "PreSample",
            "PostSample",
            "Type",
        ]

        # move/insert missing cols quietly
        out = out.reindex(columns=final_columns)

        # apply chromosome mapping now that the name is right
        if "Chromosome" in out.columns:
            out["Chromosome"] = out["Chromosome"].apply(self._map_chromosome)

        return out

    # ---------- main ingestion ---------- #

    def load_paired_data(self):
        cnv_detection_df = pd.DataFrame()

        # ---- FIX FOR CNV‑DETECTION HEADERS START ----
        try:
            if self.args.cnv_detection_filt.exists():
                raw = pd.read_csv(self.args.cnv_detection_filt, sep="\t")
                cnv_detection_df = self._standardise_cnv_detection_columns(raw)

                # safe type casting
                num_types = {
                    "CN_post": "float32",
                    "CN_pre": "float32",
                    "Start": "int32",
                    "End": "int32",
                }
                cnv_detection_df = cnv_detection_df.astype(num_types, errors="ignore")
            else:
                self.logger.error(
                    f"CNV detection file not found: {self.args.cnv_detection_filt}"
                )
        except Exception as e:
            self.logger.error(f"Error loading CNV detection data: {e}")
        # ---- FIX FOR CNV‑DETECTION HEADERS END ----

        # ---- combined summary ---- #
        summary_df = pd.read_csv(self.args.summary_tab, sep="\t", comment="#")
        summary_df.columns = [
            "Region",
            "Chromosome",
            "Start",
            "End",
            "CN_post",
            "CN_pre",
            "QS",
            "nSites_post",
            "nHets_post",
            "nSites_pre",
            "nHets_pre",
        ]
        summary_df["Chromosome"] = summary_df["Chromosome"].apply(
            self._map_chromosome
        )
        summary_df["Delta_CN"] = summary_df["CN_post"] - summary_df["CN_pre"]
        summary_df["Length"] = summary_df["End"] - summary_df["Start"]

        # ---- everything else ---- #
        processed_data = {
            # pre
            "pre_summary": self._load_table(
                self.args.summary_tab_pre,
                columns=[
                    "Region",
                    "Chromosome",
                    "Start",
                    "End",
                    "CopyNumber",
                    "Quality",
                    "nSites",
                    "nHETs",
                ],
                chr_cols=["Chromosome"],
            ),
            "pre_dat": self._load_table(
                self.args.dat_tab_pre,
                columns=["Chromosome", "Position", "BAF", "LRR"],
                chr_cols=["Chromosome"],
            ),
            "pre_cn": self._load_table(
                self.args.cn_tab_pre,
                columns=[
                    "Chromosome",
                    "Position",
                    "CN",
                    "P_CN0",
                    "P_CN1",
                    "P_CN2",
                    "P_CN3",
                ],
                chr_cols=["Chromosome"],
            ),
            # post
            "post_summary": self._load_table(
                self.args.summary_tab_post,
                columns=[
                    "Region",
                    "Chromosome",
                    "Start",
                    "End",
                    "CopyNumber",
                    "Quality",
                    "nSites",
                    "nHETs",
                ],
                chr_cols=["Chromosome"],
            ),
            "post_dat": self._load_table(
                self.args.dat_tab_post,
                columns=["Chromosome", "Position", "BAF", "LRR"],
                chr_cols=["Chromosome"],
            ),
            "post_cn": self._load_table(
                self.args.cn_tab_post,
                columns=[
                    "Chromosome",
                    "Position",
                    "CN",
                    "P_CN0",
                    "P_CN1",
                    "P_CN2",
                    "P_CN3",
                ],
                chr_cols=["Chromosome"],
            ),
            # combined / analysis
            "cnv_detection": cnv_detection_df,
            "combined_summary": summary_df,
            "union_bed": self.load_bed(self.args.union_bed),
            "roh_bed": self.load_bed(self.args.roh_bed),
            "pre_union_bed": self.load_bed(self.args.pre_union_bed),
            "pre_roh_bed": self.load_bed(self.args.pre_roh_bed),
            "post_union_bed": self.load_bed(self.args.post_union_bed),
            "post_roh_bed": self.load_bed(self.args.post_roh_bed),
            "pre_cn_bed": self.load_bed(self.args.pre_cn_bed),
            "post_cn_bed": self.load_bed(self.args.post_cn_bed),
            "paired_cn_bed": self.load_bed(self.args.paired_cn_bed),
        }

        # attach sample IDs
        for k in ["pre_summary", "pre_dat", "pre_cn"]:
            processed_data[k]["Sample"] = self.args.pre
        for k in ["post_summary", "post_dat", "post_cn"]:
            processed_data[k]["Sample"] = self.args.post

        return processed_data

    # ---------- utilities ---------- #

    def load_bed(self, path):
        df = pd.read_csv(path, sep="\t", header=None)
        df.columns = ["Chromosome", "Start", "End", "Length"][: len(df.columns)]
        df["Chromosome"] = df["Chromosome"].apply(self._map_chromosome)
        return df

    def _log_file_head(self, path, n=8):
        try:
            with open(path) as fh:
                return [next(fh).rstrip() for _ in range(n)]
        except Exception:
            return ["<missing or too short>"]

    def load_all(self):
        log_lines = ["=== RAW FILE HEADERS ==="]
        files = [
            ("Pre Summary", self.args.summary_tab_pre),
            ("Pre Dat", self.args.dat_tab_pre),
            ("Pre CN", self.args.cn_tab_pre),
            ("Post Summary", self.args.summary_tab_post),
            ("Post Dat", self.args.dat_tab_post),
            ("Post CN", self.args.cn_tab_post),
            ("CNV Detection", self.args.cnv_detection_filt),
            ("Combined Summary", self.args.summary_tab),
            ("Union BED", self.args.union_bed),
            ("ROH BED", self.args.roh_bed),
            ("Pre Union BED", self.args.pre_union_bed),
            ("Pre ROH BED", self.args.pre_roh_bed),
            ("Combined CN BED",  self.args.paired_cn_bed),
            ("Pre CN BED",       self.args.pre_cn_bed),
            ("Post CN BED",      self.args.post_cn_bed),
        ]
        
        
        for name, p in files:
            log_lines.append(f"\n{name} File: {p.name}")
            log_lines.extend(self._log_file_head(p))

        processed = self.load_paired_data()

        log_lines.append("\n\n=== PROCESSED DATA SAMPLES ===")
        log_lines.append("\n=== PRE SAMPLE DATA ===")
        for k in ["pre_summary", "pre_dat", "pre_cn"]:
            log_lines.append(f"\n{k.capitalize()} (first 5):")
            log_lines.append(processed[k].head().to_string(index=False))

        log_lines.append("\n\n=== POST SAMPLE DATA ===")
        for k in ["post_summary", "post_dat", "post_cn"]:
            log_lines.append(f"\n{k.capitalize()} (first 5):")
            log_lines.append(processed[k].head().to_string(index=False))

        log_lines.append("\n\n=== COMBINED & ANALYSIS DATA ===")
        for k in [
            "cnv_detection",
            "combined_summary",
            "union_bed",
            "roh_bed",
            # include the new BED previews here:
            "paired_cn_bed",
            "pre_cn_bed",
            "post_cn_bed",
        ]:
            log_lines.append(f"\n{k.capitalize()} (first 5):")
            log_lines.append(processed[k].head().to_string(index=False))

        log_path = self.args.output_dir / "paired_preprocess_log.txt"
        with open(log_path, "w") as fh:
            fh.write("\n".join(log_lines))

        return processed


def main():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    try:
        args = DataParser().parse_args()
        loader = DataLoader(args)
        data = loader.load_all()

        # map internal key → base filename
        filename_map = {
            "pre_summary": "pre_cn_summary_data",
            "pre_dat": "pre_baf_lrr_data",
            "pre_cn": "pre_cn_probabilities_data",
            "post_summary": "post_cn_summary_data",
            "post_dat": "post_baf_lrr_data",
            "post_cn": "post_cn_probabilities_data",
            "cnv_detection": "combined_cnv_detection_filtered",
            "combined_summary": "combined_cnv_chromosomes",
            "union_bed": "combined_union_bed",
            "roh_bed": "combined_roh_bed",
            "pre_union_bed": "pre_union_bed_single",
            "pre_roh_bed": "pre_roh_bed_single",
            "post_union_bed": "post_union_bed_single",
            "post_roh_bed": "post_roh_bed_single",
            "pre_cn_bed": "pre_cn_bed_single",
            "post_cn_bed": "post_cn_bed_single",
            "paired_cn_bed": "combined_cn_bed",
        }

        for k, df in data.items():
            fname = filename_map.get(k, k)
            out = (
                args.output_dir
                / f"{fname}_PRE_{args.pre}_POST_{args.post}.csv"
            )
            df.to_csv(out, index=False, float_format="%.6f")
            logging.info(f"Saved {out}")

        logging.info("Paired processing completed successfully")

    except Exception as e:
        logging.error("Paired processing failed", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()