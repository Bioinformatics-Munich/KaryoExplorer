#!/usr/bin/env Rscript

# Plot quality control for samples
# Written by Lucia Trastulla -- email: lucia_trastulla@psych.mpg.de


suppressPackageStartupMessages(library(argparse))
suppressPackageStartupMessages(library('ggplot2'))
suppressPackageStartupMessages(library('RColorBrewer'))
suppressPackageStartupMessages(library('ggrepel'))

parser <- ArgumentParser(description = "plot sample call rate before and after the quality control step" )

parser$add_argument("--sample_table_file", type = "character", help = ".txt file, sample table from ")
parser$add_argument("--SNP_table_info_file", type = "character", help = ".txt file, SNP info, n of SNPs retained ")
parser$add_argument("--thr_par", type = "double", default = 0.98, help = "threshold parameter for the call rate to exclude the SNPs")
parser$add_argument("--outf", type="character", default = '.', help = "Output file [basename only]")


args <- parser$parse_args()
#############################
sample_table_file <- args$sample_table_file
SNP_table_info_file <- args$SNP_table_info_file
thr_par <- args$thr_par
outFile <- args$outf



sample_table <- read.table(sample_table_file, header = TRUE, sep = '\t', stringsAsFactors = FALSE, quote = "", dec=".")
# SNP_info <- read.table(SNP_table_info_file, header = FALSE, stringsAsFactors = FALSE, quote = "", dec=".")
SNP_info <- read.table(SNP_table_info_file, header = TRUE, stringsAsFactors = FALSE, quote = "", dec=".")
sample_table$gender <- factor(sample_table$gender, levels = c('Female', 'Male', 'Undef'))

SNP_info_title <- paste(sprintf('Excluded SNPs: %i/%i  (%.3f', SNP_info$n_SNPs[20], SNP_info$n_SNPs[1], SNP_info$n_SNPs[21]*100), "%)", sep = "" )

min_cr <- ifelse(min(c(sample_table$call_rate_filt, sample_table$call_rate)) < thr_par, min(c(sample_table$call_rate_filt, sample_table$call_rate)), thr_par)

coul <- c('#dd1c77', '#2c7fb8', '#636363')


plot_sample <- ggplot(data = sample_table, aes(x = call_rate, y = call_rate_filt, color = gender))+
  geom_point(size = 1.5)+
  geom_abline(slope = 1, intercept = 0, linetype = 1, alpha = 0.3)+
  geom_vline(xintercept = thr_par, linetype = 2, color = 'red')+
  geom_hline(yintercept = thr_par, linetype = 2, color = 'red')+
  scale_color_manual(values = coul)+ 
  theme_bw()+
  ggtitle(SNP_info_title)+
  xlim(min_cr,1)+ylim(min_cr,1)+
  ylab("Call rate after QC")+xlab("Call rate")+
  theme(legend.text = element_text(size = 14), legend.title = element_text(size=16),
        axis.text=element_text(size=14),
        axis.title=element_text(size=16,face="bold"),
        strip.text = element_text(size=14), plot.title = element_text(hjust = 0, size = 17)) #+
#  geom_text_repel(data = subset(sample_table, call_rate < thr_par), aes(label = sample_ID), size = 3, fontface = 'bold', 
#                  box.padding = 1, point.padding = 0.9, segment.size =0.6 )

ggsave(filename = file.path(outFile, 'plot_CR_samples.pdf'), plot = plot_sample, width = 8, height = 8)
ggsave(filename = file.path(outFile, 'plot_CR_samples.png'), plot = plot_sample, width = 8, height = 8)
