import numpy as np
import cv2
from scipy.ndimage import distance_transform_edt


def dice_loss(pred, target, smooth=1e-6):
    pred = pred.flatten()
    target = target.flatten()

    intersection = np.sum(pred * target)
    print(intersection)

    dice = (2. * intersection + smooth) / \
        (np.sum(pred) + np.sum(target) + smooth)

    return 1 - dice


def IOU(pred_polygons, target_polygons):
    intersection = 0
    union = 0

    for pred_polygon in pred_polygons:
        for target_polygon in target_polygons:
            intersection += pred_polygon.intersection(target_polygon).area
            union += pred_polygon.union(target_polygon).area

    return intersection / union


def apply_gaussian_blur(image, kernel_size=(3, 3), sigmaX=0):

    # 應用高斯模糊
    blurred_image = cv2.GaussianBlur(image, kernel_size, sigmaX)

    return blurred_image


def MAE(pred, target):
    return np.mean(np.abs(pred - target))


def zero_one_loss(pred, target):
    num_pixels = pred.shape[0] * pred.shape[1]
    num_positive = np.sum(target)
    num_negative = num_pixels - num_positive
    positive_correct = np.sum(pred * target)
    negative_correct = np.sum((1 - pred) * (1 - target))
    return 1 - (positive_correct + negative_correct) / num_pixels


def f1score(pred, target):
    pred = pred.flatten()
    target = target.flatten()
    tp = np.sum(pred * target)
    print(tp)
    fp = np.sum(pred * (1 - target))
    print(fp)
    fn = np.sum((1 - pred) * target)
    print(fn)
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    return 2 * precision * recall / (precision + recall)


def calculate_metrics(number):
    gt_path = f"../data/lyon_2m/{number}_ans.png"
    pred_path = f"./validation/{number}.tif"

    print("Loading ground truth and prediction images...")

    # 讀取圖像

    gt = cv2.imread(gt_path, cv2.IMREAD_GRAYSCALE)
    pred = cv2.imread(pred_path, cv2.IMREAD_GRAYSCALE)

    # 檢查圖像是否成功讀取

    if gt is None:
        raise FileNotFoundError("Ground truth image not found.")

    if pred is None:
        raise FileNotFoundError("Prediction image not found.")

    # 檢查圖像大小是否相同

    if gt.shape != pred.shape:
        raise ValueError(
            "Ground truth and prediction images must have the same dimensions.")

    # 將圖像二值化

    _, gt = cv2.threshold(gt, 127, 1, cv2.THRESH_BINARY)
    _, pred = cv2.threshold(pred, 0, 1, cv2.THRESH_BINARY)

    # cv2.imshow("Ground Truth", gt)
    # cv2.imshow("Prediction", pred)
    # cv2.waitKey(0)

    # 計算 Dice Loss

    loss = fom(gt, pred)

    return loss


def fom(ref_img, img, alpha=1.0 / 9):
    """
    Computes Pratt's Figure of Merit for the given image img, using a gold
    standard image as source of the ideal edge pixels.
    """

    # Compute the distance transform for the gold standard image.
    dist = distance_transform_edt(np.invert(ref_img))

    fom = 1.0 / np.maximum(
        np.count_nonzero(img),
        np.count_nonzero(ref_img))

    N, M = img.shape

    for i in range(N):
        for j in range(M):
            if img[i, j]:
                fom += 1.0 / (1.0 + dist[i, j] * dist[i, j] * alpha)

    fom /= np.maximum(
        np.count_nonzero(img),
        np.count_nonzero(ref_img))

    return fom


if __name__ == "__main__":
    calculate_metrics(3043)
