import geopandas as gpd
from shapely.geometry import Polygon, LineString, MultiLineString, MultiPolygon
import matplotlib.pyplot as plt
import pandas as pd

import rasterio
from rasterio.plot import reshape_as_image
import matplotlib.pyplot as plt
from shapely.geometry import LineString
from shapely.ops import unary_union
import geopandas as gpd

# 指定 GeoTIFF 檔案路徑
tif_path = '../data/lyon_2m/1310.tif'
tif2_path = '../data/lyon_2m/1311.tif'


def get_right_and_bottom_tif(tif_num):

    # dict ={tif_num:{right: right_tif_num, bottom: bottom_tif_num}}
    # return f'../data/lyon_2m/{right_tif_num}.tif', f'../data/lyon_2m/{bottom_tif_num}.tif'
    return f'../data/lyon_2m/{tif_num}.tif', f'../data/lyon_2m/{tif_num+1}.tif'


def get_bounds(tif_path):
    with rasterio.open(tif_path) as src:
        bounds = src.bounds

        crs = src.crs

        east_line = LineString([
            (bounds.right, bounds.bottom),
            (bounds.right, bounds.top)
        ])

        south_line = LineString([
            (bounds.left, bounds.bottom),
            (bounds.right, bounds.bottom)
        ])

        edges = gpd.GeoDataFrame({
            'side': ['East', 'South'],
            'geometry': [east_line, south_line]
        }, crs=crs)

        return edges


def filter_polygons_on_edge(polygons, edge):
    filtered = []
    for idx, poly in polygons.iterrows():
        shared_edge = poly.geometry.intersects(edge)
        if isinstance(shared_edge, (LineString, MultiLineString)):
            filtered.append(poly)
    return gpd.GeoDataFrame(filtered, crs=polygons.crs)


def merge_polygons(polygons1, polygons2):
    merged = gpd.GeoDataFrame()
    for idx, poly1 in polygons1.iterrows():
        for idx2, poly2 in polygons2.iterrows():
            if poly1.geometry.intersects(poly2.geometry):
                shared = poly1.geometry.intersection(poly2.geometry)
                if isinstance(shared, (LineString, MultiLineString)):
                    multipolygon = unary_union(
                        [poly1.geometry, poly2.geometry])
                    merged = pd.concat([merged, gpd.GeoDataFrame(
                        {'geometry': [multipolygon]}, crs=polygons1.crs)])

    return merged


def merge_polygons_on_edge(geo_tif_num):
    tif_path = f'../data/lyon_2m/{geo_tif_num}.tif'

    tif_right_path, tif_bottom_path = get_right_and_bottom_tif(geo_tif_num)

    edges = get_bounds(tif_path)
    east_line = edges[edges.side == 'East'].geometry.values[0]
    south_line = edges[edges.side == 'South'].geometry.values[0]

    polygons = gpd.read_file(
        f'./geojson/preds/{geo_tif_num}_threshold_26_filtered_True_3857.geojson')

    polygons_right = gpd.read_file(tif_right_path)
    polygons_bottom = gpd.read_file(tif_bottom_path)

    polygons_east = filter_polygons_on_edge(polygons, east_line)
    polygons_south = filter_polygons_on_edge(polygons, south_line)

    polygons_right = filter_polygons_on_edge(polygons_right, east_line)
    polygons_bottom = filter_polygons_on_edge(polygons_bottom, south_line)

    merged = merge_polygons(polygons_east, polygons_right)
    merged.concat(merge_polygons(polygons_south, polygons_bottom))

    merged.to_file(
        f"test.geojson",
        driver='GeoJSON')


if __name__ == '__main__':
    merge_polygons_on_edge(1310)
    print("Done")
