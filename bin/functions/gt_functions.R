# Auxiliary functions for the genotyping analysis
# Written by Lucia Trastulla -- email: lucia_trastulla@psych.mpg.de

# compare two genotypes
compareGT <- function(GT_s1,GT_s2){
  
  cond_stop <- (length(GT_s1) == length(GT_s2))
  if(!cond_stop){stop('not same length')}
  
  GT_s1 <- as.factor(GT_s1)
  GT_s2 <- as.factor(GT_s2)
  
  level_GT <- levels(GT_s1)
  intersect_GT <- vector(mode = 'list', length = length(level_GT))
  
  for (i in 1:length(level_GT)){
    
    id_1 <- which(GT_s1 == level_GT[i])
    id_2 <- which(GT_s2 == level_GT[i])
    
    intersect_GT[[i]] <- intersect(id_1,id_2)   
  }
  
  # percetange of same GT
  return(sum(sapply(intersect_GT, length))/length(GT_s1))
  
  
}


# function to decide a threshold for the SNP call rate based on the number of samples considered
thr_SNPscallrate_fun <- function(nSamples){
  
  # linear growing from 24 to 500, then constant rate
  x = c(24, 500)
  y = c(0.79, 0.98)
  
  model <- lm(y~x)
  res <- ifelse(nSamples > 500, 0.98, model$coefficients[2]*nSamples + model$coefficients[1] )
  
  return(res)
  
}
