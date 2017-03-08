import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
%matplotlib inline

# this program is designed to merge all the files from NOAA
# NOAA dataset is daily records, and we need to compress them into monthly data
# another thing that we do is to calculate the range of temperature 
# specifically, the range of daily low in a month, the range of daily high in a month
# and the range of overall (the maxmimum of all - the minimum of all)

path = "/Users/haigangliu/Dropbox/Dissertation/data_file/"
names = [file for file in os.listdir(path) if file.startswith("8")] 
variables_of_interest = ["STATION","STATION_NAME","ELEVATION","LATITUDE","LONGITUDE","DATE","PRCP","TMAX","TMIN"]

#paste all files together
file_container = []
for name in names:
    data_file = pd.read_csv(path + name)[variables_of_interest]
    file_container.append(data_file)

all_files = pd.concat(file_container, axis = 0)

#coerce he data type into float
numeric_variables = ["ELEVATION","LATITUDE","LONGITUDE","DATE","PRCP","TMAX","TMIN"]
for numeric_variable in numeric_variables:
    all_files[numeric_variable] = pd.to_numeric(all_files[numeric_variable], errors= "coerce")

# construct year month day info based on date info
date_converted = pd.to_datetime(all_files.DATE, format = "%Y%m%d")
all_files["YEAR"] = date_converted.apply(lambda x: x.year)
all_files["MONTH"] = date_converted.apply(lambda x: x.month)
all_files["DAY"] = date_converted.apply(lambda x: x.day)

rain_data = all_files.copy()
del rain_data["DATE"] 
rain_data = rain_data.set_index(["STATION_NAME", "YEAR", "MONTH", "DAY"])

# keep all the time-invariate information like station name, elevation and etc
# the strategy is to treat time variant and time invarant variables differently

# this is a way to end up with least missing data because we sorted!
# this is because, after sorting, by default, the missing data will be the last

monthly_aggregated = rain_data.groupby(level = ["STATION_NAME","YEAR","MONTH"]).first()
monthly_aggregated = monthly_aggregated.reset_index(drop = False)
monthly_aggregated = monthly_aggregated.drop(["TMAX","TMIN"], axis = 1)

#next, find time-variante variables
# we convert all -9999 into 0 for now, and will handle them with MissingData Handler

# you cannot do them in one shot like sort_prcp[prcp<0] = np.nan
# in case tmax is missing and tmin is not, or vice versa
# that will make the range of temperature look crazy

sort_prcp.TMIN[sort_prcp.TMAX< 0] = np.nan
sort_prcp.TMAX[sort_prcp.TMIN< 0] = np.nan

sort_prcp.TMAX[sort_prcp.TMAX< 0] = np.nan
sort_prcp.TMIN[sort_prcp.TMIN< 0] = np.nan

# the roadmap is first convert -9999 into na, and then convert na into 0.
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
