import os

import requests
import rasterio
from rasterio.transform import from_bounds
from rasterio.crs import CRS
import uuid

RESOLUTION = 2
WIDTH = 1000
HEIGHT = 1000
STEP = 1000
WMS_URL = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export"

def get_wms_tif(
    wms_url: str,
    xmin_3857: int,
    ymin_3857: int,
    resolution: int,
    width: int,
    height: int,
    output_tif_filename: str
) -> None:
    """
    Retrieve a WMS image and save it as a GeoTIFF file with proper georeferencing.

    Args:
        wms_url (str): The URL of the WMS service.
        xmin_3857 (int): The minimum x-coordinate in EPSG:3857 projection.
        ymin_3857 (int): The minimum y-coordinate in EPSG:3857 projection.
        resolution (int): The spatial resolution of the output image.
        width (int): The width of the output image in pixels.
        height (int): The height of the output image in pixels.
        output_tif_filename (str): The file path where the output GeoTIFF should be saved.
    """
    xmax_3857 = xmin_3857 + resolution * width
    ymax_3857 = ymin_3857 + resolution * height

    params = {
        'bbox': f'{xmin_3857},{ymax_3857},{xmax_3857},{ymin_3857}',
        'bboxSR': '3857',
        'imageSR': '3857',
        'size': f"{width},{height}",
        'format': 'tiff',
        'f': 'image'
    }

    response = requests.get(wms_url, params=params)

    if response.status_code == 200:
        tmp_tif_path = './tmp.tif'
        
        with open(tmp_tif_path, 'wb') as file:
            file.write(response.content)
        print("Image saved successfully.")

        with rasterio.open(tmp_tif_path) as src:
            profile = src.profile

        profile.update(
            driver='GTiff',
            crs=CRS.from_epsg(3857),
            transform=from_bounds(
                xmin_3857,
                ymin_3857,
                xmax_3857,
                ymax_3857,
                profile['width'],
                profile['height']
            )
        )

        with rasterio.open(output_tif_filename, 'w', **profile) as dst:
            with rasterio.open(tmp_tif_path) as src:
                dst.write(src.read())
        print("Image with CRS saved successfully.")
        
        os.remove(tmp_tif_path)
    else:
        print(f"Failed to retrieve the image: {response.status_code} - {response.reason}")

x_start_3857 = 11073245
y_start_3857 = 14898
x_end_3857 = 11098246
y_end_3857 = 39899

for xmin_3857 in range(x_start_3857, x_end_3857, STEP):
    for ymin_3857 in range(y_start_3857, y_end_3857, STEP):
        print(xmin_3857)
        print(ymin_3857)
        uid = str(uuid.uuid4())
        
        get_wms_tif(
            wms_url=WMS_URL,
            xmin_3857=xmin_3857,
            ymin_3857=ymin_3857,
            resolution=RESOLUTION,
            width=WIDTH,
            height=HEIGHT,
            output_tif_filename=f'X:/Segmentation_Experiment/img_data/west_pasaman/{uid[:8]}.tif'
        )
