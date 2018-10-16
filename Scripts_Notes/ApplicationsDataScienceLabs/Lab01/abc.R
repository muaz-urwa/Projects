to.POSIXct <- function(year, monthNumber){
  ## Function to create a POSIXct time series 
  ## object from a year.month format
  
  ## Create a character vector from the numeric input
  dateStr <- paste(as.character(year), "-",
                   as.character(monthNumber), "-",
                   "01", sep = "")
  ## Return the POSIXct time series object
  as.POSIXct( strptime(dateStr, "%Y-%m-%d"))
}

order.month <- function(x){
  ## Function to make Month column an ordered factor.
  x <- substr(x, 1, 3) ## Use just the first three letters
  factor(x, 
         levels = c("Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"),
         ordered = TRUE)
}

dairy.plot <- function(df, col = 'Milk.Prod'){
  require(ggplot2)
  ggplot(df, aes_string('Date', col)) +
    geom_line() +
    ggtitle(paste('Time series of', col)) +
    xlab('Time in years')
}

result.plot <- function(df){
  require(ggplot2)
  ggplot(df, aes(ForecastDates)) +
    geom_line(aes(y=ForcastActualValues)) +
    ggtitle("Complete") +
    geom_line(aes(y=ForcastPredictedValues),colour="#000099") +
    xlab('Time in years')
  
  
}


dairy.acf <- function(df, col = 'remainder', is.df =TRUE){
  if(is.df) temp <- df[, col]
  else temp <- df
  temp = ts(temp, start = 1995, frequency = 12)
  par(mfrow = c(2,1))
  acf(temp, main = paste('ACF of', col))
  pacf(temp, main = paste('PACF of', col))
  par(mfrow = c(1,1))
}

dairy.ma <- function(df, col = 'Milk.Prod', order = 12){
  temp = df[, col]
  end = length(temp) - 1
  out = rep(0, length(temp))
  out[1] = temp[1]
  for(i in 1:end){
    if(i - order <= 1) j = 1 
    else j = j + 1
    out[i + 1] = sum(temp[j:i])/(i - j + 1)
  }
  out
}



dairy.seasons <- function(df, col = 'entry.test'){
  df$y = df[, col]
  fit = lm(y ~ 0 + Month.Name, data = df)
  predict(fit, newdata = df)
}


decomp.dairy <- function(df,  col = 'entry.test', multiplicative = TRUE, order = 12){
  if(multiplicative) {
    temp = log(df[, col])
    df[, col] = temp
  } else { 
    temp = df[, col] 
  }
  trend = dairy.ma(df, col = col, order = order)
  temp = temp - trend
  df[, col] = temp
  
  seasonal = dairy.seasons(df, col = col)
  remainder = temp - seasonal
  data.frame(trend = trend, seasonal = seasonal, remainder = remainder)
  #data.frame(trend)
}


decomp.plot <- function(df){
  require(ggplot2)
  install.packages("gridExtra")
  require(gridExtra)
  df$x = 1:nrow(df)
  ycols = c('trend', 'seasonal', 'remainder')
  p <- lapply(ycols, function(y){
    ggplot(df, aes_string('x', y)) + 
      geom_line() +
      ylab(y)
  })
  grid.arrange(p[[1]], p[[2]], p[[3]], nrow = 3)
}


dairy.decomp <- function(df, col = 'entry.test', span = 0.5, Mult = TRUE){
  if(Mult) {temp <- ts(log(df[, col]), frequency=12, start=1)
  } else {temp <- ts(df[, col], frequency=24, start=1)}
  span = span * length(temp)  
  dairyFit <- stl(temp, s.window = "periodic", t.window = span)
  plot(dairyFit, main = 'Decompositon of dairy produciton')
  cbind(df, as.data.frame(dairyFit$time.series))
}

hist.ts = function(df, col = 'entry.test', bins = 40){
  temp = df[,col]
  breaks = seq(min(temp), max(temp), length.out = (bins + 1))
  hist(temp, breaks = breaks, main = paste('Distribution of ', col), xlab = col)
}

model.dairy = function(df, col = 'remainder', order = c(0,0,1)){
  ts = ts(df[, col], frequency = 12, start = 1995)
  dairy.mod = arima(ts, order = order, include.mean = FALSE)
  print(dairy.mod)
  dairy.mod
}



dairy.box <- function(df, col = 'remainder'){
  require(ggplot2)
  p <- ggplot(df, aes_string('Month.Name', col)) +
    geom_boxplot() +
    ggtitle('Variation of remainder component of dairy production by month')
  print(p)
}




model.dairy = function(df, col = 'remainder', order = c(0,0,1)){
  ts = ts(df[, col], frequency = 12, start = 1995)
  dairy.mod = arima(ts, order = order, include.mean = FALSE)
  print(dairy.mod)
  dairy.mod
}

dairy.diff <- function(df, col = 'entry.test', out = 'entry.test'){
  ln <- nrow(df)
  temp <- ts(df[, col], frequency = 12, start = 1995)
  df[2:ln, out] <- diff(temp)
  df <- df[2:ln, ]
  df
}

