# filter out CN of poor quality
# Written by Lucia Trastulla -- email: lucia_trastulla@psych.mpg.de

suppressPackageStartupMessages(library(argparse))
##############################
suppressPackageStartupMessages(library('ggplot2'))
suppressPackageStartupMessages(library('gridExtra'))
suppressPackageStartupMessages(library('grid'))
##############################

parser_plot <- ArgumentParser(description="cnv summary (delitions and duplications) for single analysis")

parser_plot$add_argument("--inputdir", type = "character", help="input folder")
parser_plot$add_argument("--fold_fun", type = "character", help="folder for the input function")
parser_plot$add_argument("--sample_name", type = "character", help="vector of name identifying the sample (patient)")
parser_plot$add_argument("--qs_thr", type = "double", default = 2, help="quality score threshold")
parser_plot$add_argument("--nSites_thr", type = "integer", default = 10,  help="number of sites thersold for CN1")
parser_plot$add_argument("--nHet_thr", type = "integer", default = 10, help="number of sites thersold for CN3")
parser_plot$add_argument("--CN_len_thr", type = "integer", default = 200, help="CN length thr in kb")
parser_plot$add_argument("--sex", type="character", default = "M", help = "sex of the sample (patient)")
parser_plot$add_argument("--width_plot", type="double", default = 10)

parser_plot$add_argument("--outf", type="character", help = "Output file ")

args <- parser_plot$parse_args()

inputdir <- args$inputdir
fold_fun <- args$fold_fun
sample_name <- args$sample_name
qs_thr <- args$qs_thr
nSites_thr <- args$nSites_thr
nHet_thr <- args$nHet_thr
CN_len_thr <- args$CN_len_thr
sex_sample <- args$sex
width_plot <- args$width_plot
heigth_plot <- args$heigth_plot
outFile <- args$outf
parser_plot$add_argument("--heigth_plot", type="double", default = 8)
cnv_table_list <- vector(mode = 'list', length = length(post))
cnv_filt <- vector(mode = 'list', length = length(post))

#### load function
source(paste(fold_fun, 'plot_summary_cnv_function.R', sep = ""))
####

#setwd(sprintf('%s/outdir_%s_%s/',inputdir, sample_name, line))

#cnv_file <- sprintf('summary.%s.tab', line)

M <- 10^6

filter_cnv <- function(file, sex_sample, qs_thr, nSites_thr, nHet_thr, CN_len_thr, table_centr){
  cnv_table <- read.csv(file, header = TRUE, sep = '\t', skip=4, stringsAsFactors = FALSE)
  cnv_table <- cnv_table[,-1]
  colnames(cnv_table) <-  c('Chr', 'Start', 'End', 'CN',  'QS', 'nSites', 'nHets')

  cnv_table$Len <- cnv_table[,3] - cnv_table[,2]

  # Add type column based on copy number
  cnv_table$type <- ifelse(cnv_table$CN == 1, "Deletion", 
                          ifelse(cnv_table$CN == 3, "Duplication", "Normal"))
  
  # Add sample_name column
  cnv_table$sample_name <- sample_name

  # report the id of the rows to delete:
  # quality score
  id_qs <- which(cnv_table$QS < qs_thr)
  # length
  id_len <- which(cnv_table$Len <= CN_len_thr*1000)

  #### Haploipd chr
  if(sex_sample == 'F'){

    id_chrY <- which(cnv_table$Chr == 24)
    chr_lim <- 24
    id_Hap <- id_chrY

  }else{

    chr_lim <- 23
    # number of sites for delition in fibr and ipsc
    id_nH_XY <- which(cnv_table$nHets < nHet_thr & cnv_table[,4] > 1 & cnv_table$Chr >= chr_lim)

    id_Hap <- id_nH_XY
  }

  #### Autosomal chr
  # number of sites for delition in fibr and ipsc
  id_nS <- which(cnv_table$nSites < nSites_thr & cnv_table[,4] == 1 & cnv_table$Chr < chr_lim)
  id_nH <- which(cnv_table$nHets < nHet_thr & cnv_table[,4] == 3 & cnv_table$Chr < chr_lim)

  ### total
  id_tot <- unique(c(id_qs, id_len,id_Hap, id_nS, id_nH))

  cnv_table$Filt <- FALSE
  cnv_table$Filt[sort(id_tot)] <- TRUE

  return(cnv_table)
}


