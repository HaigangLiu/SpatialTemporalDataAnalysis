import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# this program means to clean the data into a nice format so that it can 
# work with spTimer package in R

# we drop the data if there is only partial records in one year
# for instance, if March is missing, we delete the record of the whole year

load_data = pd.read_csv("/Users/haigangliu/Dropbox/DataRepository/rain_with_ranged_temp.csv")
indexed_info = load_data.set_index(["STATION_NAME", "YEAR"])
filter_ = indexed_info.groupby(level = ["STATION_NAME", "YEAR"])["MONTH"].sum() ==78
with_complete_year = indexed_info[filter_].reset_index(drop = False)

# cleaning up latitude and longitude
# we want to make sure there is no contradicting location info for a single location
# the strategy is we take the first non-missing record, and use this record to overwrite everything else.

index_ = with_complete_year.set_index("STATION_NAME")
grouped = index_.groupby(level = "STATION_NAME")["LATITUDE", "LONGITUDE"].first()
grouped = grouped.reset_index(drop = False)

counts_of_appearances = with_complete_year.STATION_NAME.value_counts()
counts = counts_of_appearances.sort_index().values

locs = np.repeat(np.matrix(grouped), counts, axis = 0)
STATION_INFO = pd.DataFrame(locs, columns = ["STATION_NAME","LATITUDE","LONGITUDE"])
with_complete_year[["STATION_NAME","LATITUDE","LONGITUDE"]]= STATION_INFO[["STATION_NAME","LATITUDE","LONGITUDE"]]


# not only select data within the given range
# make sure each locations has the same length of record
# say, if we use 3 years, then each locations must has 36 records
# for instance, if loc A has two years data, but we want 2010 to 2012 (3 years), then loc A is out.

def dataFilter(data, start, end):
    
    start_ = int(start[0:4])
    end_ = int(end[0:4])
    CHECKER = np.sum(np.arange(start_, (end_+1)))*12
    
    data_within_range = data[((data.YEAR)>= start_) & ((data.YEAR) <= end_)]
    label = np.matrix(data_within_range.groupby(["STATION_NAME"])["YEAR"].sum() == CHECKER)
    
    counts_table = data_within_range.STATION_NAME.value_counts()
    counts_ = counts_table.sort_index().values
    index = np.repeat(label,counts_)

    output = data_within_range[index.T]

    print "from  %s and %s, the number of locations we have is %r" %(start, end, (output.shape[0]/(end_ - start_ + 1)/12))
    print 
    return output.reset_index(drop = False)

data_of_five_year = dataFilter(with_complete_year,  "2011-01","2015-12")
data_of_one_year = dataFilter(with_complete_year,  "2015-01","2015-12")


def fillMissing(data):
    # the missing data handler is an algorithm to fill missing data based on distance
    # can be found in the folder as well.
    from MissingDataHandler import missingDataHandler

    try:
        for feature in ["RANGE_OVERALL", "RANGE_HIGH","RANGE_LOW","PRCP"]:
            handler = missingDataHandler(data, feature)
            data[feature] = handler.data_frame_organizer()[feature] 
        return data 
        print "finished cleaning of feature %s" %feature
        
    except TypeError:
        print "you have already filled the missing data, and this step is thus skipped"
        print "or check the source code to redefine what is missing"

one_year_fill_missing = fillMissing(data_of_one_year)
five_year_fill_missing = fillMissing(data_of_five_year)

#use the SST calculator, which can found in this folder too.
import os
os.chdir("/Users/haigangliu/PythonCookbook/")
import SSTCalculator as SST

one_year_with_sst = SST.SSTcalculator(data_of_one_year, 300, "2015-01","2015-12")
one_year_with_sst = one_year_with_sst.each_locations()

five_year_with_sst = SST.SSTcalculator(data_of_five_year, 300, "2011-01","2015-12")
five_year_with_sst = five_year_with_sst.each_locations()

# REMOVE SEASONAL TREND BASED ON HARMONIC REGRESSION
import statsmodels.formula.api as smf
def regressor(df):
    df = df.reset_index(drop = True)

    timeline = np.arange(1, 1 + df.shape[0])
    df["cos"] = np.cos(timeline*np.pi/float(6))
    df["sin"] = np.sin(timeline*np.pi/float(6))

    model = smf.ols(formula= "PRCP ~ cos + sin", data = df)
    results = model.fit()
    
    intercept, cosine_coef, sin_coef = results.params

    df["RESIDUAL"] = df.PRCP - results.fittedvalues
    return {"data":df, "sin": sin_coef, "cos": cosine_coef, "intercept": intercept}

regression_results = regressor(one_year_with_sst)
a = regression_results["sin"]
b = regression_results["cos"]
intercept = regression_results["intercept"]

# this tool is for us to recover precipitation data from rain fall data.
def recoverTool(df_w_prediction):
    for keyword in ["cos", "sin", "prediction"]:
        if keyword  in df_w_prediction.columns:
            df_w_prediction["recovered"] = df_w_prediction["prediction"] + a*df_w_prediction["sin"] + b*df_w_prediction["cos"] +intercept 
            return df_w_prediction
        else:
            print "need sin term, cosin term and the predicted residual, all lower case letters"
            print "the data set is missing at lease one of them"

# DATA OUTPUT
one_year_after_trend_removed = regression_results["data"]
variables_kept = ["STATION_NAME","YEAR","MONTH", "LATITUDE","LONGITUDE","PRCP","RESIDUAL"]
variables_kept2 = ["cos", "sin", "SST", "RANGE_HIGH", "RANGE_LOW", "RANGE_OVERALL", "ELEVATION"]
variables =  variables_kept + variables_kept2
output_data = one_year_after_trend_removed[variables]

os.chdir('/Users/haigangliu/Dropbox/DataRepository/')
output_data.to_csv("Year2015RangedTempTrendRemoved.csv")

#FIVE YEAR VERSION
regression_results5 = regressor(five_year_with_sst)
a5 = regression_results["sin"]
b5 = regression_results["cos"]
intercept5 = regression_results["intercept"]

five_year_after_trend_removed = regression_results5["data"]
output_data5 = five_year_after_trend_removed[variables]
output_data5.to_csv("FiveYearRangedTempTrendRemoved.csv")
