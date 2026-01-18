#!/usr/bin/env Rscript

# Construct the annotation file as described in the manual section 3)
# Create separate files for single and paired annotation
# For single Reference column value needs to be string None
suppressPackageStartupMessages(library(argparse))

parser <- ArgumentParser(description = "construct sample annotation csv files" )

parser$add_argument("--samples_table", type = "character", help = "Sample table")
parser$add_argument("--sample_ref", type = "character", help = "tsv file with Sample and Reference")
#parser$add_argument("--outf", type="character", help = "Output file [basename only]")

args <- parser$parse_args()
#############################
samples_table <- args$samples_table
sample_ref_table <- args$sample_ref
# outFile <- args$outf

# Read the Samples Table
#samples_table="Samples Table.txt"
samples_tab <- read.table(samples_table, header = TRUE, stringsAsFactors = FALSE, sep = '\t', dec = '.')
#sample_ref_table = "sample_reference_table.tsv"
sample_ref_tab <- read.table(sample_ref_table, header = TRUE, stringsAsFactors = FALSE, sep = '\t', dec = '.')

# Merge tables
# If there are multiple comparisons to the same sample, multiple rows will be added, but only 1 PRE entry will be added
Samples_tab_merged = merge(samples_tab, sample_ref_tab, by.x = "Sample.ID", by.y="Sample")

# New table to the required format
newdf=NULL
newdfsingle=NULL

# Iter over rows
for (i in 1:nrow(Samples_tab_merged)){
  rowi = Samples_tab_merged[i,]
  
  # Get PRE and POST
  post=samples_tab[samples_tab$Sample.ID == rowi$Sample.ID,]
  
  if (rowi$Reference == "None"){
    pre=post
  }else{
    pre=samples_tab[samples_tab$Sample.ID == rowi$Reference,] 
  }

  # get sample name of pre
  sname=pre$Sample.ID

  # Single run if Reference == None
  if (rowi$Reference == "None"){
  # Add sample as PRE
  newdfsingle=rbind(newdfsingle,data.frame(ID=rowi$Sample.ID, Type="PRE", Sample_name=sname,SentrixBarcode_A=post$Array.Info.Sentrix.ID, SentrixPosition_A=post$Array.Info.Sentrix.Position, Note=""))
   next
  }  

  # Single run if Sample==Reference
  if (post$Sample.ID == pre$Sample.ID){
  # Add sample as PRE
  newdfsingle=rbind(newdfsingle,data.frame(ID=rowi$Sample.ID, Type="PRE", Sample_name=sname,SentrixBarcode_A=post$Array.Info.Sentrix.ID, SentrixPosition_A=post$Array.Info.Sentrix.Position, Note=""))
    next
  }

  # Skip if pre is already in the table
  if (pre$Sample.ID %in% newdf[newdf$Type=="PRE",]$ID){
    newdf=rbind(newdf,data.frame(ID=rowi$Sample.ID, Type="POST", Sample_name=sname,SentrixBarcode_A=post$Array.Info.Sentrix.ID, SentrixPosition_A=post$Array.Info.Sentrix.Position, Note=""))
    
  }else
  {
  newdf=rbind(newdf,data.frame(ID=rowi$Sample.ID, Type="POST", Sample_name=sname,SentrixBarcode_A=post$Array.Info.Sentrix.ID, SentrixPosition_A=post$Array.Info.Sentrix.Position, Note=""))
  newdf=rbind(newdf,data.frame(ID=rowi$Reference, Type="PRE", Sample_name=sname,SentrixBarcode_A=pre$Array.Info.Sentrix.ID, SentrixPosition_A=pre$Array.Info.Sentrix.Position, Note=""))
  }
}

# Save table
write.csv(newdf,"3_annotation_file.paired.csv", row.names = F)
write.csv(newdfsingle,"3_annotation_file.single.csv", row.names = F)
