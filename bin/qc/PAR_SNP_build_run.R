#!/usr/bin/env Rscript

# Build the par_snp txt file based on the manifest file
# Written by Lucia Trastulla -- email: lucia_trastulla@psych.mpg.de

suppressPackageStartupMessages(library(argparse))

parser <- ArgumentParser(description = "Write PAR file for each SNP in the manifest file" )

parser$add_argument("--manifest_file", type = "character", help = ".csv file, manifest file used in GenomeStudio")
parser$add_argument("--n_header_line", type = "integer", default = 7, help = "n. of header lines to skip")
parser$add_argument("--PAR_file", type = "character", help = ".txt file, PAR built from https://www.ncbi.nlm.nih.gov/assembly/GCF_000001405.13/")
parser$add_argument("--outf", type = "character", default = '.', help = "outer fold")

args <- parser$parse_args()
#############################

manifest_file <- args$manifest_file
n_header_line <- args$n_header_line
PAR_file <- args$PAR_file
outFold <- args$outf


# load the bpm file
manifest <- read.csv(manifest_file, header = TRUE, skip = n_header_line, sep = ',', stringsAsFactors = FALSE)

# delete last rows
id_rm <- which(manifest$IlmnID == '[Controls]')
if(length(id_rm) > 0){
   manifest <- manifest[-(id_rm:nrow(manifest)), ]
}

SNP_name <- manifest$Name
chr_manifest <- manifest$Chr
position_manifest <- manifest$MapInfo

df <- data.frame(name = SNP_name, chr = chr_manifest, pos = position_manifest, stringsAsFactors = FALSE)

# load the PAR table (build from https://www.ncbi.nlm.nih.gov/assembly/GCF_000001405.13/)
PAR_table <- read.table(PAR_file, header = TRUE, skip = 1, sep = '\t', stringsAsFactors = FALSE)


# the resulting table has to have the same length of SNP_name with two column:
# Name: SNP_name
# PAR: 0 if it's not in a PAR region, 1 otherwise

df_PAR <- data.frame(Name = df$name, stringsAsFactors = FALSE)
PAR_vect <- rep(0, length(SNP_name))

id_chrX <- which(df$chr == "X")
posX <- df$pos[id_chrX] 
id_chrY <- which(df$chr == "Y")
posY <- df$pos[id_chrY] 

posX_PAR <- vector(mode = 'list')
posY_PAR <- vector(mode = 'list')

for(i in 1:length(unique(PAR_table$PAR_type))){
  
  chr_X_table <- subset(PAR_table, Chr == 'X')
  posX_PAR[[i]] <- posX[which(posX <= chr_X_table$End[i] & posX >= chr_X_table$Start[i])]
  
  chr_Y_table <- subset(PAR_table, Chr == 'Y')
  posY_PAR[[i]] <- posY[which(posY <= chr_Y_table$End[i] & posY >= chr_Y_table$Start[i])]
  
}

posX_PAR <- unlist(posX_PAR)
posY_PAR <- unlist(posY_PAR)


# find the original id
if(length(posX_PAR)>0){
  
  id_PARX <- sapply(posX_PAR, function(x) which(df$pos == x & df$chr == 'X'))  
  PAR_vect[id_PARX] <- 1
  
}

if(length(posY_PAR)>0){
  
  id_PARY <- sapply(posY_PAR, function(y) which(df$pos == y & df$chr == 'Y'))  
  PAR_vect[id_PARY] <- 1

}


df_PAR$PAR <- PAR_vect


# save
write.table(file = file.path(outFold, 'PAR_SNPs.txt'), x = df_PAR, sep = "\t", row.names = FALSE, col.names = TRUE)

