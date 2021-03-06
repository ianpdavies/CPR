import __init__
import geopandas
from geopandas import GeoDataFrame as gdf
import descartes
import pandas as pd
import numpy as np
from shapely.geometry import Point, Polygon
import rasterio
import rasterio.plot
import matplotlib.pyplot as plt
import gdal
import os
import datetime
import requests
import json
import sys
import zipfile
sys.path.append('../')
from CPR.configs import data_path
from CPR.keys import noaa_key

# ======================================================================================================================

token = noaa_key
county_shp_path = data_path / 'vector' / 'tl_2019_us_county' / 'tl_2019_us_county.shp'
dfo_path = data_path / 'vector' / 'dfo_floods' / 'dfo_floods.shp'
ghcnd_station_inventory = data_path / 'ghcnd_stations.csv'

img_list = os.listdir(data_path / 'images')
removed = {'4115_LC08_021033_20131227_test'}
img_list = [x for x in img_list if x not in removed]

for i, img in enumerate(img_list):
    print('Image {}/{}, ({})'.format(i+1, len(img_list), img))
    tif_file = 'zip://' + str(data_path / 'images' / img / img) + '.zip!' + img + '_aspect.tif'
    with rasterio.open(tif_file, 'r', crs='EPSG:4326') as ds:
        img_bounds = ds.bounds

    # Need to temporarily extract this image so the arcpy script in precip_interpolation_arcpy.py can access it
    with zipfile.ZipFile(str(data_path / 'images' / img / img) + '.zip') as z:
        # extract /res/drawable/icon.png from apk to /temp/...
        z.extract(str(img + '_aspect.tif'), str(data_path / 'images' / img))

    # Can't intepolate all points without hitting memory cap, so buffer raster and interpolate only the points within
    left, bottom, right, top = img_bounds[0], img_bounds[1], img_bounds[2], img_bounds[3]
    buffer_size = 0.1  # degrees
    leftb = left - buffer_size
    bottomb = bottom - buffer_size
    rightb = right + buffer_size
    topb = top + buffer_size
    buffer_extent = [[leftb, bottomb], [rightb, bottomb], [rightb, topb], [leftb, topb]]
    buffer_extent = Polygon(buffer_extent)

    # Find US counties that intersect flood event
    counties = geopandas.read_file(county_shp_path)
    counties_select = counties[counties.intersects(buffer_extent)].COUNTYFP.to_list()
    counties_select = ['FIPS:'+county for county in counties_select]

    dfo_id = int(img.split('_')[0])
    dfo = geopandas.read_file(dfo_path)

    observation_period = -2
    flood = dfo[dfo.ID == dfo_id]
    start_date = flood.Began.iloc[0]
    end_date = img.split('_')[3]
    end_date = end_date[:4] + '-' + end_date[4:6] + '-' + end_date[6:]
    new_start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    new_start_date += datetime.timedelta(days=observation_period)
    new_start_date = new_start_date.strftime('%Y-%m-%d')

    # Initialize df for NOAA data
    df_prcp = pd.DataFrame()
    dates_prcp = []
    prcp = []
    station = []
    attributes = []

    # Fetch NOAA data
    for county in counties_select:
        req = 'https://www.ncdc.noaa.gov/cdo-web/api/v2/data?datasetid=GHCND&datatypeid=PRCP&limit=1000&locationid=' + \
              county + '&startdate=' + new_start_date + '&enddate=' + end_date
        d = json.loads(requests.get(req, headers={'token': token}).text)
        if len(d) == 0:
            continue
        items = [item for item in d['results'] if item['datatype'] == 'PRCP']
        dates_prcp += [item['date'] for item in items]
        prcp += [item['value'] for item in items]
        station += [item['station'].split(':')[1] for item in items]
        attributes += [item['attributes'] for item in items]

    df_prcp['date'] = [datetime.datetime.strptime(d, "%Y-%m-%dT%H:%M:%S") for d in dates_prcp]
    df_prcp['prcp'] = [p for p in prcp]
    df_prcp['attributes'] = [p for p in attributes]
    df_prcp['station_id'] = [p for p in station]

    # Get lat/long of stations
    station_list = pd.read_csv(ghcnd_station_inventory)
    stations = df_prcp.merge(station_list, on='station_id', how='left')

    # Save precip data
    precip_path = data_path / 'precip' / 'station_data' / img
    precip_path_shp = precip_path / 'shp'
    try:
        precip_path_shp.mkdir(parents=True)
    except FileExistsError:
        pass
    stations.to_csv(precip_path / '{}'.format(img + '_precip.csv', index=False))

    # Sum daily measurements and save as shapefile
    stations = gdf(stations, geometry=geopandas.points_from_xy(stations.long, stations.lat))
    stations = stations.groupby(['station_id', 'name', 'elevation', 'lat', 'long']).sum().reset_index()
    stations = gdf(stations, geometry=geopandas.points_from_xy(stations.long, stations.lat))
    stations.crs = 'EPSG:4269'
    stations = stations.to_crs('EPSG:4326')
    stations.to_file(str(precip_path_shp / '{}'.format(img + '_precip.shp')))




