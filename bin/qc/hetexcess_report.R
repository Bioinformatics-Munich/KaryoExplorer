#!/usr/bin/env Rscript

# HetExcess Quality Control Report Generator
# For Digital Karyotyping - Stem Cell Differentiation Studies using Illumina Infinium Arrays
# Digital Karyotyping Pipeline

suppressPackageStartupMessages(library(argparse))

parser <- ArgumentParser(description = "Generate HetExcess QC report for stem cell studies")

parser$add_argument("--snp_table", type = "character", required = TRUE,
                   help = "Path to SNP Table file from GenomeStudio")
parser$add_argument("--het_low_threshold", type = "double", default = -0.9,
                   help = "Lower threshold for HetExcess (default: -0.9)")
parser$add_argument("--het_up_threshold", type = "double", default = 0.9,
                   help = "Upper threshold for HetExcess (default: 0.9)")
parser$add_argument("--output_file", type = "character", default = "HetExcess_Report.txt",
                   help = "Output report file name")
parser$add_argument("--clonal_threshold", type = "double", default = 20.0,
                   help = "Percentage of SNPs with HetExcess > 0.95 to flag as clonal/inbred (default: 20)")

args <- parser$parse_args()

# Read SNP table
cat("Reading SNP Table...\n")
snp_table <- read.table(args$snp_table, header = TRUE, sep = '\t', 
                        stringsAsFactors = FALSE, quote = "", 
                        comment.char = "", check.names = TRUE, 
                        fill = TRUE, fileEncoding = "UTF-8")

# Check if Het Excess column exists
if (!"Het.Excess" %in% colnames(snp_table)) {
  stop("ERROR: 'Het Excess' or 'Het.Excess' column not found in SNP Table")
}

# Get HetExcess values
het_col <- if ("Het.Excess" %in% colnames(snp_table)) "Het.Excess" else "Het Excess"
het_values <- snp_table[[het_col]]

# Remove NA values
het_values_clean <- het_values[!is.na(het_values)]
total_snps <- nrow(snp_table)
valid_snps <- length(het_values_clean)

# Calculate statistics
het_mean <- mean(het_values_clean, na.rm = TRUE)
het_median <- median(het_values_clean, na.rm = TRUE)
het_sd <- sd(het_values_clean, na.rm = TRUE)
het_min <- min(het_values_clean, na.rm = TRUE)
het_max <- max(het_values_clean, na.rm = TRUE)

# Count SNPs outside thresholds (these would be EXCLUDED in QC)
snps_below_threshold <- sum(het_values_clean < args$het_low_threshold, na.rm = TRUE)
snps_above_threshold <- sum(het_values_clean > args$het_up_threshold, na.rm = TRUE)
snps_excluded <- snps_below_threshold + snps_above_threshold
pct_excluded <- (snps_excluded / valid_snps) * 100

# Detect clonal pattern (high proportion of SNPs with HetExcess near 1.0)
very_high_het <- sum(het_values_clean > 0.95, na.rm = TRUE)
pct_very_high <- (very_high_het / valid_snps) * 100

# Determine if samples are clonal/related based on HetExcess pattern
is_clonal <- pct_very_high > args$clonal_threshold

# Get chromosome breakdown for excluded SNPs
extreme_high <- snp_table[which(het_values > args$het_up_threshold), ]
extreme_low <- snp_table[which(het_values < args$het_low_threshold), ]
chr_high <- if(nrow(extreme_high) > 0) table(extreme_high$Chr) else table(character(0))
chr_low <- if(nrow(extreme_low) > 0) table(extreme_low$Chr) else table(character(0))

# Determine status
if (is_clonal) {
  status <- "CLONAL/INBRED SAMPLES DETECTED"
  status_detail <- "GenomeStudio clustering affected - SNPs may be incorrectly excluded"
} else {
  status <- "NO CLONAL PATTERN"
  status_detail <- "Samples appear unrelated - standard HetExcess filtering is appropriate"
}

# Generate report header (common for both cases)
report_lines <- c(
  "================================================================================",
  "           HETEXCESS QC REPORT - DIGITAL KARYOTYPING",
  "================================================================================",
  "",
  sprintf("Generated: %s", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  sprintf("Input: %s", basename(args$snp_table)),
  "",
  "--------------------------------------------------------------------------------",
  "WHAT IS HETEXCESS?",
  "--------------------------------------------------------------------------------",
  "",
  "HetExcess measures deviation from expected heterozygosity across samples.",
  "",
  "  Formula: HetExcess = (Obs_Het - Exp_Het) / Exp_Het",
  "",
  "  Where Obs_Het = observed heterozygote frequency",
  "        Exp_Het = expected frequency = 2 * p * q (p, q = allele frequencies)",
  "",
  "  Range: -1 (no heterozygotes) to +1 (all heterozygotes)",
  ""
)

# Different report structure based on clonal status
if (is_clonal) {
  # CLONAL CASE: Detailed report with explanation and statistical evidence
  report_lines <- c(report_lines,
    "--------------------------------------------------------------------------------",
    "WHY DOES THIS HAPPEN WITH CLONAL/INBRED SAMPLES?",
    "--------------------------------------------------------------------------------",
    "",
    "When multiple clonal or inbred samples are loaded together on an Illumina",
    "Infinium array and processed in GenomeStudio:",
    "",
    "  1. GenomeStudio expects UNRELATED samples with genotype VARIATION",
    "     It builds 3 clusters (AA, AB, BB) from signal intensity distribution",
    "",
    "  2. Clonal samples share identical genotypes at each SNP position",
    "     -> If parent was AB, ALL samples cluster at AB (1 cluster, not 3)",
    "     -> GenomeStudio interprets this as a TECHNICAL ARTIFACT",
    "",
    "  3. GenomeStudio assigns extreme HetExcess values:",
    "     -> All samples AB (parent het) -> HetExcess approaches +1.0",
    "     -> All samples AA/BB (parent hom) -> HetExcess approaches -1.0",
    "",
    "  4. Standard QC filters (|HetExcess| > 0.9) EXCLUDE these valid SNPs",
    "",
    "  This is a STUDY DESIGN artifact, not a genotyping quality issue!",
    "",
    "--------------------------------------------------------------------------------",
    "SNP STATISTICS",
    "--------------------------------------------------------------------------------",
    sprintf("Total SNPs:                 %d", total_snps),
    sprintf("Valid HetExcess values:     %d", valid_snps),
    "",
    sprintf("HetExcess Mean:    %+.4f", het_mean),
    sprintf("HetExcess Median:  %+.4f", het_median),
    sprintf("HetExcess Std Dev:  %.4f", het_sd),
    sprintf("HetExcess Range:   %+.4f to %+.4f", het_min, het_max),
    "",
    "--------------------------------------------------------------------------------",
    "STATISTICAL EVIDENCE FOR CLONAL/INBRED SAMPLES",
    "--------------------------------------------------------------------------------",
    "",
    sprintf("SNPs with HetExcess > 0.95:  %d (%.2f%%)", very_high_het, pct_very_high),
    sprintf("Detection threshold:         %.0f%%", args$clonal_threshold),
    "",
    "Evidence interpretation:",
    sprintf("  - %.2f%% of SNPs show near-perfect heterozygosity (HetExcess > 0.95)", pct_very_high),
    "  - In unrelated samples, this would be < 1%",
    sprintf("  - Your value (%.2f%%) is %.1fx higher than expected for unrelated samples", 
            pct_very_high, pct_very_high / 1.0),
    "",
    "  This strongly indicates all samples share a common parental genotype.",
    "  At positions where the parent was heterozygous (AB), ALL samples are AB,",
    "  resulting in HetExcess = (1.0 - 0.5) / 0.5 = 1.0",
    "",
    "--------------------------------------------------------------------------------",
    "SNPs TO BE EXCLUDED BY STANDARD QC",
    "--------------------------------------------------------------------------------",
    sprintf("Thresholds: HetExcess < %.2f or > %.2f", 
            args$het_low_threshold, args$het_up_threshold),
    "",
    sprintf("  High HetExcess (> %.2f):  %6d  (%.2f%%)", 
            args$het_up_threshold, snps_above_threshold, 
            (snps_above_threshold/valid_snps)*100),
    sprintf("  Low HetExcess (< %.2f):   %6d  (%.2f%%)", 
            args$het_low_threshold, snps_below_threshold,
            (snps_below_threshold/valid_snps)*100),
    "",
    sprintf("  TOTAL EXCLUDED: %d / %d (%.2f%%)", snps_excluded, valid_snps, pct_excluded),
    ""
  )
  
  # Add chromosome breakdown if there are excluded SNPs
  if (snps_excluded > 0 && (length(chr_high) > 0 || length(chr_low) > 0)) {
    report_lines <- c(report_lines,
      "--------------------------------------------------------------------------------",
      "EXCLUDED SNPs BY CHROMOSOME",
      "--------------------------------------------------------------------------------"
    )
    
    if (snps_above_threshold > 0 && length(chr_high) > 0) {
      report_lines <- c(report_lines, sprintf("High HetExcess (> %.2f):", args$het_up_threshold))
      for (chr in sort(names(chr_high))) {
        report_lines <- c(report_lines, sprintf("  Chr %-2s: %5d", chr, chr_high[chr]))
      }
      report_lines <- c(report_lines, "")
    }
    
    if (snps_below_threshold > 0 && length(chr_low) > 0) {
      report_lines <- c(report_lines, sprintf("Low HetExcess (< %.2f):", args$het_low_threshold))
      for (chr in sort(names(chr_low))) {
        report_lines <- c(report_lines, sprintf("  Chr %-2s: %5d", chr, chr_low[chr]))
      }
      report_lines <- c(report_lines, "")
    }
  }
  
  report_lines <- c(report_lines,
    "--------------------------------------------------------------------------------",
    "RESULT: CLONAL/INBRED SAMPLES DETECTED",
    "--------------------------------------------------------------------------------",
    "",
    "The HetExcess distribution confirms samples are clonally related.",
    sprintf("%d SNPs (%.2f%%) would be excluded - these are VALID SNPs.", 
            snps_excluded, pct_excluded),
    "",
    "RECOMMENDATIONS:",
    "",
    "  1. DISABLE HetExcess FILTER: Set thresholds outside possible range",
    "     (e.g., het_low_threshold = -1.0, het_up_threshold = 1.0)",
    "",
    "  2. DOCUMENT: If filtering is applied, note that SNPs were excluded",
    "     due to clonal study design, not genotyping quality issues",
    "",
    "For digital karyotyping, losing these SNPs reduces resolution and might affect the CNV algorithm outcomes but",
    "does not affect the validity of the remaining SNPs.",
    ""
  )
  
} else {
  # NON-CLONAL CASE: Brief report with statistics and result only
  report_lines <- c(report_lines,
    "--------------------------------------------------------------------------------",
    "SNP STATISTICS",
    "--------------------------------------------------------------------------------",
    sprintf("Total SNPs:                 %d", total_snps),
    sprintf("Valid HetExcess values:     %d", valid_snps),
    "",
    sprintf("HetExcess Mean:    %+.4f", het_mean),
    sprintf("HetExcess Median:  %+.4f", het_median),
    sprintf("HetExcess Std Dev:  %.4f", het_sd),
    sprintf("HetExcess Range:   %+.4f to %+.4f", het_min, het_max),
    "",
    "--------------------------------------------------------------------------------",
    "SNPs EXCLUDED BY QC THRESHOLDS",
    "--------------------------------------------------------------------------------",
    sprintf("Thresholds: HetExcess < %.2f or > %.2f", 
            args$het_low_threshold, args$het_up_threshold),
    "",
    sprintf("  High HetExcess (> %.2f):  %6d  (%.2f%%)", 
            args$het_up_threshold, snps_above_threshold, 
            (snps_above_threshold/valid_snps)*100),
    sprintf("  Low HetExcess (< %.2f):   %6d  (%.2f%%)", 
            args$het_low_threshold, snps_below_threshold,
            (snps_below_threshold/valid_snps)*100),
    "",
    sprintf("  TOTAL EXCLUDED: %d / %d (%.2f%%)", snps_excluded, valid_snps, pct_excluded),
    "",
    "--------------------------------------------------------------------------------",
    "SAMPLE RELATEDNESS CHECK",
    "--------------------------------------------------------------------------------",
    sprintf("SNPs with HetExcess > 0.95: %d (%.2f%%)", very_high_het, pct_very_high),
    sprintf("Clonal detection threshold: %.0f%%", args$clonal_threshold),
    "",
    "--------------------------------------------------------------------------------",
    "RESULT: NO CLONAL/INBRED PATTERN DETECTED",
    "--------------------------------------------------------------------------------",
    "",
    "Samples appear to be unrelated. Standard HetExcess filtering is appropriate.",
    sprintf("SNPs excluded: %d (%.2f%%)", snps_excluded, pct_excluded),
    ""
  )
}

report_lines <- c(report_lines,
  "================================================================================",
  ""
)

# Write report
writeLines(report_lines, args$output_file)

cat(sprintf("\nReport generated: %s\n", args$output_file))
cat(sprintf("Status: %s\n", status))
cat(sprintf("SNPs excluded by HetExcess QC: %d / %d (%.2f%%)\n", 
            snps_excluded, valid_snps, pct_excluded))
if (is_clonal) {
  cat("Note: Clonal samples detected - high HetExcess is expected.\n")
}

cat("\nHetExcess QC analysis completed.\n")
