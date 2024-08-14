from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from src.controllers.configController import get_and_update
from src.db_services.ConfigurationServices import get_bridges, update_bridge, get_api_call_by_name
from src.services.utils.helper import Helper
import json
import datetime 
from models.mongo_connection import db
apiCallModel = db['apicalls']


async def creates_api(request: Request, bridge_id: str):
    try:
        body = await request.json()
        function_name = body.get('id')
        payload = body.get('payload')
        url = body.get('url')
        status = body.get('status')
        org_id = request.state.org_id if hasattr(request.state, 'org_id') else None
        endpoint_name = body.get('endpoint_name')
        desc = body.get('desc')

        if not all([desc, function_name, status, bridge_id, org_id]):
            raise HTTPException(status_code=400, detail="Required details must not be empty!!")
        
        model_config = await get_bridges(bridge_id)

        if model_config.get('success') is False:
            raise HTTPException(status_code=400, detail="bridge data not found")
        
        desc = f"function_name: {endpoint_name} desc" if endpoint_name else desc
        axios_code = ""

        if status in ["published", "updated"]:
            body_content = payload.get('body') if payload else None
            required_params = []

            if body_content:
                traversed_body = traverse_body(body_content)
                required_params = traversed_body.get('required_params', [])
                axios_code = f"""def axios_call(params):
    import requests

    def set_nested_value(data, path, value):
        keys = path.split(".")
        d = data
        for key in keys[:-1]:
            d = d.setdefault(key, {{}})
        d[keys[-1]] = value
        return data

    try:
        data = {json.dumps(body_content)}
        paths = {json.dumps(traversed_body.get('paths', []))}
        for path in paths:
            keys = path.split(".")
            data = set_nested_value(data, path, params[keys[-1]])
        response = requests.post('{url}', json=data, headers={{'content-type': 'application/json'}})
        return response.json()
    except requests.RequestException as e:
        return str(e)"""
            else:
                axios_code = f"""def axios_call(params):
    import requests
    try:
        response = requests.get('{url}', headers={{'content-type': 'application/json'}})
        return response.json()
    except requests.RequestException as e:
        return str(e)"""

            fields = [{"variable_name": param, "description": '', "enum": ''} for param in required_params]
            api_id = await get_api_id(org_id, bridge_id, function_name)
            response = await save_api(desc, org_id, bridge_id, api_id, axios_code, required_params, function_name, fields, True, endpoint_name)

            if not response.get('success'):
                raise HTTPException(status_code=400, detail="Something went wrong!")

            api_object_id = response.get('api_object_id')
            data = await create_open_api(function_name, desc, api_object_id, required_params, model_config)
            result = await get_and_update(bridge_id, org_id, data['format'], function_name, 'add', model_config)

            if result.get('success'):
                return JSONResponse(status_code=200, content={
                    "message": "API saved successfully",
                    "success": True,
                    "activated": True,
                    "tools_call": result.get('tools_call')
                })
            else:
                raise HTTPException(status_code=400, detail=result)

        elif status in ["delete", "paused"]:
            result = await delete_api(function_name, org_id, bridge_id, model_config)
            if result.get('success'):
                return JSONResponse(status_code=200, content={
                    "message": "API deleted successfully",
                    "success": True,
                    "deleted": True,
                    "tools_call": result.get('tools_call')
                })
            else:
                raise HTTPException(status_code=400, detail=result)

        raise HTTPException(status_code=400, detail="Something went wrong!")

    except Exception as error:
        print(f"error in viasocket embed get api=> {error}")
        raise HTTPException(status_code=400, detail=str(error))


async def updates_api(request: Request, bridge_id: str):
    try:
        body = await request.json()
        org_id = request.state.org_id if hasattr(request.state, 'org_id') else None
        function_name = body.get('id')
        pre_function_call = body.get('preFunctionCall')

        if not all([function_name, bridge_id, org_id]):
            raise HTTPException(status_code=400, detail="Required details must not be empty!!")
    
        model_config = await get_bridges(bridge_id)

        if model_config.get('success') is False: 
            raise HTTPException(status_code=400, detail="bridge id is not found")
            
        model_config = model_config.get('bridges', {})
        tools_call = model_config.get('configuration', {}).get('tools', [])
        pre_tools_call = model_config.get('pre_tools', [])

        updated_tools_call = [tool for tool in tools_call if tool['name'] != function_name]
        updated_pre_tools_call = [tool for tool in pre_tools_call if tool != function_name]

        if pre_function_call:
            if function_name in pre_tools_call:
                raise HTTPException(status_code=400, detail='function is already added to pre function')
            updated_pre_tools_call.append(function_name)
        else:
            api_response = await get_api_call_by_name(function_name)
            api_data = api_response.get('apiCall', {})
            open_api_format = create_open_api(function_name, api_data.get('description', ""), str(api_data.get('_id', "")), api_data.get('required_params', []) )
            if function_name in tools_call:
                raise HTTPException(status_code=400, detail='function is already added to tools')
            updated_tools_call.append(open_api_format['format'])

        model_config['configuration'] = {
            **model_config["configuration"],
            "tools": updated_tools_call
        }
        model_config["pre_tools"] = updated_pre_tools_call
        result = await update_bridge(bridge_id, model_config)

        if result.get("success"):
            return Helper.response_middleware_for_bridge({
                "success": True,
                "message": "Bridge Updated successfully",
                "bridge" : result.get('result')

            })
        else:
            return JSONResponse(status_code=400, content=result)

    except Exception as error:
        print(f"error in viasocket embed get api=> {error}")
        raise HTTPException(status_code=400, detail=str(error))

def set_nested_value(data, path, value):
    keys = path.split(".")
    for key in keys[:-1]:
        data = data.setdefault(key, {})
    data[keys[-1]] = value
    return data



def traverse_body(body, required_params=None, path="", paths=None):
    if required_params is None:
        required_params = []
    if paths is None:
        paths = []

    for key, value in body.items():
        if isinstance(value, dict):
            traverse_body(value, required_params, f"{path}{key}.", paths)
        elif value == "your_value_here":
            paths.append(f"{path}{key}")
            required_params.append(key)  # [?] it can repeat

    return {"required_params": required_params, "paths": paths}



async def get_api_id(org_id, bridge_id, function_name):
    try:
        api_call_data =  apiCallModel.find_one(
        {
            "$or": [
                {"org_id": org_id, "bridge_id": bridge_id, "function_name": function_name},  # new data  function_name
                {"org_id": org_id, "bridge_id": bridge_id, "endpoint": function_name},  # previous data endpoint
            ]
        })
        api_id = api_call_data.get('_id', "") if api_call_data else ""
        return api_id
    except Exception as error:
        print(f"error: {error}")
        return ""


async def save_api(desc, org_id, bridge_id, api_id=None, code="", required_params=None, function_name="", fields=None, activated=False, endpoint_name=""):
    if fields is None:
        fields = []
    if required_params is None:
        required_params = []

    try:
        if api_id:
            api_data = apiCallModel.find_one({"_id": api_id})
            if api_data:
                # Delete certain keys from api_data
                keys_to_delete = ["required_fields", "short_description", 'axios', "optional_fields", "endpoint", 'api_description']  # Replace with actual keys to delete
                for key in keys_to_delete:
                    if key in api_data:
                        del api_data[key]
                
                api_data['description'] = desc
                api_data['code'] = code
                api_data['required_params'] = required_params
                api_data['fields'] = fields
                api_data['activated'] = activated
                api_data['updated_at'] = datetime.datetime.now()
                api_data['function_name'] = function_name # script id will be set in this in case of viasocket
                api_data['endpoint_name'] = endpoint_name # flow name will be saved in this in case of viasocket
                api_data['is_python'] = 1

                # saving updated fields in the db with same id
                saved_api =  apiCallModel.replace_one({"_id": api_id}, api_data)
                if saved_api.modified_count == 1:
                    return {
                        "success": True,
                        "api_object_id": str(api_id),
                        "required_params": api_data['required_params'],
                        "optional_fields": api_data.get('optional_fields', [])
                    }
        else:
            api_data = {
                "description": desc,
                "org_id": org_id,
                "bridge_id": bridge_id,
                "required_params": required_params,
                "fields": fields,
                "activated": activated,
                "function_name": function_name,
                "code": code,
                "endpoint_name": endpoint_name,
                "is_python": 1,
                "created_at": datetime.datetime.now(),
                "updated_at": datetime.datetime.now()
            }
            new_api =  apiCallModel.insert_one(api_data)
            return {
                "success": True,
                "api_object_id": str(new_api.inserted_id)
            }
    except Exception as error:
        print(f"error: {error}")
        return {
            "success": False,
            "error": str(error)
        }
    


async def create_open_api(function_name, desc,api_object_id, required_params=None, model_config = {}):
    if required_params is None:
        required_params = []
    
    tools_call = model_config.get('bridges', {}).get('configuration', {}).get('tools', [])
    current_function_data = [tool for tool in tools_call if tool['name'] == function_name][0]
    old_properties = current_function_data.get('properties', {})
    old_required = current_function_data.get('required', [])
    try:
        format = {
            "type": "function",
            "id":api_object_id,
            "name": function_name,
            "description": desc
        }
        properties = {}
        final_required = []
        for field in required_params:
            if old_properties.get(field):
                properties[field] = old_properties.get(field)
            else:
                properties[field] = {"type": "string"}
                final_required.append(field)

            if field in old_required:
                final_required.append(field)
        if required_params:
            format["required"] = final_required
            format["properties"] = properties
        return {"success": True, "format": format}
    except Exception as error:
        return {"success": False, "error": str(error)}
    


async def delete_api(function_name, org_id, bridge_id, model_config):
    try:
        # delete by endpoint
        # todo : testing left
        # apiCallModel.find_one_and_delete({
        #     "$or": [
        #         {"org_id": org_id, "bridge_id": bridge_id, "endpoint": function_name},
        #         {"org_id": org_id, "bridge_id": bridge_id, "name": function_name}
        #     ]
        # })
        result = await get_and_update(bridge_id, org_id, "", function_name, "delete", model_config)
        return result
    except Exception as error:
        print(f"Delete API error=> {error}")
        return {"success": False, "error": str(error)}