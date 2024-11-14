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
from shapely.ops import split

import configparser

# 讀取 config.ini 檔案
config = configparser.ConfigParser()
config.read('config.ini')

# 抽取參數
threshold = config.getint('PARAMETERS', 'threshold')
combined = config.getboolean('PARAMETERS', 'combined')
normalize = config.get('PARAMETERS', 'normalize')
sigmaX = config.getint('PARAMETERS', 'sigmaX')
pre_kernel_size = config.getint('PARAMETERS', 'pre_kernel_size')
post_kernel_size = config.getint('PARAMETERS', 'post_kernel_size')
img_path = config.get('PARAMETERS', 'img_path')


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


# def polygons_in_tif(bounds: pd.DataFrame, polygons: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
#     print(bounds)
#     # 改成用DB
#     polygons = polygons.cx[bounds.minx.min():bounds.maxx.max(),
#                            bounds.miny.min():bounds.maxy.max()]
#     # polygons.to_file(
#     #     "./polygons_in_tif.geojson", driver='GeoJSON')
#     return polygons

# 用道路、河川、鐵路分割polygon
def polygon_splitter(polygons, lines):
    if len(lines) == 0 or len(polygons) == 0:
        return polygons
    lines_polygons = lines.geometry.apply(lambda x: x.buffer(0.05))
    lines_polygons = gpd.GeoDataFrame(geometry=lines_polygons.geometry)

    # 找出不重疊的polygon
    none_intersected_polygons = gpd.overlay(
        polygons, lines_polygons, how='difference')

    return none_intersected_polygons


def filter_polygons(polygons, none_land_area_polygons):

    # 找出重疊的polygon合併, 並且去除原本的polygon
    intersected_polygons = gpd.overlay(
        polygons, none_land_area_polygons, how='intersection')

    return intersected_polygons


def remove_none_land_area(geo_path):
    polygons_path = f"./geojson/preds/{geo_path}.geojson"
    polygons = gpd.read_file(polygons_path)

    land_area_polygons = gpd.read_file(
        f"./query_result.geojson")

    polygons = filter_polygons(polygons, land_area_polygons)

    # 用道路、河川、鐵路分割polygon
    lines = gpd.read_file(
        f"./line_query_result.geojson")
    polygons = polygon_splitter(polygons, lines)

    polygons.to_file(
        f"./geojson/preds/{geo_path}.geojson", driver='GeoJSON')


if __name__ == '__main__':

    remove_none_land_area(1310)
    print("Done")
