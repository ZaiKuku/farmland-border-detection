from shapely import Polygon
import sqlalchemy as db
import geopandas as gpd
import rasterio
import os


class PathHandler:
    """
    A helper class to manage file paths for images and geojson data based on the given directory path.

    Attributes:
        img_data_path (str): The root path where image data is stored.
        region_name (str): The specific region name extracted from the path.
    """

    def __init__(self, folder):
        """
        Initializes PathHandler with the given path and sets the region name.

        Args:
            path (str): The root path to image data.
        """
        self.img_data_folder = folder

        # Extract region name from the path
        # select the folder name after the folder "../data"
        folder_parts = folder.split("/")
        if "data" in folder_parts:
            data_index = folder_parts.index("data")
            self.region_name = "/".join(folder_parts[data_index + 1:])
        else:
            self.region_name = ""

    def get_img_data_folder(self):
        """Returns the path to the main image data folder."""
        return self.img_data_folder

    def get_img_path(self, file_num=None):
        """
        Constructs the file path for a specific image based on the file number.

        Args:
            file_num (str): File identifier number.

        Returns:
            str: Path to the specific image file.
        """
        return f"{self.img_data_folder}/{file_num}.tif"

    def get_pred_gray_nps_folder(self):
        """Returns the path to the folder where gray prediction numpy arrays are stored."""
        return f"./pred_gray/{self.region_name}"

    def get_gray_mask_folder(self):
        """Returns the path to the folder where gray mask images are stored."""
        return f"./gray_mask/{self.region_name}"

    def get_gray_mask_path(self, threshold, file_num):
        """
        Constructs the file path for a gray mask TIFF file based on threshold and file number.

        Args:
            threshold (int): Threshold value used in file naming.
            file_num (str): File identifier number.

        Returns:
            str: Path to the specific gray mask file.
        """
        return f"./gray_mask/{self.region_name}/{file_num}_threshold_{threshold}.tif"

    def get_geojsons_folder(self, removed, combined):
        """
        Returns the path to the folder where geojsons are stored, based on removal and combination conditions.

        Args:
            removed (bool): If True, returns the path for removed geojsons.
            combined (bool): If True, returns the path for combined geojsons.

        Returns:
            str: Path to the relevant geojson folder.
        """
        if combined:
            return f"./geojsons/{self.region_name}/combined"
        if removed:
            return f"./geojsons/{self.region_name}/removed"

        return f"./geojsons/{self.region_name}/to_be_processed"

    def get_geojsons_path(self, removed, combined, file_num):
        """
        Constructs the file path for a geojson file based on removal, combination, and file number.

        Args:
            removed (bool): If True, specifies the path for removed geojsons.
            combined (bool): If True, specifies the path for combined geojsons.
            file_num (str): File identifier number.

        Returns:
            str: Path to the specific geojson file.
        """
        if combined:
            return f"./geojsons/{self.region_name}/combined/{file_num}.geojson"
        if removed:
            return f"./geojsons/{self.region_name}/removed/{file_num}.geojson"
        return f"./geojsons/{self.region_name}/to_be_processed/{file_num}.geojson"


def fetch_osm_landuse_data(engine: db.engine.base.Connection, table_name: str, polygon: Polygon) -> gpd.GeoDataFrame:
    """
    Fetches OSM landuse data from the specified table within the database where geometries intersect with a given polygon.

    Args:
        engine (db.engine.base.Connection): The database connection.
        table_name (str): Name of the table to query.
        polygon (Polygon): Shapely Polygon object representing the area of interest.

    Returns:
        gpd.GeoDataFrame: GeoDataFrame containing the intersected landuse data.
    """
    query = f"SELECT * FROM {
        table_name} WHERE ST_Intersects(geom, ST_GeomFromGeoJSON('{polygon}'))"

    with engine.connect() as connection:
        result = connection.execute(query)
        data = result.fetchall()
        df = gpd.GeoDataFrame(data)
        return df


def find_intersect_tifs(tifs_directory):
    """
    Finds neighboring TIFF files in the specified directory that have touching edges based on their bounding boxes.

    Args:
        tifs_directory (str): Directory path containing TIFF files.

    Returns:
        dict: Dictionary mapping each TIFF file to its neighboring TIFFs based on their spatial relations.
    """
    # List all TIFF files in the specified directory
    tifs = os.listdir(tifs_directory)

    bounds = {}  # Dictionary to store the bounds of each TIFF file
    neighbor_tifs = {}  # Dictionary to map each TIFF to its neighboring TIFFs
    for tif in tifs:
        if tif.endswith(".tif"):
            tif_num = tif.split(".")[0]
            # Initialize empty neighbors for each TIFF
            neighbor_tifs[tif_num] = {}

    # Loop through each TIFF file to extract bounds
    for tif_num in neighbor_tifs.keys():
        tif_path = f"{tifs_directory}/{tif_num}.tif"
        # Retrieve bounding box for each TIFF
        with rasterio.open(tif_path) as src:
            tif_bounds = src.bounds
            print(tif_num, tif_bounds)  # Debugging print statement
            bounds[tif_num] = tif_bounds

    # Compare bounds to find neighboring TIFFs
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
    # Directory containing TIFF files
    tifs_directory = "../data/west_pasaman/satellite_image"
    # Find neighboring TIFF files
    neighbor_tifs = find_intersect_tifs(tifs_directory)
    print(neighbor_tifs)  # Print the resulting neighbors dictionary
