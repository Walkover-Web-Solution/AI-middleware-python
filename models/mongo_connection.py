from pymongo import MongoClient, errors
from config import Config
import certifi

try:
    client = MongoClient(
        Config.MONGODB_CONNECTION_URI,
        tls=True,  # Use 'tls' instead of 'ssl'
        tlsCAFile=certifi.where()  # Use 'tlsCAFile' instead of 'ssl_ca_certs'
    )
    db = client[Config.MONGODB_DATABASE_NAME]
    print('connected to Mongo...')
except errors.ConnectionFailure as e:  # Use 'ConnectionFailure' instead of 'ConnectionError'
    print(f"Could not connect to MongoDB: {e}")