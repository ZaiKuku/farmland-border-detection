from sqlalchemy import create_engine
from urllib.parse import quote_plus

# satellite PostgreSQL
PG_LAND_US = 'datayoo'
PG_LAND_PW = '*@(!)@&#'
PG_LAND_HT = '192.168.1.104'
PG_LAND_PORT = 5434
PG_LAND_NAME = 'land'

PG_LAND_URL = f"postgresql+psycopg2://{PG_LAND_US}:{quote_plus(PG_LAND_PW)}@{PG_LAND_HT}:{PG_LAND_PORT}/{PG_LAND_NAME}"

PGLandEngine = create_engine(PG_LAND_URL)
