from pymongo import MongoClient
from config import Config

client = MongoClient(Config.MONGODB_CONNECTION_URI)
db = client[Config.MONGODB_DATABASE_NAME]
print('connected to Mongo...')


