import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from rasterio.transform import from_origin
import rasterio

# 讀取經緯度資料的函數


def read_coord():
    coord = pd.read_csv("../data/crop_delineation/clean_data.csv", header=0)
    return coord


if __name__ == '__main__':
    img_path = "../data/crop_delineation/masks"
    csv_path = "../data/crop_delineation/clean_data.csv"  # CSV 路徑
    df = pd.read_csv(csv_path)  # 讀取經緯度資料

    # 確認 TIFF 檔案保存路徑是否存在，若不存在則創建
    output_tif_path = './tifs/answers/'
    os.makedirs(output_tif_path, exist_ok=True)

    for file in os.listdir(img_path):
        if file.endswith(".png"):
            file_num = int(file.split(".")[0])  # 獲取文件對應的數字編號

            # 從 CSV 中提取對應的經緯度邊界
            try:
                max_lat = df[df["indices"] == file_num]["max_lat"].values[0]
                min_lat = df[df["indices"] == file_num]["min_lat"].values[0]
                max_lon = df[df["indices"] == file_num]["max_lon"].values[0]
                min_lon = df[df["indices"] == file_num]["min_lon"].values[0]
            except IndexError:
                print(f"找不到 {file_num} 的經緯度邊界")
                continue

            # 讀取 JPEG 圖片並轉為 numpy 陣列
            img = plt.imread(os.path.join(img_path, file))
            img = np.array(img)

            # 計算光柵的寬度和高度
            height, width = img.shape[:2]
            grid_size_lon = (max_lon - min_lon) / width
            grid_size_lat = (max_lat - min_lat) / height
            print(grid_size_lon, grid_size_lat)

            # 確保圖像為 2D（灰階）或 3D（RGB）格式
            if img.ndim == 2:
                count = 1  # 灰階影像只有一個通道
            elif img.ndim == 3:
                count = img.shape[2]  # RGB 或其他多通道影像
            else:
                print(f"無法處理 {file} 的維度：{img.ndim}")
                continue

            # 設定光柵的變換，從左上角開始 (min_lon, max_lat)，步幅為 grid_size
            transform = from_origin(
                min_lon, max_lat, grid_size_lon, grid_size_lat)

            # 設定保存 TIFF 文件的路徑
            tiff_path = os.path.join(output_tif_path, f'{file_num}.tif')

            # 使用 rasterio 將光柵數據保存為 TIFF
            with rasterio.open(
                    tiff_path, 'w+',
                    driver='GTiff',
                    height=img.shape[0],
                    width=img.shape[1],
                    count=count,
                    dtype=img.dtype,
                    crs='EPSG:4326',  # 設定為 WGS 84 CRS
                    transform=transform) as dst:
                if count == 1:
                    dst.write(img, 1)  # 灰階影像寫入
                else:
                    for i in range(1, count + 1):
                        dst.write(img[:, :, i - 1], i)  # 多通道影像逐層寫入

            print(f"影像已保存為 {tiff_path}")
