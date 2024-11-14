import os
import numpy as np
import rasterio
import configparser

# 導入自定義模組中的函數
from borderdetection.borderdetection import detect
from borderdetection.mask2geojson import mask2geojson
from borderdetection.npy2mask import npy2mask
from borderdetection.geojson2tif import geojson2tif
from borderdetection.loss import calculate_metrics
from remove_none_land_area import remove_none_land_area
from osm_data_fetcher import fetch_osm_landuse_data
from border_polygon_merger import merge_polygons_on_edge
from utils import find_intersect_tifs, PathHandler


# 讀取 config.ini 檔案以設定參數
config = configparser.ConfigParser()
config.read('config.ini')

# 抽取參數，從設定檔案中讀取
threshold = config.getint('PARAMETERS', 'threshold')
combined = config.getboolean('PARAMETERS', 'combined')
normalize = config.get('PARAMETERS', 'normalize')
sigmaX = config.getint('PARAMETERS', 'sigmaX')
pre_kernel_size = config.getint('PARAMETERS', 'pre_kernel_size')
post_kernel_size = config.getint('PARAMETERS', 'post_kernel_size')
img_path = config.get('PARAMETERS', 'img_path')


def main(threshold=12, combined=True, normalize='rescale', sigmaX=5, pre_kernel_size=3, post_kernel_size=3, img_path="../data/west_pasaman/satellite_image"):
    """
    主函數，用於執行整體邊界檢測和後處理流程。

    Args:
        threshold (int): 檢測邊界的閾值。
        combined (bool): 是否合併重疊的多邊形。
        normalize (str): 正規化方法。
        sigmaX (int): Gaussian 模糊的 sigma 值。
        pre_kernel_size (int): 邊界檢測前處理核大小。
        post_kernel_size (int): 邊界檢測後處理核大小。
        img_path (str): 衛星影像的路徑。
    """

    # 初始化路徑處理器
    path_handler = PathHandler(img_path)
    print(path_handler.region_name)
    # 設定最大邊界變數與座標參考系 (CRS)
    max_bound = {'right': None, 'bottom': None, 'left': None, 'top': None}
    crs = None

    # 讀取圖像的邊界
    for tif_num in os.listdir(img_path):
        if tif_num.endswith(".tif"):
            tif_num = tif_num.split(".")[0]
            with rasterio.open(f"{img_path}/{tif_num}.tif") as src:
                bounds = src.bounds
                crs = src.crs
                # 更新最大邊界
                if max_bound['right'] is None:
                    max_bound = {'right': bounds.right, 'bottom': bounds.bottom,
                                 'left': bounds.left, 'top': bounds.top}
                    continue
                max_bound = {
                    'right': max(max_bound['right'], bounds.right),
                    'bottom': min(max_bound['bottom'], bounds.bottom),
                    'left': min(max_bound['left'], bounds.left),
                    'top': max(max_bound['top'], bounds.top)
                }
    print(f"Max bound: {max_bound}")

    # 提取 OSM 地區用途資料
    fetch_osm_landuse_data(max_bound, crs)

    # 執行邊界檢測
    detect(normalize=normalize, sigmaX=sigmaX, pre_kernel_size=(pre_kernel_size, pre_kernel_size),
           post_kernel_size=(post_kernel_size, post_kernel_size), img_path=img_path)
    print("Border detection completed.")

    # 後處理步驟：將檢測到的灰度影像轉為 GeoJSON 格式
    pred_gray_nps_path = path_handler.get_pred_gray_nps_folder()
    pred_gray_nps = os.listdir(pred_gray_nps_path)
    geo_folder = path_handler.get_geojsons_folder(
        removed=False, combined=False)

    for pred_gray_np in pred_gray_nps:
        if pred_gray_np.endswith(".npy"):
            np_num = pred_gray_np.split(".")[0]
            print(f"Processing {np_num}")

            # 檢查並建立灰度遮罩資料夾
            mask_folder = path_handler.get_gray_mask_folder()
            if not os.path.exists(mask_folder):
                os.makedirs(mask_folder)

            # 轉換 npy 檔為遮罩圖
            npy2mask(file_num=np_num, ans=False,
                     threshold=threshold, img_path=img_path)

            # 檢查並建立 GeoJSON 資料夾
            if not os.path.exists(geo_folder):
                os.makedirs(geo_folder)

            # 將遮罩圖轉為 GeoJSON 格式
            mask_path = path_handler.get_gray_mask_path(threshold, np_num)
            store_path = path_handler.get_geojsons_path(
                removed=False, combined=False, file_num=np_num)
            mask2geojson(mask_path, thres=threshold, combined=combined,
                         rmv_overlap=True, ans=False, file_num=np_num, store_path=store_path)

    # 去除非土地區域
    for geo_path in os.listdir(geo_folder):
        if geo_path.endswith(".geojson"):
            geo_num = geo_path.split(".")[0]
            print(f"Processing {geo_num}")
            remove_none_land_area(geo_num, path_handler)

    # 合併邊界上的多邊形
    neighbor_tifs = find_intersect_tifs(img_path)
    geo_removed_folder = path_handler.get_geojsons_folder(
        removed=True, combined=False)

    for geo_path in os.listdir(geo_removed_folder):
        if geo_path.endswith(".geojson"):
            geo_num = geo_path.split(".")[0]
            print(f"Processing {geo_num}")
            merge_polygons_on_edge(
                geo_num, neighbor_tifs=neighbor_tifs, path_handler=path_handler)


if __name__ == "__main__":
    main(threshold=threshold, combined=combined, normalize=normalize, sigmaX=sigmaX,
         pre_kernel_size=pre_kernel_size, post_kernel_size=post_kernel_size, img_path=img_path)
