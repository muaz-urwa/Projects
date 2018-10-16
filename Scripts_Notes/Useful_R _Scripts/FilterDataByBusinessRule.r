businessrule <- function(data){  
  tsvalues <- data$Sales
  
  # Select Eligible Time Series:
  # Rule 1: if a time series has no more than <min.length> non-NA values, discard
  if (sum(!is.na(tsvalues)) < min.length) return(c(judge = 1))
  
  # Rule 2: if a time series has any sales quantity <= value.threshold , discard
  if (length(tsvalues[tsvalues > value.threshold]) != length(tsvalues)) return(c(judge = 2))
 
  return(c(judge = 0))
}

judge.all <- ddply(data, .(Store), businessrule)
judge.good <- as.data.frame(judge.all[judge.all$judge == 0, c("Store")])
colnames(judge.good) <- c("Store")
data.good <- join(data, judge.good, by = "Store", type = "inner")
