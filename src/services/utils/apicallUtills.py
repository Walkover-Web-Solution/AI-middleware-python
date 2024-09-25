import datetime 
from models.mongo_connection import db
apiCallModel = db['apicalls']

async def get_api_id(org_id, function_name):
    try:
        api_call_data =  apiCallModel.find_one(
        {
            "$or": [
                {"org_id": org_id, "function_name": function_name},  # new data  function_name
                {"org_id": org_id, "endpoint": function_name},  # previous data endpoint
            ]
        })
        api_id = api_call_data.get('_id', "") if api_call_data else ""
        return api_id
    except Exception as error:
        print(f"error: {error}")
        return ""



async def save_api(desc, org_id, api_id=None, code="", required_params=None, function_name="", fields=None, activated=False, endpoint_name="", status = 1, version="v2"):
    if fields is None:
        fields = []
    if required_params is None:
        required_params = []

    try:
        if api_id:
            api_data = apiCallModel.find_one({"_id": api_id})
            if api_data:
                fields = updateFields(api_data.get('fields',{} if api_data.get('version', 'v1')== 'v2' else []), fields , api_data.get('version', 'v1') == version)
                # Delete certain keys from api_data
                keys_to_delete = ["required_fields", "short_description", 'axios', "optional_fields", "endpoint", 'api_description']  # Replace with actual keys to delete
                for key in keys_to_delete:
                    if key in api_data:
                        del api_data[key]
                
                api_data['description'] = desc
                api_data['code'] = code
                api_data['required_params'] = api_data['required_params'] if api_data.get('version', 'v1')== 'v2' else required_params
                api_data['fields'] = fields
                api_data['activated'] = activated
                api_data['updated_at'] = datetime.datetime.now()
                api_data['function_name'] = function_name # script id will be set in this in case of viasocket
                api_data['endpoint_name'] = endpoint_name # flow name will be saved in this in case of viasocket
                api_data['is_python'] = 1
                api_data["status"] = status
                api_data['version']= version

                # saving updated fields in the db with same id
                saved_api =  apiCallModel.replace_one({"_id": api_id}, api_data)
                if saved_api.modified_count == 1:
                    return {
                        "success": True,
                        "api_data": api_data,
                    }
        else:
            api_data = {
                "description": desc,
                "org_id": org_id,
                "required_params": required_params,
                "fields": fields,
                "activated": activated,
                "function_name": function_name,
                "code": code,
                "endpoint_name": endpoint_name,
                "is_python": 1,
                "status": status,
                "created_at": datetime.datetime.now(),
                "updated_at": datetime.datetime.now(),
                "version": version
            }
            new_api =  apiCallModel.insert_one(api_data)
            return {
                "success": True,
                 "api_data": {
                    "_id": str(new_api.inserted_id),
                    **api_data
                },
            }
    except Exception as error:
        print(f"error: {error}")
        return {
            "success": False,
            "error": str(error)
        }
    
    
def updateFields(oldFields, newFields, versionCheck):
    def update_recursive(old, new):
        for key in new:
            if key in old:
                # Update fields based on old_dict values
                new[key]['description'] = old[key].get('description') if new[key].get('description') == '' else new[key].get('description')
                new[key]['type'] = old[key].get('type') or new[key].get('type')
                new[key]['enum'] = old[key].get('enum') if new[key].get('enum') == [] else []
                if isinstance(old[key], dict) and isinstance(new[key], dict):
                    # Recursively update nested dictionaries
                    update_recursive(old[key]['parameter'], new[key]['parameter'])
            else:
                # Preserve additional keys in new_dict
                if isinstance(new[key], dict):
                    update_recursive({}, new[key])  # No update needed if old doesn't have the key
        return new

    if(versionCheck): 
        updateField = update_recursive(oldFields, newFields)
    else:
        transformed_data = {item["variable_name"]: {"description": item["description"], "enum": item["enum"]} for item in oldFields}
        updateField = update_recursive(transformed_data, newFields)
    return updateField

async def delete_api(function_name, org_id, status = 0):
    try:
        data = apiCallModel.find_one_and_update({
            "$or": [
                {"org_id": org_id, "endpoint": function_name},
                {"org_id": org_id, "function_name": function_name},
            ]
        }, {"$set": {"status": status}}, return_document=True)
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
        print(f"Delete API error=> {error}")
        return {"success": False, "error": str(error)}