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
path = f"./gray_mask/preds/threshold_{thres}.tif"
# mode = "filtered"


def find_polygons_in_distance(polygons, distance=0.0005):
    # in_range = []
    # for polygon in polygons:
    #     if target == polygon:
    #         continue
    #     if target.distance(polygon) <= distance and polygon.area < 1041:
    #         in_range.append(polygon)
    # 假設 polygon_gdf 有 114 行
    n = len(polygons)  # 獲取 GeoDataFrame 的行數
    # 生成 [0, 0, 0, ..., 113, 113] 的矩陣
    row_indices = np.repeat(np.arange(n), n)
    # 生成 [0, 1, 2, ..., 113, 0, 1, 2, ..., 113] 的矩陣
    col_indices = np.tile(np.arange(n), n)

    gdf = gpd.GeoDataFrame(geometry=polygons, crs=3857)

    a_gdf = gdf.iloc[row_indices]
    b_gdf = gdf.iloc[col_indices]

    # 如果需要計算 pariwised 距離
    # a_gdf.geometry.distance(b_gdf.geometry, align=False)

    gdf_within_result = a_gdf.geometry.dwithin(
        b_gdf.geometry, distance, align=False)

    # 整理結果至 dict
    output_dict = {}
    for row_idx, col_idx in zip(row_indices[gdf_within_result], col_indices[gdf_within_result]):
        if row_idx != col_idx:  # Only add pairs where row_idx != col_idx
            if row_idx not in output_dict:
                output_dict[row_idx] = []
            output_dict[row_idx].append(col_idx)
    return output_dict


def remove_overlapping(polygons):
    n = len(polygons)  # 獲取 GeoDataFrame 的行數

    row_indices = np.repeat(np.arange(n), n)

    col_indices = np.tile(np.arange(n), n)

    gdf = gpd.GeoDataFrame(geometry=polygons, crs=3857)

    a_gdf = gdf.iloc[row_indices]
    b_gdf = gdf.iloc[col_indices]

    gdf_intersects_result = a_gdf.geometry.intersects(
        b_gdf.geometry, align=False)

    output_dict = {}
    for row_idx, col_idx in zip(row_indices[gdf_intersects_result], col_indices[gdf_intersects_result]):
        if row_idx != col_idx:  # Only add pairs where row_idx != col_idx
            if row_idx not in output_dict:
                output_dict[row_idx] = []
            output_dict[row_idx].append(col_idx)

    output_polygons = []

    for i in range(len(polygons)):
        if i not in output_dict.keys():
            output_polygons.append(polygons[i])
        else:
            try:
                for j in output_dict[i]:
                    if polygons[i].contains(polygons[j]):
                        polygons[j] = Polygon()
                        output_dict.pop(j)
                    elif polygons[j].contains(polygons[i]):
                        polygons[i] = Polygon()
                        output_dict.pop(i)
                        break
                    elif polygons[i].area > polygons[j].area:
                        polygons[j] = polygons[j].difference(polygons[i])
                    else:
                        polygons[i] = polygons[i].difference(polygons[j])
            except:
                print(f'Error at {i} and {j}')
                continue
            output_polygons.append(polygons[i])

    output_polygons = [p for p in output_polygons if not p.is_empty]
    return output_polygons


def find_convex_hull(polygons, distance):
    convex_hulls = []
    in_range = find_polygons_in_distance(polygons, distance)
    for key, value in in_range.items():
        union = union_all([polygons[key]] + [polygons[v] for v in value])
        convex_hull = union.convex_hull
        convex_hulls.append(convex_hull)

    for i in range(len(polygons)):
        if i not in in_range.keys():
            convex_hulls.append(polygons[i])

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

    print("Start find convex hull")
    if combined:
        polygons = find_convex_hull(polygons, 0.0005)

    # 創建 GeoDataFrame
    th_4_sf = gpd.GeoDataFrame({'geometry': polygons}, crs=src.crs)

    # 過濾和處理 polygons
    th_4_disagg_sf = th_4_sf[th_4_sf.geometry.type == 'Polygon']
    th_4_disagg_sf['area'] = th_4_disagg_sf.geometry.area

    # aggregate polygons
    # th_4_disagg_sf = th_4_disagg_sf[th_4_disagg_sf.area >= 5.616049e-09]

    # 過濾掉 geometry 為空之 rows
    th_4_disagg_sf_filtered = th_4_disagg_sf[~th_4_disagg_sf.is_empty]
    th_4_disagg_sf_filtered = th_4_disagg_sf[th_4_disagg_sf_filtered.area >= 1000]
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
    if len(th_4_disagg_sf_list) > 0:
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

        print("To GeoJSON success")


if __name__ == "__main__":
    mask2geojson(
        f"./gray_mask/2m_preds/threshold_{thres}.tif", thres, combined, rmv_overlap, ans, file_num)
