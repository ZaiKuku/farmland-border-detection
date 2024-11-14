import numpy as np
import rioxarray
import xarray

from utils import PathHandler


file_num = 37259
ans = False
file_num: int = '087fad6b'
ans: bool = False
threshold: int = 16


def npy2mask(file_num: int = '087fad6b', ans: bool = False, threshold: int = 16, img_path: str = "../data/west_pasaman/satellite_image") -> None:
    # 匯入邊緣檢測結果
    path_handler = PathHandler(img_path)
    pred_gray_nps_path = path_handler.get_pred_gray_nps_folder()

    gray_np_array = np.load(
        f"{pred_gray_nps_path}/{file_num}.npy")
    gray_np_array = gray_np_array.astype(np.uint32)

    # 匯入 .tif （主要是從裡面拿輸出結果的地理資訊 metadata, 再把這些地理資訊 metadata apply 到 numpy matrix 上，使之能輸出為 .tif 檔案）
    gray_da = rioxarray.open_rasterio(
        f"{img_path}/{file_num}.tif")
    # crs: 地理座標系統
    gray_crs = gray_da.rio.crs
    gray_x_coords = gray_da.x
    gray_y_coords = gray_da.y
    # transform: .tif 邊界資訊
    gray_transform = gray_da.rio.transform()

    threshold
    # for i in range(gray_np_array.min(), 150, 2):
    # 比較每個元素是否超過 threshold i, 並將結果從 boolean (True, False) 轉為 int (1, 0)
    ind_mat = (gray_np_array >= threshold).astype(int)

    # 將 npy 轉為 DataArray 並加入地理資訊 metadata
    ind_mat_da = xarray.DataArray(ind_mat, dims=("y", "x"), coords={
        "y": gray_y_coords, "x": gray_x_coords})  # x, y coords
    ind_mat_da.rio.write_crs(gray_crs, inplace=True)  # crs
    ind_mat_da.rio.write_transform(
        gray_transform, inplace=True)  # transform

    mask_path = path_handler.get_gray_mask_path(threshold, file_num)

    # 將含有地理資訊 metadata & data matrix (numpy matrix) 的 DataArray 匯出成 .tif
    ind_mat_da.rio.to_raster(mask_path)

    print(f"No.{file_num}, {threshold} threshold mask saved.")
