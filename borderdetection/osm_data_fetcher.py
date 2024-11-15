from shapely.geometry import box
from database import PGLandEngine
import geopandas as gpd
import os
import rasterio


EXCLUDED_CLASSES = [
    'transport', 'traffic', 'pois', 'pofw', 'buildings', 'water']
EXCLUDED_LANDUSE_SUBCLASSES = ['commercial', 'industrial', 'retail',
                               'residential', 'military', 'cemetery', 'recreation_ground', 'quarry']
LINE_CLASSES = ['railways', 'roads', 'waterways']


def fetch_osm_landuse_data(bounds, crs):
    sql_query = f'''
        WITH excluded_classes AS (
            -- Defines the set of general classes in the OSM data to exclude
            SELECT unnest(ARRAY{EXCLUDED_CLASSES}) AS class
        ),
        excluded_landuse_subclasses AS (
            -- Specifies land use subclasses to exclude within the 'landuse' class
            SELECT 'landuse' AS class, unnest(ARRAY{EXCLUDED_LANDUSE_SUBCLASSES}) AS sub_class
        ),
        bounding_box AS (
            -- Defines the bounding box polygon with given latitude and longitude bounds, then transforms it to the desired CRS
            SELECT ST_Transform(
                ST_MakeEnvelope(
                    {bounds['right']},  -- xmin
                    {bounds['bottom']},  -- ymin
                    {bounds['left']},  -- xmax
                    {bounds['top']},  -- ymax
                    {crs.to_epsg()}  -- source CRS
                ),
                4326            -- target CRS
            ) AS bound_geom
        ),
        excluded_geometries_within_bounds AS (
            -- Filters geometries that intersect the bounding box and match exclusion criteria
            SELECT ST_Union(geometry) as union_exclude_geom
            FROM osm, bounding_box
            WHERE ST_Intersects(geometry, bound_geom)
            AND (
                -- Match classes from excluded_classes
                class IN (SELECT class FROM excluded_classes)
                OR
                -- Match specific landuse subclasses
                (class = 'landuse' AND sub_class IN (SELECT sub_class FROM excluded_landuse_subclasses))
            )
        )
        -- Calculates the difference between the bounding box and the union of excluded geometries
        SELECT ST_Transform(ST_Difference(b.bound_geom, o.union_exclude_geom), 3857) AS difference_geom
        FROM bounding_box b
        CROSS JOIN excluded_geometries_within_bounds o;
        '''

    with PGLandEngine.connect() as conn:
        gdf = gpd.GeoDataFrame.from_postgis(
            sql=sql_query, con=conn, geom_col='difference_geom')
        gdf.to_file('./query_result.geojson', driver='GeoJSON')


def fetch_osm_landuse_line_data(bounds, crs):
    sql_query = f'''
        WITH line_classes AS (
            -- Defines the set of general classes in the OSM data to exclude
            SELECT unnest(ARRAY{LINE_CLASSES}) AS class
        ),
        bounding_box AS (
            -- Defines the bounding box polygon with given latitude and longitude bounds, then transforms it to the desired CRS
            SELECT ST_Transform(
                ST_MakeEnvelope(
                    {bounds['right']},  -- xmin
                    {bounds['bottom']},  -- ymin
                    {bounds['left']},  -- xmax
                    {bounds['top']},  -- ymax
                    {crs.to_epsg()}  -- source CRS
                ),
                4326            -- target CRS
            ) AS bound_geom
        ),
        line_geometries_within_bounds AS (
            -- Filters geometries that intersect the bounding box and match exclusion criteria
            SELECT geometry as line_geom
            FROM osm, bounding_box
            WHERE ST_Intersects(geometry, bound_geom)
            AND (
                class IN (SELECT class FROM line_classes)
            )
        )
        SELECT ST_Transform(o.line_geom, 3857) AS line_geom
        FROM line_geometries_within_bounds o;
        '''

    with PGLandEngine.connect() as conn:
        gdf = gpd.GeoDataFrame.from_postgis(
            sql=sql_query, con=conn, geom_col='line_geom')
        gdf.to_file('./line_query_result.geojson', driver='GeoJSON')


# with PGLandEngine.connect() as conn:
#     gdf = gpd.GeoDataFrame.from_postgis(
#         sql=sql_query, con=conn, geom_col='difference_geom')

# # output to shapely object
# gdf.geometry.iloc[0]

# # output to .geojson
# gdf.to_file('./query_result.geojson')
if __name__ == "__main__":
    img_path = "../data/west_pasaman/satellite_image"
    bounds = (13275323,  2767997, 13581323, 2803997)

    for tif_num in os.listdir(img_path):
        if tif_num.endswith(".tif"):
            tif_num = tif_num.split(".")[0]
            # print(f"Processing {tif_num}")
            with rasterio.open(f"{img_path}/{tif_num}.tif") as src:
                crs = src.crs

    fetch_osm_landuse_data(bounds, crs=crs)
