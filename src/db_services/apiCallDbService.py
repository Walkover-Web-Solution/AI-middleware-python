from models.mongo_connection import db
from bson.json_util import dumps, loads
from bson import ObjectId
from pymongo import ReturnDocument, errors
from ..services.cache_service import delete_in_cache
configurationModel = db["configurations"]
apiCallModel = db['apicalls']
templateModel = db['templates']
versionModel = db['configuration_versions']
from globals import *
from src.configs.constant import redis_keys

# todo :: to make it more better
async def get_all_api_calls_by_org_id(org_id, folder_id, user_id, isEmbedUser):
    query = {"org_id": org_id}
    query["folder_id"] = folder_id or  None
    if user_id and isEmbedUser:
        query["user_id"] = user_id
    pipeline = [
        {'$match': query},
        {'$addFields': {
            '_id': {'$toString': '$_id'},
            'bridge_ids': {'$map': {
                'input': '$bridge_ids',
                'as': 'bridge_id',
                'in': {'$toString': '$$bridge_id'}
            }},
            'created_at': {
                '$cond': {
                    'if': {'$eq': [{'$type': '$created_at'}, 'string']},
                    'then': '$created_at',
                    'else': {'$dateToString': {'format': '%Y-%m-%d %H:%M:%S', 'date': '$created_at'}}
                }
            },
            'updated_at': {
                '$cond': {
                    'if': {'$eq': [{'$type': '$updated_at'}, 'string']},
                    'then': '$updated_at',
                    'else': {'$dateToString': {'format': '%Y-%m-%d %H:%M:%S', 'date': '$updated_at'}}
                }
            }
        }}
    ]
    api_calls = await apiCallModel.aggregate(pipeline).to_list(length=None)
    
    for index, api_data in enumerate(api_calls):
        fields = api_data.get('fields', {})
        transformed_data = {}
        if not fields:  # Check if fields is empty or null
            transformed_data = {}
        elif api_data.get("version") != "v2":
            transformed_data = {
                item["variable_name"]: {
                    "description": item["description"], 
                    "enum": [] if(item["enum"] == '') else item.get("enum", []),
                    "type": "string",
                    "parameter": {}
                } for item in fields}
        else: transformed_data = fields
        api_calls[index]['fields'] = transformed_data
    return api_calls or []