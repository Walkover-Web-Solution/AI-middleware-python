from models.mongo_connection import db
foldersModel = db['folders']
from bson import ObjectId

async def get_folder_data(folder_id):
    folder_data = await foldersModel.find_one({'_id': ObjectId(folder_id)})
    return folder_data