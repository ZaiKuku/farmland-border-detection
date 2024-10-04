import rasterio
from rasterio import features
import geopandas as gpd
import pandas as pd
from shapely.geometry import shape, Polygon
from shapely import concave_hull, union_all
import numpy as np

thres = 20
file_num = "tile_0"
combined = True
rmv_overlap = True
ans = False

# mode = "filtered"


def find_polygons_in_distance(target, polygons, distance):
    in_range = []
    for polygon in polygons:
        if target == polygon:
            continue
        if target.distance(polygon) <= distance and polygon.area < 1041:
            in_range.append(polygon)
    return in_range


def remove_overlapping(polygons):
    for i in range(len(polygons)):
        if polygons[i].is_empty:
            continue
        for j in range(i+1, len(polygons)):
            if polygons[i].intersects(polygons[j]):
                if polygons[i].contains(polygons[j]):
                    print("remove contains")
                    polygons[j] = Polygon()
                elif polygons[j].contains(polygons[i]):
                    print("remove contains")
                    polygons[i] = Polygon()
                    break
                # else:
                #     if polygons[i].area > polygons[j].area:
                #         polygons[j] = polygons[j].difference(polygons[i])
                #         print("remove overlap")
                #     else:
                #         polygons[i] = polygons[i].difference(polygons[j])
                #         print("remove overlap")
    return polygons


def find_convex_hull(polygons, distance):
    convex_hulls = []
    for polygon in polygons:
        # if polygon.area < 5e-06:
        #     continue
        print("processing", polygon)
        in_range = find_polygons_in_distance(polygon, polygons, distance)
        if len(in_range) == 0:
            continue
        # 將目標多邊形與所有在範圍內的多邊形合併
        union = union_all([polygon] + in_range)
        # print("combined", union)
        # 創建凸包
        convex_hull = union.convex_hull
        convex_hulls.append(convex_hull)

        # 刪除被合併的多邊形
        for p in in_range:
            polygons.remove(p)

        # 刪除目標多邊形
        polygons.remove(polygon)

    for polygon in polygons:
        convex_hulls.append(polygon)
    if rmv_overlap:
        convex_hulls = remove_overlapping(convex_hulls)

    return convex_hulls


def find_concave_hull(polygons, distance):
    concave_hulls = []
    for polygon in polygons:
        in_range = find_polygons_in_distance(polygon, polygons, distance)
        if len(in_range) == 0:
            continue
        # 將目標多邊形與所有在範圍內的多邊形合併
        union = union_all([polygon] + in_range)

        # 創建凹包
        concave_ = concave_hull(union, ratio=0.8)
        print("concave success")
        concave_hulls.append(concave_)

        # 刪除被合併的多邊形
        for p in in_range:
            polygons.remove(p)

        # 刪除目標多邊形
        polygons.remove(polygon)


def mask2geojson(path, thres, combined, rmv_overlap, ans, file_num):
    mode = "combined" if combined else "filtered"
    folder = "answers" if ans else "preds"
    # 讀取 raster 文件
    with rasterio.open(path) as src:
        image = src.read(1)  # 假設是單波段圖像
        transform = src.transform

    # 將 raster 轉換為 polygons (disaggregate)
    shapes = features.shapes(image, transform=transform)
    polygons = [shape(s) for s, v in shapes if v == 0]

    # remove small polygons
    polygons = [p for p in polygons if p.area >= 60]

    if combined:
        polygons = find_convex_hull(polygons, 0.0005)

    # 創建 GeoDataFrame
    th_4_sf = gpd.GeoDataFrame({'geometry': polygons}, crs=src.crs)

    # 過濾和處理 polygons
    th_4_disagg_sf = th_4_sf[th_4_sf.geometry.type == 'Polygon']
    th_4_disagg_sf['area'] = th_4_disagg_sf.geometry.area
    print(th_4_disagg_sf.describe())

    # aggregate polygons
    # th_4_disagg_sf = th_4_disagg_sf[th_4_disagg_sf.area >= 5.616049e-09]

    # 過濾掉 geometry 為空之 rows
    th_4_disagg_sf_filtered = th_4_disagg_sf[~th_4_disagg_sf.is_empty]

    # 創建凸包 (convexhull) (或凹包(concavehull))
    th_4_disagg_sf_list = []
    for idx, row in th_4_disagg_sf_filtered.iterrows():
        if not row.geometry.is_empty:
            # 使用 convex_hull
            # convex_hull = row.geometry.convex_hull
            # 使用 concave_hull
            try:
                row_geom_concave_hull = concave_hull(row.geometry, ratio=0.8)
                th_4_disagg_sf_list.append(gpd.GeoDataFrame(
                    {'geometry': [row_geom_concave_hull]}, crs=th_4_disagg_sf_filtered.crs))
            except:
                print("concave hull failed")
                continue

    # 合併結果
    result = pd.concat(th_4_disagg_sf_list)

    if not ans:
        # 保存為 GeoJSON
        # 19772_threshold_26_combined_True_3857
        result.to_file(f"./geojson/{folder}/{file_num}_threshold_{thres}_{mode}_{rmv_overlap}_3857.geojson",
                       driver='GeoJSON')

        # 將 EPSG:3857 之 geo-dataframe 的座標系統轉回 EPSG:4326 (經緯度)
        result_4326 = result.to_crs(4326)
        result_4326.to_file(
            f"./geojson/{folder}/{file_num}_threshold_{thres}_{mode}_{rmv_overlap}_4326.geojson", driver='GeoJSON')
    else:
        result.to_file(f"./geojson/{folder}/{file_num}_answer.geojson",
                       driver='GeoJSON')


if __name__ == "__main__":
    mask2geojson(
        f"./gray_mask/2m_preds/threshold_{thres}.tif", thres, combined, rmv_overlap, ans, file_num)
