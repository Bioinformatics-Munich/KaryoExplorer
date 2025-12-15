#!/usr/bin/env Rscript

# Plot CNVs for different CN detected in each comparison
# Written by Thomas W., HMGU

suppressPackageStartupMessages(library(argparse))
##############################
suppressPackageStartupMessages(library('ggplot2'))
suppressPackageStartupMessages(library('gridExtra'))
suppressPackageStartupMessages(library('grid'))
##############################

parser_plot <- ArgumentParser(description="Plot cnv summary for all comparisons")

parser_plot$add_argument("--post", type = "character", nargs = '*', help=" vector of genome studio name identifyng the post repreogramming lines")
parser_plot$add_argument("--pre", type = "character",  help="genome studio name for the pre reprogramming lines")
parser_plot$add_argument("--CN_len_thr", type = "integer", default = 200, help="CN length thr in kb")
parser_plot$add_argument("--CN_len_thr_big", type = "integer", default = 1000, help="CN length (big) thr in kb")
parser_plot$add_argument("--width_plot", type="double", default = 10)
parser_plot$add_argument("--outf", type="character", help = "Output file ", default = ".")

args <- parser_plot$parse_args()

post <- args$post 
pre_name <- args$pre
CN_len_thr <- args$CN_len_thr
CN_len_thr_big <- args$CN_len_thr_big
width_plot <- args$width_plot
outFile <- args$outf

# set heigth_plot based on the number of post
heigth_plot <- 9+(length(post)-1)

# read and merge the diff tables
df <- NULL


for (postsample in post){
  # filename
  fn=paste0(postsample,"_",pre_name,"/",pre_name,"_CNV_diff.txt")
  tab=read.table(fn, header=T, sep="\t")
  df=rbind(df,tab)
}

# write table
dir.create(outFile)
write.table(x = df, file = paste(outFile, sprintf('/%s_CNV_diff.txt', pre_name), sep = ''), quote = FALSE, sep = '\t', col.names = TRUE, row.names = FALSE)

# Create the plot for each post

# create df for plot
df_plot <- rbind(df[,1:6], df[,1:6])
df_plot$Ndiff = c(df$Ndiff_200kb, df$Ndiff_1Mb)
df_plot$thr = c(rep(sprintf('%s Mb', as.character(CN_len_thr/1000)), nrow(df)), rep(sprintf('%s Mb', as.character(CN_len_thr_big/1000)), nrow(df)))
df_plot$Chr <- factor(df_plot$Chr, levels = c(1:22, 'X', 'Y', 'tot'))

# Save table
tab=df_plot[df_plot$Chr=="tot",c("pre_ID","post_ID","Chr","thr","Ndiff")]
write.table(x = tab, file = paste(outFile, sprintf('/%s_CNV_diff_tot.tsv', pre_name), sep = ''), quote = FALSE, sep = '\t', col.names = FALSE, row.names = FALSE)

# rm tot in the plot
df_plot = df_plot[df_plot$Chr != "tot", ]

plot_CN <- ggplot(data = df_plot, aes(x = Chr, y = Ndiff))+
  geom_bar(stat = "identity", aes(fill = thr), colour = "black",  position=position_dodge())+
  theme_bw()+
  ggtitle(sprintf('Different CN wrt %s', pre_name))+
  ylab("N. of diff CN")+xlab("Chr")+
  facet_wrap(~post_ID, ncol = 1)+
  scale_fill_discrete(name = "length >")+
  theme(legend.text = element_text(size = 14), legend.title = element_text(size=16),
        axis.text=element_text(size=14),
        axis.title=element_text(size=16,face="bold"),
        strip.text = element_text(size=14), plot.title = element_text(hjust = 0, size = 17))

#print(plot_CN)
ggsave(filename = paste(outFile, sprintf('/%s_CNV_diff.pdf', pre_name), sep = ''), plot = plot_CN, width = width_plot, height = heigth_plot)
ggsave(filename = paste(outFile, sprintf('/%s_CNV_diff.png', pre_name), sep = ''), plot = plot_CN, width = width_plot, height = heigth_plot)
