import numpy as np

# load npy
np_demo = np.load(r'.\pred_gray\baihsien\satellite_image\0fc0cc1e.npy')


# binarilize
np_demo[np_demo < 16] = 0
np_demo[np_demo >= 16] = 255


print(np_demo)
