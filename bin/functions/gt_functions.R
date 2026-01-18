# Auxiliary functions for the genotyping analysis
# Written by Lucia Trastulla -- email: lucia_trastulla@psych.mpg.de

# compare two genotypes
# Optimized version: vectorized comparison while preserving original logic
compareGT <- function(GT_s1, GT_s2){
  
  cond_stop <- (length(GT_s1) == length(GT_s2))
  if(!cond_stop){stop('not same length')}
  
  # Direct vector comparison - much faster than factor-based intersection
  # This preserves the original logic: count all matching positions (including NC==NC)
  # divided by total positions
  return(sum(GT_s1 == GT_s2) / length(GT_s1))
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
