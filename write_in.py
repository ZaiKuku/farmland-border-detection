from database import PGLandEngine
import geopandas as gpd
from sqlalchemy import create_engine
from geoalchemy2 import Geometry, WKTElement
from shapely import wkt
file_path = "../data/gis_osm_railways_free_taiwan/gis_osm_railways_free_1.shp"

railways = gpd.read_file(file_path)
gpd.GeoDataFrame.to_postgis(
    railways, 'land', PGLandEngine, if_exists='append', index=False)
