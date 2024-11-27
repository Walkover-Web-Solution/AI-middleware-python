import os
from dotenv import load_dotenv

load_dotenv(override=True)


class Config:
    ENVIROMENT = os.getenv('ENVIROMENT')
    MONGODB_CONNECTION_URI = os.getenv('MONGODB_CONNECTION_URI')
    MONGODB_DATABASE_NAME = os.getenv('MONGODB_DATABASE_NAME')
    JWT_TOKEN_SECRET = os.getenv('JWT_TOKEN_SECRET')
    MONGODB_USER_DATABASE = os.getenv('MONGODB_USER_DATABASE')
    MONGODB_USER_DATABASE_COLLECTION = os.getenv('MONGODB_USER_DATABASE_COLLECTION')
    
    DB_NAME = os.getenv('DB_NAME')
    DB_USER = os.getenv('DB_USER')
    DB_PASS = os.getenv('DB_PASS')
    DB_HOST = os.getenv('DB_HOST')
    
    chatBotFLow = os.getenv('chatBotFLow')
    TIMESCALE_SERVICE_URL = os.getenv('TIMESCALE_SERVICE_URL')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    SecretKey = os.getenv('SecretKey')
    Encreaption_key = os.getenv('Encreaption_key')
    Secret_IV = os.getenv('Secret_IV')
    ALGORITHM = os.getenv('ALGORITHM')
    Access_key = os.getenv('Access_key')
    ORG_ID = os.getenv('ORG_ID')
    PROJECT_ID = os.getenv('PROJECT_ID')
    RTLAYER_AUTH = os.getenv('RTLAYER_AUTH')
    PORT = os.getenv('PORT', 8080)
    CHATBOTSECRETKEY = os.getenv('CHATBOTSECRETKEY')
    TEMPLATE_ID = os.getenv('TEMPLATE_ID')
    max_workers = os.getenv('max_workers')
    MUI_TEMPLATE_ID = os.getenv('MUI_TEMPLATE_ID')
    MUI_TEMPLATE_ID_WITHOUT_ACTION = os.getenv('MUI_TEMPLATE_ID_WITHOUT_ACTION')
    CHATBOT_OPTIONS_TEMPLATE_ID = os.getenv('CHATBOT_OPTIONS_TEMPLATE_ID')
    QUEUE_CONNECTIONURL = os.getenv('QUEUE_CONNECTIONURL')
    QUEUE_NAME = os.getenv('QUEUE_NAME')
    PREFETCH_COUNT = os.getenv('PREFETCH_COUNT')
    CONSUMER_STATUS = os.getenv('CONSUMER_STATUS')
    OPTIONS_APIKEY = os.getenv('OPTIONS_APIKEY')