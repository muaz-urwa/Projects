data$Date <- as.Date(data$Date, format=timeformat)

min.time <- min(data$Date)
max.time <- max(data$Date)

unique.time <- seq(from = min.time, to = max.time, by = observation.freq)

# For every (ID1, ID2) pair, create (ID1, ID2, time) combination 
unique.Store <- unique(data[, "Store"])
comb.Store <- rep(unique.Store, each = length(unique.time))
#comb.ID2 <- rep(unique.ID12$ID2, each = length(unique.time))
comb.time <- rep(unique.time, times = length(unique.Store))
comb <- data.frame(Store = comb.Store, Date = comb.time)

# Join the combination with original data
data <- join(comb, data, by = c("Store", "Date"), type = "left")