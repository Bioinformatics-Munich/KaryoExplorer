#!/usr/bin/env Rscript

# -------------------------------------
# 1. Libraries and Argument Parsing
# -------------------------------------
suppressPackageStartupMessages(library(argparse))
suppressPackageStartupMessages(library(data.table))
suppressPackageStartupMessages(library(ggplot2))
suppressPackageStartupMessages(library(patchwork)) 

parser <- ArgumentParser(description = "LoH Single Sample Analysis (Expanded)")
parser$add_argument("--summary", type = "character", required = TRUE,
                    help = "Path to summary.tab file (segmentation data).")
parser$add_argument("--data", type = "character", required = TRUE,
                    help = "Path to dat.tab file (marker-level data).")
parser$add_argument("--cn", type = "character", required = TRUE,
                    help = "Path to cn.tab file (copy number data).")
parser$add_argument("--sex", type = "character", required = TRUE,
                    help = "Sex of the sample (M/F)")
parser$add_argument("--outdir", type = "character", required = TRUE,
                    help = "Output directory where TSVs and plots will be saved.")
parser$add_argument("--sample_name", type = "character", default = "UnknownSample",
                    help = "Sample name used for labeling outputs.")
parser$add_argument("--p_cn_threshold", type = "double", default = 0.9,
                    help = "Minimum probability for a confident CNV call (default: 0.9).")
parser$add_argument("--baf_threshold", type = "double", default = 0.2,
                    help = "BAF deviation threshold (distance from 0.5) to call LoH (default: 0.2).")
parser$add_argument("--lrr_min", type = "double", default = -0.4,
                    help = "Minimum LRR for filtering out large deletions (default: -0.4).")
parser$add_argument("--lrr_max", type = "double", default = 0.3,
                    help = "Maximum LRR for filtering out large amplifications (default: 0.3).")
parser$add_argument("--lohc_threshold", type = "double", default = 0.3,
                    help = "LoH confidence threshold to filter segments (default: 0.3).")
parser$add_argument("--n_sites_min", type = "integer", default = 10,
                    help = "Minimum number of SNPs for a region to be considered (default: 10).")

args <- parser$parse_args()

# For convenience
summary_file      <- args$summary
dat_file          <- args$data
cn_file           <- args$cn
outdir            <- args$outdir
sample_name       <- args$sample_name
P_CN_THRESHOLD    <- args$p_cn_threshold
BAF_THRESHOLD     <- args$baf_threshold
LRR_MIN           <- args$lrr_min
LRR_MAX           <- args$lrr_max
LOH_CONF_THRESHOLD<- args$lohc_threshold
N_SITES_MIN       <- args$n_sites_min

# Get sex parameter
sex_sample <- args$sex

######################################################
# 2. READ AND CLEAN MAIN SUMMARY DATA
######################################################
# 2A. Read summary_data (which has a normal header)
summary_data <- fread(summary_file, header = TRUE)

# 2B. Remove the column named "# RG, Regions" if it exists
if ("# RG, Regions" %in% colnames(summary_data)) {
  summary_data[, `# RG, Regions` := NULL]
}

# 2C. A helper to strip bracketed text in column names, if present
clean_names <- function(x) gsub(".*\\]", "", x)

# 2D. Rename columns by removing bracket notations (if any)
setnames(summary_data, old = names(summary_data), new = clean_names(names(summary_data)))

# 2E. If there's a column starting with "Copy number:", rename it to "Copy_Number"
cn_col <- grep("^Copy number:", colnames(summary_data), value = TRUE)
if (length(cn_col) == 1) {
  setnames(summary_data, old = cn_col, new = "Copy_Number")
}

# Convert key columns to proper types
summary_data[, Chromosome := as.character(Chromosome)]
summary_data[, Start      := as.integer(Start)]
summary_data[, End        := as.integer(End)]

######################################################
# 3. READ AND CLEAN SNP-LEVEL (BAF/LRR) DATA
######################################################
# If the .dat file has a normal header, keep header=TRUE
baf_lrr_data <- fread(dat_file, header = TRUE)

# Clean columns
setnames(baf_lrr_data, old = names(baf_lrr_data), new = clean_names(names(baf_lrr_data)))

# Ensure columns are correct types
baf_lrr_data[, Chromosome := as.character(Chromosome)]
baf_lrr_data[, Position   := as.integer(Position)]

######################################################
# 4. READ AND CLEAN CNV DATA (CN FILE)
######################################################
cnv_data <- fread(cn_file, header = TRUE)
setnames(cnv_data, old = names(cnv_data), new = clean_names(names(cnv_data)))

cnv_data[, Chromosome := as.character(Chromosome)]
cnv_data[, Position   := as.integer(Position)]

######################################################
# 5. READ BCFTOOLS SEGMENTS FROM summary_file
#    BY FILTERING OUT LINES STARTING WITH '#'
######################################################
lines_raw  <- readLines(summary_file)
lines_data <- lines_raw[ !grepl("^#", lines_raw) ]  # keep only lines NOT starting with '#'

seg.bcftools <- fread(
  text   = lines_data,
  header = FALSE,
  fill   = TRUE  # handle shorter lines if needed
)

# Manually assign column names (8 columns)
setnames(seg.bcftools, c("RG", "Chr", "Start", "End", "CN", "QS", "nSites", "nHets"))

# Convert to numeric/character
seg.bcftools[, Chr    := as.character(Chr)]
seg.bcftools[, Start  := as.integer(Start)]
seg.bcftools[, End    := as.integer(End)]
seg.bcftools[, CN     := as.numeric(CN)]
seg.bcftools[, QS     := as.numeric(QS)]
seg.bcftools[, nSites := as.integer(nSites)]
seg.bcftools[, nHets  := as.integer(nHets)]

# Create segments_data with seg.mean
segments_data <- seg.bcftools[
  ,
  .(
    Chromosome = Chr,
    Start      = Start,
    End        = End,
    seg.mean   = fifelse(CN > 0, log2(CN / 2), 0)
  )
]

# Merge bcftools info into summary_data
summary_data <- merge(
  summary_data,
  segments_data,
  by    = c("Chromosome", "Start", "End"),
  all.x = TRUE
)

######################################################
# 6. SNP-LEVEL LoH CLASSIFICATION
######################################################
# 6A. Compute BAF deviation
baf_lrr_data[, BAF_deviation := abs(BAF - 0.5)]

# 6B. Filter SNPs by LRR range
baf_lrr_data <- baf_lrr_data[LRR >= LRR_MIN & LRR <= LRR_MAX]

# 6C. Assign default CN=2 if no SNP-level CN
baf_lrr_data[, CN := 2]

# 6D. LoH classification
baf_lrr_data[, LoH_Type := "No LoH"]
baf_lrr_data[CN == 2 & BAF_deviation > BAF_THRESHOLD, LoH_Type := "Copy-neutral LoH"]
baf_lrr_data[CN == 1 & BAF_deviation > BAF_THRESHOLD, LoH_Type := "Deletion-associated LoH"]

######################################################
# 7. SEGMENT-LEVEL LoH (SUMMARY DATA)
######################################################
# If 'Quality' is present, compute LoH_Confidence
if ("Quality" %in% colnames(summary_data)) {
  summary_data[, LoH_Confidence := (Quality / max(Quality, na.rm = TRUE)) +
                 (nSites  / max(nSites,  na.rm = TRUE))]
} else {
  summary_data[, LoH_Confidence := 0]
}

# Filter for potential LoH segments
loh_regions <- summary_data[
  nHETs == 0 &
    nSites >= N_SITES_MIN &
    LoH_Confidence >= LOH_CONF_THRESHOLD
]

######################################################
# 8. OVERLAP SNPs WITH LoH REGIONS
######################################################
setkey(loh_regions, Chromosome, Start, End)

baf_lrr_data[, SNP_Start := Position]
baf_lrr_data[, SNP_End   := Position]
setkey(baf_lrr_data, Chromosome, SNP_Start, SNP_End)

annotated_snps <- foverlaps(
  x       = baf_lrr_data,
  y       = loh_regions,
  by.x    = c("Chromosome", "SNP_Start", "SNP_End"),
  by.y    = c("Chromosome", "Start", "End"),
  type    = "within",
  nomatch = 0
)

######################################################
# 9. CREATE AN EXPANDED REGION TABLE
######################################################
loh_regions_expanded <- annotated_snps[
  ,
  .(
    Chromosome     = first(Chromosome),
    Region_Start   = first(Start),
    Region_End     = first(End),
    Copy_Number    = first(Copy_Number),
    nHETs          = first(nHETs),
    nSites         = first(nSites),
    Quality        = first(Quality),
    LoH_Confidence = first(LoH_Confidence),
    
    Num_SNPs          = .N,
    Num_LoH_SNPs      = sum(LoH_Type != "No LoH"),
    Fraction_LoH_SNPs = mean(LoH_Type != "No LoH"),
    Mean_CN           = mean(CN, na.rm = TRUE),
    Mean_BAF          = mean(BAF, na.rm = TRUE),
    Mean_LRR          = mean(LRR, na.rm = TRUE),
    Mean_BAF_Dev      = mean(BAF_deviation, na.rm = TRUE),
    
    Region_LoH_Type = {
      loh_subset <- LoH_Type[LoH_Type != "No LoH"]
      if (length(loh_subset) == 0) {
        "No LoH"
      } else {
        freq_table <- table(loh_subset)
        names(which.max(freq_table))
      }
    }
  ),
  by = .(Chromosome, Start, End)
]

######################################################
# 10. WRITE OUTPUT FILES (UPDATED STRUCTURE)
######################################################
# Create structured output directories
results_dir <- file.path(outdir, "LoH_results")
plots_dir <- file.path(outdir, "LoH_plots")
dir.create(results_dir, showWarnings = FALSE, recursive = TRUE)
dir.create(plots_dir, showWarnings = FALSE, recursive = TRUE)

# Save all relevant data files
fwrite(baf_lrr_data,    file.path(results_dir, paste0("SNP_Level_LoH_Calls_", sample_name, ".tsv")), sep = "\t", quote = FALSE)
fwrite(loh_regions_expanded, file.path(results_dir, paste0("Region_Level_LoH_Calls_Expanded_", sample_name, ".tsv")), sep = "\t", quote = FALSE)
fwrite(loh_regions,     file.path(results_dir, paste0("Region_Level_LoH_Calls_", sample_name, ".tsv")), sep = "\t", quote = FALSE)
fwrite(annotated_snps,  file.path(results_dir, paste0("Annotated_SNPs_in_LoH_Regions_", sample_name, ".tsv")), sep = "\t", quote = FALSE)

######################################################
# 11. VISUALIZATIONS (UPDATED)
######################################################

plot_loh_bcftools_style <- function(filtered_data, loh_regions, sample_name, chromosome) {
  data_chr <- filtered_data[Chromosome == chromosome]
  loh_chr  <- loh_regions[Chromosome == chromosome]
  
  # BAF plot
  p_baf <- ggplot(data_chr, aes(x = Position, y = BAF)) +
    geom_point(alpha = 0.5, color = "blue") +
    geom_rect(
      data = loh_chr,
      aes(xmin = Start, xmax = End, ymin = 0, ymax = 1),
      fill = "red", alpha = 0.3, inherit.aes = FALSE
    ) +
    labs(
      title = paste("BAF with LOH Regions\n", sample_name, "Chr", chromosome),
      x = "Position", y = "BAF"
    ) +
    theme_minimal()
  
  # LRR plot
  p_lrr <- ggplot(data_chr, aes(x = Position, y = LRR)) +
    geom_point(alpha = 0.5, color = "green") +
    geom_rect(
      data = loh_chr,
      aes(xmin = Start, xmax = End, ymin = -1, ymax = 1),
      fill = "red", alpha = 0.3, inherit.aes = FALSE
    ) +
    labs(
      title = paste("LRR with LOH Regions\n", sample_name, "Chr", chromosome),
      x = "Position", y = "LRR"
    ) +
    theme_minimal()
  
  # Stack vertically
  p_baf / p_lrr
}

# Generate chromosome-specific plots
unique_chromosomes <- sort(unique(baf_lrr_data$Chromosome))
for (chr in unique_chromosomes) {
  loh_plot <- plot_loh_bcftools_style(
    filtered_data = baf_lrr_data,
    loh_regions   = loh_regions,
    sample_name   = sample_name,
    chromosome    = chr
  )
  
  png_file <- file.path(plots_dir, paste0("LoH_", sample_name, "_chr", chr, ".png"))
  ggsave(png_file, loh_plot, width = 10, height = 6, device = "png", dpi = 300)
}

message("LoH analysis single sample complete for: ", sample_name)

