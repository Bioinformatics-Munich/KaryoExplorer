# auxiliary functions for the QC of CNV and the plots
# Written by Lucia Trastulla -- email: lucia_trastulla@psych.mpg.de


find_centromere <- function(df_ch, initial = FALSE){
  
  centr_coord = rep(NA,2)

  len <- length(df_ch)
  if (len > 0) {
    diff_pos <- df_ch[-1] - df_ch[-len]
    id_max_gap <- which.max(diff_pos)
    centr_coord <- df_ch[(id_max_gap):(id_max_gap+1)] + c(1,-1)
    if(initial){centr_coord <- rep(0,2)}
  }
  return(centr_coord)
}

transform_tab <- function(file_name, QC = FALSE, M = 10^6, gap_df = NULL, sex_sample = 'M'){

  if(QC){
    
    sample_cnv <- read.table(file_name, header = TRUE, sep = '\t', stringsAsFactors = FALSE)
    colnames(sample_cnv) <- c('Chromosome', 'Start', 'End', 'CNS', 'Quality', 'nSites', 'nHETs', 'Len', 'Filt')
    
    # if not ordered from 1 to 24, adjust
    ord <- order(sample_cnv$Chromosome)
    sample_cnv <- sample_cnv[ord,]
    
    # substitute the CN in correspondence of Filt == TRUE with 2
    sample_cnv[which(sample_cnv$Filt & sample_cnv$Chromosome <= 22),4] <- 2
    
    if(sex_sample == 'M'){
      
      sample_cnv[which(sample_cnv$Filt & sample_cnv$Chromosome > 22),4] <- 1
    
    }else{
      
      sample_cnv[which(sample_cnv$Filt & sample_cnv$Chromosome == 23),4] <- 2
      sample_cnv[which(sample_cnv$Filt & sample_cnv$Chromosome == 24),4] <- 0
    }
    
  }else{
    
    # file_name <- paste('summary.', sample_name, '.tab', sep = "")
    sample_cnv <- read.csv(file_name, header = FALSE, sep = '\t', skip=1, stringsAsFactors = FALSE)
  
    # exclude the first column (contain only RG)
    sample_cnv <- sample_cnv[,-1]
    
    # insert colnames
    colnames(sample_cnv) <- c('Chromosome', 'Start', 'End', 'CNS', 'Quality', 'nSites', 'nHETs')
  
  }
  
 
  
  chr_name <- dimnames(table(sample_cnv$Chromosome))[[1]]
  chr_id <- lapply(chr_name, function(x) which(sample_cnv$Chromosome == x))

  # # save the position and the CN state
  # # divide the position by 10^6 (M)
  #
  # position <- lapply(chr_id, function(x) as.vector(t(sample_cnv[x,2:3]))/M)
  # CNS <- as.vector(sapply(sample_cnv$CNS, function(x) rep(x, 2)))

  # compute start and end, divide per chromosome
  start <- lapply(chr_id, function(x) sample_cnv[x,2]/M)
  end <- lapply(chr_id, function(x) sample_cnv[x,3]/M)

  # combine in a single vector
  last_val <- sapply(end, function(x) x[length(x)])
  add_vect <- c(0, cumsum(last_val)[-length(last_val)])

  start_continue <- unlist(mapply(function(x,y) x + y, x = start, y=add_vect))
  end_continue <- unlist(mapply(function(x,y) x + y, x = end, y=add_vect))

  # create start and end also for the gap file, produce this table only if the gap_df object is not null
  if (!is.null(gap_df)){

    start_continue_gap <- gap_df$start + add_vect
    end_continue_gap <- gap_df$end + add_vect

    gap_df_new <- gap_df
    gap_df_new$start <- start_continue_gap
    gap_df_new$end <- end_continue_gap

  }


  # # create a unique vector for the position, correct numbering
  # last_val_position <- sapply(position, function(x) x[length(x)])
  # add_vect <- c(0, cumsum(last_val_position)[-length(last_val_position)])
  # position_continue <- unlist(mapply(function(x,y) x + y, x = position, y=add_vect))

  sample_cnv_combined <- data.frame(CNS = sample_cnv$CNS)
  sample_cnv_combined$start <- start_continue
  sample_cnv_combined$end <- end_continue
  sample_cnv_combined$chr <- sample_cnv$Chromosome

  if (!is.null(gap_df)){return(list( gap_df_new = gap_df_new, add_vect = add_vect ))
    }else{ return( sample_cnv_combined)}


}






# sample_cnv <- transform_tab(sample_name = '27_201216350195_R02C01')


combine_pos <- function(cnv_df_fibr, cnv_df_ipsc, centromere_df, M = 10^6){
  
  start_ipsc <- lapply(cnv_df_ipsc, function(x) x$start)
  start_fibr <- cnv_df_fibr$start
  start_centr <- centromere_df$start[-c(13:15,22)]
  # to be added to the end column
  end_fromstart_centr <- start_centr - 1/M  
  
  end_ipsc <- lapply(cnv_df_ipsc, function(x) x$end)
  end_fibr <- cnv_df_fibr$end
  end_centr <- centromere_df$end[-c(13:15,22)]
  # to be added to the start column
  start_fromend_centr <- end_centr + 1/M  
  
  # assembly
  start_ipsc_all <- unique(sort(do.call(c, start_ipsc)))
  start_all <- unique(sort(c(start_ipsc_all, start_fibr, start_centr, start_fromend_centr)))
  
  end_ipsc_all <- unique(sort(do.call(c, end_ipsc)))
  end_all <- unique(sort(c(end_ipsc_all, end_fibr, end_centr, end_fromstart_centr)))
  
  
  # #############################
  # pos_all <- sort(c(start_all, end_all))
  # pos_all <- matrix(pos_all, byrow = TRUE, ncol=2)
  # #############################
  
   
  #cnv_df_fibr_new <- data.frame(start = start_all, end = end_all)
  #n_row <- nrow(cnv_df_fibr_new)

  
  enlarge <- function(cnv_df, start, end, start_centr, fibr = FALSE){
  
    n_row <- length(start)
    
    CNS <- vector(mode = 'numeric', length = n_row)
    chr <- vector(mode = 'numeric', length = n_row)
    
    for (i in 1:nrow(cnv_df)){
      
      id_in <- which(cnv_df$start[i] == start)
      #print(paste(id_in, 'in'))
      id_fin <- which(cnv_df$end[i] == end)
      #print(paste(id_fin, 'fin'))
      
      CNS[id_in:id_fin] <- cnv_df$CNS[i]
      chr[id_in:id_fin] <- cnv_df$chr[i]
      
    } 
    
    # adjust for the centromere
    id_centr <- sapply(start_centr, function(x) which(start == x))
    # # the same as
    # sapply(end_centr, function(x) which(end == x))
    CNS[unlist(id_centr)] <- -1
    if (fibr){ 
      CNS[unlist(id_centr)] <- '-1'
      CNS <- as.character(CNS)
      # print(CNS)
    }
    # -1 for CNS indicate the centromere position
    
    
    
  df_new <- data.frame(chr = chr, start = start, end = end, CNS = CNS, stringsAsFactors = FALSE )
  
  return(df_new)  
  
  }
  
  cnv_df_fibr_new <- enlarge(cnv_df = cnv_df_fibr, start = start_all, end = end_all, start_centr = start_centr, fibr = TRUE)
  # print(str(cnv_df_fibr_new))
  cnv_df_ipsc_new <- lapply(cnv_df_ipsc, function(x) enlarge(x, start = start_all, end = end_all,  start_centr = start_centr))
  
  return(list(cnv_df_fibr_new, cnv_df_ipsc_new))
  
}


change_CNS_centromere <- function(df, sex){
  
  # search the position of the sex chromosomes
  id_X <- which(df$chr == 23)
  id_Y <- which(df$chr == 24)
  
  # find centromere position
  id_centr <- which(as.numeric(as.character(df$CNS[-c(id_X, id_Y)]))< 0 )
  
  id_centr_X <- which(as.numeric(as.character(df$CNS[id_X]))< 0)
  id_centr_Y <- which(as.numeric(as.character(df$CNS[id_Y]))< 0)
  df$CNS[id_centr] <- 2
  
  if(sex == 'M'){
    df$CNS[id_X][id_centr_X] <- 1
    df$CNS[id_Y][id_centr_Y] <- 1
  }else{
    
    df$CNS[id_X][id_centr_X] <- 2
    df$CNS[id_Y][id_centr_Y] <- 0
    
  
  }
  
  
  return(df)
  
  
}


# combine the fibroblast files: 
# if a region overlap add a "overlap" color
combine_pre_tab <- function(cnv_df_fibr){
  
  
  start_fibr <- lapply(cnv_df_fibr, function(x) x$start)
  start_fibr_all <- unique(sort(do.call(c, start_fibr)))
  
  end_fibr <- lapply(cnv_df_fibr, function(x) x$end)
  end_fibr_all <- unique(sort(do.call(c, end_fibr)))
  
  cnv_df_fibr_new <- data.frame(start = start_fibr_all, end = end_fibr_all)
  n_row <- nrow(cnv_df_fibr_new)

  enlarge <- function(cnv_df, start, end){
    
    n_row <- length(start)
    
    CNS <- vector(mode = 'numeric', length = n_row)
    chr <- vector(mode = 'numeric', length = n_row)
    
    for (i in 1:nrow(cnv_df)){
      
      id_in <- which(cnv_df$start[i] == start)
      #print(paste(id_in, 'in'))
      id_fin <- which(cnv_df$end[i] == end)
      #print(paste(id_fin, 'fin'))
      
      CNS[id_in:id_fin] <- cnv_df$CNS[i]
      chr[id_in:id_fin] <- cnv_df$chr[i]
      
    } 
    
    
    df_new <- data.frame(chr = chr, start = start, end = end, CNS = CNS )
    
    return(df_new)  
    
  }
  
  cnv_df_fibr_new <- lapply(cnv_df_fibr, function(x) enlarge(x, start = start_fibr_all, end = end_fibr_all))
  
  CNS_fibr <- sapply(cnv_df_fibr_new, function(x) x$CNS )
  id_match_CNS <- apply(CNS_fibr,1, function(x) length(unique(x)) == 1)
  
  cnv_df_fibr_tot <- cnv_df_fibr_new[[1]]
  
  
  # save the different values:
  notmatched_CNS <- CNS_fibr[!id_match_CNS,]
  
  string_notmatched <- c()
  for(i in 1:nrow(notmatched_CNS)){
    
    temp <- notmatched_CNS[i,1]
    
    for(j in 2:ncol(notmatched_CNS)){
      temp <- paste(temp, notmatched_CNS[i,j], sep = ',')
    }
    
    string_notmatched[i] <- temp
  
  }
  
  # string_notmatched <- apply(notmatched_CNS,1, function(x) do.call(paste, as.list(x)))
  
  cnv_df_fibr_tot$CNS[!id_match_CNS] <- string_notmatched
  
  return(cnv_df_fibr_tot)
}





