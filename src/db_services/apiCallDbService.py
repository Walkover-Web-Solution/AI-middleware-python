from models.mongo_connection import db
from bson.json_util import dumps, loads
from bson import ObjectId
from pymongo import ReturnDocument
from ..services.cache_service import delete_in_cache
configurationModel = db["configurations"]
apiCallModel = db['apicalls']
templateModel = db['templates']

# todo :: to make it more better
async def get_all_api_calls_by_org_id(org_id):
    try:
        pipeline = [
            {'$match': {'org_id': org_id}},
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
    except Exception as error:
        print(error)
        return {
            'success': False,
            'error': "Error in getting api calls of a organization!!"
        }
    


async def update_api_call_by_function_id(org_id, function_id, data_to_update):
    try:      
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
        print(updated_document)
        bridge_ids = updated_document.get('bridge_ids') or []
        version_ids = updated_document.get('version_ids') or []
        if bridge_ids:
            for bridge_id in bridge_ids:
                await delete_in_cache(bridge_id)
        if version_ids:
            for version_id in version_ids:
                await delete_in_cache(version_id)
        if updated_document:
                return {
                "success": True, 
                "data": updated_document 
         }
        else:
                return {
                "success": False,
                "message": "Data not found or not modified."
            }
     
    except Exception as error:
        return {
            'success': False,
            'error': f"Error in updating the API call: {str(error)}"
        }
async def get_function_by_id(function_id):
    try:
        if not ObjectId.is_valid(function_id):
            return {"success": False, "message": "Invalid function_id format."}
        
        db_data =  await apiCallModel.find_one({"_id": ObjectId(function_id)})
                
        return {"success": True, "data": db_data}
    
    except Exception as e:
        print(f"Error retrieving function by id: {e}")
        return {"success": False, "message": f"Error retrieving function: {str(e)}"}
