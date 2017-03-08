# SpatialTemporalDataAnalysis

The workflow is we first merge all raw files in one document, with ranges of temperature calculated, then perform harmonic regresson. On the other hand, the SST calculator and MissingDataHandler will be used as external classes to handle missing data and caculate SST based features. 

This workflow is followed by the data analysis work in R, which is reflected in the R file, SpatialTemporalDataAnalysis. Two different scenarios are taken into consideration, the one-year (2015) and the five-year (from 2011 to 2015).

Lastly, there is benchmark file to compare the performace of different methods. We used the random forest (based on sklearn package) and neural networks (based on tensorflow), along with a simple linear regression model. 

