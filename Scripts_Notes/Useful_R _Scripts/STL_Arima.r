# data input
data <- maml.mapInputPort(1) # class: data.frame
input <- maml.mapInputPort(2) # class: data.frame
attach(input)

library(forecast)
library(plyr)

# Date format clean-up
data$Date <- as.POSIXct(as.numeric(as.POSIXct(data$Date, format = timeformat, tz = "UTC", origin = "1970-01-01"), tz = "UTC"), tz = "UTC", origin = "1970-01-01")

# Helper functions extracting date-related information
weeknum <- function(date){ date <- as.Date(date, format=timeformat); as.numeric(format(date, "%U"))}
year <- function(date){ date <- as.Date(date, format=timeformat); as.numeric(format(date, "%Y"))}
date.info <- function(df){ date <- df$Date[1]; c(year(date), weeknum(date))}

# Forecasting set-up
if (!("horizon" %in% colnames(input)) & "test.length" %in% colnames(input)) {print(TRUE); horizon <- input$test.length}

# Forecasting Function
arima.single.id <- function(data){
  method.name <- "STL_ARIMA"
  
  # Train and test split
  data.length <- nrow(data)
  train.length <- data.length - horizon
  train <- data[1:train.length, ]
  test <- data[(train.length+1):data.length, ]
  
  # Missing data: replace na with average
  train$Traffic[is.na(train$Traffic)] <- mean(train$Traffic, na.rm = TRUE)

  # Build forecasting models
  train.ts <- ts(train$Traffic, frequency = seasonality, start = date.info(train))
  train.model <- stlf(train.ts, h = horizon, method = "arima", s.window = "periodic")

  forecast.Traffic <- train.model$mean
  forecast.lo95 <- train.model$lower[,1]
  forecast.hi95 <- train.model$upper[,1]
  
  output <- data.frame(Date = test$Date, cbind(forecast.Traffic, forecast.lo95, forecast.hi95))
  colnames(output)[-1] <- paste(c("forecast", "lo95", "hi95"), method.name, sep = ".") 
  
  return(output)
}

output <- ddply(data, .(StoreID), arima.single.id)

maml.mapOutputPort("output");