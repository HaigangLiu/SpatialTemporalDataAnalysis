import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from netCDF4 import Dataset
from haversine import haversine
from functools import partial 
from scipy.stats import norm

import seaborn
seaborn.set()

class missingDataHandler(object):
    
    def __init__(self, data, feature):
               
        self.data = data
        self.feature =feature
        
        if self.feature.startswith("RANGE"):
            self.known_data = data[data[feature] > 0]
            self.missing_data = data[data[feature] <= 0]
        else:
            self.known_data = data[data[feature] >= 0]
            self.missing_data = data[data[feature] < 0]
        
        self.known_data["LATITUDE"] = pd.to_numeric(self.known_data["LATITUDE"])
        self.known_data["LONGITUDE"] = pd.to_numeric(self.known_data["LONGITUDE"])

    def complete_the_missing_feature(self, rec):
        lon = float(rec.LONGITUDE); lat = float(rec.LATITUDE)
        partial_haversine = partial(haversine, (lon, lat), miles = True)
        
        known_info = self.known_data[(self.known_data.MONTH == rec.MONTH) & (self.known_data.YEAR == rec.YEAR)]
        distance = known_info[[ "LATITUDE","LONGITUDE"]].apply(partial_haversine, axis = 1)
        
        scale_param = 0.25*(np.max(distance) - np.min(distance))
        pdf1 = norm.pdf(distance, loc = np.mean(distance), scale = scale_param)       
        filled_feature = sum((pdf1/sum(pdf1))*known_info[self.feature])
        
        return filled_feature
    
    def data_frame_organizer(self):
        del self.missing_data[self.feature]
        k = self.missing_data.apply(self.complete_the_missing_feature, axis = 1)
        self.missing_data[self.feature] = k
        completed_version = self.known_data.append(self.missing_data)
        output = completed_version.sort_values(["STATION_NAME", "YEAR","MONTH"])
        return output
        