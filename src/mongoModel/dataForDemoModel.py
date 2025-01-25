from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import os

mongo_uri = os.getenv("MONGODB_CONNECTION_URI")
client = MongoClient(mongo_uri)
db = client[os.getenv("MONGODB_DATABASE_NAME")]

demo_model_schema = {
    'name': str,
    'img_url': str,
    'description': str,
    'link': str,
    'created_at': datetime
}

# Insert index for unique constraint on name
db.demo_collection.create_index([('name', 1)], unique=True)

# Example of inserting a new document
def insert_demo_model(name, img_url, description, link):
    new_demo = {
        'name': name,
        'img_url': img_url,
        'description': description,
        'link': link,
        'created_at': datetime.now()
    }
    try:
        db.demo_collection.insert_one(new_demo)
        print("Document inserted successfully")
    except Exception as error:
        print("Error inserting document:", error)

# Example function to retrieve a document by id
def get_demo_model_by_id(document_id):
    try:
        document = db.demo_collection.find_one({'_id': ObjectId(document_id)})
        if document:
            return document
        else:
            print("No document found with the given id")
    except Exception as error:
        print("Error retrieving document:", error)

def get_all_demo_models():
    try:
        documents = db.demo_collection.find()
        return list(documents)
    except Exception as error:
        print("Error retrieving documents:", error)
        return []
