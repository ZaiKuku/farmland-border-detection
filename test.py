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
    merged = []
    for idx, poly1 in polygons1.iterrows():
        for idx2, poly2 in polygons2.iterrows():
            if poly1.geometry.intersects(poly2.geometry):
                shared = poly1.geometry.intersection(poly2.geometry)
                if isinstance(shared, (Polygon, MultiPolygon)):
                    merged.append(shared)
    return gpd.GeoDataFrame(merged, crs=polygons1.crs)


with rasterio.open(tif_path) as src:
    bounds = src.bounds

    crs = src.crs

    west_line = LineString([
        (bounds.left, bounds.bottom),
        (bounds.left, bounds.top)
    ])

    east_line = LineString([
        (bounds.right, bounds.bottom),
        (bounds.right, bounds.top)
    ])

    south_line = LineString([
        (bounds.left, bounds.bottom),
        (bounds.right, bounds.bottom)
    ])

    north_line = LineString([
        (bounds.left, bounds.top),
        (bounds.right, bounds.top)
    ])

    edges = gpd.GeoDataFrame({
        'side': ['West', 'East', 'South', 'North'],
        'geometry': [west_line, east_line, south_line, north_line]
    }, crs=crs)

    for idx, row in edges.iterrows():
        print(f"{row['side']} 邊界座標: {list(row['geometry'].coords)}")

    # 視覺化
    fig, ax = plt.subplots(figsize=(8, 8))

    # 繪製光柵圖像
    image = reshape_as_image(src.read())
    ax.imshow(image)

    polygons = gpd.read_file(
        f"./geojson/preds/1310_threshold_26_combined_True_3857.geojson")

    polygons2 = gpd.read_file(
        f"./geojson/preds/1311_threshold_26_combined_True_3857.geojson")

    # 偵測共邊
    shared_edges = []
    for idx, poly in polygons.iterrows():
        for idx2, poly2 in polygons2.iterrows():
            if poly.geometry.intersects(poly2.geometry):
                shared_edges.append((idx, idx2))

    for pair in shared_edges:
        print(f"Polygon {pair[0]+1} 與 {pair[1]+1} 共享邊界")

    # 合併共享邊界polygons
    shared_polygons = gpd.GeoDataFrame()

    for pair in shared_edges:
        poly1 = polygons.iloc[pair[0]].geometry
        poly2 = polygons2.iloc[pair[1]].geometry
        shared = poly1.intersection(poly2)
        if isinstance(shared, (LineString, MultiLineString)):
            multipolygon = unary_union([poly1, poly2])
            shared_polygons = pd.concat([shared_polygons, gpd.GeoDataFrame(
                {'geometry': [multipolygon]}, crs=polygons.crs)])

    # save the result as GeoJSON
    shared_polygons.to_file(
        f"shared_polygons.geojson", driver='GeoJSON')
