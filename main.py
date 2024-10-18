import os
import numpy as np

import mlflow

from borderdetection.borderdetection import detect
from borderdetection.mask2geojson import mask2geojson
from borderdetection.npy2mask import npy2mask
from borderdetection.geojson2tif import geojson2tif
from borderdetection.loss import calculate_metrics


def main(threshold=12, combined=True, normalize='rescale', sigmaX=5, pre_kernel_size=3, post_kernel_size=3):
    mlflow.set_tracking_uri("http://192.168.1.104:5000")
    mlflow.set_experiment("border-detection")

    with mlflow.start_run():

        # detect edges
        mlflow.log_param('sigmaX', sigmaX)

        mlflow.log_param('pre_kernel_size', (pre_kernel_size, pre_kernel_size))
        mlflow.log_param('post_kernel_size',
                         (post_kernel_size, post_kernel_size))
        mlflow.log_param('threshold', threshold)
        mlflow.log_param('Normalize', normalize)

        detect(normalize=normalize, sigmaX=sigmaX,
               pre_kernel_size=(pre_kernel_size, pre_kernel_size), post_kernel_size=(post_kernel_size, post_kernel_size))
        print("Border detection completed.")
        pred_gray_nps = os.listdir("./pred_gray/preds")
        for pred_gray_np in pred_gray_nps:
            if pred_gray_np.endswith(".npy"):
                np_num = pred_gray_np.split(".")[0]

                npy2mask(np_num, False, threshold)
                path = f"./gray_mask/preds/threshold_{threshold}.tif"

                mask2geojson(
                    path, thres=threshold, combined=combined, rmv_overlap=True, ans=False, file_num=np_num)

                geojson2tif(np_num, threshold=threshold, filtered='combined')
                loss = calculate_metrics(np_num)
                mlflow.log_metric("FOM", loss[0], step=int(np_num))
                mlflow.log_metric("RMSE", loss[1], step=int(np_num))
                mlflow.log_metric("PSNR", loss[2], step=int(np_num))


if __name__ == "__main__":
    for threshold in range(12, 32, 2):
        for normalize in ['rescale', 'standardize', 'translate']:
            for kernel_size in range(3, 8, 2):
                print(f"Starting threshold {threshold}, normalize {
                      normalize}, kernel size {kernel_size}")
                main(threshold=threshold, combined=True, normalize=normalize,
                     pre_kernel_size=kernel_size, post_kernel_size=kernel_size)
                print(f"Threshold {threshold} completed.")
                print("--------------------------------------------------")
