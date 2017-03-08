
library(spTimer); 
library(coda); 
library(graphics)

setwd("/Users/haigangliu/Dropbox/DataRepository/")
Year2015 = read.csv("Year2015RangedTempTrendRemoved.csv")
FiveYears = read.csv("FiveYearRangedTempTrendRemoved.csv")

chunk_size = 12

training_test_splitter = function(data, chunk_size){
  # chunk size = 12 if its one year, and 24 if two years, so on and so forth
  # will return the training set and test set in a list
  num_of_locs = dim(data)[1]/chunk_size
  randomized_indices = rep(sample(num_of_locs, size = num_of_locs), each = chunk_size )
  data["randomized_indices"] = randomized_indices 
  
  splitting_point = round((dim(data)[1]/chunk_size)*0.7, 0)
  training= subset(data, randomized_indices <= splitting_point)
  test = subset(data, randomized_indices > splitting_point)
  
  return(list(training,test))
}


dataCleaner  <- function(data_set) {
  
  # just to rename all the data to be compatible to legacy code 
  data_set = data_set[c("YEAR", "MONTH","LATITUDE","LONGITUDE","ELEVATION", "PRCP", "STATION_NAME", "RANGE_HIGH", "RANGE_LOW", "RANGE_OVERALL","SST", "RESIDUAL", "cos", "sin")]
  
  names(data_set) = c("Year", "Month","Latitude","Longitude","ELEVATION", "PRCP","STATION_NAME","RANGE_HIGH", "RANGE_LOW", "RANGE_OVERALL","SST", "RESIDUAL", "cos", "sin")

  # try(data_set$Latitude <- as.numeric(levels(data_set$Latitude)[data_set$Latitude]), silent = T)
  # try(data_set$Longitude <- as.numeric(levels(data_set$Longitude)[data_set$Longitude]),silent = T)
  # try(data_set$ELEVATION <- as.numeric(levels(data_set$ELEVATION)[data_set$ELEVATION]),silent = T) 
  # try(data_set$RANGE_OVERALL<- as.numeric(levels(data_set$RANGE_OVERALL)[data_set$RANGE_OVERALL]),silent = T) 
  # try(data_set$RANGE_HIGH<- as.numeric(levels(data_set$RANGE_HIGH)[data_set$RANGE_HIGH]),silent = T) 
  # try(data_set$RANGE_LOW<- as.numeric(levels(data_set$LOW)[data_set$RANGE_LOW]),silent = T) 
  
  print(paste("finished cleaning, the missing record is number is", sum(is.na(data_set))))
  return(data_set)
}


theResidualRetriever = function(model_ouptut, new_data){
  prediction =  predict(model_ouptut, newdata = new_data, newcoords = ~ Longitude + Latitude)
  monthly_pred = apply(prediction$pred.samples, 1, median)
  matrix_pred =  matrix(data = monthly_pred, nrow = dim(new_data)[1]/chunk_size , ncol = chunk_size, byrow = FALSE)
  recovered_data = 10^(matrix_pred) - (overhead + amount_to_make_positive)
  
  print(dim(recovered_data))
  
  return(recovered_data)
}


theOriginalDataHandler = function(new_data){
  observed = new_data$RESIDUAL
  reshaped  = matrix(data = observed, nrow = dim(new_data)[1]/chunk_size, ncol = chunk_size, byrow = FALSE)
  return(reshaped)
}

thePlotter = function(the_pred, the_original){
  par(mfrow = c(5,6))
  for (i in 1:chunk_size){
    plot(the_pred[,i], 2*the_original[,i], main = paste("month", i), ylab = "observed", xlab ="predicted")
    abline(0,1)
  }
}

pipeline = function(data, logbase = 10 ){
  #log transformation
  type_corrected_data = dataCleaner(data)
  
  amount_to_make_positive = abs(min(type_corrected_data ["RESIDUAL"]))
  overhead = 0.01
  type_corrected_data["LOG"] = log(amount_to_make_positive + overhead + type_corrected_data["RESIDUAL"], base = logbase)
  
  #cleaning the type
  
  #split the data into training and test
  splitted = training_test_splitter(type_corrected_data, chunk_size = chunk_size )
  training_data = splitted[[1]]; test_data =splitted[[2]]
  
  the_sp_model = spT.Gibbs(formula = LOG ~RANGE_OVERALL + RANGE_LOW + RANGE_HIGH + SST + ELEVATION + SST*RANGE_LOW, 
                           nItr=5000, nBurn=1000, data = training_data, model = "AR",
                           coords = ~ Longitude + Latitude, tol.dist = 0.01, scale.transform = "NONE",
                           spatial.decay = spT.decay(distribution = Gamm(2, 10), tuning = 0.1))
  
  plot(the_sp_model, residuals = TRUE)
  summary(the_sp_model)
  
  #diagnosis
  the_observed = theOriginalDataHandler(test_data)
  the_predicted = theResidualRetriever(the_sp_model, test_data) #transformed back in this step
  
  thePlotter(the_predicted, the_observed)
  
  return(the_sp_model)
}

chunksize = 12
kk = pipeline(Year2015)


