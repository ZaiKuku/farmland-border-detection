import cv2


def apply_gaussian_blur(image, kernel_size=(5, 5), sigmaX=0):

    # 應用高斯模糊
    blurred_image = cv2.GaussianBlur(image, kernel_size, sigmaX)

    return blurred_image


def generate_superpixels(image, num_segments=100, compactness=10):
    # 創建SLIC超像素生成器
    slic = cv2.ximgproc.createSuperpixelSLIC(
        image, algorithm=cv2.ximgproc.SLIC, region_size=50, ruler=compactness)

    # 計算超像素
    slic.iterate(num_iterations=10)

    # 獲取標籤
    labels = slic.getLabels()

    # 生成標籤邊界
    mask_slic = slic.getLabelContourMask()

    # 覆蓋邊界於影像
    image_with_contours = image.copy()
    image_with_contours[mask_slic == 255] = [0, 0, 0]
    image_gray = cv2.cvtColor(image_with_contours, cv2.COLOR_RGB2GRAY)

    return labels, image_gray


def crop_quadrants(image):
    # crop into 4 quadrants
    h, w = image.shape[:2]
    center = (w // 2, h // 2)

    image_quadrants = [
        image[:center[1], :center[0]],
        image[:center[1], center[0]:],
        image[center[1]:, :center[0]],
        image[center[1]:, center[0]:]
    ]

    return image_quadrants


def magnify(image, scale=1.5):
    # magnify the image
    h, w = image.shape[:2]

    image_magnified = cv2.resize(
        image, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)

    return image_magnified


def crop_and_magnify(image, crop=True, magnify_=True, scale=3):
    if crop:
        image = crop_quadrants(image)
        if magnify_:
            image = [magnify(img, scale) for img in image]
        return image
    elif magnify_:
        return [magnify(image, scale)]


if __name__ == '__main__':
    image_path = "../data/crop_delineation/imgs/3043.jpeg"
    image = cv2.imread(image_path)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    labels, image_with_contours = generate_superpixels(image_rgb)

    # image_with_contours = apply_gaussian_blur(image_with_contours)

    # image_quadrants = crop_and_magnify(
    #     image_with_contours, crop=True, magnify_=True)

    cv2.imshow("Image", image_with_contours)
    # cv2.imshow("Top Left", image_quadrants[0])
    # cv2.imshow("Top Right", image_quadrants[1])
    # cv2.imshow("Bottom Left", image_quadrants[2])
    # cv2.imshow("Bottom Right", image_quadrants[3])
    cv2.waitKey(0)
