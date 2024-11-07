from shapely import Polygon
import sqlalchemy as db
import geopandas as gpd
import rasterio
import os


def fetch_osm_landuse_data(engine: db.engine.base.Connection, table_name: str, polygon: Polygon) -> gpd.GeoDataFrame:
    """
    Fetch OSM landuse data from the database
    """
    query = f"SELECT * FROM {
        table_name} WHERE ST_Intersects( geom, ST_GeomFromGeoJSON('{polygon}') )"

    with engine.connect() as connection:
        result = connection.execute(query)
        data = result.fetchall()
        df = gpd.GeoDataFrame(data)
        return df


def find_intersect_tifs(tifs_directory):
    tifs = os.listdir(tifs_directory)

    neighbor_tifs = {}
    for tif in tifs:
        if tif.endswith(".tif"):
            tif_num = int(tif.split(".")[0])
            neighbor_tifs[tif_num] = {}

    for tif_num in neighbor_tifs.keys():
        tif_path = f"{tifs_directory}/{tif_num}.tif"
        # 取出tif的邊界
        with rasterio.open(tif_path) as src:
            bounds = src.bounds
