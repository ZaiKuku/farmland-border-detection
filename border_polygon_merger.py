import geopandas as gpd
from shapely.geometry import Polygon, LineString, MultiLineString, MultiPolygon
import matplotlib.pyplot as plt
import pandas as pd
import os

import rasterio
from rasterio.plot import reshape_as_image
from shapely.geometry import LineString
from shapely.ops import unary_union

from utils import find_intersect_tifs, PathHandler


def get_bounds(tif_path):
    """
    取得影像的邊界，並生成用於合併操作的邊界線。

    Args:
        tif_path (str): GeoTIFF 影像檔案的路徑。

    Returns:
        edges (GeoDataFrame): 包含影像邊界線的 GeoDataFrame，並標記方向（東或南）。
    """
    with rasterio.open(tif_path) as src:
        bounds = src.bounds
        crs = src.crs

        # 建立東邊和南邊的邊界線
        east_line = LineString([
            (bounds.right, bounds.bottom),
            (bounds.right, bounds.top)
        ])
        south_line = LineString([
            (bounds.left, bounds.bottom),
            (bounds.right, bounds.bottom)
        ])

        # 儲存邊界線並設置坐標系
        edges = gpd.GeoDataFrame({
            'side': ['East', 'South'],
            'geometry': [east_line, south_line]
        }, crs=crs)

        return edges


def filter_polygons_on_edge(polygons, edge):
    """
    過濾出與指定邊界線相交的多邊形。

    Args:
        polygons (GeoDataFrame): 包含多邊形的 GeoDataFrame。
        edge (LineString): 用於過濾的邊界線。

    Returns:
        filtered (GeoDataFrame): 與邊界線相交的多邊形。
    """
    filtered = gpd.GeoDataFrame()
    for idx, poly in polygons.iterrows():
        # 檢查多邊形是否與邊界相交
        if poly.geometry.intersects(edge):
            # 將相交的多邊形添加到結果中
            filtered = pd.concat([filtered, gpd.GeoDataFrame(
                {'geometry': [poly.geometry]}, crs=polygons.crs)])

    return filtered


def merge_polygons(polygons1, polygons2):
    """
    合併兩個 GeoDataFrame 中的多邊形，僅合併相交的多邊形。

    Args:
        polygons1 (GeoDataFrame): 第一組多邊形。
        polygons2 (GeoDataFrame): 第二組多邊形。

    Returns:
        merged (GeoDataFrame): 合併後的多邊形。
    """
    merged = gpd.GeoDataFrame()
    for idx, poly1 in polygons1.iterrows():
        for idx2, poly2 in polygons2.iterrows():
            if poly1.geometry.intersects(poly2.geometry):
                # 計算共享區域並合併
                shared = poly1.geometry.intersection(poly2.geometry)
                if shared:
                    multipolygon = unary_union(
                        [poly1.geometry, poly2.geometry])
                    merged = pd.concat([merged, gpd.GeoDataFrame(
                        {'geometry': [multipolygon]}, crs=polygons1.crs)])

    return merged


def merge_polygons_on_edge(geo_tif_num, neighbor_tifs=None, path_handler: PathHandler = None):
    """
    在影像邊界處合併相鄰影像的多邊形。

    Args:
        geo_tif_num (str): 影像編號，用於辨識特定影像。
        neighbor_tifs (dict): 相鄰影像的字典，指定相鄰的影像檔案。
        path_handler (PathHandler): 用於處理路徑的工具類別實例。
    """
    # 讀取當前影像的多邊形
    geo_path = path_handler.get_geojsons_path(
        removed=True, combined=False, file_num=geo_tif_num)
    polygons = gpd.read_file(geo_path)

    # 取得當前影像的邊界
    img_path = path_handler.get_img_path(geo_tif_num)
    edges = get_bounds(img_path)

    # 檢查邊界上的相鄰影像，並進行合併
    for pos in ['right', 'bottom']:
        tif = neighbor_tifs[geo_tif_num].get(pos)
        if tif is None:
            continue
        polygons_path = path_handler.get_geojsons_path(
            removed=True, combined=False, file_num=tif)
        direction = 'East' if pos == 'right' else 'South'
        edge = edges[edges.side == direction].geometry.values[0]

        # 讀取並過濾與邊界相交的多邊形
        polygons_pos = gpd.read_file(polygons_path)
        polygons_pos_on_edge = filter_polygons_on_edge(polygons_pos, edge)
        if polygons_pos_on_edge.empty:
            continue

        # 合併相交的多邊形
        polygons_intersect = merge_polygons(polygons, polygons_pos_on_edge)
        if polygons_intersect.empty:
            continue

        # 移除重疊區域後更新檔案
        polygons_pos = gpd.overlay(
            polygons_pos, polygons_intersect, how='difference')
        polygons = gpd.overlay(polygons, polygons_intersect, how='difference')
        if polygons_pos.empty or polygons.empty:
            continue
        polygons_pos.to_file(polygons_path, driver='GeoJSON')
        polygons = pd.concat([polygons, polygons_intersect])

    # 儲存最終的合併結果
    store_folder = path_handler.get_geojsons_folder(
        removed=True, combined=True)
    if not os.path.exists(store_folder):
        os.makedirs(store_folder)

    store_path = path_handler.get_geojsons_path(
        removed=True, combined=True, file_num=geo_tif_num)
    polygons.to_file(store_path, driver='GeoJSON')
