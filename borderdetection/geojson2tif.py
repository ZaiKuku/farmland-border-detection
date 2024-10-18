import geopandas as gpd
import rasterio
from rasterio.features import rasterize
import numpy as np


def geojson2tif(number, threshold, filtered):
    polygons = gpd.read_file(
        f"./geojson/preds/{number}_threshold_{threshold}_{filtered}_True_3857.geojson")

    # 將 polygon 轉為 linestring
    multi_strings = polygons['geometry'].boundary

    template_raster_filepath = f"../data/lyon_2m/{number}_ans.tif"

    # Step 2: Open the raster (TIF file) using rasterio and extract metadata
    with rasterio.open(template_raster_filepath) as src:
        raster_meta = src.meta.copy()
        transform = src.transform
        raster_shape = src.shape

    strings = [(string_geom, 1)
               # List of linestring geometries
               for string_geom in multi_strings]

    binary_mask = rasterize(
        shapes=strings,
        out_shape=raster_shape,        # Match the raster grid
        transform=transform,           # Use the same transform as the raster
        fill=0,                        # Areas outside the polygons get value 0
        dtype=np.uint8                 # Output as a binary mask (0 and 1)
    )

    # Step 4: Update the metadata for the new binary output (single band, dtype of UInt8)
    raster_meta.update({
        "count": 1,
        "dtype": 'uint8',  # Since it's binary (0 and 1)
        "compress": 'lzw'  # Optional: compression to reduce file size
    })

    # Remove the nodata value from the metadata
    if 'nodata' in raster_meta:
        del raster_meta['nodata']

    # Step 5: Write the binary mask to a new .tif file
    with rasterio.open(f"./validation/{number}.tif", 'w', **raster_meta) as dst:
        dst.write(binary_mask, 1)  # Write to the first band (single band)
