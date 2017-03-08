import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from netCDF4 import Dataset
from haversine import haversine
from functools import partial 
from scipy.stats import norm

import seaborn
seaborn.set()

from numba import autojit


class SSTcalculator(object):
    def __init__(self, data, radius, start_month, end_month):

        data_content = Dataset('/Users/haigangliu/Desktop/data_file_new/sst.mnmean.nc', mode = "r")
        lons = data_content.variables['lon'][:]; lats = data_content.variables['lat'][:]
        lons_converted = np.array([term if term <= 180 else (term -360) for term in lons])
        timeline = data_content.variables['time'][:]
        
        self.longitude_axis,self.latitude_axis = np.meshgrid(lons_converted, lats)
        self.start_month = start_month
        self.end_month = end_month
        
        self.sst = data_content.variables['sst'][:]
        self.data = data[(data.YEAR <=  int(end_month[0:4])) & (data.YEAR >=  int(start_month[0:4]))]

        self.radius = radius
        
        new_dates = pd.to_datetime("1800-01-01") + pd.to_timedelta(timeline , unit = "d")        
        dict_for_time = {str(new_dates[i])[0:7]: i for i in np.arange(len(timeline))}
        self.selected_month_indice = np.arange( dict_for_time[self.start_month], dict_for_time[self.end_month] +1)
        
        self.number_of_years = int(end_month[0:4])-int(start_month[0:4]) + 1
    
    @autojit    
    # just determine which part is actually sea.
    def mask_df_generator(self):
        mask_content = Dataset('/Users/haigangliu/Desktop/data_file_new/lsmask.nc', mode = "r")
        mask = mask_content.variables["mask"][0,:,:]
        df_mask_ = pd.DataFrame(zip(self.latitude_axis.ravel(),self.longitude_axis.ravel())) 
        df_mask_.columns = ["Latitude","Longitude"]
        df_mask_["Label"] = mask.ravel()
        return df_mask_
   
    @autojit
    # get the sst of a range of months
  
    def monthly_sst_df_constructor(self):
        df_mask_with_sst = self.mask_df_generator()
        for index in self.selected_month_indice:
            month = "month %d" %(index - self.selected_month_indice[0] +1)
            df_mask_with_sst[month] = self.sst[index,:,:].ravel()
        return df_mask_with_sst
    
    @autojit
    def with_sst_just_sea(self, rec):
        lon = float(rec.LONGITUDE); 
        lat = float(rec.LATITUDE)
        
        df_with_sst_and_mask = self.monthly_sst_df_constructor()
        haversine_for_given_location = partial(haversine, (lat, lon), miles = True)
        
        observation_at_sea= df_with_sst_and_mask[df_with_sst_and_mask.Label == 1]
        observation_at_sea["distance"] = observation_at_sea[["Latitude", "Longitude"]].apply(haversine_for_given_location, axis = 1)
        in_range_data = observation_at_sea[observation_at_sea.distance<= self.radius]
        
        scale_param = 0.25*(np.max(in_range_data.distance) - np.min(in_range_data.distance))
        density = norm.pdf(in_range_data.distance, loc =0, scale = scale_param )
        standardized_density  =  density/np.sum(density)

        one_loc_container = np.empty(len(self.selected_month_indice))

        for i in np.arange(1,(1+len(self.selected_month_indice))):
            month = "month %d" %i
            one_loc_container[i-1] = np.sum(standardized_density*in_range_data[month]) 
            
            
        return {"data frame": in_range_data, "size": in_range_data.shape[0], "derived feature": one_loc_container}      
    

    def each_locations(self):
        number_of_locs = self.data.shape[0]/(12*self.number_of_years)
        tokens = [i*12 for i in xrange(number_of_locs)]
        locations = self.data.iloc[tokens,:]
        container_temp = []
        
        for i in np.arange(number_of_locs):
            container_temp.append(self.with_sst_just_sea(locations.iloc[i,:])["derived feature"])
            
            if i%10 == 0:
                print "finished %d of %d locations " %(i, number_of_locs)
            
        output =  self.data
        output["SST"] = np.ravel(np.array(container_temp)) 
        
        return output
        

        
