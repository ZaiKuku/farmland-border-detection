import rasterio
from rasterio import features
import geopandas as gpd
import pandas as pd
from shapely.geometry import shape, Polygon
from shapely import concave_hull, union_all
import numpy as np
import os

from utils import PathHandler


def find_polygons_in_distance(polygons: list[Polygon], distance: float = 0.0005) -> dict:
    """
    找出所有在指定距離內的多邊形。

    Args:
        polygons (list[Polygon]): 多邊形的列表。
        distance (float): 設定的距離範圍。

    Returns:
        dict: 包含每個多邊形索引和其鄰近的多邊形索引。
    """
    n = len(polygons)
    row_indices = np.repeat(np.arange(n), n)
    col_indices = np.tile(np.arange(n), n)
    gdf = gpd.GeoDataFrame(geometry=polygons, crs=3857)

    a_gdf = gdf.iloc[row_indices]
    b_gdf = gdf.iloc[col_indices]

    gdf_within_result = a_gdf.geometry.dwithin(
        b_gdf.geometry, distance, align=False)

    output_dict = {}
    for row_idx, col_idx in zip(row_indices[gdf_within_result], col_indices[gdf_within_result]):
        if row_idx != col_idx:
            if row_idx not in output_dict:
                output_dict[row_idx] = []
            output_dict[row_idx].append(col_idx)
    return output_dict


def remove_overlapping(polygons: list[Polygon]) -> list[Polygon]:
    """
    移除重疊區域的多邊形，並保留僅含非重疊部分的多邊形。

    Args:
        polygons (list[Polygon]): 多邊形的列表。

    Returns:
        list[Polygon]: 移除重疊部分後的多邊形列表。
    """
    n = len(polygons)
    row_indices = np.repeat(np.arange(n), n)
    col_indices = np.tile(np.arange(n), n)
    gdf = gpd.GeoDataFrame(geometry=polygons, crs=3857)

    a_gdf = gdf.iloc[row_indices]
    b_gdf = gdf.iloc[col_indices]
    gdf_intersects_result = a_gdf.geometry.intersects(
        b_gdf.geometry, align=False)

    output_dict = {}
    for row_idx, col_idx in zip(row_indices[gdf_intersects_result], col_indices[gdf_intersects_result]):
        if row_idx != col_idx:
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


def find_convex_hull(polygons: list[Polygon], distance: float, rmv_overlap: bool = True) -> list[Polygon]:
    """
    建立指定距離內的多邊形的凸包，並可選擇是否移除重疊部分。

    Args:
        polygons (list[Polygon]): 多邊形的列表。
        distance (float): 設定的距離範圍。
        rmv_overlap (bool): 是否移除重疊部分。預設為 True。

    Returns:
        list[Polygon]: 包含凸包的多邊形列表。
    """
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


def find_concave_hull(polygons: list[Polygon], distance: float) -> None:
    """
    建立指定距離內的多邊形的凹包。

    Args:
        polygons (list[Polygon]): 多邊形的列表。
        distance (float): 設定的距離範圍。
    """
    concave_hulls = []
    for polygon in polygons:
        in_range = find_polygons_in_distance(polygon, polygons, distance)
        if len(in_range) == 0:
            continue
        union = union_all([polygon] + in_range)
        concave_ = concave_hull(union, ratio=0.8)
        concave_hulls.append(concave_)

        for p in in_range:
            polygons.remove(p)
        polygons.remove(polygon)


def mask2geojson(path: str, thres: int, combined: bool, rmv_overlap: bool, ans: bool, file_num: str, store_path: str) -> None:
    """
    將遮罩 (mask) 影像轉換為 GeoJSON 格式的多邊形資料。

    Args:
        path (str): 遮罩影像文件的路徑。
        thres (int): 設定的閾值。
        combined (bool): 是否合併相鄰的多邊形。
        rmv_overlap (bool): 是否移除重疊區域。
        ans (bool): 是否將結果儲存於答案資料夾。
        file_num (str): 檔案號碼。
        store_path (str): 存檔路徑。
    """
    mode = "combined" if combined else "filtered"
    folder = "answers" if ans else "preds"

    with rasterio.open(path) as src:
        image = src.read(1)
        transform = src.transform

    shapes = features.shapes(image, transform=transform)
    polygons = [shape(s) for s, v in shapes if v == 0]

    polygons = [p for p in polygons if p.area >= 60]

    print("Start find convex hull")
    if combined:
        polygons = find_convex_hull(polygons, 0.0000005, rmv_overlap)

    th_4_sf = gpd.GeoDataFrame({'geometry': polygons}, crs=src.crs)

    th_4_disagg_sf = th_4_sf[th_4_sf.geometry.type == 'Polygon']
    th_4_disagg_sf['area'] = th_4_disagg_sf.geometry.area

    th_4_disagg_sf_filtered = th_4_disagg_sf[~th_4_disagg_sf.is_empty]
    th_4_disagg_sf_filtered = th_4_disagg_sf[th_4_disagg_sf_filtered.area >= 1000]
    th_4_disagg_sf_list = []

    for idx, row in th_4_disagg_sf_filtered.iterrows():
        if not row.geometry.is_empty:
            try:
                row_geom_concave_hull = concave_hull(row.geometry, ratio=0.8)
                th_4_disagg_sf_list.append(gpd.GeoDataFrame(
                    {'geometry': [row_geom_concave_hull]}, crs=th_4_disagg_sf_filtered.crs))
            except:
                print("concave hull failed")
                continue

    if len(th_4_disagg_sf_list) > 0:
        result = pd.concat(th_4_disagg_sf_list)
        result.to_file(store_path, driver='GeoJSON')
        print("To GeoJSON success")


if __name__ == "__main__":
    thres = 20
    file_num = "tile_0"
    combined = True
    rmv_overlap = True
    ans = False
    path = f"./gray_mask/preds/threshold_{thres}.tif"
    mask2geojson(
        f"./gray_mask/2m_preds/threshold_{thres}.tif", thres, combined, rmv_overlap, ans, file_num)
