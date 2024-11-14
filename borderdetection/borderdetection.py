import os
import cv2
import numpy as np
from borderdetection.process_method import apply_gaussian_blur, generate_superpixels, crop_and_magnify
from utils import PathHandler


def preprocess_image(image, kernel_size=(3, 3), sigmaX=5):
    """Applies Gaussian blur to the image for noise reduction."""
    return apply_gaussian_blur(image, kernel_size=kernel_size, sigmaX=sigmaX)


def detect_edges(processed_image, method, canny_threshold=(10, 200)):
    """Detects edges using specified edge detection method."""
    if method == 'canny':
        pred = cv2.Canny(
            processed_image, canny_threshold[0], canny_threshold[1])
    elif method == 'marr_hildreth':
        laplacian = cv2.Laplacian(processed_image, cv2.CV_64F)
        pred = cv2.convertScaleAbs(np.absolute(laplacian), alpha=10)
    return pred


def postprocess_image(image, kernel_size=(3, 3), sigmaX=5):
    """Applies Gaussian blur again after edge detection to smoothen edges."""
    return apply_gaussian_blur(image, kernel_size=kernel_size, sigmaX=sigmaX)


def normalize_brightness(image, normalize='rescale', target_brightness=30):
    """Adjusts brightness using specified normalization method."""
    if normalize == 'rescale':
        return rescale(image, target_brightness)
    elif normalize == 'standardize':
        return standardize(image)
    elif normalize == 'translate':
        return translate(image, target_brightness)


def rescale(image, target_brightness=30):
    mean_brightness = np.mean(image)
    brightness_factor = target_brightness / mean_brightness
    normalized_image = np.clip(
        image * brightness_factor, 0, 255).astype(np.uint8)
    return normalized_image


def standardize(image, target_brightness=30):
    mean_brightness = np.mean(image)
    std_brightness = np.std(image)
    normalized_image = ((image - mean_brightness) /
                        std_brightness * target_brightness + mean_brightness)
    return np.clip(normalized_image, 0, 255).astype(np.uint8)


def translate(image, target_brightness=30):
    brightness_factor = target_brightness - np.mean(image)
    normalized_image = np.clip(
        image + brightness_factor, 0, 255).astype(np.uint8)
    return normalized_image


def detect(normalize='rescale', sigmaX=5, pre_kernel_size=(3, 3), post_kernel_size=(3, 3), img_path="../data/west_pasaman/satellite_image"):
    """
    Processes all images in the specified directory and saves the processed images.

    Args:
        normalize (str): Brightness normalization method.
        sigmaX (int): Gaussian blur sigma value.
        pre_kernel_size (tuple): Kernel size for pre-processing.
        post_kernel_size (tuple): Kernel size for post-processing.
        img_path (str): Path to the satellite image directory.
    """

    # Initialize the path handler
    path_handler = PathHandler(img_path)
    images = [img for img in os.listdir(img_path) if img.endswith(
        ".tif") and not img.endswith("_ans.tif")]

    for image_name in images:
        image_path = os.path.join(img_path, image_name)
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

        if image is None:
            print(f"{image_path} not found.")
            continue

        processed_image = preprocess_image(
            image, kernel_size=pre_kernel_size, sigmaX=sigmaX)
        pred = detect_edges(processed_image, method='marr_hildreth')
        postprocessed_image = postprocess_image(
            pred, kernel_size=post_kernel_size, sigmaX=sigmaX)
        postprocessed_image = normalize_brightness(
            postprocessed_image, normalize)

        # Save the processed image in both .npy and .png formats
        pred_gray_nps_path = path_handler.get_pred_gray_nps_folder()
        os.makedirs(pred_gray_nps_path, exist_ok=True)
        np.save(os.path.join(pred_gray_nps_path, f"{
                os.path.splitext(image_name)[0]}.npy"), postprocessed_image)
        cv2.imwrite(os.path.join(pred_gray_nps_path, f"{
                    os.path.splitext(image_name)[0]}.png"), postprocessed_image)


if __name__ == "__main__":
    params = {
        'sigmaX': 5,
        'pre_kernel_size': (3, 3),
        'post_kernel_size': (3, 3),
        'canny_threshold': (10, 200),
    }
    detect(**params)
    print("Image processing completed.")
