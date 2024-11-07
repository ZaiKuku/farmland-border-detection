EXCLUDED_CLASSES = ['transport', 'traffic', 'pois', 'pofw', 'buildings', 'water']
EXCLUDED_LANDUSE_SUBCLASSES = ['commercial', 'industrial', 'retail', 'residential', 'military', 'cemetery', 'recreation_ground', 'quarry']

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
            13275323,     -- xmin
            2767997,      -- ymin
            13581323,     -- xmax
            2803997,      -- ymax
            3857          -- original CRS
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

import geopandas as gpd
from database import PGLandEngine

with PGLandEngine.connect() as conn:
    gdf = gpd.GeoDataFrame.from_postgis(sql=sql_query, con=conn, geom_col='difference_geom')

gdf.to_file('./query_result.geojson')
