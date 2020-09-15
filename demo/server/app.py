import io
import random

from flask import Response, Flask, request
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import seaborn as sns

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import geopandas

import datetime as dt
import scipy.stats as stats
from io import StringIO

# new includes from Joe
from sklearn.preprocessing import MinMaxScaler
from tqdm import tqdm
from scipy import interpolate
from model import counterfactual
from typing import Tuple
from geopy.distance import geodesic

import pgeocode

# set up global access to Nominatim
# pip install pgeocode
nomi = pgeocode.Nominatim('us')

file_location = 'data/locations.csv'
locations = pd.read_csv(file_location)

def zip_to_latlong(zipcode: str) -> Tuple[float, float]:
    zip = nomi.query_postal_code(zipcode)
    return (zip.latitude, zip.longitude)

def closest_station(zipcode: str) -> str:
    lat, long = zip_to_latlong(zipcode)

    cur_min = 100000
    cur_id = ''
    for latitude, longitude, id in zip(locations.Latitude, locations.Longitude, locations.Station):
        dist = geodesic((lat, long), (latitude, longitude)).miles
        if dist < cur_min:
            cur_id = id
            cur_min = dist

    return cur_id

app = Flask(__name__)

@app.route('/plot.png')
def serve_counterfactual():
    zipcode = request.args.get('zip', '')
    metric = request.args.get('metric', '')
    urban = float(request.args.get('urban', -100)) / 100.
    forest = float(request.args.get('forest', -100)) / 100.
    farm = float(request.args.get('farm', -100)) / 100.

    fig = create_figure(zipcode=zipcode, metric=metric, urban=urban, forest=forest, farm=farm)
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')

def create_figure(zipcode, metric, urban, forest, farm):
    fig = Figure()
    fig.suptitle(f'Projected values of {metric} near {zipcode}')
    axis = fig.add_subplot(1, 1, 1)
    axis.set_ylabel(f'{metric}')
    axis.set_xlabel('months')

    station = closest_station(zipcode)
    print(station)
    months, years, current, changed, (u_t, fo_t, fa_t) = counterfactual(station, urban, farm, forest)
    corrected_months = [(year-min(years))*12+month for month, year in zip(months, years)]

    axis.plot(corrected_months, current, label='Projected (no change)')

    if urban >= 0 and forest >= 0 and farm >= 0:
        u_t = urban ; fa_t = farm ; fo_t = forest
        axis.plot(corrected_months, changed, label='Projected (scenario)')

    axis.set_title(f'Urban: {u_t*100:.1f}%; Farm: {fa_t*100:.1f}%; Forest: {fo_t*100:.1f}%')
    axis.legend()

    return fig

if __name__ == '__main__':
    app.run()
