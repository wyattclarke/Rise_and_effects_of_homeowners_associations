# -*- coding: utf-8 -*-
"""
Created on Tue Jun  6 12:07:30 2017

@author: wyatt.clarke
"""

import pandas as pd
import numpy as np
from pygeocoder import Geocoder
import geopandas as gpd
from shapely.geometry import Point
import os

os.chdir(r'C:\Users\wyatt.clarke\Documents\Research\HOAs\Redfin')

# Import house listings from Redfin and turn that into a geo-dataframe
pts = pd.read_csv(r'csv_data\Downloads\_all_properties.csv')
geometry = [Point(xy) for xy in zip(pts['LATITUDE'], pts['LONGITUDE'])] #Creates a "geometry" column from the lat and lon, which is what distinguishes a geodataframe from a normal dataframe
#crs = {'proj': 'aea', 'lat_1': 29.5, 'lat_2': 45.5, 'lat_0': 37.5, 'lon_0': -96, 'x_0': 0, 'y_0': 0, 'datum': 'NAD83', 'units': 'm', 'no_defs': True} #Defines the spatial projection to be WGS84. (Remember we're just graphing things.)
crs = {'init': 'epsg:4269'}
pts_plot = gpd.GeoDataFrame(pts, crs=crs, geometry=geometry)

# Import shapefile of Census tracts, using year 2000 boundaries, from NHGIS
#tracts_2000 = gpd.read_file('US_tract_2000.shp')
tracts_2000 = gpd.read_file('cb_2016_us_state_500k.shp')



# Assign each house listing to a Census tract
pts_plot = gpd.sjoin(pts_plot, tracts_2000, how="inner", op='intersects')

# Create a binary variable for being in an HOA
pts_plot['HOA_YN'] = pts_plot['HOA/MONTH'].notnull()
pts_plot['counter'] = 1

# Aggregate items purchased by sector, ethnicity and education of user
pts_plot['HOA_tract_n'] = pts_plot.groupby(["GISJOIN"])["HOA_YN"].transform(sum)
pts_plot['total_tract_n'] = pts_plot.groupby(["GISJOIN"])["counter"].transform(sum)

HOA_tract_pct = pts_plot[['GISJOIN', 'HOA_tract_n', 'total_tract_n']].drop_duplicates("GISJOIN")
HOA_tract_pct['HOA_tract_pct'] = HOA_tract_pct['HOA_tract_n']/HOA_tract_pct['total_tract_n']


zipdate_sector = items.drop_duplicates(["city", "transaction_dt", "sector"])



# Create a binary variable for being in an HOA
pts_plot['HOA_YN'] = pts_plot['HOA/MONTH'].notnull()


test = pts_plot.head()



tracts_2000.head().plot()
pts_plot.head(1000).plot()


pts_plot = gpd.sjoin(pts_plot, tracts_2000, how="inner", op='intersects')



def spatial_overlays(df1, df2, how='intersection'):
    '''Compute overlay intersection of two 
        GeoPandasDataFrames df1 and df2
    '''
    df1 = df1.copy()
    df2 = df2.copy()
    df1['geometry'] = df1.geometry.buffer(0)
    df2['geometry'] = df2.geometry.buffer(0)
    if how=='intersection':
        # Spatial Index to create intersections
        spatial_index = df2.sindex
        df1['bbox'] = df1.geometry.apply(lambda x: x.bounds)
        df1['histreg']=df1.bbox.apply(lambda x:list(spatial_index.intersection(x)))
        pairs = df1['histreg'].to_dict()
        nei = []
        for i,j in pairs.items():
            for k in j:
                nei.append([i,k])
        
        pairs = gpd.GeoDataFrame(nei, columns=['idx1','idx2'], crs=df1.crs)
        pairs = pairs.merge(df1, left_on='idx1', right_index=True)
        pairs = pairs.merge(df2, left_on='idx2', right_index=True, suffixes=['_1','_2'])
        pairs['Intersection'] = pairs.apply(lambda x: (x['geometry_1'].intersection(x['geometry_2'])).buffer(0), axis=1)
        pairs = gpd.GeoDataFrame(pairs, columns=pairs.columns, crs=df1.crs)
        cols = pairs.columns.tolist()
        cols.remove('geometry_1')
        cols.remove('geometry_2')
        cols.remove('histreg')
        cols.remove('bbox')
        cols.remove('Intersection')
        dfinter = pairs[cols+['Intersection']].copy()
        dfinter.rename(columns={'Intersection':'geometry'}, inplace=True)
        dfinter = gpd.GeoDataFrame(dfinter, columns=dfinter.columns, crs=pairs.crs)
        dfinter = dfinter.loc[dfinter.geometry.is_empty==False]
        return dfinter
    elif how=='difference':
        spatial_index = df2.sindex
        df1['bbox'] = df1.geometry.apply(lambda x: x.bounds)
        df1['histreg']=df1.bbox.apply(lambda x:list(spatial_index.intersection(x)))
        df1['new_g'] = df1.apply(lambda x: reduce(lambda x, y: x.difference(y).buffer(0), [x.geometry]+list(df2.iloc[x.histreg].geometry)) , axis=1)
        df1.geometry = df1.new_g
        df1 = df1.loc[df1.geometry.is_empty==False].copy()
        df1.drop(['bbox', 'histreg', new_g], axis=1, inplace=True)
        return df1
    
events_zip_intersect = spatial_overlays(tracts_2000, pts_plot.head(), how='intersection')


