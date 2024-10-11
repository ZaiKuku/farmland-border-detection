import geopandas as gpd
from shapely.geometry import Polygon, LineString, MultiLineString
import matplotlib.pyplot as plt
import pandas as pd

# # 定義多個多邊形
# polygons = [
#     Polygon([(0, 0), (2, 0), (2, 2), (0, 2)]),  # Polygon 1
#     Polygon([(2, 0), (4, 0), (4, 2), (2, 2)]),  # Polygon 2，共邊與 Polygon 1
#     Polygon([(4, 0), (6, 0), (6, 2), (4, 2)]),  # Polygon 3，共邊與 Polygon 2
#     Polygon([(0, 2), (2, 2), (2, 4), (0, 4)]),  # Polygon 4，共邊與 Polygon 1
#     Polygon([(5, 5), (7, 5), (7, 7), (5, 7)])   # Polygon 5，獨立
# ]

# polygons2 = [
#     Polygon([(4, 2), (6, 2), (6, 4), (4, 4)]),  # Polygon 6，共邊與 Polygon 3
#     Polygon([(2, 2), (4, 2), (4, 5), (2, 5)]),  # Polygon 7，共邊與 Polygon 2

# ]


# # 創建 GeoDataFrame
# gdf = gpd.GeoDataFrame({'geometry': polygons2})

# # 建立空間索引
# gdf_sindex = gdf.sindex

# # 函數：檢查兩個多邊形是否共享邊界


# def share_boundary(poly1, poly2):
#     intersection = poly1.intersection(poly2)
#     return isinstance(intersection, (LineString, MultiLineString)) and not intersection.is_empty


# # 偵測共享邊界的多邊形對
# shared_edges = []

# for idx, poly in gdf.iterrows():
#     possible_matches_index = list(
#         gdf_sindex.intersection(poly.geometry.bounds))
#     for match_idx in possible_matches_index:
#         if match_idx <= idx:
#             continue
#         match_poly = gdf.iloc[match_idx].geometry
#         if share_boundary(poly.geometry, match_poly):
#             shared_edges.append((idx, match_idx))

# # 輸出結果
# for pair in shared_edges:
#     print(f"Polygon {pair[0]+1} 與 Polygon {pair[1]+1} 共享邊界")

# # 視覺化
# fig, ax = plt.subplots(figsize=(8, 8))
# gdf.boundary.plot(ax=ax, color='blue', linewidth=1)

# for pair in shared_edges:
#     poly1 = gdf.iloc[pair[0]].geometry
#     poly2 = gdf.iloc[pair[1]].geometry
#     shared = poly1.intersection(poly2)
#     if isinstance(shared, (LineString, MultiLineString)):
#         gpd.GeoSeries([shared]).boundary.plot(ax=ax, color='red', linewidth=2)

# plt.title('共享邊界的多邊形對（紅色線段表示共享邊界）')
# plt.xlabel('X')
# plt.ylabel('Y')
# plt.show()

import rasterio
from rasterio.plot import reshape_as_image
import matplotlib.pyplot as plt
from shapely.geometry import LineString
import geopandas as gpd

# 指定 GeoTIFF 檔案路徑
tif_path = '../data/lyon_2m/1310.tif'
tif2_path = '../data/lyon_2m/1311.tif'


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
            shared_polygons = shared_polygons.append(
                gpd.GeoDataFrame({'geometry': [shared]}, crs=crs))

    shared_polygons.plot(ax=ax, color='red')

    # 繪製邊界
    edges.boundary.plot(ax=ax, color='blue', linewidth=1)

    plt.title('共享邊界的多邊形對（紅色線段表示共享邊界）')

    plt.show()
