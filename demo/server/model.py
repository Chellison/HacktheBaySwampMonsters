# -*- coding: utf-8 -*-

#load modules
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import urllib.request
import math
import os

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
from features import HUC12_percent, HUC10_percent, HUC8_percent, stream_percent

import pickle


def setup():
    #measurements data (with HUCS)
    file_location = 'data/WateQuality_wHUC_Percents.csv'
    datadf = pd.read_csv(file_location)

    #stream flow data
    file_location = 'data/TrueLocationsStreamFlow.csv'
    streamFlow = pd.read_csv(file_location)

    #merge on locations
    datadf = pd.merge(datadf, streamFlow, how = 'left', left_on = ['Latitude','Longitude'], right_on = ['Latitude','Longitude'])

    #remove 196 entries
    datadf = datadf.dropna(subset=['PctVALUE_95'])

    #select entries with Nitrogen
    datadf = datadf.dropna(subset=['TOTAL NITROGEN'])

    #get month and year
    datadf['year'] = pd.DatetimeIndex(datadf['DateTime']).year
    datadf['month'] = pd.DatetimeIndex(datadf['DateTime']).month

    #set train/test set
    train = datadf[datadf['year']<=2015]
    test = datadf[datadf['year']>2016]

    return train, test


def train_model():
    #gradient boosted trees
    X = train[depVar]
    Y = train['TOTAL NITROGEN']

    lr_tn = GradientBoostingRegressor()
    lr_tn.fit(X,Y)
    score_train = lr_tn.score(X, Y)
    print('train', score_train)
    score_test = lr_tn.score(test[depVar], test['TOTAL NITROGEN'])
    print('gradient boost, HUC12,HUC10, and HUC8, stream test',score_test)

    with open(pkl_filename, 'wb') as file:
        pickle.dump(lr_tn, file)

    return lr_tn


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

pkl_filename = "models/boosted_regression.pkl"
train, test = setup()

depVar = ['Latitude', 'Longitude','month','year']+HUC12_percent+HUC10_percent+HUC8_percent+stream_percent

if os.path.exists(pkl_filename):
    with open(pkl_filename, 'rb') as file:
        lr_tn = pickle.load(file)
else:
    lr_tn = train_model()
