read.data <- function(path = 'E:/Cortana Competition'){
  ## Read the csv file
  filePath <- file.path(path, 'Loan Granting Binary Classification.csv')
  loan.data <- read.csv(filePath, header = TRUE, 
                        stringsAsFactors = FALSE)
  }


## Features to plot
name.list <- function(x) {
  names <- names(x)
  len <- length(names)
  names[-len]
}

## Bar plot of categorical features
bar.income <- function(x){
  library(ggplot2)
  if(!is.numeric(Income[,x])) {
    capture.output(
      plot( ggplot(Income, aes_string(x)) +
              geom_bar() + 
              facet_grid(. ~ income) + 
              ggtitle(paste("Counts of income level by",x))))
  }}



## Create Box plot of numeric features
box.income <- function(x){
  library(ggplot2)
  if(is.numeric(Income[,x])) {
    capture.output(
      plot( ggplot(Income, aes_string('income', x)) +
              geom_boxplot() +
              ggtitle(paste("Counts of income level by",x))))
  }}


bar.plot <- function(x, cut = 200){
  require(ggplot2)
  if(is.factor(loan.data[, x]) | is.character(loan.data[, x]) & (x != 'Loan.Status') & (x != 'Loan.ID') & (x != 'Customer.ID') & (x != 'Maximum.Open.Credit') & (x != 'Monthly.Debt') ){
    colList = c('Loan.Status', x)
    loan.data[, colList] = lapply(loan.data[, colList], as.factor)
    sums <- summary(loan.data[, x], counts = n())
    msk <- names(sums[which(sums > cut)])
    tmp <- loan.data[loan.data[, x] %in% msk, colList]
    capture.output(
      if(strsplit(x, '[-]')[[1]][1] == x){
        g <- ggplot(tmp, aes_string(x)) +
          geom_bar() +
          facet_grid(. ~ Loan.Status) +
          ggtitle(paste('Loan.Status by level of', x))
        print(g) 
      } 
    )    
  } 
}
