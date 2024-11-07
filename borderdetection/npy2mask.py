import numpy as np
import rioxarray
import xarray


file_num = 37259
ans = False


def npy2mask(file_num: int, ans: bool, threshold: int) -> None:
    folder = "answers" if ans else "preds"
    # 匯入邊緣檢測結果
    gray_np_array = np.load(
        f"./pred_gray/{folder}/{file_num}.npy")
    gray_np_array = gray_np_array.astype(np.uint32)

    # 匯入 .tif （主要是從裡面拿輸出結果的地理資訊 metadata, 再把這些地理資訊 metadata apply 到 numpy matrix 上，使之能輸出為 .tif 檔案）
    gray_da = rioxarray.open_rasterio(
        f"../data/lyon_2m/{file_num}.tif")
    # crs: 地理座標系統
    gray_crs = gray_da.rio.crs
    gray_x_coords = gray_da.x
    gray_y_coords = gray_da.y
    # transform: .tif 邊界資訊
    gray_transform = gray_da.rio.transform()

    if not ans:
        i = threshold
        # for i in range(gray_np_array.min(), 150, 2):
        # 比較每個元素是否超過 threshold i, 並將結果從 boolean (True, False) 轉為 int (1, 0)
        ind_mat = (gray_np_array >= i).astype(np.uint8)

        # 將 npy 轉為 DataArray 並加入地理資訊 metadata
        ind_mat_da = xarray.DataArray(ind_mat, dims=("y", "x"), coords={
            "y": gray_y_coords, "x": gray_x_coords})  # x, y coords
        ind_mat_da.rio.write_crs(gray_crs, inplace=True)  # crs
        ind_mat_da.rio.write_transform(
            gray_transform, inplace=True)  # transform

        # 將含有地理資訊 metadata & data matrix (numpy matrix) 的 DataArray 匯出成 .tif
        ind_mat_da.rio.to_raster(
            f"./gray_mask/preds/threshold_{i}.tif")
    else:
        gray_np_array = (gray_np_array >= 5).astype(np.uint8)
        gray_da = xarray.DataArray(gray_np_array, dims=("y", "x"), coords={
            "y": gray_y_coords, "x": gray_x_coords})
        gray_da.rio.write_crs(gray_crs, inplace=True)
        gray_da.rio.write_transform(gray_transform, inplace=True)

        gray_da.rio.to_raster(f"./gray_mask/{folder}/{file_num}.tif")

    print(f"No.{file_num}, {threshold} threshold mask saved.")


if __name__ == '__main__':
    ans = False
    file_num = "tile_0"
    folder = "2m_preds"
    gray_np_array = np.load(
        f"./pred_gray/{folder}/{file_num}.npy")
    gray_np_array = gray_np_array.astype(np.uint32)

    # 匯入 .tif （主要是從裡面拿輸出結果的地理資訊 metadata, 再把這些地理資訊 metadata apply 到 numpy matrix 上，使之能輸出為 .tif 檔案）
    gray_da = rioxarray.open_rasterio(
        f"../data/dk/{file_num}.tif")
    # crs: 地理座標系統
    gray_crs = gray_da.rio.crs
    gray_x_coords = gray_da.x
    gray_y_coords = gray_da.y
    # transform: .tif 邊界資訊
    gray_transform = gray_da.rio.transform()

    if not ans:
        i = 20
        # for i in range(gray_np_array.min(), 150, 2):
        # 比較每個元素是否超過 threshold i, 並將結果從 boolean (True, False) 轉為 int (1, 0)
        ind_mat = (gray_np_array >= i).astype(np.uint8)

        # 將 npy 轉為 DataArray 並加入地理資訊 metadata
        ind_mat_da = xarray.DataArray(ind_mat, dims=("y", "x"), coords={
            "y": gray_y_coords, "x": gray_x_coords})  # x, y coords
        ind_mat_da.rio.write_crs(gray_crs, inplace=True)  # crs
        ind_mat_da.rio.write_transform(
            gray_transform, inplace=True)  # transform

        # 將含有地理資訊 metadata & data matrix (numpy matrix) 的 DataArray 匯出成 .tif
        ind_mat_da.rio.to_raster(
            f"./gray_mask/2m_preds/threshold_{i}.tif")
    else:
        gray_np_array = (gray_np_array >= 5).astype(np.uint8)
        gray_da = xarray.DataArray(gray_np_array, dims=("y", "x"), coords={
            "y": gray_y_coords, "x": gray_x_coords})
        gray_da.rio.write_crs(gray_crs, inplace=True)
        gray_da.rio.write_transform(gray_transform, inplace=True)

        gray_da.rio.to_raster(f"./gray_mask/{folder}/{file_num}.tif")
