import rasterio
from rasterio import features
import geopandas as gpd
import pandas as pd
from shapely.geometry import shape, Polygon, LineString, MultiLineString, MultiPolygon, box
from shapely import concave_hull, union_all
from shapely.ops import split
import geopandas as gpd

import matplotlib.pyplot as plt
import numpy as np

from utils import fetch_osm_landuse_data


'''
gis_osm_{name}_a_free_1
    buildings
    landuse
    natural
    traffic
    transport
gis_osm_{name}_free_1
    waterways
    railways
    roads
1. 找出tif內的polygons, Lines


2. 把非農田區去除 (去除後的坑坑巴巴怎麼處理?)
3. 用roads分割polygons
'''

# 改成 fetch data

# 　把跟辨識結果tif的polygons做交集


def polygons_in_tif(bounds: pd.DataFrame, polygons: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    print(bounds)
    # 改成用DB
    polygons = polygons.cx[bounds.minx.min():bounds.maxx.max(),
                           bounds.miny.min():bounds.maxy.max()]
    # polygons.to_file(
    #     "./polygons_in_tif.geojson", driver='GeoJSON')
    return polygons


def filter_polygons(polygons, none_land_area_polygons):

    intersected_polygons = gpd.overlay(
        polygons, none_land_area_polygons, how='intersection')

    intersected_polygons.to_file(
        "./intersected_polygons.geojson", driver='GeoJSON')


def main(tif_num):
    polygons_path = f"./geojson/preds/{
        tif_num}_threshold_12_combined_True_4326.geojson"
    polygons = gpd.read_file(polygons_path)

    # 取出bounds
    bounds = polygons.bounds

    land_use_list = ['meadow', 'farmland',
                     'grass', 'vineyard', 'orchard', 'farmyard']  #

    none_land_area_polygons = gpd.read_file(
        f"../data/land_use_shp/gis_osm_landuse_a_free_1.shp")

    # none_land_area_polygons = fetch_osm_landuse_data(engine, 'gis_osm_landuse_a_free_1',
    #                                                  polygon=Polygon(bounds.to_dict('records')[0]))

    none_land_area_polygons = none_land_area_polygons[none_land_area_polygons['fclass'].isin(
        land_use_list)]

    in_tif_farmlands = polygons_in_tif(bounds, none_land_area_polygons)

    polygons = filter_polygons(polygons, in_tif_farmlands)


if __name__ == '__main__':

    main(102)
