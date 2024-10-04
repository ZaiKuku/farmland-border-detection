import rasterio
from rasterio import features
import geopandas as gpd
import pandas as pd
from shapely.geometry import shape, Polygon
from shapely import concave_hull, union_all
import numpy as np
import cv2

poly1 = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])

poly2 = Polygon([(0.5, 0.5), (1.5, 0.5), (1.5, 1.5), (0.5, 1.5)])


def remove_overlapping(polygons):
    for i in range(len(polygons)):
        if polygons[i].is_empty:
            continue
        for j in range(i+1, len(polygons)):
            if polygons[i].intersects(polygons[j]):
                if polygons[i].contains(polygons[j]):
                    print("remove contains")
                    polygons[j] = Polygon()
                elif polygons[j].contains(polygons[i]):
                    print("remove contains")
                    polygons[i] = Polygon()
                    break
                else:
                    if polygons[i].area > polygons[j].area:
                        polygons[j] = polygons[j].difference(polygons[i])
                        print("remove overlap")
                    else:
                        polygons[i] = polygons[i].difference(polygons[j])
                        print("remove overlap")
    return polygons


print(poly1.difference(poly2))
