from fastapi import Request, HTTPException
from src.db_services.ConfigurationServices import get_bridges, update_bridge, get_bridges_with_tools
from src.services.utils.helper import Helper
from src.services.utils.apicallUtills import  get_api_data, save_api, delete_api
import json
import datetime 
from models.mongo_connection import db
apiCallModel = db['apicalls']


async def creates_api(request: Request):
    try:
        body = await request.json()
        org_id = request.state.profile.get("org",{}).get("id","")
        function_name = body.get('id')
        payload = body.get('payload')
        url = body.get('url')
        status = body.get('status')
        org_id = request.state.org_id if hasattr(request.state, 'org_id') else None
        endpoint_name = body.get('title')
        desc = body.get('desc')

        if not all([desc, function_name, status, org_id]):
            raise HTTPException(status_code=400, detail="Required details must not be empty!!")
        
        axios_code = ""

        if status in ["published", "updated"]:
            body_content = payload.get('body') if payload else None
            required_params = []

            traversed_body = traverse_body(body_content)
            required_params = traversed_body.get('required_params', [])
            fields = [{"variable_name": param, "description": '', "enum": ''} for param in required_params]
            api_data = await get_api_data(org_id, function_name)
            result  = await save_api(desc, org_id, api_data, axios_code, required_params, function_name, fields, True, endpoint_name, 1, 'v1')
            result['api_data']['_id'] = str(result['api_data']['_id'])
            if 'created_at' in result['api_data'] and isinstance(result['api_data']['created_at'], datetime.datetime):
                        result['api_data']['created_at'] = result['api_data']['created_at'].strftime('%Y-%m-%d %H:%M:%S')  # Convert datetime to string

            if 'updated_at' in result['api_data'] and isinstance(result['api_data']['updated_at'], datetime.datetime):
                        result['api_data']['updated_at'] = result['api_data']['updated_at'].strftime('%Y-%m-%d %H:%M:%S')  
             # Convert ObjectId to string
            if 'bridge_ids' in result['api_data']:
                result['api_data']['bridge_ids'] = [str(bid) for bid in result['api_data']['bridge_ids']] 

            if not result.get('success'):
                raise HTTPException(status_code=400, detail="Something went wrong!")

            if result.get('success'):
                response_data = {
                    "success": True,
                    "message": "API saved successfully",
                    "data": {"activated": True, "data": result['api_data']}    
                    }
                request.state.statusCode = 200
                request.state.response = response_data
                return {}
            else:
                raise HTTPException(status_code=400, detail=result)

        elif status in ["delete", "paused"]:
            result = await delete_api(function_name, org_id)
            if result:
                response_data = {
                    "success": True,
                    "message": "API deleted successfully",
                    "data": {"deleted": True, "data": result}   
                    }
                request.state.statusCode = 200
                request.state.response = response_data
                return {}
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
        pre_tools = body.get('pre_tools')

        if not all([pre_tools is not None, bridge_id, org_id]):
            raise HTTPException(status_code=400, detail="Required details must not be empty!!")
    
        model_config = await get_bridges(bridge_id, org_id)

        if model_config.get('success') is False: 
            raise HTTPException(status_code=400, detail="bridge id is not found")
    
        data_to_update = {}
        data_to_update['pre_tools'] = pre_tools
        result = await update_bridge(bridge_id, data_to_update)

        result = await get_bridges_with_tools(bridge_id, org_id)

        if result.get("success"):
            return Helper.response_middleware_for_bridge({
                "success": True,
                "message": "Bridge Updated successfully",
                "bridge" : result.get('bridges')

            })
        else:
            response_data = {
                "success": False,
                "message": None,
                "data": result  
                }
            request.state.statusCode = 400
            request.state.response = response_data
            return {}

    except Exception as error:
        print(f"error in viasocket embed get api => {error}")
        raise HTTPException(status_code=400, detail=str(error))


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


async def create_open_api(function_name, desc,api_object_id, required_params=None, model_config = {}):
    if required_params is None:
        required_params = []
    
    tools_call = model_config.get('bridges', {}).get('configuration', {}).get('tools', [])
    current_function_data = next((tool for tool in tools_call if tool['name'] == function_name), None)

    old_properties = current_function_data.get('properties', {}) if current_function_data else {}
    old_required = current_function_data.get('required', []) if current_function_data else []
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
    
