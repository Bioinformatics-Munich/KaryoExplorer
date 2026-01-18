#!/usr/bin/env Rscript

# -------------------------------------
# 0. Libraries and Argument Parsing
# -------------------------------------
suppressPackageStartupMessages(library(argparse))
suppressPackageStartupMessages(library(data.table))
suppressPackageStartupMessages(library(ggplot2))
suppressPackageStartupMessages(library(patchwork))

parser <- ArgumentParser(description = "LoH Paired Analysis: PRE vs POST")
# PRE sample arguments
parser$add_argument("--pre_summary", type = "character", required = TRUE,
                    help = "Path to PRE summary.tab file (segmentation data).")
parser$add_argument("--pre_data", type = "character", required = TRUE,
                    help = "Path to PRE dat.tab file (marker-level data).")
parser$add_argument("--pre_cn", type = "character", required = TRUE,
                    help = "Path to PRE cn.tab file (copy number data).")
parser$add_argument("--pre_sample_name", type = "character", required = TRUE,
                    help = "PRE sample name used for labeling outputs.")
# POST sample arguments
parser$add_argument("--post_summary", type = "character", required = TRUE,
                    help = "Path to POST summary.tab file (segmentation data).")
parser$add_argument("--post_data", type = "character", required = TRUE,
                    help = "Path to POST dat.tab file (marker-level data).")
parser$add_argument("--post_cn", type = "character", required = TRUE,
                    help = "Path to POST cn.tab file (copy number data).")
parser$add_argument("--post_sample_name", type = "character", required = TRUE,
                    help = "POST sample name used for labeling outputs.")

parser$add_argument("--sex", type = "character", required = TRUE,
                    help = "Sex of the sample (M/F)")
parser$add_argument("--outdir", type = "character", required = TRUE,
                    help = "Output directory where TSVs and plots will be saved.")
parser$add_argument("--p_cn_threshold", type = "double", default = 0.9,
                    help = "Minimum probability for a confident CNV call (default: 0.9).")
parser$add_argument("--baf_threshold", type = "double", default = 0.2,
                    help = "BAF deviation threshold to call LoH (default: 0.2).")
parser$add_argument("--lrr_min", type = "double", default = -0.4,
                    help = "Minimum LRR for filtering out large deletions (default: -0.4).")
parser$add_argument("--lrr_max", type = "double", default = 0.3,
                    help = "Maximum LRR for filtering out large amplifications (default: 0.3).")
parser$add_argument("--lohc_threshold", type = "double", default = 0.3,
                    help = "LoH confidence threshold (default: 0.3).")
parser$add_argument("--n_sites_min", type = "integer", default = 10,
                    help = "Minimum number of SNPs for a region (default: 10).")

args <- parser$parse_args()

pre_summary_file  <- args$pre_summary
pre_dat_file      <- args$pre_data
pre_cn_file       <- args$pre_cn
sample_pre        <- args$pre_sample_name

post_summary_file <- args$post_summary
post_dat_file     <- args$post_data
post_cn_file      <- args$post_cn
sample_post       <- args$post_sample_name

sex_sample        <- args$sex
outdir            <- args$outdir
P_CN_THRESHOLD    <- args$p_cn_threshold
BAF_THRESHOLD     <- args$baf_threshold
LRR_MIN           <- args$lrr_min
LRR_MAX           <- args$lrr_max
LOH_CONF_THRESHOLD<- args$lohc_threshold
N_SITES_MIN       <- args$n_sites_min

######################################################
# 2. PROCESS PRE SAMPLE (reference)                  #
######################################################

# ----------------------------
# 2.1 Load PRE Summary Data
# ----------------------------
pre_summary <- fread(
  pre_summary_file,
  header = FALSE, 
  skip = "# RG, Regions"
)
setnames(pre_summary, c("RG","Chromosome","Start","End","CN","QS","nSites","nHETs"))
pre_summary[, RG := NULL]
pre_summary[, `:=`(
  Chromosome = as.character(Chromosome),
  Start      = as.integer(Start),
  End        = as.integer(End)
)]

# ----------------------------
# 2.2 Load PRE BAF/LRR Data
# ----------------------------
pre_baf_lrr <- fread(
  pre_dat_file,
  header = TRUE,
  skip = "# [1]Chromosome"
)
setnames(pre_baf_lrr, c("Chromosome","Position","BAF","LRR"))

pre_baf_lrr[, CN := 2]

# Compute BAF deviation
pre_baf_lrr[, BAF_deviation := abs(BAF - 0.5)]

# Classify LoH
pre_baf_lrr[, LoH_Type := "No LoH"]
pre_baf_lrr[CN == 2 & BAF_deviation > BAF_THRESHOLD, LoH_Type := "Copy-neutral LoH"]
pre_baf_lrr[CN == 1 & BAF_deviation > BAF_THRESHOLD, LoH_Type := "Deletion-associated LoH"]

# ----------------------------
# 2.3 Process Segments (PRE)
# ----------------------------
pre_lines_raw  <- readLines(pre_summary_file)
pre_lines_data <- pre_lines_raw[!grepl("^#", pre_lines_raw)]
pre_seg.bcftools <- fread(text = pre_lines_data, header = FALSE, fill = TRUE)

setnames(pre_seg.bcftools, c("RG","Chr","Start","End","CN","QS","nSites","nHets"))
pre_seg.bcftools[, `:=`(
  Chr    = as.character(Chr),
  Start  = as.integer(Start),
  End    = as.integer(End),
  CN     = as.numeric(CN),
  QS     = as.numeric(QS),
  nSites = as.integer(nSites),
  nHets  = as.integer(nHets)
)]

# Create segments data with a log2-ratio style value
pre_segments_data <- pre_seg.bcftools[, .(
  Chromosome = Chr,
  Start,
  End,
  seg.mean   = fifelse(CN > 0, log2(CN/2), 0)
)]

# ----------------------------
# 2.4 Merge with Summary + LoH Confidence (PRE)
# ----------------------------
pre_summary_merged <- merge(
  pre_summary,
  pre_segments_data,
  by = c("Chromosome","Start","End"),
  all.x = TRUE
)

# Simple LoH confidence metric
pre_summary_merged[, LoH_Confidence := (QS/max(QS, na.rm = TRUE)) + 
                     (nSites/max(nSites, na.rm = TRUE))]

# Identify LOH regions
pre_loh_regions <- pre_summary_merged[
  nHETs == 0 & 
    nSites >= N_SITES_MIN & 
    LoH_Confidence >= LOH_CONF_THRESHOLD
]

# Prepare a copy of the BAF data keyed for overlaps
pre_baf_prepped <- copy(pre_baf_lrr)
pre_baf_prepped[, `:=`(SNP_Start = Position, SNP_End = Position)]


pre_baf_prepped[, Chromosome := as.character(Chromosome)]
setkey(pre_baf_prepped, Chromosome, SNP_Start, SNP_End)

pre_loh_regions[, Chromosome := as.character(Chromosome)]

setkey(pre_loh_regions, Chromosome, Start, End)

# Overlap SNPs onto LOH regions (PRE)
pre_annotated_snps <- foverlaps(
  x       = pre_baf_prepped,
  y       = pre_loh_regions,
  by.x    = c("Chromosome", "SNP_Start", "SNP_End"),
  by.y    = c("Chromosome", "Start", "End"),
  type    = "within",
  nomatch = 0
)

# Summarize region-level data (PRE)
pre_loh_regions_expanded <- pre_annotated_snps[
  , .(
    Chromosome      = first(Chromosome),
    Region_Start    = first(Start),
    Region_End      = first(End),
    Copy_Number     = first(CN),
    nHETs           = first(nHETs),
    nSites          = first(nSites),
    Quality         = first(QS),
    LoH_Confidence  = first(LoH_Confidence),
    Num_SNPs        = .N,
    Num_LoH_SNPs    = sum(LoH_Type != "No LoH"),
    Fraction_LoH_SNPs = mean(LoH_Type != "No LoH"),
    Mean_CN         = mean(CN, na.rm = TRUE),
    Mean_BAF        = mean(BAF, na.rm = TRUE),
    Mean_LRR        = mean(LRR, na.rm = TRUE),
    Mean_BAF_Dev    = mean(BAF_deviation, na.rm = TRUE),
    Region_LoH_Type = {
      loh_subset <- LoH_Type[LoH_Type != "No LoH"]
      if (length(loh_subset) == 0) "No LoH" else names(which.max(table(loh_subset)))
    }
  ),
  by = .(Chromosome, Start, End)
]

message("PRE sample analysis complete: ", sample_pre)


######################################################
# 3. PROCESS POST SAMPLE                              #
######################################################

# ----------------------------
# 3.1 Load POST Summary Data
# ----------------------------
post_summary <- fread(
  post_summary_file,
  header = FALSE,
  skip = "# RG, Regions"
)
setnames(post_summary, c("RG","Chromosome","Start","End","CN","QS","nSites","nHETs"))
post_summary[, RG := NULL]
post_summary[, `:=`(
  Chromosome = as.character(Chromosome),
  Start      = as.integer(Start),
  End        = as.integer(End)
)]

# ----------------------------
# 3.2 Load POST BAF/LRR Data
# ----------------------------
post_baf_lrr <- fread(
  post_dat_file,
  header = TRUE,
  skip = "# [1]Chromosome"
)
setnames(post_baf_lrr, c("Chromosome","Position","BAF","LRR"))

post_baf_lrr[, CN := 2]
post_baf_lrr[, BAF_deviation := abs(BAF - 0.5)]
post_baf_lrr[, LoH_Type := "No LoH"]
post_baf_lrr[CN == 2 & BAF_deviation > BAF_THRESHOLD, LoH_Type := "Copy-neutral LoH"]
post_baf_lrr[CN == 1 & BAF_deviation > BAF_THRESHOLD, LoH_Type := "Deletion-associated LoH"]

# ----------------------------
# 3.3 Process Segments (POST)
# ----------------------------
post_lines_raw  <- readLines(post_summary_file)
post_lines_data <- post_lines_raw[!grepl("^#", post_lines_raw)]
post_seg.bcftools <- fread(text = post_lines_data, header = FALSE, fill = TRUE)

setnames(post_seg.bcftools, c("RG","Chr","Start","End","CN","QS","nSites","nHets"))
post_seg.bcftools[, `:=`(
  Chr    = as.character(Chr),
  Start  = as.integer(Start),
  End    = as.integer(End),
  CN     = as.numeric(CN),
  QS     = as.numeric(QS),
  nSites = as.integer(nSites),
  nHets  = as.integer(nHets)
)]

post_segments_data <- post_seg.bcftools[, .(
  Chromosome = Chr,
  Start,
  End,
  seg.mean   = fifelse(CN > 0, log2(CN/2), 0)
)]

# ----------------------------
# 3.4 Merge with Summary + LoH Confidence (POST)
# ----------------------------
post_summary_merged <- merge(
  post_summary,
  post_segments_data,
  by = c("Chromosome","Start","End"),
  all.x = TRUE
)

post_summary_merged[, LoH_Confidence := (QS/max(QS, na.rm = TRUE)) + 
                      (nSites/max(nSites, na.rm = TRUE))]


# For reference, we do identify POST sample’s own LOH

post_loh_regions <- post_summary_merged[
  nHETs == 0 & 
    nSites >= N_SITES_MIN & 
    LoH_Confidence >= LOH_CONF_THRESHOLD
]


post_baf_prepped <- copy(post_baf_lrr)
post_baf_prepped[, `:=`(SNP_Start = Position, SNP_End = Position)]


post_baf_prepped[, Chromosome := as.character(Chromosome)]
setkey(post_baf_prepped, Chromosome, SNP_Start, SNP_End)

post_loh_regions[, Chromosome := as.character(Chromosome)]

setkey(post_loh_regions, Chromosome, Start, End)

post_annotated_snps <- foverlaps(
  x = post_baf_prepped,
  y = post_loh_regions,
  by.x = c("Chromosome", "SNP_Start", "SNP_End"),
  by.y = c("Chromosome", "Start", "End"),
  type = "within",
  nomatch = 0
)

post_loh_regions_expanded <- post_annotated_snps[
  , .(
    Chromosome      = first(Chromosome),
    Region_Start    = first(Start),
    Region_End      = first(End),
    Copy_Number     = first(CN),
    nHETs           = first(nHETs),
    nSites          = first(nSites),
    Quality         = first(QS),
    LoH_Confidence  = first(LoH_Confidence),
    Num_SNPs        = .N,
    LoH_Type = {
      loh_subset <- LoH_Type[LoH_Type != "No LoH"]
      if (length(loh_subset) == 0) "No LoH" else names(which.max(table(loh_subset)))
    }
  ),
  by = .(Chromosome, Start, End)
]

message("POST sample analysis complete: ", sample_post)


######################################################
# 4. MERGE PRE & POST AT THE SNP LEVEL (Define changes)
######################################################

# 4.1 Minimal columns
pre_snp_min <- pre_annotated_snps[, .(
  Chromosome,
  Position,
  LoH_Type_PRE = LoH_Type
)]
post_snp_min <- post_annotated_snps[, .(
  Chromosome,
  Position,
  LoH_Type_POST = LoH_Type
)]

# 4.2 Merge
paired_snps <- merge(
  pre_snp_min,
  post_snp_min,
  by = c("Chromosome","Position"),
  all = TRUE
)

# If a SNP was not in a LOH region in one sample, label as “No LoH” 
paired_snps[is.na(LoH_Type_PRE),  LoH_Type_PRE  := "No LoH"]
paired_snps[is.na(LoH_Type_POST), LoH_Type_POST := "No LoH"]

# 4.3 Mark “new” or “resolved” LOH changes
paired_snps[, LoH_Change := "No change"]
paired_snps[LoH_Type_PRE == "No LoH" & LoH_Type_POST != "No LoH", LoH_Change := "New LOH"]
paired_snps[LoH_Type_PRE != "No LoH" & LoH_Type_POST == "No LoH", LoH_Change := "Resolved LOH"]
paired_snps[
  LoH_Type_PRE  != "No LoH" &
    LoH_Type_POST != "No LoH",
  LoH_Change := "Persistent LOH"
]

message("Paired SNP-level comparison done.")


######################################################
# 5. OVERLAY “PRE” LOH REGIONS ON POST SNPs 
#    (Reference-based region calls)
######################################################
# We define the region boundaries from PRE (the reference).
# Then see how the POST sample’s SNPs fall within them, 
# marking new/resolved/persistent LOH at the region level.

# 5.1 Key the PRE-based LOH regions
setkey(pre_loh_regions, Chromosome, Start, End)

# 5.2 For the POST SNPs, do foverlaps with PRE reference 
post_baf_prepped_refBased <- foverlaps(
  x    = post_baf_prepped,     # POST SNPs
  y    = pre_loh_regions,      # PRE-based LOH region boundaries
  by.x = c("Chromosome","SNP_Start","SNP_End"),
  by.y = c("Chromosome","Start","End"),
  type = "within",
  nomatch = 0  # only keep SNPs inside the PRE-based LOH regions
)

# Now each POST SNP inside a PRE LOH region can be “No LoH” or not in the POST sample
post_baf_prepped_refBased[, LoH_Change_Region := "Persistent or Resolved?"]
post_baf_prepped_refBased[
  LoH_Type == "No LoH",
  LoH_Change_Region := "Resolved LOH in POST"
]

message("POST sample annotated according to PRE-based region boundaries.")


######################################################
# 6. MERGE PRE & POST REGION-LEVEL LOH (Optional)
######################################################
# Define new column names including sample IDs
pre_colname  <- paste0("Region_LoH_Type_PRE_", sample_pre)
post_colname <- paste0("Region_LoH_Type_POST_", sample_post)


pre_regions_min <- pre_loh_regions_expanded[, .(
  Chromosome,
  Region_Start,
  Region_End,
  Region_LoH_Type = Region_LoH_Type
)]
setnames(pre_regions_min, "Region_LoH_Type", pre_colname)

post_regions_min <- post_loh_regions_expanded[, .(
  Chromosome,
  Region_Start,
  Region_End,
  LoH_Type
)]
setnames(post_regions_min, "LoH_Type", post_colname)

# Merge the pre and post region calls by Chromosome, Region_Start, and Region_End
paired_loh_regions <- merge(
  pre_regions_min,
  post_regions_min,
  by = c("Chromosome", "Region_Start", "Region_End"),
  all = TRUE
)


paired_loh_regions[is.na(get(pre_colname)), (pre_colname) := "No LOH"]
paired_loh_regions[is.na(get(post_colname)), (post_colname) := "No LOH"]

paired_loh_regions[, Region_Change := "No change"]
paired_loh_regions[
  get(pre_colname) == "No LOH" & get(post_colname) != "No LOH",
  Region_Change := "New LOH region"
]
paired_loh_regions[
  get(pre_colname) != "No LOH" & get(post_colname) == "No LOH",
  Region_Change := "Resolved LOH region"
]
paired_loh_regions[
  get(pre_colname) != "No LOH" & get(post_colname) != "No LOH",
  Region_Change := "Persistent LOH region"
]

message("Paired region-level comparison done.")


######################################################
# 7. PREPARE “ANNOTATED_SNPS” FOR FINAL EXPANSION
######################################################


annotated_snps <- post_baf_prepped_refBased[
  ,
  .(
    Chromosome,
    Start,
    End,
    Position,
    BAF,
    LRR,
    CN,
    BAF_deviation,
    LoH_Type,         # from POST
    nHETs,
    nSites,
    Quality = QS,
    LoH_Confidence
  )
]

# If a SNP is not in any PRE region, it’s excluded. If you want all SNPs, set nomatch=NA


######################################################
# 8. CREATE AN EXPANDED REGION TABLE (#9 EQUIVALENT)
######################################################
loh_regions_expanded <- annotated_snps[
  ,
  .(
    Chromosome     = first(Chromosome),
    Region_Start   = first(Start),
    Region_End     = first(End),
    PRE_Sample = sample_pre,
    POST_Sample = sample_post,
    Copy_Number    = first(CN),
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
# 9. WRITE OUTPUT FILES (#10 EQUIVALENT)
######################################################
results_dir <- file.path(outdir, "LoH_results")
plots_dir   <- file.path(outdir, "LoH_plots")
dir.create(results_dir, showWarnings = FALSE, recursive = TRUE)
dir.create(plots_dir,   showWarnings = FALSE, recursive = TRUE)

paired_label <- paste0("PRE_",sample_pre, "_vs_", "POST_", sample_post)


fwrite(
  paired_snps, 
  file.path(results_dir, paste0("SNP_Level_LoH_Comparison_", paired_label, ".tsv")),
  sep = "\t",
  quote = FALSE
)
fwrite(
  loh_regions_expanded,
  file.path(results_dir, paste0("Region_Level_LoH_RefBased_", paired_label, ".tsv")),
  sep = "\t",
  quote = FALSE
)
fwrite(
  paired_loh_regions,
  file.path(results_dir, paste0("Region_Level_LoH_Comparison_", paired_label, ".tsv")),
  sep = "\t",
  quote = FALSE
)
fwrite(
  annotated_snps,
  file.path(results_dir, paste0("Annotated_SNPs_in_PRE_",sample_pre,"_based_Regions_on_POST_", sample_post, ".tsv")),
  sep = "\t",
  quote = FALSE
)

message("Results saved to: ", results_dir)


######################################################
# 10. VISUALIZATIONS
######################################################

plot_loh_bcftools_style <- function(filtered_data, loh_regions, sample_post, sample_pre, chromosome) {
  data_chr <- filtered_data[Chromosome == chromosome]
  loh_chr  <- loh_regions[Chromosome == chromosome]
  
  # Subset to only the columns needed for plotting to avoid duplicate column names
  loh_chr_plot <- unique(loh_chr[, .(Region_Start, Region_End)])
  
  # BAF plot with LOH overlay
  p_baf <- ggplot(data_chr, aes(x = Position, y = BAF)) +
    geom_point(alpha = 0.5, color = "blue") +
    geom_rect(
      data = loh_chr_plot,
      aes(xmin = Region_Start, xmax = Region_End, ymin = 0, ymax = 1),
      fill = "red", alpha = 0.3, inherit.aes = FALSE
    ) +
    labs(
      title = paste("POST_", sample_post, " BAF with PRE_", sample_pre, " LOH Regions - Chr", chromosome),
      x = "Position", y = "BAF"
    ) +
    theme_minimal()
  
  # LRR plot with LOH overlay
  p_lrr <- ggplot(data_chr, aes(x = Position, y = LRR)) +
    geom_point(alpha = 0.5, color = "green") +
    geom_rect(
      data = loh_chr_plot,
      aes(xmin = Region_Start, xmax = Region_End, ymin = -1, ymax = 1),
      fill = "red", alpha = 0.3, inherit.aes = FALSE
    ) +
    labs(
      title = paste("POST_", sample_post, " LRR with PRE_", sample_pre, " LOH Regions - Chr", chromosome),
      x = "Position", y = "LRR"
    ) +
    theme_minimal()
  
  p_baf / p_lrr
}

# Generate chromosome-specific LOH overlay plots for the POST sample,
# showing the POST data with PRE-based LOH regions.
unique_chromosomes <- sort(unique(post_baf_lrr$Chromosome))
for (chr in unique_chromosomes) {
  loh_plot <- plot_loh_bcftools_style(
    filtered_data = post_baf_lrr,      # POST sample SNP-level data
    loh_regions   = loh_regions_expanded, 
    sample_post   = sample_post,
    sample_pre    = sample_pre,
    chromosome    = chr
  )
  
  png_file <- file.path(plots_dir, paste0("POST_", sample_post, "_LOH_Comparsion_REF_PRE_",sample_pre,"_Chr", chr, ".png"))
  ggsave(png_file, loh_plot, width = 10, height = 6, device = "png")
}

message("LoH analysis (paired) complete for: PRE_", sample_pre, " vs. POST_", sample_post)
