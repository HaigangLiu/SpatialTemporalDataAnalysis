import pandas as pd
import numpy as np
import os

def file_reader_and_merger(file_name):
    numeric_variables = ["ELEVATION","LATITUDE","LONGITUDE","DATE","PRCP","TMAX","TMIN"]
    data_file = pd.read_csv(path + file_name)[variables_of_interest]
    
    for numeric_variable in numeric_variables:
        data_file[numeric_variable] = pd.to_numeric(data_file[numeric_variable], errors= "coerce")

    # construct year month day info based on date info
    date_converted = pd.to_datetime(data_file.DATE, format = "%Y%m%d")
    data_file["YEAR"] = date_converted.dt.year
    data_file["MONTH"] = date_converted.dt.month
    data_file["DAY"] = date_converted.dt.day

    rain_data = data_file.copy()
    del rain_data["DATE"] 
    rain_data = rain_data.set_index(["STATION_NAME", "YEAR", "MONTH", "DAY"])

    # keep all the time-invariate information like station name, elevation and etc
    # the strategy is to treat time variant and time invarant variables differently

    # this is a way to end up with least missing data because we sorted!
    # this is because, after sorting, by default, the missing data will be the last

    monthly_aggregated = rain_data.groupby(level = ["STATION_NAME","YEAR","MONTH"]).first()
    monthly_aggregated = monthly_aggregated.reset_index(drop = False)
    monthly_aggregated = monthly_aggregated.drop(["TMAX","TMIN"], axis = 1)
    
    #make sure two sources share the same order
    sorted_data = rain_data.sort_index( level= ["STATION_NAME","YEAR","MONTH"])

    #next, find time-variante variables
    # we convert all -9999 into 0 for now, and will handle them with MissingData Handler

    # you cannot do them in one shot like sort_prcp[prcp<0] = np.nan
    # in case tmax is missing and tmin is not, or vice versa
    # that will make the range of temperature look crazy

    sorted_data.TMIN[sorted_data.TMAX < 0] = np.nan
    sorted_data.TMAX[sorted_data.TMIN < 0] = np.nan

    sorted_data.TMAX[sorted_data.TMAX < 0] = np.nan
    sorted_data.TMIN[sorted_data.TMIN < 0] = np.nan

    # the roadmap is first convert -9999 into na, and then convert na into 0.
    sorted_data = sorted_data.fillna(0)

    max_high = sorted_data.groupby(level =["STATION_NAME", "YEAR", "MONTH"] )["TMAX"].max()
    min_high = sorted_data.groupby(level =["STATION_NAME", "YEAR", "MONTH"] )["TMAX"].min()
    max_low = sorted_data.groupby(level =["STATION_NAME", "YEAR", "MONTH"] )["TMIN"].max()
    min_low = sorted_data.groupby(level =["STATION_NAME", "YEAR", "MONTH"] )["TMIN"].min()

    high_range = max_high - min_high
    low_range = max_low - min_low
    overall_range = max_high - min_low
    mid_range = 0.5*(max_high + min_low)

    monthly_aggregated = monthly_aggregated.copy()
    #merge everything together
    monthly_aggregated["RANGE_HIGH"] = high_range.reset_index(drop = False).iloc[:,-1]
    monthly_aggregated["RANGE_LOW"] = low_range.reset_index(drop = False).iloc[:,-1]
    monthly_aggregated["RANGE_OVERALL"] = overall_range.reset_index(drop = False).iloc[:,-1]
    monthly_aggregated["RANGE_MID"] = mid_range.reset_index(drop = False).iloc[:,-1]
    
    return monthly_aggregated

path = "/Users/haigangliu/Dropbox/Dissertation/data_file/"
names = [file for file in os.listdir(path) if file.startswith("8")] 
variables_of_interest = ["STATION","STATION_NAME","ELEVATION","LATITUDE","LONGITUDE","DATE","PRCP","TMAX","TMIN"]

import concurrent
cores_of_computer = 8

executor = concurrent.futures.ProcessPoolExecutor(max_workers = cores_of_computer)
result = executor.map(file_reader_and_merger, names)
out_put_data_frame = pd.concat([df for df in result]).sort_values(["STATION_NAME", "YEAR","MONTH"])

os.chdir("/Users/haigangliu/Dropbox/DataRepository/")
out_put_data_frame.to_csv("raw_data_with_4_ranges.csv")
