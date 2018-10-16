# Fourier Features
num.ts <- length(unique(data[, c("StoreID")]))
ts.length <- nrow(data)/num.ts  

t <- (index(data) - 1) %% ts.length %% seasonality 

for (s in 1:4){
  data[[paste("FreqCos", toString(s), sep="")]] = cos(t*2*pi*s/seasonality)
  data[[paste("FreqSin", toString(s), sep="")]] = sin(t*2*pi*s/seasonality)
}