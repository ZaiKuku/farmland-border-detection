import os
import numpy as np

from borderdetection.borderdetection import detect
from borderdetection.mask2geojson import mask2geojson
from borderdetection.npy2mask import npy2mask
from borderdetection.geojson2tif import geojson2tif
from borderdetection.loss import calculate_metrics


def main(threshold=12, combined=True, normalize='rescale', sigmaX=5, pre_kernel_size=3, post_kernel_size=3):

    detect(normalize=normalize, sigmaX=sigmaX,
           pre_kernel_size=(pre_kernel_size, pre_kernel_size), post_kernel_size=(post_kernel_size, post_kernel_size))
    print("Border detection completed.")
    pred_gray_nps = os.listdir("./pred_gray/preds")

    for pred_gray_np in pred_gray_nps:
        if pred_gray_np.endswith(".npy"):
            np_num = pred_gray_np.split(".")[0]
            print(f"Processing {np_num}")

            npy2mask(np_num, False, threshold)
            path = f"./gray_mask/preds/threshold_{threshold}.tif"

            mask2geojson(
                path, thres=threshold, combined=combined, rmv_overlap=True, ans=False, file_num=np_num)


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
    threshold = 16
    combined = True
    normalize = 'translate'
    sigmaX = 5
    pre_kernel_size = 5
    post_kernel_size = 5

    main(threshold=threshold, combined=combined, normalize=normalize,
         sigmaX=sigmaX, pre_kernel_size=pre_kernel_size, post_kernel_size=post_kernel_size)
