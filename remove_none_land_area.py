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
import os

from utils import fetch_osm_landuse_data, PathHandler
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
query_result = config.get('PARAMETERS', 'query_result_path')
line_query_result = config.get('PARAMETERS', 'line_query_result_path')


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


def remove_none_land_area(geo_num, path_handler: PathHandler):
    geo_path = path_handler.get_geojsons_path(
        removed=False, combined=False, file_num=geo_num)
    polygons_path = geo_path
    polygons = gpd.read_file(polygons_path)

    land_area_polygons = gpd.read_file(query_result)

    polygons = filter_polygons(polygons, land_area_polygons)

    # 用道路、河川、鐵路分割polygon
    lines = gpd.read_file(line_query_result)
    polygons = polygon_splitter(polygons, lines)

    store_folder = path_handler.get_geojsons_folder(
        removed=True, combined=False)

    if not os.path.exists(store_folder):
        os.makedirs(store_folder)

    store_path = path_handler.get_geojsons_path(
        removed=True, combined=False, file_num=geo_num)

    polygons.to_file(
        store_path, driver='GeoJSON')


if __name__ == '__main__':

    remove_none_land_area(1310)
    print("Done")
