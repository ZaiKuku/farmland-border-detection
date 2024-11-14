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

from utils import find_intersect_tifs


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
    return gpd.GeoDataFrame(geometry=filtered, crs=polygons.crs)


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


def merge_polygons_on_edge(geo_tif_num, img_path, data_path, threshold=12, neighbor_tifs=None):
    geo_tif_num = geo_tif_num.split("_")[0]
    polygons = gpd.read_file(
        f'./geojson/preds/{geo_tif_num}_threshold_{threshold}_combined_True_3857.geojson')
    edges = get_bounds(f'{img_path}/{geo_tif_num}.tif')
    print(edges)
    pos = 'right'
    for pos in ['right', 'bottom']:
        tif = neighbor_tifs[geo_tif_num].get(pos)
        print(tif)
        polygons_path = f'{
            data_path}/{tif}_threshold_{threshold}_combined_True_3857.geojson'
        direction = 'East' if pos == 'right' else 'South'
        edge = edges[edges.side == direction].geometry.values[0]
        polygons_pos = gpd.read_file(polygons_path)
        polygons_pos = filter_polygons_on_edge(polygons_pos, edge)
        polygons = merge_polygons(polygons, polygons_pos)

    polygons.to_file(
        f"./geojson/preds/{geo_tif_num}_threshold_{threshold}_combined_True_3857.geojson", driver='GeoJSON')


if __name__ == '__main__':
    merge_polygons_on_edge(1310)
    print("Done")
