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

    bounds = {}
    neighbor_tifs = {}
    for tif in tifs:
        if tif.endswith(".tif"):
            tif_num = tif.split(".")[0]
            neighbor_tifs[tif_num] = {}

    for tif_num in neighbor_tifs.keys():
        tif_path = f"{tifs_directory}/{tif_num}.tif"
        # 取出tif的邊界
        with rasterio.open(tif_path) as src:
            tif_bounds = src.bounds
            print(tif_num, tif_bounds)
            bounds[tif_num] = tif_bounds

    for tif_num in bounds.keys():
        if neighbor_tifs[tif_num].get('right') is not None and neighbor_tifs[tif_num].get('bottom') is not None:
            continue
        for tif_num2 in bounds.keys():
            if bounds[tif_num].right == bounds[tif_num2].left and bounds[tif_num].top == bounds[tif_num2].top:
                neighbor_tifs[tif_num]['right'] = tif_num2
                continue
            if bounds[tif_num].bottom == bounds[tif_num2].top and bounds[tif_num].right == bounds[tif_num2].right:
                neighbor_tifs[tif_num]['bottom'] = tif_num2
                continue
            if bounds[tif_num].left == bounds[tif_num2].right and bounds[tif_num].top == bounds[tif_num2].top:
                neighbor_tifs[tif_num2]['right'] = tif_num
                continue
            if bounds[tif_num].top == bounds[tif_num2].bottom and bounds[tif_num].right == bounds[tif_num2].right:
                neighbor_tifs[tif_num2]['bottom'] = tif_num
                continue

    return neighbor_tifs


if __name__ == "__main__":
    tifs_directory = "../data/west_pasaman/satellite_image"
    neighbor_tifs = find_intersect_tifs(tifs_directory)
    print(neighbor_tifs)
