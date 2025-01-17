import os
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker, declarative_base
from config import Config

# Configuration
DB_NAME = Config.DB_NAME
DB_USER = Config.DB_USER
DB_PASS = Config.DB_PASS
DB_HOST = Config.DB_HOST

DATABASE_URL = Config.TIMESCALE_SERVICE_URL

# Engine and session setup
engine = sa.create_engine(DATABASE_URL, pool_pre_ping=True)
Session = sessionmaker(bind=engine, autoflush=False)

Base = declarative_base()

# Retry strategy
retry_strategy = {
    'max_retries': 100,
    'pool_recycle': 300,
}

# Function to test database connection
def init_dbservice():
    try:
        with engine.connect() as connection:
            connection.execute(sa.text("SELECT 1"))
        print('Connected to the Timescale database Yoooooooo.')
    except Exception as error:
        print('Unable to connect to the database:', error)

# Initialize database connection
init_dbservice()

# Metadata reflection for dynamic table access
metadata = sa.MetaData()
metadata.reflect(bind=engine)

# Example: Accessing tables dynamically
db = {
    'engine': engine,
    'session': Session,
}
for table_name in metadata.tables:
    db[table_name] = metadata.tables[table_name]

# The `db` dictionary is now ready for use
