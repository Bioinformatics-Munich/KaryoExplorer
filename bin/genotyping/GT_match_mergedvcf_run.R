# Compute the heatmap for the GT match and update the annotation file with the GT match
# Written by Lucia Trastulla -- email: lucia_trastulla@psych.mpg.de

suppressPackageStartupMessages(library(argparse))
suppressPackageStartupMessages(library('ComplexHeatmap'))
suppressPackageStartupMessages(library('RColorBrewer'))
suppressPackageStartupMessages(library('circlize'))
suppressPackageStartupMessages(library('doParallel'))


parser <- ArgumentParser(description = "Merge two annotation files and compute the GT match" )

parser$add_argument("--fold_fun", type = "character", nargs = '*', help = "folder containing GT")
parser$add_argument("--ann_file", type = "character", nargs = '*', help = "more than one file merge them with the annotation")
parser$add_argument("--GT_file", type = "character", nargs = '*', help = ".txt file, GT file for each genotype, complete")
parser$add_argument("--samples_name", type = "character", nargs = '*', help = "samples name to be considered")
parser$add_argument("--comm_SNPs_file", type = "character", nargs = '*', help = ".txt file, common SNPs")
parser$add_argument("--ncores", type = "integer", nargs = '*', help = "cores")
parser$add_argument("--outf", type="character", help = "Output file [basename only]")


#######
args <- parser$parse_args()

fold_fun <- args$fold_fun
ann_file <- args$ann_file
GT_file <- args$GT_file
samples_name <- args$samples_name
comm_SNPs_file <- args$comm_SNPs_file
ncores <- args$ncores
outFile <- args$outf
#######
source(paste(fold_fun, 'gt_functions.R', sep = ""))
#######

comm_SNPs <- read.table(comm_SNPs_file, header = FALSE, stringsAsFactors = FALSE, sep = '\t') 
GT_table_list <- lapply(GT_file, function(x) read.table(x, header = TRUE, sep = '\t', stringsAsFactors = FALSE))

ann_table <- lapply(ann_file, function(x) read.csv(file = x, header = TRUE, stringsAsFactors = FALSE, sep = ','))

for(i in 1:length(ann_table)){
  
  ann_table[[i]][,2] <- ann_table[[i]]$Type
  ann_table[[i]][,3] <- ann_table[[i]]$Sample_name
  ann_table[[i]][,6] <- ann_table[[i]]$Gender
  
  ann_table[[i]] <- ann_table[[i]][,1:6]
  colnames(ann_table[[i]]) <- c('ID', 'Type', 'Sample_name', 'SentrixBarcode_A', 'SentrixPosition_A', 'Gender')
  
}

ann_table_tot <- do.call(rbind, ann_table) 

# add a column indicating which is the id for the file
len_table <- sapply(ann_table, nrow)
ann_table_tot$table_type <- unlist(sapply(1:length(ann_table), function(x) rep(sprintf('table_%i', x), len_table[x])))

# restrict the table to the sample considered
id_samples <- which(ann_table_tot$Sample_name %in% samples_name)
ann_table_samples <- ann_table_tot[id_samples,]

# create a new column with the correct code
sample_id_new <- apply(ann_table_samples[,4:5], 1, function(x) paste(x[1], x[2], sep = "_"))
ann_table_samples$sample_complete_id <- sample_id_new


### consider only the common SNPs
GT_table_red_list <- lapply(GT_table_list, function(x) x[which(x$ID %in% comm_SNPs$V1),])
# the order of the snps may not be correct, order by chr and SNP position
for(i in 1:length(GT_file)){
  
  GT_table_red_list[[i]]$CHROM <- as.numeric(GT_table_red_list[[i]]$CHROM)
  
  # order chr
  GT_table_red_list[[i]] <- GT_table_red_list[[i]][order(GT_table_red_list[[i]]$CHROM),]  
  pos_skip <-  c(0,cumsum(table(GT_table_red_list[[i]]$CHROM))[-24])
  pos_skip <- unname(pos_skip)
  
  # order snp pos
  new_ord <- sapply(1:24, function(x) order(GT_table_red_list[[i]]$POS[GT_table_red_list[[i]]$CHROM == x]))
  new_ord <- unlist(mapply(function(x,y) x + y, x = new_ord, y = pos_skip))       
  GT_table_red_list[[i]] <- GT_table_red_list[[i]][new_ord,]
  
}


# the SNP info is the same in all the files
info <- GT_table_red_list[[1]][,1:3]
GT_table_red_list <- lapply(GT_table_red_list, function(x) x[,-(1:3)])

GT_table_tot <- do.call(cbind, GT_table_red_list)
GT_table_tot <- cbind(info, GT_table_tot)
# correct sample names (delete X in front)
samples_name_GTtable <- colnames(GT_table_tot[,-(1:3)])
samples_name_GTtable <- sapply(samples_name_GTtable, function(x) strsplit(x, "X")[[1]][2])
names(samples_name_GTtable) <- NULL


# restrict the GT table only to the samples considered
id <- which(samples_name_GTtable %in% ann_table_samples$sample_complete_id)
GT_table_samples <- GT_table_tot[,id + 3]

# compare GT
registerDoParallel(cores = ncores)
nsamples <- ncol(GT_table_samples)

GT_comp <- foreach(i = 1:(nsamples-1))%dopar%{
  
  print(i)
  id_in <- rep(i, nsamples-i)
  id_fin <- (i+1):nsamples
  
  mapply(function(x,y) compareGT(GT_s1 = GT_table_samples[,x], GT_s2 = GT_table_samples[,y]), x = id_in, y = id_fin)
}

GT_comp_vect <- unlist(GT_comp)

GT_comp <- matrix(0, nrow=nsamples, ncol=nsamples) 
GT_comp[lower.tri(GT_comp, diag = FALSE)] <- GT_comp_vect 
GT_comp <- GT_comp + t(GT_comp) - diag(diag(GT_comp)) 
diag(GT_comp) <- 1

# add samples name
colnames(GT_comp) <- sapply(colnames(GT_table_samples), function(x) strsplit(x, "X")[[1]][2])
rownames(GT_comp) <- sapply(colnames(GT_table_samples), function(x) strsplit(x, "X")[[1]][2])

write.table(x = GT_comp, file = paste(outFile, 'GT_comp.txt', sep = ''), dec = '.', sep = '\t', quote = FALSE, row.names = TRUE, col.names = TRUE)


########################################################
# heatmap
diss <- as.dist(1-GT_comp)
# str(diss)
hclust_sample <- hclust(d = diss, method = 'ward.D')

P <- length(samples_name)

##### set colours #####
coul <- brewer.pal(9, "BuPu") 
coul <- colorRampPalette(coul)(10)
coul[1] <- 'white'
nbins <- 10
######################

# create the colour palette
col_name <- brewer.pal(n = 8, name = 'Paired')
col_name <- colorRampPalette(col_name)(P)
if(P <= length(col_name)){
  
  col_name <- col_name[1:P]
  
}else{
  
  n_rep <- ceiling(P/8)
  col_name <- rep(col_name, n_rep)
  col_name <- col_name[1:P]
  
}

col_match <- col_name
names(col_match) <- samples_name


ord_samples <- sapply(colnames(GT_comp) ,function(i) which(i  == ann_table_samples$sample_complete_id))
df_samples <- data.frame(Sample_name = ann_table_samples$Sample_name[ord_samples])


ha = HeatmapAnnotation(df = df_samples, col = list(Sample_name = col_match),  
                       annotation_legend_param = list(Sample_name = list(ncol = 1, title = "Samples", title_gp = gpar(fontsize = 15, fontface = "bold"), title_position = "topcenter",                                                       
                       grid_height = unit(8, "mm"), gap = unit(4, "mm"), labels_gp = gpar(fontsize = 15))))


hm <- Heatmap(GT_comp, name = "GT match",  cluster_rows = hclust_sample, cluster_columns = hclust_sample, row_dend_reorder = FALSE, column_dend_reorder = FALSE, top_annotation = ha,
              show_row_names = FALSE, show_column_names = TRUE, show_row_dend = FALSE, show_column_dend = TRUE,
              column_title_gp = gpar(fontsize = 25, fontface = "bold"), col = colorRamp2(seq(min(min(GT_comp), 0.73), 1, length = nbins), coul), heatmap_legend_param = list(color_bar = "continuous", legend_height = unit(10, "cm"), labels_gp = gpar(fontsize = 17), title_gp = gpar(fontsize = 15, fontface = "bold")))

GT_comp_name <- GT_comp
colnames(GT_comp_name) <- ann_table_samples$ID[ord_samples]
rownames(GT_comp_name) <- ann_table_samples$ID[ord_samples]

hm_name <- Heatmap(GT_comp_name, name = "GT match",  cluster_rows = hclust_sample, cluster_columns = hclust_sample, row_dend_reorder = FALSE, column_dend_reorder = FALSE, top_annotation = ha,
              show_row_names = FALSE, show_column_names = TRUE, show_row_dend = FALSE, show_column_dend = TRUE,
              column_title_gp = gpar(fontsize = 25, fontface = "bold"), col = colorRamp2(seq(min(min(GT_comp_name), 0.73), 1, length = nbins), coul), heatmap_legend_param = list(color_bar = "continuous", legend_height = unit(10, "cm"), labels_gp = gpar(fontsize = 17), title_gp = gpar(fontsize = 15, fontface = "bold")))


padding = unit.c(unit(9, "mm"), unit(0.5, "cm"), unit(c(3, 3), "mm"))

png(paste(outFile, 'hm_GT.png', sep = ""), width = 3000, height = 3000, res = 300, pointsize = 12)
draw(hm, padding = padding)
dev.off()

pdf(paste(outFile, 'hm_GT.pdf', sep = ""), width = 10, height = 10)
draw(hm, padding = padding)
dev.off()

padding = unit.c(unit(20, "mm"), unit(0.5, "cm"), unit(c(3, 3), "mm"))

png(paste(outFile, 'hm_GT_samplename.png', sep = ""), width = 3000, height = 3000, res = 300, pointsize = 12)
draw(hm_name, padding = padding)
dev.off()


pdf(paste(outFile, 'hm_GT_samplename.pdf', sep = ""), width = 10, height = 10)
draw(hm_name, padding = padding)
dev.off()


### check for mismatch
# same element should have a match higher than 96%, if a sample is of poor quality labelled in a different way
#############
list.flatten = function (x, use.names = TRUE, classes = "ANY") 
{
  len <- sum(rapply(x, function(x) 1L, classes = classes))
  y <- vector("list", len)
  i <- 0L
  items <- rapply(x, function(x) {
    i <<- i + 1L
    y[[i]] <<- x
    TRUE
  }, classes = classes)
  if (use.names && !is.null(nm <- names(items))) 
    names(y) <- nm
  y
}

#############

gr_names <- NULL
logic_vect <- rep(TRUE, nrow(GT_comp))
names_samples <- rownames(GT_comp)

for(i in 1:nrow(GT_comp)){
  
  if(logic_vect[i]){
    
    id <- which(GT_comp[i,] > 0.96)
    id <- id[which(logic_vect[id])]
    # print(names_samples[id])
    gr_names <- list.flatten(list(gr_names, names_samples[id]))
    logic_vect[id] <- F 
    
  }
  
}


# create a file that match the orignal sample annotations and the one obtained from GT match
# if they are concordant use the original name, otherwise reassign
ann_table_samples$Sample_name_new <- rep(0, nrow(ann_table_samples))

count <- 0

for(i in 1:length(gr_names)){
  
  id <- which(ann_table_samples$sample_complete_id %in% gr_names[[i]])
  cond1 <- length(unique(ann_table_samples$Sample_name[id]))==1 # check if the matching one have the same name
  cond2 <- length(which(ann_table_samples$Sample_name %in% ann_table_samples$Sample_name[id])) == length(id) # check if the sample considered are labelled with other ones
  cond <- cond1 & cond2 # both must be TRUE
  
  if(cond){ann_table_samples$Sample_name_new[id] <- ann_table_samples$Sample_name[id]}
  
  else{
    count <- count+1
    ann_table_samples$Sample_name_new[id] <- sprintf('MISMATCHED_SAMPLE_%i', count)}
  
}


# save the table
write.table(x = ann_table_samples, file = paste(outFile, 'annotation_file_GTmatch.csv', sep = ''), dec = '.', sep = ',', quote = FALSE, row.names = FALSE)

