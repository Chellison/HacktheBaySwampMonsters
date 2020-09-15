# -*- coding: utf-8 -*-

#load modules
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request
import math

#models
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import GradientBoostingRegressor

#install geopandas through cluster page: libraries->pypi search->"geopandas"
import geopandas

#time series graphing
import seaborn as sns
import datetime as dt
import scipy.stats as stats
from io import StringIO
from typing import Tuple

#read in data

#measurements data (with HUCS)
file_location = 'data/WateQuality_wHUC_Percents.csv'
datadf = pd.read_csv(file_location)
print(datadf)

#stream flow data
file_location = 'data/TrueLocationsStreamFlow.csv'
streamFlow = pd.read_csv(file_location)
print(streamFlow)

#merge on locations
datadf = pd.merge(datadf, streamFlow, how = 'left', left_on = ['Latitude','Longitude'], right_on = ['Latitude','Longitude'])

datadf

#remove null
#check for nulls
print(datadf.isnull().sum())

#remove 196 entries
datadf = datadf.dropna(subset=['PctVALUE_95'])
print(datadf.isnull().sum())

#names- HUC12, HUC10, HUC8, stream percents
HUC12_percent = ['V_11_PERCENT', 'V_21_PERCENT',
       'V_22_PERCENT', 'V_23_PERCENT', 'V_24_PERCENT', 'V_31_PERCENT',
       'V_41_PERCENT', 'V_42_PERCENT', 'V_43_PERCENT', 'V_45_PERCENT',
       'V_46_PERCENT', 'V_52_PERCENT', 'V_71_PERCENT', 'V_81_PERCENT',
       'V_82_PERCENT', 'V_90_PERCENT', 'V_95_PERCENT']


HUC10_percent = ['V_11_PERCENT_10', 'V_21_PERCENT_10', 'V_22_PERCENT_10',
       'V_23_PERCENT_10', 'V_24_PERCENT_10', 'V_31_PERCENT_10',
       'V_41_PERCENT_10', 'V_42_PERCENT_10', 'V_43_PERCENT_10',
       'V_45_PERCENT_10', 'V_46_PERCENT_10', 'V_52_PERCENT_10',
       'V_71_PERCENT_10', 'V_81_PERCENT_10', 'V_82_PERCENT_10',
       'V_90_PERCENT_10', 'V_95_PERCENT_10']

HUC8_percent = ['V_11_PERCENT_8','V_21_PERCENT_8', 'V_22_PERCENT_8', 'V_23_PERCENT_8', 'V_24_PERCENT_8',
       'V_31_PERCENT_8', 'V_41_PERCENT_8', 'V_42_PERCENT_8', 'V_43_PERCENT_8',
       'V_45_PERCENT_8', 'V_46_PERCENT_8', 'V_52_PERCENT_8', 'V_71_PERCENT_8',
       'V_81_PERCENT_8', 'V_82_PERCENT_8', 'V_90_PERCENT_8', 'V_95_PERCENT_8',]

stream_percent =['PctVALUE_11', 'PctVALUE_21', 'PctVALUE_22', 'PctVALUE_23',
       'PctVALUE_24', 'PctVALUE_31', 'PctVALUE_41', 'PctVALUE_42',
       'PctVALUE_43', 'PctVALUE_45', 'PctVALUE_46', 'PctVALUE_52',
       'PctVALUE_71', 'PctVALUE_81', 'PctVALUE_82', 'PctVALUE_90',
       'PctVALUE_95']

landcover_types = ['open water','developed, open space', 'developed low intensity',
                  'developed medium intensity', 'developed high intensity', 'barren land', 'deciduous forest',
                  'evergreen forest', 'mixed forest', 'shrub-Forest', 'herbaceous-Forest', 'shrub or scrub', 'grassland or herbaceous',
                   'pasture and hay', 'cultivated crops', 'woody wetland',
                  'emergent herbaceous wetland']

#select entries with Nitrogen
datadf = datadf.dropna(subset=['TOTAL NITROGEN'])

#get month and year
datadf['year'] = pd.DatetimeIndex(datadf['DateTime']).year
datadf['month'] = pd.DatetimeIndex(datadf['DateTime']).month

#set train/test set
train = datadf[datadf['year']<=2015]
test = datadf[datadf['year']>2016]

#gradient boosted trees
depVar = ['Latitude', 'Longitude','month','year']+HUC12_percent+HUC10_percent+HUC8_percent+stream_percent
X = train[depVar]
Y = train['TOTAL NITROGEN']

lr_tn = GradientBoostingRegressor()
lr_tn.fit(X,Y)
score_train = lr_tn.score(X, Y)
print('train', score_train)
score_test = lr_tn.score(test[depVar], test['TOTAL NITROGEN'])
print('gradient boost, HUC12,HUC10, and HUC8, stream test',score_test)

def counterfactual(station: str,
                   percent_urban: float,
                   percent_farm: float,
                   percent_forest: float):

    # want to predict on the station
    filtered_test = test[test.Station == station].copy()
    filtered_test_projection = filtered_test.copy()
    urban_types = ['PctVALUE_21', 'PctVALUE_22','PctVALUE_23','PctVALUE_24']
    forest_types = ['PctVALUE_41', 'PctVALUE_42', 'PctVALUE_43', 'PctVALUE_45', 'PctVALUE_46']
    farm_types = ['PctVALUE_81', 'PctVALUE_82']

    urban_total = filtered_test[urban_types].iloc[0].sum()
    forest_total = filtered_test[forest_types].iloc[0].sum()
    farm_total = filtered_test[farm_types].iloc[0].sum()
    full_total = urban_total + forest_total + farm_total

    urban_total /= full_total
    forest_total /= full_total
    farm_total /= full_total

    unchanged = ['PctVALUE_11','PctVALUE_31', 'PctVALUE_52', 'PctVALUE_71', 'PctVALUE_90', 'PctVALUE_95']

    for pct, types in [(percent_urban, urban_types), (percent_farm, farm_types), (percent_forest, forest_types)]:
        for t in types:
            filtered_test_projection[t] = (pct / len(types))

    current = lr_tn.predict(filtered_test[depVar])
    projection = lr_tn.predict(filtered_test_projection[depVar])

    return list(filtered_test.month), list(filtered_test.year), current, projection, (urban_total, forest_total, farm_total)
