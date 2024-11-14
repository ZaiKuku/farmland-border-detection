import os
import cv2
import numpy as np
import matplotlib.pyplot as plt

from borderdetection.process_method import apply_gaussian_blur, generate_superpixels, crop_and_magnify

params = {
    'sigmaX': 5,
    'post_binary_threshold': 60,
    'pre_kernel_size': (3, 3),
    'post_kernel_size': (3, 3),
    'canny_threshold': (10, 200),
}


def preprocess_image(image, kernel_size=(3, 3), sigmaX=5):
    # Convert the original image to grayscale

    # labels, image = generate_superpixels(image)

    # 應用高斯模糊
    image = apply_gaussian_blur(image, kernel_size=kernel_size, sigmaX=sigmaX)

    # crop into 4 quadrants
    # image = crop_and_magnify(image, crop=False, magnify_=False, scale=2)

    return image


def detect_edges(processed_image, method):
    if method == 'canny':
        pred = cv2.Canny(processed_image, params['canny_threshold'][0],
                         params['canny_threshold'][1])
    elif method == 'marr_hildreth':
        laplacian = cv2.Laplacian(processed_image, cv2.CV_64F)
        laplacian_abs = np.absolute(laplacian)
        pred = cv2.convertScaleAbs(laplacian_abs, alpha=10)

    return pred


def postprocess_image(image, kernel_size=(3, 3), sigmaX=5):

    # 應用高斯模糊
    image = apply_gaussian_blur(
        image, kernel_size=kernel_size, sigmaX=sigmaX)
    # _, image = cv2.threshold(
    #     image, params['post_binary_threshold'], 255, cv2.THRESH_BINARY)

    return image


def normalize_brightness(image, normalize='rescale', target_brightness=30):
    if normalize == 'rescale':
        return rescale(image, target_brightness)
    elif normalize == 'standardize':
        return standardize(image)
    elif normalize == 'translate':
        return translate(image, target_brightness)


def rescale(image, target_brightness=30):
    # rescale
    mean_brightness = np.mean(image)

    brightness_factor = target_brightness / mean_brightness

    normalized_image = image * brightness_factor

    normalized_image = np.clip(normalized_image, 0, 255).astype(np.uint8)

    return normalized_image


def standardize(image, target_brightness=30):
    # standardize
    mean_brightness = np.mean(image)
    std_brightness = np.std(image)

    normalized_image = (image - mean_brightness) / std_brightness

    normalized_image = normalized_image * target_brightness + mean_brightness

    normalized_image = np.clip(normalized_image, 0, 255).astype(np.uint8)

    return normalized_image


def translate(image, target_brightness=30):
    # translate
    mean_brightness = np.mean(image)

    brightness_factor = target_brightness - mean_brightness

    normalized_image = image + brightness_factor

    normalized_image = np.clip(normalized_image, 0, 255).astype(np.uint8)

    return normalized_image


def detect(normalize: str = 'rescale', sigmaX: int = 5, pre_kernel_size: tuple = (3, 3), post_kernel_size: tuple = (3, 3), img_path: str = "../data/west_pasaman/satellite_image") -> None:
    # 設置路徑
    images = os.listdir(img_path)

    losses = []
    # start to preprocess images
    for image in images:
        if not image.endswith(".tif") or image.endswith("_ans.tif"):
            continue

        image_path = os.path.join(img_path, image)
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

        if image is None:
            print(image_path + " not found.")
            continue

        # preprocess image
        processed_image = preprocess_image(
            image, kernel_size=pre_kernel_size, sigmaX=sigmaX)

        # detect edges
        # ['canny', 'marr_hildreth']
        pred = detect_edges(processed_image, method='marr_hildreth')

        # postprocess image
        postprocessed_image = postprocess_image(
            pred, kernel_size=post_kernel_size, sigmaX=sigmaX)

        # 檢查圖像大小是否相同

        postprocessed_image = normalize_brightness(
            postprocessed_image, normalize)

        # 補中間檔的路徑
        # if not os.path.exists("./pred_gray/preds"):
        #     os.makedirs("./pred_gray/preds")

        # save the result as npy

        if not os.path.exists(f"./pred_gray/preds"):
            os.makedirs(f"./pred_gray/preds")

        np.save(
            f"./pred_gray/preds/{os.path.basename(image_path).split('.')[0]}.npy", postprocessed_image)
        cv2.imwrite(
            f"./pred_gray/preds/{os.path.basename(image_path).split('.')[0]}.png", postprocessed_image)


if __name__ == "__main__":
    # 設置路徑
    images = os.listdir("../data/dk")

    losses = []
    goodcases = 0
    # start to preprocess images
    for image in images:
        image_path = os.path.join("../data/dk", image)
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

        if image is None:
            print(image_path + " not found.")
            continue

        # preprocess image
        processed_image = preprocess_image(image)

        # detect edges
        # ['canny', 'marr_hildreth']
        pred = detect_edges(processed_image, method='marr_hildreth')

        # postprocess image
        postprocessed_image = postprocess_image(pred)

        cv2.imshow("Original Image", postprocessed_image)
        cv2.waitKey(3000)
        cv2.destroyAllWindows()

        # # save the result as npy
        np.save(
            f"./pred_gray/2m_preds/{os.path.basename(image_path).split('.')[0]}.npy", postprocessed_image)
        cv2.imwrite(
            f"./pred_gray/2m_preds/{os.path.basename(image_path).split('.')[0]}.png", postprocessed_image)

        # cv2.imshow("Processed Image", postprocessed_image)
        # cv2.imshow("Ground Truth", gt)
        # cv2.imshow("Original Image", image)
        # lines = cv2.HoughLinesP(
        #     postprocessed_image, 1, np.pi / 180, 100, minLineLength=100, maxLineGap=10)
        # cv2.imshow("Hough Lines", cv2.convertScaleAbs(lines))
