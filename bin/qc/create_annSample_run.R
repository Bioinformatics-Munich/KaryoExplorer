#!/usr/bin/env Rscript

# Construct the txt annotation file for each comparison
# Written by Lucia Trastulla -- email: lucia_trastulla@psych.mpg.de

# note: output 1 column file, first element refers to pre reprogrammed, all the other elements to post reprogrammed

suppressPackageStartupMessages(library(argparse))

parser <- ArgumentParser(description = "construct sample annotation txt files" )

parser$add_argument("--sample_name", type = "character", help = "sample name (e.g. amish7)")
parser$add_argument("--ann_file", type = "character", help = "csv file with all the samples name and chip id, if coming from merged table, column table_type present")
parser$add_argument("--outf", type="character", help = "Output file [basename only]")

args <- parser$parse_args()
#############################
sample_name <- args$sample_name
ann_file <- args$ann_file
outFile <- args$outf

##############
# function from rlist package needed
list.flatten <- function (x, use.names = TRUE, classes = "ANY") 
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
##############


# NOTE: if ann_file more than one file, the first is the new the second is the old

# load the annotation file
ann_table <- read.csv(file = ann_file, header = TRUE, stringsAsFactors = FALSE, colClasses=c("Gender"="character"))

ann_table$SentrixBarcode_A <- as.character(ann_table$SentrixBarcode_A)
#ann_table[,2] <- ann_table$Type
# use the new sample names
#ann_table[,3] <- ann_table$Sample_name_new
#ann_table[,6] <- as.charachter(ann_table$Gender)
#print(ann_table[,6])

sel=c('ID', 'Type', 'Sample_name', 'SentrixBarcode_A', 'SentrixPosition_A', 'Gender')
ann_table_tot <- ann_table[,sel]

#ann_table_tot <- ann_table[,1:6]
#colnames(ann_table_tot) <- c('ID', 'Type', 'Sample_name', 'SentrixBarcode_A', 'SentrixPosition_A', 'Gender')
  
# ann_table_tot <- do.call(rbind, ann_table) 
# add a column indicating which is the id for the file
if(length(ann_table$table_type)>0){
  ann_table_tot$table_type <- ann_table$table_type
}else{
  ann_table_tot$table_type <- rep(sprintf('table_%i', 1), nrow(ann_table_tot))
}

# restrict the table to the sample considered
id_sample <- which(ann_table_tot$Sample_name == sample_name)
ann_table_sample <- ann_table_tot[id_sample,]

# create a new column with the correct code
# changed
# sample_id_new <- apply(ann_table_sample[,4:5], 1, function(x) paste(as.character(x[1]), as.character(x[2]), sep = "_"))
ann_table_sample$new_id <- ann_table_sample$ID

# if only 1 sample (single analysis) transform "POST" in "PRE" (used afterwards, not important for the analysis)
if(nrow(ann_table_sample) == 1){ann_table_sample$Type <- "PRE"}

# # if the original material (pre) is not in table_1, keep only the original material from the older table
# # (avoid comparison already taken in consideration)
id_pre <- which(ann_table_sample$Type == 'PRE')

# if more than one annotation table considered, avoid the comparison of pre and post (reprogramming) in the same table
more_table <- length(unique(ann_table_sample$table_type)) > 1
table_pre <- unique(sapply(id_pre, function(x) ann_table_sample$table_type[x]))
# cond_prog <- sapply(id_prog, function(x) ann_table_sample$table_type[x] != 'table_1')

id_pre_update <- vector(mode = 'list', length = length(table_pre))

if(more_table){
  
  ann_table_sample_pre <- vector(mode = 'list', length = length(table_pre))
  
  for(i in 1:length(table_pre)){
    
    ## corrected on 04/03/2019
    id_to_delete <- c(which(ann_table_sample$table_type == table_pre[i] & ann_table_sample$Type == 'POST'), 
                      which(ann_table_sample$table_type != table_pre[i] & ann_table_sample$Type == 'PRE')) 
    
    # reduce the df with only pre from the old file  
    if(length(id_to_delete)>0){
      
      ann_table_sample_pre[[i]] <- ann_table_sample[-id_to_delete,] 
      # update idpre
      id_pre_update[[i]] <- which(ann_table_sample_pre[[i]]$Type == 'PRE')
    }else{
      ann_table_sample_pre[[i]] <- ann_table_sample 
      id_pre_update[[i]] <- which(ann_table_sample_pre[[i]]$Type == 'PRE')
    }
      
  }
  
}else{
  
  id_pre_update <- list(id_pre)
  ann_table_sample_pre <- list(ann_table_sample)
}

# id_prog_update <- unlist(id_prog_update)




# if more than one progenitor, more than one file as output
# first element refers to progenitor, the other to ipsc

# new_file <- lapply(id_prog, function(x) c(ann_table_sample$new_id[x], ann_table_sample$new_id[-id_prog]))
new_file <- vector(mode = 'list', length = length(table_pre))

for(i in 1:length(table_pre)){
  
  new_file[[i]] <- lapply(1:length(id_pre_update[[i]]), function(x) c(ann_table_sample_pre[[i]]$new_id[id_pre_update[[i]][x]], ann_table_sample_pre[[i]]$new_id[-id_pre_update[[i]]]))
  # new_file[[i]] <- rbind(ann_table_sample_pre[[i]]$Gende[which(ann_table_sample_pre[[i]]$Type == 'PRE')], new_file[[i]])
  
}

# new_file <- lapply(1:length(table_prog), function(x) c(ann_table_sample_prog[[x]]$new_id[id_prog[x]], ann_table_sample_prog[[x]]$new_id[-id_prog[x]]))
new_file <- list.flatten(new_file)

for(i in 1:length(id_pre)){
  
  df <- data.frame(new_file[[i]], stringsAsFactors = F)
  df <- rbind(ann_table_sample_pre[[i]]$Gender[which(ann_table_sample_pre[[i]]$Type == 'PRE')], df)
  
  write.table(x = df, file = paste(outFile, sample_name, sprintf('_%i.txt', i), sep = ""), col.names = FALSE,  quote = FALSE, row.names = FALSE)
  
  # Save also as tab with sex, pre, post column one per row or (post=none for single)
  df2=NULL
  if (nrow(df)==2){
  df2 = data.frame(sex=df[1,1], pre=df[2,1], post="None")
  }else{
  for (z in 3:nrow(df)){
  df2=rbind(df2,data.frame(sex=df[1,1], pre=df[2,1], post=df[z,1]))
  }  
  }
  colnames(df2) = c("sex", "pre", "post")
  write.table(df2, file = paste(outFile, sample_name, sprintf('_%i.tsv', i), sep = ""), col.names = TRUE,  quote = FALSE, row.names = FALSE, sep="\t")


}
