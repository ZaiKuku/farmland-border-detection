import os
import sys

import mlflow

from borderdetection.borderdetection import detect
from borderdetection.mask2geojson import mask2geojson
from borderdetection.npy2mask import npy2mask
from borderdetection.geojson2tif import geojson2tif
from borderdetection.loss import calculate_metrics


def main():
    mlflow.set_tracking_uri("http://192.168.1.104:5000")
    mlflow.set_experiment("border-detection")

    with mlflow.start_run():

        # detect edges
        mlflow.log_param('sigmaX', 5)
        mlflow.log_param('post_binary_threshold', 60)

        mlflow.log_param('pre_kernel_size', (3, 3))
        mlflow.log_param('post_kernel_size', (3, 3))
        mlflow.log_param('canny_threshold', (10, 200))
        mlflow.log_param('threshold', 26)

        detect()

        foms = []
        pred_gray_nps = os.listdir("./pred_gray/preds")
        for pred_gray_np in pred_gray_nps:
            if pred_gray_np.endswith(".npy"):
                np_num = pred_gray_np.split(".")[0]
                npy2mask(np_num, False)
                path = f"./gray_mask/preds/threshold_26.tif"
                mask2geojson(
                    path, thres=26, combined=False, rmv_overlap=True, ans=False, file_num=np_num)

                geojson2tif(np_num)
                foms.append(calculate_metrics(np_num))

        mlflow.log_metric("FOM", sum(foms) / len(foms))


if __name__ == "__main__":
    main()
