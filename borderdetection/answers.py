import numpy as np
import rioxarray
import xarray
import cv2
import os


def read_images(path):
    img_dict = {}
    for img in os.listdir(path):
        if img.endswith(".png"):
            img_path = os.path.join(path, img)
            image = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
            if image is None:
                print(img_path + " not found.")
                continue
            img_dict[img.split(".")[0]] = image
    return img_dict


def save_images(img_dict, path):
    for img_name, img in img_dict.items():
        np.save(f"{path}/{img_name}.npy", img)


if __name__ == '__main__':
    img_path = "../data/crop_delineation/masks"
    img_dict = read_images(img_path)
    save_images(img_dict, "./pred_gray/answers")
