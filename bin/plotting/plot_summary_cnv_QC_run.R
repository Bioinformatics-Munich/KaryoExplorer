#!/usr/bin/env Rscript

# Plot CNV for a sample (PRE and POST lines) in the entire genome, use QC summary files
# Written by Lucia Trastulla -- email: lucia_trastulla@psych.mpg.de


suppressPackageStartupMessages(library(argparse))
##############################
suppressPackageStartupMessages(library('ggplot2'))
suppressPackageStartupMessages(library('gridExtra'))
suppressPackageStartupMessages(library('grid'))
##############################

parser_plot <- ArgumentParser(description="cnv plot for a sample (different lines)")

parser_plot$add_argument("--inputdir", type = "character", help="input folder")
parser_plot$add_argument("--fold_fun", type = "character", help="folder for the input function")
parser_plot$add_argument("--post", type = "character", nargs = '*', help=" vector of genome studio name identifyng the post samples")
parser_plot$add_argument("--pre", type = "character", nargs = '*', help="vector of genome studio name for the pre sample")
parser_plot$add_argument("--sample_name", type = "character", nargs = '*', help="vector of name identifying the sample (patient)")
parser_plot$add_argument("--sex", type="character", default = "M", help = "sex of the sample (patient)")
parser_plot$add_argument("--width_plot", type="double", default = 20)
parser_plot$add_argument("--outf", type="character", help = "Output file ")

args <- parser_plot$parse_args()

inputdir <- args$inputdir
fold_fun <- args$fold_fun
post <- args$post 
pre <- args$pre
sample_name <- args$sample_name
sex_sample <- args$sex
width_plot <- args$width_plot
outFile <- args$outf

# set heigth_plot based on the number of post
heigth_plot <- 9+2*(length(post)-1)

# load function
source(paste(fold_fun, 'plot_summary_cnv_function.R', sep = ""))

M <- 10^6


# setwd(sprintf('%s/outdir_%s_%s/',inputdir, sample_name, pre)) 
cnv_analysis_resdir=sprintf('%s/outdir_%s_%s/',inputdir, post, pre)
cnv_diff_resdir=sprintf('%s/%s_%s/',inputdir, post, pre)

#comp_dir <- sapply(post, function(x) sprintf('output_%s/', x))
#post_file <- mapply(function(x,y) paste(x, 'summary_QC.', y, '.tab', sep = ""), x = comp_dir, y = post)
#pre_file <- sapply(comp_dir, function(x) paste(x, 'summary_QC.', pre, '.tab', sep = ""))

# changed
post_file <- paste0(cnv_diff_resdir,'/summary_QC.',post,'.tab')
pre_file <- paste0(cnv_diff_resdir,'/summary_QC.',pre,'.tab')

cnv_tab_post <-  lapply(post_file, function(x) transform_tab(file_name = x, QC = TRUE, sex_sample = sex_sample))
cnv_tab_pre <-  lapply(pre_file, function(x) transform_tab(file_name = x, QC = TRUE, sex_sample = sex_sample))



############### compute the centromere from the first pre file ####################
#pre_file_dat <- paste(comp_dir[[1]], 'dat.', pre, '.tab', sep = "")
pre_file_dat <- paste(cnv_analysis_resdir, '/dat.', pre, '.tab', sep = "")

# compute the centromere position for the chromosome having it in the middle (exclude 13, 14, 15, special case for Y)
pre_dat <- read.table(pre_file_dat, header = FALSE, sep = '\t', stringsAsFactors = FALSE, colClasses = c(rep("integer", 2), rep("NULL", 2)))
colnames(pre_dat) <- c('chr', 'pos')
# split according the chromosome
chr_id <- lapply(1:24, function(x) which(pre_dat$chr == x))
pre_pos_list <- lapply(chr_id, function(x) pre_dat$pos[x])
names(pre_pos_list) <- 1:24

initial_vect <- rep(FALSE, 24)
# chromosome with the centromere at the beginning
initial_vect[c(13:15,22)] <- TRUE
table_centr <- t(mapply(function(x,y) find_centromere(df_ch = x, initial = y)/M, x = pre_pos_list, y=initial_vect, SIMPLIFY = TRUE))
table_centr <- as.data.frame(table_centr)
colnames(table_centr) <- c('start', 'end')

table_centr$chr <- 1:24
#################################################################################################################

# transoform the table to have a continuoum scale for the genome, add the position of the centromere (in CNS is indicated as 'centr')
new_tabs <-  transform_tab(file_name = pre_file[[1]],  gap_df = table_centr, QC = TRUE)
gap_table_centr_new <- new_tabs$gap_df_new

# save original start and the added vector to obtain the contious coordinate
add_vect <- new_tabs$add_vect*M
start_vect <- sapply(pre_pos_list, function(x) x[1])



######### transform the list of pre df in a unique df, 
# CNS for preoblast is a factor, the ambigous states will be then transformed in CNS=4 

if(length(post)>1){cnv_tab_pre_tot <- combine_pre_tab(cnv_df_fibr = cnv_tab_pre)
}else{
  cnv_tab_pre_tot <- cnv_tab_pre[[1]]
}



# combine the start and end of the datasets
cnv_tab_comb <- combine_pos(cnv_tab_pre_tot, cnv_tab_post, centromere_df = gap_table_centr_new, M = M)

cnv_tab_comb_pre <- cnv_tab_comb[[1]]
#print(cnv_tab_comb_pre$CNS)
cnv_tab_comb_pre$sample <- factor(rep(pre, nrow(cnv_tab_comb_pre)))
cnv_tab_comb_pre <- change_CNS_centromere(cnv_tab_comb_pre, sex = sex_sample)
cnv_tab_comb_pre$CNS <- as.factor(cnv_tab_comb_pre$CNS)
#print(cnv_tab_comb_pre$CNS)

cnv_tab_comb_post <- cnv_tab_comb[[2]]
for (i in 1:length(post)){
  
  cnv_tab_comb_post[[i]]$sample <- factor(rep(post[i], nrow(cnv_tab_comb_post[[i]])))
  cnv_tab_comb_post[[i]] <- change_CNS_centromere(cnv_tab_comb_post[[i]], sex = sex_sample)
}


##################################################################################################################################################
# save the dataframe and print
chr_id_length <- sapply(1:24, function(x) length(which(cnv_tab_comb_pre$chr == x )))
sub_vect <- unlist(mapply(function(x,y) rep(y,x), x = chr_id_length, y = add_vect))

start_original <- round(cnv_tab_comb_pre$start*M - sub_vect)
end_original <- round(cnv_tab_comb_pre$end*M - sub_vect)

df_summary <- data.frame( cnv_tab_comb_pre$chr, start_original, end_original)
df_summary <- cbind(df_summary, cnv_tab_comb_pre$CNS) 

col_name <- vector()
for (i in 1:length(post)){
  
  col_name[i] <- paste("CNS_", post[i], sep = "")
  df_summary <- cbind(df_summary, cnv_tab_comb_post[[i]]$CNS) 
  
}


#print(df_summary$`cnv_tab_comb_pre$CNS`)
#print(cnv_tab_comb_pre$start)
#print(cnv_tab_comb_pre$end)

# report the differences between preoblast and post:
# create a column with 0 and n \in [1,..., length(post)], 0 refers to no differences between pre and all post, n indicates that there 
# is a difference in n comparison for that region 


id_notmatch <- which(is.na(as.numeric(as.character(cnv_tab_comb_pre$CNS))))
#print(id_notmatch)
id_match <- which(!is.na(as.numeric(as.character(cnv_tab_comb_pre$CNS))))
#print(id_match)

df_diff_pre <- matrix(nrow = nrow(df_summary), ncol = length(post))

pre_vect_match <- as.numeric(as.character(df_summary[id_match, 4]))
pre_df_match <- matrix(rep(pre_vect_match, length(post)), ncol =  length(post))
#print(pre_df_match)
colnames(pre_df_match) <- col_name

df_diff_pre[id_match, 1:length(post)] <- pre_df_match

if(length(id_notmatch) > 0){
  
  pre_vect_notmatch <- as.character(df_summary[id_notmatch, 4])
  pre_df_notmatch <- t(sapply(pre_vect_notmatch, function(x) as.numeric(strsplit(x, split = ',')[[1]])))
  #print(pre_df_notmatch)
  colnames(pre_df_notmatch) <- col_name
  
  df_diff_pre[id_notmatch, 1:length(post)] <- pre_df_notmatch
  
}





df_diff_post<- df_summary[,5:(length(post) + 4)]

if(length(post)==1){df_diff_post <- matrix(df_diff_post, ncol = 1)} 

#print(str(df_diff_post))
# save the differences in each comparison
diff_comp <- matrix(nrow = nrow(df_summary), ncol = length(post))

for( i in 1:length(post)){
  
  diff_comp[,i] <- (df_diff_pre[,i] == df_diff_post[,i])
  
}

diff_comp_total <- apply(diff_comp, 1, function(x) length(which(!x)))
###################################################
# add this information to df_summary
df_summary <- cbind(df_summary,diff_comp_total)
############## save the table #####################
colnames(df_summary) <- c('chr', 'start', 'end', paste("CNS_", pre, sep = ""), col_name, 'n. different comparison')
write.table(df_summary, paste(outFile, '_QC_summary', '.txt',sep = ""), quote = FALSE, row.names = FALSE, col.names = TRUE, sep = '\t')
###################################################

# transform the df for the preoblast, ambigous CN = 4  
id_notmatch <- is.na(as.numeric(as.character(cnv_tab_comb_pre$CNS)))
new_CNS <- rep(0, nrow(cnv_tab_comb_pre))
new_CNS[id_notmatch] <- 4
new_CNS[!id_notmatch] <- as.numeric(as.character(cnv_tab_comb_pre$CNS[!id_notmatch]))

cnv_tab_comb_pre$CNS <- new_CNS
#print(cnv_tab_comb_pre$CNS)

# save the start of the chromosomes
# the same for each sample
# choose the first dataset (pre)
start_chr_id <- sapply(1:24, function(x) which(cnv_tab_comb[[1]]$chr == x)[1])
start_chr <- cnv_tab_comb[[1]]$start[start_chr_id]
label_graph_y_start <- sapply(trunc(start_chr), function(x) paste(x, 'M', sep = ""))
label_graph_y_chr <- c(sapply(1:22, function(x) paste('chr', x, sep = "")), "chrX", "chrY")

label_graph_y <- mapply(function(x,y) paste(x,y,sep = " ") ,x = label_graph_y_chr, y = label_graph_y_start)
names(label_graph_y) <- NULL


# produce two plot, the first plots the different CN the second (just one row) highligth if where are differences between the preoblas and the post lines
############################# data frame for the first plot ################################
cnv_tab_comb_post_total <- do.call(rbind, cnv_tab_comb_post)
# combine preoblast and post
cnv_tab_comb_total <- rbind(cnv_tab_comb_pre ,cnv_tab_comb_post_total)
# cnv_tab_comb_total$CNS <- as.factor(cnv_tab_comb_total$CNS)
cnv_tab_comb_total$CNS <- factor(cnv_tab_comb_total$CNS, level = c(0:4))



############################# data frame for the second plot ################################
# use df_summary
colnames(df_summary)[ncol(df_summary)] <- 'n_diff'
df_summary$start <- cnv_tab_comb_pre$start
df_summary$end <- cnv_tab_comb_pre$end
#df_summary$n_diff <- factor(df_summary$n_diff, level = c(0:length(post)))
#print(df_summary)
df_summary$comp <- rep('comparison',nrow(df_summary))

# construct the plot
n_row <- nrow(cnv_tab_comb_total)

darkblue_color <- "#0000CD"
lightblue_color <- "#87CEFA"
darkred_color <- "#8B0000"
purple_color <- "#8B008B"
grey_color <- "#D3D3D3"


cols <- c(purple_color, '#4EAEE0', "transparent", "#FF993E", "#D51C1C") 
# cols <- c(purple_color, grey_color, "transparent", darkblue_color, "red") 


########### first plot ###########
#cnv_tab_comb_total$CNS[1] = "0"

n_row_1 <- length(which(cnv_tab_comb_total$CNS == 1))
n_row_0 <- length(which(cnv_tab_comb_total$CNS == 0))
n_row_2 <- length(which(cnv_tab_comb_total$CNS == 2))
n_row_3 <- length(which(cnv_tab_comb_total$CNS == 3))
n_row_4 <- length(which(cnv_tab_comb_total$CNS == 4))
#print(cnv_tab_comb_total$CNS)
#print(n_row_0)

plot_cnv <- ggplot(cnv_tab_comb_total, aes(xmin = start, xmax=end, ymin=rep(0,n_row), ymax=rep(3,n_row)) ) +
  scale_fill_manual(values = alpha(cols, c(1,1,0.1,1,1)),  name="Copy number\nstatus", labels=c("CN0", "CN1", "CN2", "CN3", "undef CN"), drop = FALSE,
                    guide = guide_legend(override.aes=list(size = 0.2, color = 'black')))+
  ggtitle("")+
  ylab("")+
  theme_bw() +
  scale_x_continuous(breaks=start_chr ,  labels = label_graph_y, expand = c(0, 2))+
  scale_y_continuous(expand = c(0, 0.01))+
  theme(axis.text.x=element_text(angle=90, hjust=1),  axis.title.x=element_blank(),
        axis.title.y=element_blank(), axis.text.y=element_blank(), axis.ticks.y=element_blank(), axis.ticks.x = element_line(size=.3, color="black"),
        panel.grid.major.x = element_line( size=0.3, color="black"), panel.grid.major.y = element_blank(),
        panel.grid.minor.x = element_blank(), panel.grid.minor.y = element_blank(),
        plot.title = element_text(hjust = 0.5, size=22))+
  facet_grid(sample ~ ., switch  = 'y')

#str(subset(cnv_tab_comb_total, CNS  == 0))


if(n_row_0 > 0){plot_cnv <- plot_cnv +
  geom_rect(data = subset(cnv_tab_comb_total, CNS  == 0) , mapping = aes(xmin=start, xmax=end, ymin=rep(0,n_row_0), ymax=rep(3,n_row_0), fill = CNS ), color = cols[1], size = 1/(1e+16))}
#geom_rect( aes(xmin=cnv_tab_comb_total$start[which(cnv_tab_comb_total$CNS == 0)], xmax=cnv_tab_comb_total$end[which(cnv_tab_comb_total$CNS == 0)], ymin=rep(0,n_row_0), ymax=rep(3,n_row_0), fill = cols[1]), color = cols[1], size = 1/(1e+16))}

if(n_row_1 > 0 ){plot_cnv <- plot_cnv +
  geom_rect(data = subset(cnv_tab_comb_total, CNS  == 1) , mapping = aes(xmin=start, xmax=end, ymin=rep(0,n_row_1), ymax=rep(3,n_row_1), fill = CNS), color = cols[2], size = 1/(1e+16))}

if(n_row_2 > 0){plot_cnv <- plot_cnv +
  geom_rect(data = subset(cnv_tab_comb_total, CNS  == 2) , mapping = aes(xmin=start, xmax=end, ymin=rep(0,n_row_2), ymax=rep(3,n_row_2), fill = CNS), color = cols[3], size = 1/(1e+16))}

if(n_row_3 > 0 ){plot_cnv <- plot_cnv +
  geom_rect(data = subset(cnv_tab_comb_total, CNS  == 3) , mapping = aes(xmin=start, xmax=end, ymin=rep(0,n_row_3), ymax=rep(3,n_row_3), fill = CNS), color = cols[4], size = 1/(1e+16))}

if(n_row_4 > 0){plot_cnv <- plot_cnv +
  geom_rect(data = subset(cnv_tab_comb_total, CNS  == 4) , mapping = aes(xmin=start, xmax=end, ymin=rep(0,n_row_4), ymax=rep(3,n_row_4), fill = CNS), color = cols[5], size = 1/(1e+16))}


#plot_cnv <- plot_cnv + facet_grid(sample ~ ., switch  = 'y')

########## second plot ###########
labels_diff <- c("n. diff = 0", "n.diff > 0")
# col_palette <- c(RColorBrewer::brewer.pal(8,'Dark2')[-1], RColorBrewer::brewer.pal(8,'Accent'))
# col_diff <- c('transparent', RColorBrewer::brewer.pal(10,'RdYlGn')[10])
col_diff <- c('transparent', "#0000FF")
nrow_summ <- nrow(df_summary)


#df_summary$diff <- as.numeric(as.character(df_summary$n_diff))
df_summary$diff <- df_summary$n_diff
df_summary$diff[which(df_summary$diff>0)] <- 1
df_summary$diff <- factor(df_summary$diff, level = 0:1)



plot_diff <- ggplot(df_summary, aes(xmin = start, xmax=end, ymin=rep(0,nrow_summ), ymax=rep(3,nrow_summ)) ) +
  scale_fill_manual(values = alpha(col_diff, c(0.1,1)),  name="Comparison  ", labels=labels_diff, drop = FALSE,
                    guide = guide_legend(override.aes=list(size = 0.2, color = 'black')))+
  ggtitle("")+
  ylab("")+
  theme_bw() +
  scale_x_continuous(breaks=start_chr , labels = label_graph_y, expand = c(0, 2), position = "top")+
  scale_y_continuous(expand = c(0, 0.01))+
  theme(axis.text.x=element_text(angle=90, hjust=1),  axis.title.x=element_blank(),
        axis.title.y=element_blank(), axis.text.y=element_blank(), axis.ticks.y=element_blank(), axis.ticks.x = element_line(size=0.3, color="black"),
        panel.grid.major.x = element_line( size=0.3, color="black"), panel.grid.major.y = element_blank(),
        panel.grid.minor.x = element_blank(), panel.grid.minor.y = element_blank(),
        plot.title = element_text(hjust = 0.5, size=22))+
  facet_grid(comp ~ ., switch  = 'y')

n_row_diff0 <- length(which(df_summary$diff==0))
n_row_diff <- length(which(df_summary$diff==1))


if(n_row_diff0 > 0){plot_diff <- plot_diff +
  geom_rect(data = subset(df_summary, diff  == 0) , mapping = aes(xmin=start, xmax=end, ymin=rep(0,n_row_diff0), ymax=rep(3,n_row_diff0), fill = diff), color = col_diff[1], size = 1/(1e+16))}

if(n_row_diff > 0){plot_diff <- plot_diff +
  geom_rect(data = subset(df_summary, diff  == 1) , mapping = aes(xmin=start, xmax=end, ymin=rep(0,n_row_diff), ymax=rep(3,n_row_diff), fill = diff), color = col_diff[2], size = 1/(1e+16))}


############################################################
# save the two plots

#ggsave(file = 'fig.pdf', plot = plot_cnv, device = NULL, path = NULL, scale = 1, width = 20, height = 10, dpi = 1000) 
#ggsave(file = 'fig1.pdf', plot = plot_diff, device = NULL, path = NULL, scale = 1, width = 20, height = 10, dpi = 1000)


ggsave(file = paste(outFile, '_QC.pdf', sep = ""), 
       #plot = grid.arrange(plot_diff,plot_cnv, heights=c(1.1/(length(post)+1), (length(post)-0.1)/(length(post)+1)), 
       # plot = grid.arrange(plot_diff,plot_cnv, heights=c(1/(length(post)+2), (length(post) + 1)/(length(post)+2)),
       plot = grid.arrange(plot_diff,plot_cnv, heights= c(3, heigth_plot -3),
                           ncol=1, top = textGrob(sample_name,gp=gpar(fontsize=23,font=1))), 
       device = NULL, path = NULL, scale = 1, width = width_plot, height = heigth_plot, dpi = 1000)

ggsave(file = paste(outFile, '_QC.png', sep = ""),
       #plot = grid.arrange(plot_diff,plot_cnv, heights=c(1.1/(length(post)+1), (length(post)-0.1)/(length(post)+1)),
       # plot = grid.arrange(plot_diff,plot_cnv, heights=c(1/(length(post)+2), (length(post) + 1)/(length(post)+2)),
       plot = grid.arrange(plot_diff,plot_cnv, heights= c(3, heigth_plot -3),
                           ncol=1, top = textGrob(sample_name,gp=gpar(fontsize=23,font=1))),
       device = NULL, path = NULL, scale = 1, width = width_plot, height = heigth_plot, dpi = 200)



