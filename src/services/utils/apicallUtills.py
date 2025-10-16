import datetime 
from models.mongo_connection import db
from src.services.cache_service import delete_in_cache
apiCallModel = db['apicalls']
from globals import *
from src.configs.constant import redis_keys

async def get_api_data(org_id, function_name, folder_id, user_id, isEmbedUser):
    try:
        query = {"org_id": org_id, "function_name": function_name}
        if folder_id:
            query["folder_id"] = folder_id
        if user_id and isEmbedUser:
            query["user_id"] = user_id
        api_call_data =  await apiCallModel.find_one(query)
        api_call_data['__id'] = str(api_call_data.get('_id')) if api_call_data.get('_id') else None
        return api_call_data  if api_call_data.get('_id') else None
    except Exception as error:
        logger.error(f"Error in get_api_data: {str(error)}")
        return ""



async def save_api(desc, org_id, folder_id, user_id, api_data=None, required_params=None, function_name="", fields=None, endpoint_name="", version="v2"):
    if fields is None:
        fields = []
    if required_params is None:
        required_params = []

    try:
        if api_data:
            old_fields  = api_data.get('fields',{} if api_data.get('version', 'v1')== 'v2' else [])
            fields = updateFields(old_fields, fields , api_data.get('version', 'v1') == version)
            required_params = [key for key in fields if key not in api_data.get('fields') or key in api_data["required_params"]] if api_data.get('version', 'v1')== 'v2' else required_params

            api_data['description'] = desc
            api_data['required_params'] = required_params
            api_data['fields'] = fields
            api_data['old_fields'] = old_fields
            api_data['updated_at'] = datetime.datetime.now()
            api_data['function_name'] = function_name # script id will be set in this in case of viasocket
            api_data['endpoint_name'] = endpoint_name # flow name will be saved in this in case of viasocket
            api_data['version']= version

            # saving updated fields in the db with same id
            saved_api = await apiCallModel.replace_one({"_id": api_data["_id"]}, api_data) # delete from history
            await delete_all_version_and_bridge_ids_from_cache(api_data)
            if saved_api.modified_count == 1:
                return {
                    "success": True,
                    "api_data": api_data,
                }
        else:
            api_data = {
                "description": desc,
                "org_id": org_id,
                "folder_id": folder_id,
                "user_id": user_id,
                "required_params": list(fields.keys()),
                "fields": fields,
                "function_name": function_name,
                "endpoint_name": endpoint_name,
                "created_at": datetime.datetime.now(),
                "updated_at": datetime.datetime.now(),
                "version": version
            }
            new_api =  await apiCallModel.insert_one(api_data)
            return {
                "success": True,
                 "api_data": {
                    "_id": str(new_api.inserted_id),
                    **api_data
                },
            }
    except Exception as error:
        logger.error(f"error: {str(error)}")
        return {
            "success": False,
            "error": str(error)
        }
    
    
def updateFields(oldFields, newFields, versionCheck):
    def update_recursive(old, new):
        # Now update/merge remaining keys
        for key in new:
            if key in old:
                new[key]['description'] = old[key].get('description') if not new[key].get('description') else new[key].get('description')
                if(new[key].get("type") == 'string'): new[key]["type"] = old[key]["type"]
                if old[key].get("type") == 'string' and new[key].get('type') == 'object': old[key]["type"] = new[key]["type"]
                new[key]['enum'] = old[key].get('enum') if not new[key].get('enum') else new[key].get('enum')
                if isinstance(old[key], dict) and isinstance(new[key], dict):
                    if old[key].get("type") == "object" and new[key].get('type') == 'object':
                        update_recursive(old[key].get('parameter', {}), new[key].get('parameter', {}))
                    elif old[key].get("type") == "array" and new[key].get('type') == 'array':
                        update_recursive(old[key].get('items', {}), new[key].get('items', {}))
            else:
                old[key] = new[key]
                if isinstance(new[key], dict):
                    update_recursive({}, new[key])
        return old

    if versionCheck: 
        updated = oldFields.copy()
        for key in list(updated.keys()):
            if key not in newFields:
                del updated[key]
        update_recursive(updated, newFields)
        return updated
    else:
        transformed_data = {item["variable_name"]: {"description": item["description"], "enum": item["enum"]} for item in oldFields}
        return update_recursive(transformed_data, newFields)

async def delete_api(function_name, org_id, status = 0):
    try:
        data = await apiCallModel.find_one_and_update({"org_id": org_id, "function_name": function_name}, {"$set": {"status": status}}, return_document=True)
        if data:
            data['_id'] = str(data['_id'])  # Convert ObjectId to string
            if 'bridge_ids' in data:
                data['bridge_ids'] = [str(bid) for bid in data['bridge_ids']]  # Convert bridge_ids to string
            if 'created_at' in data:
                data['created_at'] = data['created_at'].strftime('%Y-%m-%d %H:%M:%S')  # Convert datetime to string
            if 'updated_at' in data:
                data['updated_at'] = data['updated_at'].strftime('%Y-%m-%d %H:%M:%S')  
        return data
    except Exception as error:
        logger.error(f"Delete API error=> {str(error)}")
        return {"success": False, "error": str(error)}
    


async def delete_all_version_and_bridge_ids_from_cache(Id_to_delete):
    for ids in Id_to_delete.get('bridge_ids', []):
        cache_key = f"{redis_keys['get_bridge_data_']}{str(ids)}"
        await delete_in_cache(cache_key)
    for ids in Id_to_delete.get('version_ids', []):
        cache_key = f"{redis_keys['get_bridge_data_']}{str(ids)}"
        await delete_in_cache(cache_key)
    
def validate_required_params(data_to_update):
    if not isinstance(data_to_update, dict):
        return data_to_update

    if "required_params" in data_to_update:
        valid_keys = set()

        if "properties" in data_to_update and isinstance(data_to_update["properties"], dict):
            valid_keys.update(data_to_update["properties"].keys())
        if "parameter" in data_to_update and isinstance(data_to_update["parameter"], dict):
            valid_keys.update(data_to_update["parameter"].keys())
        
        data_to_update["required_params"] = [key for key in data_to_update["required_params"] if key in valid_keys]

    for key, value in data_to_update.items():
        if isinstance(value, dict):
            data_to_update[key] = validate_required_params(value)

    return data_to_update