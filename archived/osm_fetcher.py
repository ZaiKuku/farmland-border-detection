import os
import wget
import requests
from bs4 import BeautifulSoup
import re
import uuid
from zipfile import ZipFile

# Initialize empty list for hrefs
href_list = []

# Define the base directory where files will be downloaded and unzipped
dstn_dirpath = "/mnt/pic_satellite/Segmentation_Experiment/osm"

# Define a function to download and unzip files
def download_and_unzip_to_dstn_folder(ref, dstn_dirpath):
    # Generate a temporary zip file name
    randomuuid = str(uuid.uuid4())[:8]
    tmp_zip_filepath = f'./tmp_{randomuuid}.zip'

    # Extract country name from the URL
    region_name = '_'.join(re.sub(r'-latest-free\.shp\.zip', '', ref).split('/')[4:])

    # Download the zip file
    wget.download(url=ref, out=tmp_zip_filepath)

    # Create the destination directory if it doesn't exist
    dstn_path = os.path.join(dstn_dirpath, region_name)
    os.makedirs(dstn_path, exist_ok=True)
    
    # Unzip the file
    with ZipFile(tmp_zip_filepath, 'r') as zip_ref:
        zip_ref.extractall(dstn_path)
    
    # Remove the temporary zip file
    os.remove(tmp_zip_filepath)
    return True


# Define base URL for geofabrik downloads
base_url = 'https://download.geofabrik.de/'

# Iterate over each continent
for continent in ['africa', 'asia', 'australia-oceania', 'central-america', 'europe', 'north-america', 'south-america']:
    # Get HTML content of the continent page
    continent_url = f'{base_url}{continent}.html'
    continent_html = requests.get(continent_url).content
    osm_html = BeautifulSoup(continent_html, 'html.parser')
    
    # Get subregion hrefs
    sub_region_nodes = osm_html.select(".subregion a")
    sub_region_hrefs = [
        base_url + continent + '/' + link['href'] for link in sub_region_nodes if '.html' in link['href']
    ]
    
    # Combine continent page URL and subregion URLs
    html_pool = [continent_url] + sub_region_hrefs
    
    for html in html_pool:
        # Parse each page to get the .shp.zip download links
        html_parsed = BeautifulSoup(requests.get(html).content, 'html.parser')
        osm_nodes = html_parsed.select("td:nth-child(4) a")
        
        for osm_node in osm_nodes:
            href = osm_node['href']
            # Append full URL to the list
            href_list.append(base_url + href)

# Remove duplicate hrefs
href_list = list(set(href_list))
href_list = ['https://download.geofabrik.de/asia/indonesia/java-latest-free.shp.zip',
'https://download.geofabrik.de/asia/indonesia/kalimantan-latest-free.shp.zip',
'https://download.geofabrik.de/asia/indonesia/maluku-latest-free.shp.zip',
'https://download.geofabrik.de/asia/indonesia/nusa-tenggara-latest-free.shp.zip',
'https://download.geofabrik.de/asia/indonesia/papua-latest-free.shp.zip',
'https://download.geofabrik.de/asia/indonesia/sulawesi-latest-free.shp.zip',
'https://download.geofabrik.de/asia/indonesia/sumatra-latest-free.shp.zip'
]
# Loop over each href and download/unzip the files
for href in href_list:
    print(href)
    try:
        download_result = download_and_unzip_to_dstn_folder(href, dstn_dirpath)
    except Exception as e:
        print(f"Error downloading {href}: {e}")

