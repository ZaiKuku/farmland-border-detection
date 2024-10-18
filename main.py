import os
import numpy as np

import mlflow

from borderdetection.borderdetection import detect
from borderdetection.mask2geojson import mask2geojson
from borderdetection.npy2mask import npy2mask
from borderdetection.geojson2tif import geojson2tif
from borderdetection.loss import calculate_metrics


def main(threshold=12, combined=True, normalize='rescale'):
    mlflow.set_tracking_uri("http://192.168.1.104:5000")
    mlflow.set_experiment("border-detection")

    with mlflow.start_run():

        # detect edges
        mlflow.log_param('sigmaX', 5)

        mlflow.log_param('pre_kernel_size', (3, 3))
        mlflow.log_param('post_kernel_size', (3, 3))
        mlflow.log_param('threshold', threshold)
        mlflow.log_param('combined', combined)
        mlflow.log_param('Normalize', normalize)

        # detect()
        print("Border detection completed.")
        loss = []
        pred_gray_nps = os.listdir("./pred_gray/preds")
        for pred_gray_np in pred_gray_nps:
            if pred_gray_np.endswith(".npy"):
                np_num = pred_gray_np.split(".")[0]

                npy2mask(np_num, False, threshold)
                path = f"./gray_mask/preds/threshold_{threshold}.tif"

                mask2geojson(
                    path, thres=threshold, combined=combined, rmv_overlap=True, ans=False, file_num=np_num)

                geojson2tif(np_num, threshold=threshold, filtered='combined')
                calculated_loss = calculate_metrics(np_num)

                loss.append(calculated_loss)

        loss_np = np.array(loss)

        mlflow.log_metric("FOM", loss_np[:, 0].mean())
        mlflow.log_metric("RMSE", loss_np[:, 1].mean())
        mlflow.log_metric("PSNR", loss_np[:, 2].mean())


if __name__ == "__main__":
    combined = True
    normalize = 'rescale'  # 'rescale' or 'standardize' or 'translate'
    # main(12, combined, normalize)
    for i in range(12, 30, 2):
        print(f"Sarting threshold {i}")
        main(i)
        print(f"Threshold {i} completed.")
        print("--------------------------------------------------")
