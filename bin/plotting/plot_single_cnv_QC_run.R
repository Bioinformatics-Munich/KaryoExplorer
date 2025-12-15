#!/usr/bin/env Rscript

# Plot CNV for a single line in the entire genome, use QC summary files
# Written by Lucia Trastulla -- email: lucia_trastulla@psych.mpg.de


suppressPackageStartupMessages(library(argparse))
##############################
suppressPackageStartupMessages(library('ggplot2'))
suppressPackageStartupMessages(library('gridExtra'))
suppressPackageStartupMessages(library('grid'))
##############################

parser_plot <- ArgumentParser(description="cnv plot single line")

parser_plot$add_argument("--inputdir", type = "character", help="input folder")
parser_plot$add_argument("--fold_fun", type = "character", help="folder for the input function")
parser_plot$add_argument("--line", type = "character", nargs = '*', help=" vector of genome studio name identifyng the ipsc samples")
parser_plot$add_argument("--sample_name", type = "character", nargs = '*', help="vector of name identifying the sample (patient)")
parser_plot$add_argument("--sex", type="character", default = "M", help = "sex of the sample (patient)")
parser_plot$add_argument("--width_plot", type="double", default = 20)
parser_plot$add_argument("--heigth_plot", type="double", default = 4)
parser_plot$add_argument("--outf", type="character", help = "Output file ")

args <- parser_plot$parse_args()

inputdir <- args$inputdir
fold_fun <- args$fold_fun
line <- args$line
sample_name <- args$sample_name
sex_sample <- args$sex
width_plot <- args$width_plot
heigth_plot <- args$heigth_plot
outFile <- args$outf


# load function
source(file.path(fold_fun, 'plot_summary_cnv_function.R'))

M <- 10^6

#setwd(sprintf('%s/outdir_%s_%s/',inputdir, sample_name, line)) 

line_file <- file.path(inputdir,line, paste0('summary_QC.', line, '.tab'))

cnv_tab <-  transform_tab(file_name = line_file, QC = TRUE, sex_sample = sex_sample)
cnv_tab$CNS <- factor(cnv_tab$CNS, levels = c(0,1,2,3,4))

### already adjusted for the centromere ####
file_dat <- file.path(inputdir,paste0("outdir_",line), paste0('dat.', line, '.tab'))

# compute the centromere position for the chromosome having it in the middle (exclude 13, 14, 15, special case for Y)
file_dat <- read.table(file_dat, header = FALSE, sep = '\t', stringsAsFactors = FALSE, colClasses = c(rep("integer", 2), rep("NULL", 2)))
colnames(file_dat) <- c('chr', 'pos')
# split according the chromosome
chr_id <- lapply(1:24, function(x) which(file_dat$chr == x))
pos_list <- lapply(chr_id, function(x) file_dat$pos[x])
names(pos_list) <- 1:24

initial_vect <- rep(FALSE, 24)
# chromosome with the centromere at the beginning
initial_vect[c(13:15,22)] <- TRUE
table_centr <- t(mapply(function(x,y) find_centromere(df_ch = x, initial = y)/M, x = pos_list, y=initial_vect, SIMPLIFY = TRUE))
table_centr <- as.data.frame(table_centr)
colnames(table_centr) <- c('start', 'end')

table_centr$chr <- 1:24
#################################################################################################################
# 
# # transoform the table to have a continuoum scale for the genome, add the position of the centromere (in CNS is indicated as 'centr')
new_tabs <-  transform_tab(file_name = line_file,  gap_df = table_centr, QC = TRUE)
gap_table_centr_new <- new_tabs$gap_df_new

# save original start and the added vector to obtain the contious coordinate
add_vect <- new_tabs$add_vect*M
##################################################################################################################################################

# save the dataframe and print
chr_id_length <- sapply(1:24, function(x) length(which(cnv_tab$chr == x )))
sub_vect <- unlist(mapply(function(x,y) rep(y,x), x = chr_id_length, y = add_vect))

start_original <- round(cnv_tab$start*M - sub_vect)
end_original <- round(cnv_tab$end*M - sub_vect)

df_summary <- data.frame( cnv_tab$chr, start_original, end_original, cnv_tab$CNS)


# save the start of the chromosomes
# the same for each sample
# choose the first dataset (fibr)
start_chr_id <- sapply(1:24, function(x) which(cnv_tab$chr == x)[1])
start_chr <- cnv_tab$start[start_chr_id]
label_graph_y_start <- sapply(trunc(start_chr), function(x) paste(x, 'M', sep = ""))
label_graph_y_chr <- c(sapply(1:22, function(x) paste('chr', x, sep = "")), "chrX", "chrY")

label_graph_y <- mapply(function(x,y) paste(x,y,sep = " ") ,x = label_graph_y_chr, y = label_graph_y_start)
names(label_graph_y) <- NULL



# construct the plot
n_row <- nrow(df_summary)

darkblue_color <- "#0000CD"
lightblue_color <- "#87CEFA"
darkred_color <- "#8B0000"
purple_color <- "#8B008B"
grey_color <- "#D3D3D3"


cols <- c(purple_color, '#4EAEE0', "transparent", "#FF993E", "#D51C1C") 
# cols <- c(purple_color, grey_color, "transparent", darkblue_color, "red") 


########### first plot ###########
#cnv_tab_comb_total$CNS[1] = "0"

n_row_1 <- length(which(cnv_tab$CNS == 1))
n_row_0 <- length(which(cnv_tab$CNS == 0))
n_row_2 <- length(which(cnv_tab$CNS == 2))
n_row_3 <- length(which(cnv_tab$CNS == 3))
n_row_4 <- length(which(cnv_tab$CNS == 4))
#print(cnv_tab_comb_total$CNS)
#print(n_row_0)

plot_cnv <- ggplot(cnv_tab, aes(xmin = start*M, xmax=end*M, ymin=rep(0,n_row), ymax=rep(3,n_row)) ) +
  scale_fill_manual(values = alpha(cols, c(1,1,0.1,1,1)),  name="Copy number\nstatus", labels=c("CN0", "CN1", "CN2", "CN3", "undef CN"), drop = FALSE,
                    guide = guide_legend(override.aes=list(size = 0.2, color = 'black')))+
  ggtitle(sample_name)+
  ylab(line)+
  theme_bw() +
  scale_x_continuous(breaks=start_chr*M ,  labels = label_graph_y, expand = c(0, 2))+
  scale_y_continuous(expand = c(0, 0.01))+
  theme(axis.text.x=element_text(angle=90, hjust=1, size = 14),  axis.title.x=element_blank(),
        axis.title.y=element_text(size = 16), axis.text.y=element_blank(), axis.ticks.y=element_blank(), axis.ticks.x = element_line(size=.3, color="black"),
        panel.grid.major.x = element_line( size=0.3, color="black"), panel.grid.major.y = element_blank(),
        panel.grid.minor.x = element_blank(), panel.grid.minor.y = element_blank(),legend.text=element_text(size=14),
        plot.title = element_text(hjust = 0.5, size=22),legend.title=element_text(size=14))
  #facet_grid(sample ~ ., switch  = 'y')

#str(subset(cnv_tab_comb_total, CNS  == 0))
#plot_cnv

if(n_row_0 > 0){plot_cnv <- plot_cnv +
  geom_rect(data = subset(cnv_tab, CNS  == 0) , mapping = aes(xmin=start*M, xmax=end*M, ymin=rep(0,n_row_0), ymax=rep(3,n_row_0), fill = CNS ), color = cols[1], size = 1/(1e+16))}
#geom_rect( aes(xmin=cnv_tab_comb_total$start[which(cnv_tab_comb_total$CNS == 0)], xmax=cnv_tab_comb_total$end[which(cnv_tab_comb_total$CNS == 0)], ymin=rep(0,n_row_0), ymax=rep(3,n_row_0), fill = cols[1]), color = cols[1], size = 1/(1e+16))}

if(n_row_1 > 0 ){plot_cnv <- plot_cnv +
  geom_rect(data = subset(cnv_tab, CNS  == 1) , mapping = aes(xmin=start*M, xmax=end*M, ymin=rep(0,n_row_1), ymax=rep(3,n_row_1), fill = CNS), color = cols[2], size = 1/(1e+16))}

if(n_row_2 > 0){plot_cnv <- plot_cnv +
  geom_rect(data = subset(cnv_tab, CNS  == 2) , mapping = aes(xmin=start*M, xmax=end*M, ymin=rep(0,n_row_2), ymax=rep(3,n_row_2), fill = CNS), color = cols[3], size = 1/(1e+16))}

if(n_row_3 > 0 ){plot_cnv <- plot_cnv +
  geom_rect(data = subset(cnv_tab, CNS  == 3) , mapping = aes(xmin=start*M, xmax=end*M, ymin=rep(0,n_row_3), ymax=rep(3,n_row_3), fill = CNS), color = cols[4], size = 1/(1e+16))}

if(n_row_4 > 0){plot_cnv <- plot_cnv +
  geom_rect(data = subset(cnv_tab, CNS  == 4) , mapping = aes(xmin=start*M, xmax=end*M, ymin=rep(0,n_row_4), ymax=rep(3,n_row_4), fill = CNS), color = cols[5], size = 1/(1e+16))}


# save the plot

ggsave(file = file.path(outFile, sprintf('cnv_%s.pdf', sample_name)), plot = plot_cnv, device = NULL, path = NULL, scale = 1, width = width_plot, height = heigth_plot, dpi = 1000) 
ggsave(file = file.path(outFile, sprintf('cnv_%s.png', sample_name)), plot = plot_cnv, device = NULL, path = NULL, scale = 1, width = width_plot, height = heigth_plot, dpi = 500)
