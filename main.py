import os
import numpy as np
import rasterio

from borderdetection.borderdetection import detect
from borderdetection.mask2geojson import mask2geojson
from borderdetection.npy2mask import npy2mask
from borderdetection.geojson2tif import geojson2tif
from borderdetection.loss import calculate_metrics

from remove_none_land_area import remove_none_land_area
from osm_data_fetcher import fetch_osm_landuse_data
from border_polygon_merger import merge_polygons_on_edge
from utils import find_intersect_tifs

import configparser

# 讀取 config.ini 檔案
config = configparser.ConfigParser()
config.read('config.ini')

# 抽取參數
threshold = config.getint('PARAMETERS', 'threshold')
combined = config.getboolean('PARAMETERS', 'combined')
normalize = config.get('PARAMETERS', 'normalize')
sigmaX = config.getint('PARAMETERS', 'sigmaX')
pre_kernel_size = config.getint('PARAMETERS', 'pre_kernel_size')
post_kernel_size = config.getint('PARAMETERS', 'post_kernel_size')
img_path = config.get('PARAMETERS', 'img_path')


def main(threshold=12, combined=True, normalize='rescale', sigmaX=5, pre_kernel_size=3, post_kernel_size=3, img_path="../data/west_pasaman/satellite_image"):

    # land area
    max_bound = {'right': None, 'bottom': None, 'left': None, 'top': None}
    crs = None
    for tif_num in os.listdir(img_path):

        if tif_num.endswith(".tif"):
            tif_num = tif_num.split(".")[0]
            # print(f"Processing {tif_num}")
            with rasterio.open(f"{img_path}/{tif_num}.tif") as src:
                bounds = src.bounds
                crs = src.crs
                if max_bound['right'] is None:
                    max_bound = {'right': bounds.right, 'bottom': bounds.bottom,
                                 'left': bounds.left, 'top': bounds.top}
                    continue
                max_bound = {'right': max(max_bound['right'], bounds.right), 'bottom': min(
                    max_bound['bottom'], bounds.bottom), 'left': min(max_bound['left'], bounds.left), 'top': max(max_bound['top'], bounds.top)}

    print(max_bound, crs)

    # fetch osm landuse data
    fetch_osm_landuse_data(max_bound, crs)

    # detection
    detect(normalize=normalize, sigmaX=sigmaX,
           pre_kernel_size=(pre_kernel_size, pre_kernel_size), post_kernel_size=(post_kernel_size, post_kernel_size), img_path=img_path)
    print("Border detection completed.")

    # clear previous results
    # only works on linux
    if os.path.exists("./gray_mask/preds"):
        os.system("rm -r ./gray_mask/preds")

    if os.path.exists("./geojsons/preds"):
        os.system("rm -r ./geojsons/preds")

    # post-processing
    pred_gray_nps = os.listdir("./pred_gray/preds")

    for pred_gray_np in pred_gray_nps:
        if pred_gray_np.endswith(".npy"):
            np_num = pred_gray_np.split(".")[0]
            print(f"Processing {np_num}")

            npy2mask(np_num, False, threshold, img_path=img_path)
            path = f"./gray_mask/preds/threshold_{threshold}.tif"

            mask2geojson(
                path, thres=threshold, combined=combined, rmv_overlap=True, ans=False, file_num=np_num)

    # remove none land area
    for geo_path in os.listdir("./geojson/preds"):
        if geo_path.endswith(".geojson"):
            geo_path = geo_path.split(".")[0]
            print(f"Processing {geo_path}")
            remove_none_land_area(geo_path)

    # merge polygons on edge
    neighbor_tifs = find_intersect_tifs(img_path)

    for geo_num in os.listdir("./geojson/preds"):
        print(f"Processing {geo_num}")
        if geo_num.endswith(".geojson"):
            geo_num = geo_num.split(".")[0]
            merge_polygons_on_edge(
                geo_num, img_path=img_path, data_path="./geojson/preds", threshold=threshold, neighbor_tifs=neighbor_tifs)


if __name__ == "__main__":
    ########################################################################################
    # multiple runs
    # for threshold in range(8, 12, 2):
    #     for normalize in ['standardize', 'rescale', 'translate']:
    #         for kernel_size in range(3, 8, 2):
    #             print(f"Starting threshold {threshold}, normalize {
    #                 normalize}, kernel size {kernel_size}")
    #             main(threshold=threshold, combined=True, normalize=normalize,
    #                  pre_kernel_size=kernel_size, post_kernel_size=kernel_size)
    #             print(f"Threshold {threshold} completed.")
    #             print("--------------------------------------------------")

    ########################################################################################
    # single run

    main(threshold=threshold, combined=combined, normalize=normalize,
         sigmaX=sigmaX, pre_kernel_size=pre_kernel_size, post_kernel_size=post_kernel_size, img_path=img_path)
