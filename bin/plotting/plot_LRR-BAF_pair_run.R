#!/usr/bin/env Rscript

# Plot LRR and BAF for a pairwise compasion, add the info on CN
# Code similar to the python automatic code produced by bcftools
# Written by Lucia Trastulla -- email: lucia_trastulla@psych.mpg.de

suppressPackageStartupMessages(library(argparse))
suppressPackageStartupMessages(library('ggplot2'))
suppressPackageStartupMessages(library('gridExtra'))
suppressPackageStartupMessages(library('grid'))

parser <- ArgumentParser(description = "Plot LRR and BAF for a comparison" )

parser$add_argument("--inputfold", type = "character", help = "input folder")
parser$add_argument("--pre_id", type = "character",  help = "sample ID for PRE sample")
parser$add_argument("--post_id", type = "character",  help = "sample ID for POST sample")
#parser$add_argument("--ann_file", type = "character",  help = ".csv annotation file")
parser$add_argument("--chr", type = "integer",  nargs='*', default = 0, help = "chromosomes to be plotted")
parser$add_argument("--outf", type="character", help = "Output file [basename only]")

args <- parser$parse_args()
#############################
inputfold <- args$inputfold
#ann_file <- args$ann_file
pre <- args$pre_id
post <- args$post_id
chr_set <- args$chr 
outFile <- args$outf
#############################

# print(ann_file)
# Changed
#ann_table <- read.csv(ann_file, stringsAsFactors = FALSE, header = TRUE)
#pre_name <- ann_table$ID[which(ann_table$sample_complete_id == pre)]
#post_name <- ann_table$ID[which(ann_table$sample_complete_id == post)]
pre_name = pre
post_name = post

# print(inputfold)
# load dat., cn. and summary(total) files

# load summary
summary_tab <- read.csv(paste0(inputfold, 'summary.tab'), header = TRUE, sep = '\t', skip=3, stringsAsFactors = FALSE)
summary_tab <- summary_tab[,-1]
colnames(summary_tab) <- c('Chr', 'Start', 'End', sprintf('CN_post_%s', post),  sprintf('CN_pre_%s', pre), 'QS', 'nSites_post', 'nHets_post', 'nSites_pre', 'nHets_pre')

# load dat
dat_pre <- read.csv(paste0(inputfold, 'dat.', pre, '.tab'), header = T, sep = '\t', stringsAsFactors = FALSE)
colnames(dat_pre) <- c('Chr', 'Position', 'BAF', 'LRR')
dat_post <- read.csv(paste0(inputfold, 'dat.', post, '.tab'), header = T, sep = '\t', stringsAsFactors = FALSE)
colnames(dat_post) <- c('Chr', 'Position', 'BAF', 'LRR')


# load cn 
cn_pre <- read.csv(paste0(inputfold, 'cn.', pre, '.tab'), header = T, sep = '\t', stringsAsFactors = FALSE)
colnames(cn_pre) <- c('Chr', 'Position', 'CN', 'P(CN0)',  'P(CN1)',  'P(CN2)',  'P(CN3)')
cn_post <- read.csv(paste0(inputfold, 'cn.', post, '.tab'), header = T, sep = '\t', stringsAsFactors = FALSE)
colnames(cn_post) <- c('Chr', 'Position', 'CN', 'P(CN0)',  'P(CN1)',  'P(CN2)',  'P(CN3)')


if(chr_set == 0){chr_set <- 1:24}

for(chr in chr_set){
  
  print(paste('chr:' , chr))
  
  # plot BAF and LRR for PRE
  dat_pre_chr <- dat_pre[dat_pre$Chr == chr,] 
  
  # fix chr24 undef
  if (nrow(dat_pre_chr)==0){
    next
  }


  nsnps_pre <- nrow(dat_pre_chr)
  
  df_pre <- data.frame(Coordinate = rep(dat_pre_chr$Position, 2))
  df_pre$val <- c(dat_pre_chr$LRR, dat_pre_chr$BAF)
  
  df_pre$type <- c(rep('LRR', nsnps_pre), rep('BAF', nsnps_pre))
  df_pre$type <- factor(df_pre$type, levels = c('BAF', 'LRR'))
  
  plot_pre <- ggplot(data = df_pre, aes(x = Coordinate, y = val))+
    geom_point(size = 0.1, col = 'red')+
    facet_grid(type ~ ., scales = 'free_y')+
    theme_bw()+
    ggtitle('')+
    xlab("")+ylab("")+
    scale_x_continuous(limits = c(0,max(df_pre$Coordinate)), expand = c(0.01, 0.01))+
    theme(legend.text = element_text(size = 14), legend.title = element_text(size=16),
          axis.text=element_text(size=14),
          axis.title=element_text(size=16,face="bold"),
          strip.text = element_text(size=14), plot.title = element_text(hjust = 0, size = 17),
          axis.title.x=element_blank(),axis.text.x=element_blank(),axis.ticks.x=element_blank(), plot.margin=margin(t=-0.8,unit="cm"), panel.spacing = unit(0, "lines"))
  
  
  # plot BAF and LRR for POST
  dat_post_chr <- dat_post[dat_post$Chr == chr,]
  
  nsnps <- nrow(dat_post_chr)
  
  df_post <- data.frame(Coordinate = rep(dat_post_chr$Position, 2))
  df_post$val <- c(dat_post_chr$LRR, dat_post_chr$BAF)
  
  df_post$type <- c(rep('LRR', nsnps), rep('BAF', nsnps))
  df_post$type <- factor(df_post$type, levels = c('LRR', 'BAF'))
  
  plot_post <- ggplot(data = df_post, aes(x = Coordinate, y = val))+
    geom_point(size = 0.1, col = 'blue')+
    facet_grid(type ~ ., scales = 'free_y')+
    theme_bw()+
    ggtitle('')+
    xlab(sprintf("Coord. chromosome %s", chr))+ylab("")+
    scale_x_continuous(limits = c(0,max(df_post$Coordinate)), expand = c(0.01, 0.01))+
    theme(legend.text = element_text(size = 14), legend.title = element_text(size=16),
          axis.text=element_text(size=14),
          axis.title=element_text(size=15,face="bold"),
          strip.text = element_text(size=14), plot.title = element_text(hjust = 0, size = 17), plot.margin=margin(t=-0.8,unit="cm"), panel.spacing = unit(0, "lines"))
  

  # plot CN for PRE and POST
  cn_pre_chr <- cn_pre[cn_pre$Chr == chr,]
  cn_pre_chr <- cn_pre_chr[which(cn_pre_chr$Position %in% dat_pre_chr$Position), ]
  
  cn_post_chr <- cn_post[cn_post$Chr == chr,]
  cn_post_chr <- cn_post_chr[which(cn_post_chr$Position %in% dat_post_chr$Position), ]
  
  log <- cn_pre_chr$Position %in% setdiff(cn_pre_chr$Position, cn_post_chr$Position)
  cn_pre_chr <- cn_pre_chr[!log, ]
  log <- cn_post_chr$Position %in% setdiff(cn_post_chr$Position, cn_pre_chr$Position)
  cn_post_chr <- cn_post_chr[!log, ]
  
  df_cn_pre <- data.frame(x1=cn_pre_chr$Position[-nrow(cn_pre_chr)], x2=cn_pre_chr$Position[-1]-1, y1=cn_pre_chr$CN[-nrow(cn_pre_chr)] - 0.5, 
                          y2=cn_pre_chr$CN[-nrow(cn_pre_chr)] + 0.5, y = cn_pre_chr$CN[-nrow(cn_pre_chr)])
  df_cn_post <- data.frame(x1=cn_post_chr$Position[-nrow(cn_post_chr)], x2=cn_post_chr$Position[-1]-1, y1=cn_post_chr$CN[-nrow(cn_post_chr)] - 0.5, 
                           y2=cn_post_chr$CN[-nrow(cn_post_chr)] + 0.5, y = cn_post_chr$CN[-nrow(cn_post_chr)])
  
  df_cn <- rbind(df_cn_pre, df_cn_post)
  df_cn$y_inv <- c(df_cn_post$y, df_cn_pre$y) 
  df_cn$sample <- c(rep('CN pre', length(cn_pre_chr$Position)-1), rep('CN post', length(cn_post_chr$Position)-1))
  df_cn$sample <- factor(df_cn$sample, levels = c('CN pre', 'CN post'))
  df_cn$sample_inv <-  c(rep('CN post', length(cn_pre_chr$Position)-1), rep('CN pre', length(cn_post_chr$Position)-1))
  df_cn$sample_inv <- factor(df_cn$sample_inv, levels = c('CN pre', 'CN post'))
  
  
  plot_cn <- ggplot()+
    geom_rect(data=df_cn, mapping=aes(xmin=x1, xmax=x2, ymin=y1, ymax=y2, fill = sample), alpha=0.8)+
    geom_line(data=df_cn, mapping=aes(x=x1, y=y_inv, colour = sample_inv))+
    geom_line(data=df_cn, mapping=aes(x=x1, y=y), colour = 'black')+
    scale_fill_manual(values=c("#FF0000", "#0000FF"))+
    scale_colour_manual(values=c("#FF0000", "#0000FF"))+
    facet_grid(sample ~ .)+
    theme_bw()+
    ggtitle('')+
    xlab("")+ylab("")+
    scale_x_continuous(limits = c(0,max(df_cn$x2)), expand = c(0.01, 0.01))+
    scale_y_continuous(limits = c(-0.6,3.6), expand = c(0, 0))+
    theme(legend.text = element_text(size = 14), legend.title = element_text(size=16), legend.position = 'none',
          axis.text=element_text(size=14),
          axis.title=element_text(size=16,face="bold"),
          strip.text = element_text(size=14), plot.title = element_text(hjust = 0, size = 17),
          axis.title.x=element_blank(),axis.text.x=element_blank(),axis.ticks.x=element_blank(), plot.margin=margin(t=-0.8,unit="cm"), panel.spacing = unit(0, "lines"))
  
  # adjust alignment 
  plot_pre <- ggplot_gtable(ggplot_build(plot_pre))
  plot_cn <- ggplot_gtable(ggplot_build(plot_cn))
  plot_post <- ggplot_gtable(ggplot_build(plot_post))
  
  maxWidth <-  unit.pmax(plot_pre$widths[4], plot_cn$widths[4], plot_post$widths[4])
  
  plot_pre$widths[4] <- maxWidth
  plot_cn$widths[4] <- maxWidth
  plot_post$widths[4] <- maxWidth
  
  title <- textGrob(sprintf("%s vs %s", post_name, pre_name), gp=gpar(fontface="bold", fontsize=16), vjust=0.01)
  ggsave(filename = paste0(outFile, sprintf('plot_%s_vs_%s_chr%i.png', post, pre, chr)), plot = grid.arrange(plot_pre, plot_cn, plot_post, ncol=1, vp=viewport(width=0.99, height=0.99), top=title),
                                                                             width = 10, height = 10)
  
}
