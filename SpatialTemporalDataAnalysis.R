library(spTimer)
library(coda)
library(graphics)

# this program is designed to implement the AR model from spTimer package
# two scenario: one year (2015) and five year (2011 - 2015)
# change chunk size to 60 before doing the five year case

setwd("/Users/haigangliu/Dropbox/DataRepository/")
Year2015 = read.csv("Year2015RangedTempTrendRemoved.csv")
FiveYears = read.csv("FiveYearRangedTempTrendRemoved.csv")

chunk_size = 12

training_test_splitter = function(data, chunk_size){
  
  # function will return the training set and test set in a list
  # NOTE: we can only shuffle locations but cannot shuffle months!!!
  
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

  return(data_set)
}


theResidualRetriever = function(model_ouptut, new_data){
  
  # get the predictiion residuals from test set (new_data)
  
  prediction =  predict(model_ouptut, newdata = new_data, newcoords = ~ Longitude + Latitude)
  monthly_pred = apply(prediction$pred.samples, 1, median)
  
  matrix_pred =  matrix(data = monthly_pred, nrow = dim(new_data)[1]/chunk_size , ncol = chunk_size, byrow = FALSE)
  recovered_data = 10^(matrix_pred) - (overhead + amount_to_make_positive) # back-transformed 
 
  return(recovered_data)
}


theOriginalDataHandler = function(new_data){
  # reshape the observed data to be comparable to the prediction
  observed = new_data$RESIDUAL
  reshaped  = matrix(data = observed, nrow = dim(new_data)[1]/chunk_size, ncol = chunk_size, byrow = FALSE)
  return(reshaped)
}

thePlotter = function(the_pred, the_original){
  
  # plot the prediction v.s. observed for 12/60 months   
  par(mfrow = c(3,4))
  for (i in 1:chunk_size){
    plot(the_pred[,i], 2*the_original[,i], main = paste("month", i), ylab = "observed", xlab ="predicted")
    abline(0,1)
  }
}

pipeline = function(data, logbase = 10 ){
  
  # call all previous functions to do data munging
  # after that the AR model from spTimer is called
  # followed by diagnosis plots
  
  name_corrected_data = dataCleaner(data)
  
  amount_to_make_positive = abs(min(name_corrected_data ["RESIDUAL"]))
  overhead = 0.01
  type_corrected_data["LOG"] = log(amount_to_make_positive + overhead + type_corrected_data["RESIDUAL"], base = logbase)
  
  
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
output_of_2015 = pipeline(Year2015)

chunksize = 60
output_of_2015 = pipeline(FiveYears)
