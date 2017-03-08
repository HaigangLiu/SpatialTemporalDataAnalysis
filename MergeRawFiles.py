import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
%matplotlib inline

path = "/Users/haigangliu/Dropbox/Dissertation/data_file/"
names = [file for file in os.listdir(path) if file.startswith("8")] 
variables_of_interest = ["STATION","STATION_NAME","ELEVATION","LATITUDE","LONGITUDE","DATE","PRCP","TMAX","TMIN"]

#paste all files together
file_container = []
for name in names:
    data_file = pd.read_csv(path + name)[variables_of_interest]
    file_container.append(data_file)

all_files = pd.concat(file_container, axis = 0)

#handle the data type
numeric_variables = ["ELEVATION","LATITUDE","LONGITUDE","DATE","PRCP","TMAX","TMIN"]
for numeric_variable in numeric_variables:
    all_files[numeric_variable] = pd.to_numeric(all_files[numeric_variable], errors= "coerce")
    
date_converted = pd.to_datetime(all_files.DATE, format = "%Y%m%d")
all_files["YEAR"] = date_converted.apply(lambda x: x.year)
all_files["MONTH"] = date_converted.apply(lambda x: x.month)
all_files["DAY"] = date_converted.apply(lambda x: x.day)


rain_data = all_files.copy()
del rain_data["DATE"] 
rain_data = rain_data.set_index(["STATION_NAME", "YEAR", "MONTH", "DAY"])

# keep all the time-invariate information
# this is a way to end up with least missing data because we sorted!
monthly_aggregated = rain_data.groupby(level = ["STATION_NAME","YEAR","MONTH"]).first()
monthly_aggregated = monthly_aggregated.reset_index(drop = False)
monthly_aggregated = monthly_aggregated.drop(["TMAX","TMIN"], axis = 1)

#find ranges of three kinds
sort_prcp = rain_data.sortlevel(["STATION_NAME", "YEAR", "MONTH", "DAY"])
sort_prcp[sort_prcp<0] = np.nan
sort_prcp = sort_prcp.fillna(0)

max_high = sort_prcp.groupby(level =["STATION_NAME", "YEAR", "MONTH"] )["TMAX"].max()
min_high = sort_prcp.groupby(level =["STATION_NAME", "YEAR", "MONTH"] )["TMAX"].min()
max_low = sort_prcp.groupby(level =["STATION_NAME", "YEAR", "MONTH"] )["TMIN"].max()
min_low = sort_prcp.groupby(level =["STATION_NAME", "YEAR", "MONTH"] )["TMIN"].min()

high_range = max_high - min_high
low_range = max_low - min_low
overall_range = max_high - min_low

#merge everything together
monthly_aggregated["RANGE_HIGH"] = high_range.reset_index(drop = False).iloc[:,-1]
monthly_aggregated["RANGE_LOW"] = low_range.reset_index(drop = False).iloc[:,-1]
monthly_aggregated["RANGE_OVERALL"] = overall_range.reset_index(drop = False).iloc[:,-1]

os.chdir("/Users/haigangliu/Dropbox/DataRepository/")
monthly_aggregated.to_csv("rain_with_ranged_temp.csv")