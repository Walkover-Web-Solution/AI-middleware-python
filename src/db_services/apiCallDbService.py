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

# todo :: to make it more better
async def get_all_api_calls_by_org_id(org_id, folder_id = None, user_id = None, isEmbedUser = False):
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
    


async def update_api_call_by_function_id(org_id, function_id, data_to_update):
    updated_document = await apiCallModel.find_one_and_update(
        {
            '_id': ObjectId(function_id),  
            'org_id': org_id  
        },
        {
            '$set': data_to_update  
        },
        return_document=ReturnDocument.AFTER 
    )
    
    if updated_document:
        updated_document['_id'] = str(updated_document['_id'])
    else: 
        raise BadRequestException("Document not found or not modified.")
    
    bridge_ids = updated_document.get('bridge_ids') or []
    version_ids = updated_document.get('version_ids') or []
    if bridge_ids:
        await delete_in_cache(bridge_ids)
    if version_ids:
        await delete_in_cache(version_ids)
    return {
        "success": True, 
        "data": updated_document 
    }

async def get_function_by_id(function_id):
    try:
        db_data = await apiCallModel.find_one({"_id": ObjectId(function_id)})
        if not db_data:
            raise errors.InvalidId("Function not found.")
        return db_data

    except errors.InvalidId:
        raise BadRequestException(f"Invalid function id")
    except Exception as e:
        logger.error(f"Error retrieving function by id: {e}")
        raise BadRequestException(f"Error retrieving function: {str(e)}")


async def delete_function_from_apicalls_db(org_id, function_name): # This function is throwing error because result is not defined. 
    bridge_data = await apiCallModel.find_one(
        {'org_id': org_id, 'function_name': function_name},
        {'bridge_ids': 1,'version_ids' : 1, '_id': 1}
    )
    
    bridge_ids = bridge_data.get('bridge_ids') or []
    version_ids = bridge_data.get('version_ids') or []
    function_id = bridge_data.get('_id')

    if isinstance(function_id, str):
        function_id = ObjectId(function_id)
    
    if bridge_ids:
        for bridge_id in bridge_ids:
            if isinstance(bridge_id, str):
                bridge_id = ObjectId(bridge_id)
            
            await versionModel.update_one(
                {'_id': bridge_id},
                {'$pull': {'function_ids': function_id}}
            )
    if version_ids:
        for version_id in version_ids:
            if isinstance(version_id, str):
                version_id = ObjectId(version_id)
            
            await versionModel.update_one(
                {'_id': version_id},
                {'$pull': {'function_ids': function_id}}
            )
    
    result = await apiCallModel.delete_one({
        'org_id': org_id,
        'function_name': function_name
    })
    
    if result.deleted_count > 0:
        return {
            "success": True,
            "message": "Function deleted successfully."
        }
    else:
        raise BadRequestException("No matching function found to delete.")