#!/usr/bin/env Rscript

# plot LRR and BAF for a single line, add the info on CN
# code similar to the python automatic code produced by bcftools
# Written by Lucia Trastulla -- email: lucia_trastulla@psych.mpg.de

suppressPackageStartupMessages(library(argparse))
suppressPackageStartupMessages(library('ggplot2'))
suppressPackageStartupMessages(library('gridExtra'))
suppressPackageStartupMessages(library('grid'))

parser <- ArgumentParser(description = "Plot LRR and BAF for a single line" )

parser$add_argument("--inputfold", type = "character", help = "input folder")
parser$add_argument("--line_id", type = "character",  help = "sample ID for sample (single line)")
#parser$add_argument("--ann_file", type = "character",  help = ".csv annotation file")
parser$add_argument("--chr", type = "integer",  nargs='*', default = 0, help = "chromosomes to be plotted")
parser$add_argument("--outf", type="character", help = "Output file [basename only]")

args <- parser$parse_args()
#############################
inputfold <- args$inputfold
#ann_file <- args$ann_file
line <- args$line_id
chr_set <- args$chr 
outFile <- args$outf
#############################

# print(ann_file)

#ann_table <- read.csv(ann_file, stringsAsFactors = FALSE, header = TRUE)
#line_name <- ann_table$ID[which(ann_table$sample_complete_id == line)]

# print(inputfold)
# load dat., cn. and summary(total) files

# load dat
dat_line <- read.csv(file.path(inputfold, paste0('dat.', line, '.tab')), header = T, sep = '\t', stringsAsFactors = FALSE)
colnames(dat_line) <- c('Chr', 'Position', 'BAF', 'LRR')

# load cn 
cn_line <- read.csv(file.path(inputfold, paste0('cn.', line, '.tab')), header = T, sep = '\t', stringsAsFactors = FALSE)
colnames(cn_line) <- c('Chr', 'Position', 'CN', 'P(CN0)',  'P(CN1)',  'P(CN2)',  'P(CN3)')


if(chr_set == 0){chr_set <- unique(dat_line$Chr)}

for(chr in chr_set){
  
  print(paste('chr:' , chr))
  
  # plot BAF and LRR for the line
  dat_chr <- dat_line[dat_line$Chr == chr,]

  nsnps <- nrow(dat_chr)
  
  df_line <- data.frame(Coordinate = rep(dat_chr$Position, 2))
  df_line$val <- c(dat_chr$LRR, dat_chr$BAF)
  
  df_line$type <- c(rep('LRR', nsnps), rep('BAF', nsnps))
  df_line$type <- factor(df_line$type, levels = c('BAF', 'LRR'))
  
  plot_line <- ggplot(data = df_line, aes(x = Coordinate, y = val))+
    geom_point(size = 0.1, col = '#3CB371')+
    facet_grid(type ~ ., scales = 'free_y')+
    theme_bw()+
    ggtitle('')+
    xlab("")+ylab("")+
    scale_x_continuous(limits = c(0,max(df_line$Coordinate)), expand = c(0.01, 0.01))+
    theme(legend.text = element_text(size = 14), legend.title = element_text(size=16),
          axis.text=element_text(size=14),
          axis.title=element_text(size=16,face="bold"),
          strip.text = element_text(size=14), plot.title = element_text(hjust = 0, size = 17),
          axis.title.x=element_blank(),axis.text.x=element_blank(),axis.ticks.x=element_blank(), plot.margin=margin(t=-0.8,unit="cm"), panel.spacing = unit(0, "lines"))
  
  
  # plot CN for the line
  cn_chr <- cn_line[cn_line$Chr == chr,]
  cn_chr <- cn_chr[which(cn_chr$Position %in% dat_chr$Position), ]

  df_cn <- data.frame(x1=cn_chr$Position[-nrow(cn_chr)], x2=cn_chr$Position[-1]-1, y1=cn_chr$CN[-nrow(cn_chr)] - 0.5, 
                          y2=cn_chr$CN[-nrow(cn_chr)] + 0.5, y = cn_chr$CN[-nrow(cn_chr)])
 
  df_cn$sample <- rep('CN', nrow(df_cn))
  df_cn$sample <- factor(df_cn$sample)
 
  plot_cn <- ggplot()+
    geom_rect(data=df_cn, mapping=aes(xmin=x1, xmax=x2, ymin=y1, ymax=y2, fill = sample), alpha=0.8)+
    geom_line(data=df_cn, mapping=aes(x=x1, y=y), colour = 'black')+
    scale_fill_manual(values=c("#3CB371"))+
    facet_grid(sample ~ .)+
    theme_bw()+
    ggtitle('')+
    xlab(sprintf("Coord. chromosome %s", chr))+ylab("")+
    scale_x_continuous(limits = c(0,max(df_cn$x2)), expand = c(0.01, 0.01))+
    scale_y_continuous(limits = c(-0.6,3.6), expand = c(0, 0))+
    theme(legend.text = element_text(size = 14), legend.title = element_text(size=16), legend.position = 'none',
          axis.text=element_text(size=14),
          axis.title=element_text(size=16,face="bold"),
          strip.text = element_text(size=14), plot.title = element_text(hjust = 0, size = 17),
          plot.margin=margin(t=-0.8,unit="cm"), panel.spacing = unit(0.1, "lines"))
  
  # adjust alignment 
  plot_line <- ggplot_gtable(ggplot_build(plot_line))
  plot_cn <- ggplot_gtable(ggplot_build(plot_cn))
  
  maxWidth <-  unit.pmax(plot_line$widths[4], plot_cn$widths[4])
  
  plot_line$widths[4] <- maxWidth
  plot_cn$widths[4] <- maxWidth

  title <- textGrob(line, gp=gpar(fontface="bold", fontsize=16), vjust=0.01)
  ggsave(filename = file.path(outFile, sprintf('plot_%s_chr%i.png', line, chr)), plot = grid.arrange(plot_line, plot_cn, ncol=1, vp=viewport(width=0.99, height=0.99), top=title),
         width = 10, height = 5)
  
}

