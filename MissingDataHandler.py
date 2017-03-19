import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from haversine import haversine
from functools import partial 
from scipy.stats import norm

class missingDataHandler(object):
    def __init__(self, data, feature):
        
        self.data = data
        self.feature = feature
        
        if feature.startswith("RANGE"):
            self.known_data = self.data[self.data[feature] > 0]
            self.missing_data = self.data[self.data[feature] <= 0]
            
        else:
            self.known_data = self.data[self.data[feature] >= 0]
            self.missing_data = self.data[self.data[feature] < 0]
            
        #extract the index of known data for better performance
        self.month_index = self.known_data.set_index(["MONTH"]).index
        self.year_index = self.known_data.set_index(["YEAR"]).index
            
    def complete_the_missing_feature(self,rec):
        lon = rec.LONGITUDE
        lat = rec.LATITUDE
        partial_haversine = partial(haversine, (lat, lon), miles = True)

        known_info = self.known_data[(self.month_index == rec.MONTH) & (self.year_index == rec.YEAR)]
        distance = known_info[[ "LATITUDE","LONGITUDE"]].apply(partial_haversine, axis = 1)

        scale_param = 0.25*(np.max(distance) - np.min(distance))
        pdf1 = norm.pdf(distance, loc = 0, scale = scale_param)       
        filled_feature = np.dot((pdf1/np.sum(pdf1)), known_info[self.feature])

        return filled_feature

    def data_frame_organizer(self):
        self.missing_data[self.feature] = self.missing_data.apply(self.complete_the_missing_feature, axis = 1)
        completed_version = self.known_data.append(self.missing_data)
        output = completed_version.sort_values(["STATION_NAME", "YEAR","MONTH"])
        return output.iloc[:,1:]
