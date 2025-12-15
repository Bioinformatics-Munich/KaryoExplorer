#!/usr/bin/env Rscript

# Compute the summary report for different CN detected in the single line analysis
# find the centromere position
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
parser_plot$add_argument("--line", type = "character", help=" vector of genome studio name identifyng the line samples")
parser_plot$add_argument("--sample_name", type = "character", help="vector of name identifying the sample (patient)")
parser_plot$add_argument("--qs_thr", type = "double", default = 2, help="quality score threshold")
parser_plot$add_argument("--nSites_thr", type = "integer", default = 10,  help="number of sites thersold for CN1")
parser_plot$add_argument("--nHet_thr", type = "integer", default = 10, help="number of sites thersold for CN3")
parser_plot$add_argument("--CN_len_thr", type = "integer", default = 200, help="CN length thr in kb")
parser_plot$add_argument("--sex", type="character", default = "M", help = "sex of the sample (patient)")
parser_plot$add_argument("--width_plot", type="double", default = 10)
parser_plot$add_argument("--heigth_plot", type="double", default = 8)
parser_plot$add_argument("--outf", type="character", help = "Output file ")

args <- parser_plot$parse_args()

inputdir <- args$inputdir
fold_fun <- args$fold_fun
line <- args$line
qs_thr <- args$qs_thr
nSites_thr <- args$nSites_thr
nHet_thr <- args$nHet_thr
CN_len_thr <- args$CN_len_thr
sample_name <- args$sample_name
sex_sample <- args$sex
width_plot <- args$width_plot
outFile <- args$outf
heigth_plot <- args$heigth_plot


#### load function
source(file.path(fold_fun, 'gt_functions.R'))
source(file.path(fold_fun, 'plot_summary_cnv_function.R'))
####

# CNVs summary function
CNV_summary_function = function(chr_cnv_del, cnv_del, type="NA"){
  
  if (nrow(cnv_del)==0){
    return("NA")
  }

  resultvec = numeric(0)
  
  for (chr in chr_cnv_del){
    # subset
    df = cnv_del[cnv_del$Chr==chr,]
    
    result <- character(nrow(df))
    
    for (i in 1:nrow(df)) {
      if(df[i, "Chr"] == 23){
        chrname = "X"
      }else if (df[i, "Chr"] == 24){
        chrname = "Y"
      }else{
        chrname = df[i, "Chr"]
      }
      result[i] <- paste(type, " Chr", chrname, " (", df[i, "Len"], "bp)", sep = "")
    }
    resultvec=c(resultvec, paste(result, collapse = ", "))
  }
  return(resultvec)
}

#setwd(sprintf('%s/outdir_%s_%s/',inputdir, sample_name, line)) 

cnv_file <- file.path(inputdir,sprintf('summary.%s.tab', line))

M <- 10^6


############### compute the centromere from the file ####################
file_dat <- file.path(inputdir, paste0('dat.', line, '.tab'))

# compute the centromere position for the chromosome having it in the middle (exclude 13, 14, 15, special case for Y)
line_dat <- read.table(file_dat, header = FALSE, sep = '\t', stringsAsFactors = FALSE, colClasses = c(rep("integer", 2), rep("NULL", 2)))
colnames(line_dat) <- c('chr', 'pos')
# split according the chromosome
chr_id <- lapply(1:24, function(x) which(line_dat$chr == x))
pos_list <- lapply(chr_id, function(x) line_dat$pos[x])
names(pos_list) <- 1:24

initial_vect <- rep(FALSE, 24)
# chromosome with the centromere at the beginning
initial_vect[c(13:15,22)] <- TRUE
table_centr <- t(mapply(function(x,y) find_centromere(df_ch = x, initial = y), x = pos_list, y=initial_vect, SIMPLIFY = TRUE))
table_centr <- as.data.frame(table_centr)
colnames(table_centr) <- c('Start', 'End')

table_centr$Chr <- 1:24
#################################################################################################################

cnv_table <- read.csv(cnv_file, header = TRUE, sep = '\t', skip=4, stringsAsFactors = FALSE)
cnv_table <- cnv_table[,-1]
colnames(cnv_table) <-  c('Chr', 'Start', 'End', 'CN',  'QS', 'nSites', 'nHets')
  
# adjust for the centromere, add to the copy state 'centr'
cnv_chr_list <- vector(mode = 'list', length = 24)

# initalize
nrow_pred <- 0

for(chr in cnv_table$Chr){
  
  #print(chr)
  
  id_chr <-  which(cnv_table$Chr == chr)
  cnv_chr <- cnv_table[id_chr, ]
  
  # if the centromere is not at the beginning update
  if(!initial_vect[chr]){
    
    cnv_chr <- rbind(c(chr,table_centr$Start[chr], table_centr$End[chr], -1, 0,0,0), cnv_chr)
    cnv_chr$Start <- as.numeric(cnv_chr$Start)
    cnv_chr$End <- as.numeric(cnv_chr$End)
    
    ord_id <- order(cnv_chr$Start, decreasing = FALSE)
    
    cnv_chr <- cnv_chr[ord_id, ]
    
    id_pos <- which(cnv_chr[,4] == -1)
    # correct
    end_val <- cnv_chr$End[id_pos-1]
    CN_val <- cnv_chr[id_pos-1,4:7]
    cnv_chr$End[id_pos-1] <- cnv_chr$Start[id_pos] -1
    
    cnv_chr <- rbind(c(chr,cnv_chr$End[id_pos] + 1, end_val, as.numeric(CN_val)), cnv_chr)
    cnv_chr <- cnv_chr[ order(cnv_chr$Start, decreasing = FALSE), ]
    
  }
  
  # update number of rows to combine
  rownames(cnv_chr) <- (nrow_pred+1):(nrow(cnv_chr)+nrow_pred)
  nrow_pred <- nrow_pred + nrow(cnv_chr)
  
  # update
  cnv_chr_list[[chr]] <- cnv_chr
  
}

cnv_table <- do.call(rbind, cnv_chr_list)
cnv_table$Len <- cnv_table[,3] - cnv_table[,2]

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

# exclude also the centromeres
cnv_table$Filt[which(cnv_table[,4] == -1)] <- TRUE

id_centr <- which(cnv_table[,4] == -1)
# Add a label column for centromeres instead of converting CN to character
cnv_table$CN_Label <- as.character(cnv_table$CN)
cnv_table$CN_Label[id_centr] <- 'centr'

write.table(x = cnv_table, file = file.path(outFile, sprintf('summary_QC.%s.tab', line)), col.names = TRUE, quote = FALSE, row.names = FALSE, sep ='\t')

chr_lim <- ifelse(sex_sample == 'F',24,23)
cnv_filt<- cnv_table[-which(cnv_table$Filt),]
# plot CN1 or CN3
id_Autosomal <- which(cnv_filt[,4] != 2 & cnv_filt$Chr < chr_lim)

if(sex_sample == 'F'){
  
  id_Hap <-NULL  

}else{
  
  id_Hap <- which(cnv_filt[,4] != 1 & cnv_filt$Chr >= chr_lim)
  
}

cnv_detection <- cnv_filt[c(id_Autosomal, id_Hap),] 

df <- data.frame(Sample_name = rep(sample_name, 25*2), Chip_ID = rep(line, 25*2))
df$Chr <- rep(c(1:22, 'X', 'Y', 'tot'),2)
df$CN_200kb <- rep(0, 25*2)
df$CN_1Mb <- rep(0, 25*2)
df$CN_type <- c(rep('Deletion', 25), rep('Duplication', 25))  
df$CNVs <- c(rep('NA', 25), rep('NA', 25))  

# Create empty df with proper column structure
CNVdf=cnv_detection[0,]
# Add Type column (capitalized to match Python expectations)
CNVdf$Type=character(0)
# Add sample_name column  
CNVdf$sample_name=character(0)

if(nrow(cnv_detection)>0){
  
    cnv_del <- cnv_detection[which(cnv_detection[,4] == 1 & cnv_detection$Chr < chr_lim),]
    cnv_dup <- cnv_detection[which(cnv_detection[,4] == 3 & cnv_detection$Chr < chr_lim),]

    if(sex_sample == 'M'){
      
      cnv_del_Hap <- cnv_detection[which(cnv_detection[,4] == 0 & cnv_detection$Chr >= chr_lim), ]
      cnv_dup_Hap <- cnv_detection[which(cnv_detection[,4] > 1 & cnv_detection$Chr >= chr_lim),]
     
      cnv_del <- rbind(cnv_del, cnv_del_Hap)
      cnv_dup <- rbind(cnv_dup, cnv_dup_Hap)
    }

    cnv_del_cp = cnv_del
    if(nrow(cnv_del_cp)>0){
    cnv_del_cp$Type="Deletion"
    }
    
    cnv_dup_cp = cnv_dup
    if(nrow(cnv_dup_cp)>0){
    cnv_dup_cp$Type="Duplication"
    } 
    
    CNVdf=rbind(CNVdf,cnv_del_cp)
    CNVdf=rbind(CNVdf,cnv_dup_cp)
    
    chr_cnv_del <- sort(unique(cnv_del$Chr))
    chr_cnv_dup <- sort(unique(cnv_dup$Chr))
    
    n_cnv200_del <- sapply(chr_cnv_del, function(x) length(which(cnv_del$Chr == x)))

    n_cnv200_del_summary = CNV_summary_function(chr_cnv_del, cnv_del, "Deletion")
    
    n_cnv1_del <- sapply(chr_cnv_del, function(x) length(which(cnv_del$Chr == x & cnv_del$Len > 10^6)))
    
    n_cnv200_dup <- sapply(chr_cnv_dup, function(x) length(which(cnv_dup$Chr == x))) 
    
    n_cnv200_dup_summary = CNV_summary_function(chr_cnv_dup, cnv_dup, "Duplication")

    n_cnv1_dup <- sapply(chr_cnv_dup, function(x) length(which(cnv_dup$Chr == x & cnv_dup$Len > 10^6)))
    
    if(length(n_cnv200_del)>0){
      df$CN_200kb[chr_cnv_del] <- n_cnv200_del
      df$CN_200kb[25] <- sum(n_cnv200_del)  
      df$CNVs[chr_cnv_del] <- n_cnv200_del_summary
    }
    
    if(length(n_cnv200_dup)>0){
      df$CN_200kb[25 + chr_cnv_dup] <- n_cnv200_dup
      df$CN_200kb[50] <- sum(n_cnv200_dup)
      df$CNVs[25 + chr_cnv_dup] <- n_cnv200_dup_summary
    }
    
    if(length(n_cnv1_del)){
      df$CN_1Mb[chr_cnv_del] <- n_cnv1_del
      df$CN_1Mb[25] <- sum(n_cnv1_del)
    }
    
    if(length(n_cnv1_dup)){
      df$CN_1Mb[25 + chr_cnv_dup] <- n_cnv1_dup
      df$CN_1Mb[50] <- sum(n_cnv1_dup)
    }
  
}

# write table
write.table(x = df, file = file.path(outFile, sprintf('CNV_detection_%s.txt', sample_name)), quote = TRUE, sep = '\t', col.names = TRUE, row.names = FALSE)

# tsv table w/o tot
tsvtab = df[df$Chr != "tot",]
tsvtab = tsvtab[,c("Sample_name","Chr","CN_200kb","CN_1Mb","CN_type","CNVs"),]
write.table(x = tsvtab, file = file.path(outFile, sprintf('CNV_detection_chromosomes_%s.tsv', sample_name)), quote = TRUE, sep = '\t', col.names = TRUE, row.names = FALSE)

# write table
if (nrow(CNVdf)>0){
CNVdf$sample_name = sample_name
CNVdf$Filt=NULL
} else {
# Ensure proper column structure even when empty
CNVdf <- data.frame(
  Chr = character(0),
  Start = numeric(0), 
  End = numeric(0),
  CN = character(0),
  QS = numeric(0),
  nSites = numeric(0),
  nHets = numeric(0),
  Len = numeric(0),
  Type = character(0),
  sample_name = character(0),
  stringsAsFactors = FALSE
)
}
write.table(x = CNVdf, file = file.path(outFile, sprintf('CNV_detection_filt_%s.tsv', sample_name)), col.names = TRUE, quote = FALSE, row.names = FALSE, sep ='\t')


# make the plot for each ipsc
df_plot <- rbind(df[,-(4:5)], df[,-(4:5)])
df_plot$CN = c(df$CN_200kb, df$CN_1Mb)
df_plot$thr = c(rep('0.2 Mb', nrow(df)), rep('1 Mb', nrow(df)))
df_plot$Chr <- factor(df_plot$Chr, levels = c(1:22, 'X', 'Y', 'tot'))

# Save table
tab=df_plot[df_plot$Chr=="tot",c("Sample_name","CN_type","Chr","thr","CN")]
write.table(x = tab, file = paste(outFile, sprintf('/%s_CNV_single_tot.tsv', sample_name), sep = ''), quote = FALSE, sep = '\t', col.names = FALSE, row.names = FALSE)

# rm tot from the plot
df_plot = df_plot[df_plot$Chr != "tot", ]

plot_CN <- ggplot(data = df_plot, aes(x = Chr, y = CN))+
  geom_bar(stat = "identity", aes(fill = thr), colour = "black",  position=position_dodge())+
  theme_bw()+
  ggtitle(sprintf('CN detected in %s', sample_name))+
  ylab("N. of CN")+xlab("Chr")+
  facet_wrap(~CN_type, ncol = 1, scales = "free")+
  scale_fill_discrete(name = "length >")+
  theme(legend.text = element_text(size = 14), legend.title = element_text(size=16),
        axis.text=element_text(size=14),
        axis.title=element_text(size=16,face="bold"),
        strip.text = element_text(size=14), plot.title = element_text(hjust = 0, size = 17))

ggsave(filename = file.path(outFile, sprintf('CNV_detection_%s.pdf', sample_name)), plot = plot_CN, width = width_plot, height = heigth_plot)
ggsave(filename = file.path(outFile, sprintf('CNV_detection_%s.png', sample_name)), plot = plot_CN, width = width_plot, height = heigth_plot)
