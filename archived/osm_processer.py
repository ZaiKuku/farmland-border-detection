import geopandas as gpd
from sqlalchemy import create_engine
import pandas as pd
from urllib.parse import quote_plus

engine = create_engine(...)
conn = engine.connect()

# 讀取和處理所有 OSM 檔案
def get_osm_file_dict(folder_path: str) -> str:
    return {
        'transport': (f'{folder_path}gis_osm_transport_a_free_1.shp', 'transport'),
        'traffic': (f'{folder_path}gis_osm_traffic_a_free_1.shp', 'traffic'),
        'pois': (f'{folder_path}gis_osm_pois_a_free_1.shp', 'public_facilities'),
        'pofw': (f'{folder_path}gis_osm_pofw_a_free_1.shp', 'religious_sites'),
        'natural': (f'{folder_path}gis_osm_natural_a_free_1.shp', 'natural'),
        'landuse': (f'{folder_path}gis_osm_landuse_a_free_1.shp', 'landuse'),
        'water': (f'{folder_path}gis_osm_water_a_free_1.shp', 'water'),
        'buildings':  (f'{folder_path}gis_osm_buildings_a_free_1.shp', 'buildings')
    }

# 定義資料處理函數
def process_osm_file(file_path, class_name, sub_class_field='fclass'):
    """
    讀取並處理 OSM shapefiles
    
    Parameters:
    file_path (str): Shapefile 路徑
    class_name (str): 要設定的 class 值
    sub_class_field (str): 子分類欄位名稱，預設為 'fclass'
    
    Returns:
    GeoDataFrame: 處理後的資料
    """
    gdf = gpd.read_file(file_path)
    gdf['class'] = class_name
    
    # 重命名和選擇欄位
    if class_name == 'buildings':
        sub_class_field = 'type'

    columns_mapping = {
        'osm_id': 'osm_id',
        'class': 'class',
        sub_class_field: 'sub_class',
        'name': 'name',
        'geometry': 'geometry'
    }
    
    return gdf[list(columns_mapping.keys())].rename(columns=columns_mapping)

folders = ['~/work/pic_satellite_98/Segmentation_Experiment/osm/taiwan/',
           #'~/work/pic_satellite_98/Segmentation_Experiment/osm/indonesia_java/',
           '~/work/pic_satellite_98/Segmentation_Experiment/osm/indonesia_kalimantan/',
           '~/work/pic_satellite_98/Segmentation_Experiment/osm/indonesia_maluku/',
           '~/work/pic_satellite_98/Segmentation_Experiment/osm/indonesia_nusa-tenggara/',
           '~/work/pic_satellite_98/Segmentation_Experiment/osm/indonesia_papua/',
           '~/work/pic_satellite_98/Segmentation_Experiment/osm/indonesia_sulawesi/',
           '~/work/pic_satellite_98/Segmentation_Experiment/osm/indonesia_sumatra/']

for folder in folders:
    osm_files = get_osm_file_dict(folder)
    for file_info in osm_files.values():
        gdf = process_osm_file(file_info[0], file_info[1])
        gpd.GeoDataFrame.to_postgis(self=gdf, name='osm', con=conn, if_exists='append')
        print(len(gdf))
