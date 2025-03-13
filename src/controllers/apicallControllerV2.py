from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from src.db_services.ConfigurationServices import get_bridges, update_bridge, get_bridges_with_tools
from src.services.utils.helper import Helper
from src.services.utils.apicallUtills import  get_api_data, save_api, delete_api
import pydash as _
import datetime


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

        if status in ["published", "updated"]:
            body_content = payload.get('body') if payload else None

            traversed_body = traverse_body(body_content)
            fields = traversed_body.get('fields',{})
            api_data = await get_api_data(org_id, function_name)

            result  = await save_api(desc, org_id, api_data, [], function_name, fields, endpoint_name)
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
                return JSONResponse(status_code=200, content={
                    "message": "API saved successfully",
                    "success": True,
                    "activated": True,
                    "data": result['api_data']
                })
            else:
                raise HTTPException(status_code=400, detail=result)

        elif status in ["delete", "paused"]:
            result = await delete_api(function_name, org_id)
            if result:
                return JSONResponse(status_code=200, content={
                    "message": "API deleted successfully",
                    "success": True,
                    "deleted": True,
                    "data": result
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
        version_id = body.get('version_id')
        org_id = request.state.org_id if hasattr(request.state, 'org_id') else None
        pre_tools = body.get('pre_tools')

        if not all([pre_tools is not None, bridge_id, org_id]):
            raise HTTPException(status_code=400, detail="Required details must not be empty!!")
    
        model_config = await get_bridges(bridge_id, org_id, version_id)

        if model_config.get('success') is False: 
            raise HTTPException(status_code=400, detail="bridge id is not found")
    
        data_to_update = {}
        data_to_update['pre_tools'] = pre_tools
        result = await update_bridge(bridge_id, data_to_update, version_id)

        result = await get_bridges_with_tools(bridge_id, org_id, version_id)

        if result.get("success"):
            return Helper.response_middleware_for_bridge({
                "success": True,
                "message": "Bridge Updated successfully",
                "bridge" : result.get('bridges')

            })
        else:
            return JSONResponse(status_code=400, content=result)

    except Exception as error:
        print(f"error in viasocket embed get api => {error}")
        raise HTTPException(status_code=400, detail=str(error))


# /**
# * Recursively traverses a nested object structure to build a structured representation
#  * of its fields, paths, and parameter requirements.
#  * 
#  * This function analyzes a hierarchical object and:
#  * - Extracts paths to specific values (fields with "your_value_here")
#  * - Builds a structured fields object that maintains the hierarchy with type information
#  * - Tracks required parameters at each level of the hierarchy
#  * 
#  * @param {Object} body - The object to traverse
#  * @param {Array} path - Current path in the traversal (internal tracking)
#  * @param {Array} paths - Collects dot-notation paths to all "your_value_here" fields
#  * @param {Object} fields - Builds a structured representation of the object hierarchy
#  * @param {Array} required_params - Collects names of required parameters
#  * @returns {Object} Object containing paths, fields structure, and required parameters
#  * 
#  * Example usage:
#  * traverse_body({
#  *   "r": {
#  *     "demo": {
#  *       "value": {
#  *         "demo3": "your_value_here"
#  *       }
#  *     }
#  *   },
#  *   "r1": {
#  *     "demo5": {
#  *       "value2": "your_value_here"
#  *     }
#  *   },
#  *   "nsr": {
#  *     "demo": "your_value_here"
#  *   }
#  * })
#  **/
def traverse_body(body, path=None, paths=None, fields=None, required_params=None):
    # Initialize default parameters
    if path is None:
        path = []
    if paths is None:
        paths = []
    if fields is None:
        fields = {}
    if required_params is None:
        required_params = []
    
    if not body:
        return {
            "paths": paths,
            "fields": fields,
            "required_params": required_params
        }
    
    for key, value in body.items():
        current_path = path + [key]
        
        # If we're at the root level, initialize the key in fields
        if len(path) == 0:
            if key not in fields:
                fields[key] = {
                    "description": "",
                    "type": "object",
                    "enum": [],
                    "required_params": [],
                    "parameter": {}
                }
        
        # If the value is a dictionary, process as nested object
        if isinstance(value, dict):
            # Determine the parent path and update its fields
            if path:
                # Build parent path string
                parent_path = path[0]
                parent_obj = fields[parent_path]
                
                for i in range(1, len(path)):
                    parent_obj = parent_obj["parameter"][path[i]]
                
                # Add current key to parent's required_params if not there
                if key not in parent_obj["required_params"]:
                    parent_obj["required_params"].append(key)
                
                # Ensure the key exists in the parent's parameter object
                if key not in parent_obj["parameter"]:
                    parent_obj["parameter"][key] = {
                        "description": "",
                        "type": "object",
                        "enum": [],
                        "required_params": [],
                        "parameter": {}
                    }
            
            # Recursively traverse the nested object
            traverse_body(value, current_path, paths, fields, required_params)
        
        # If we found a placeholder value
        elif value == "your_value_here":
            # Add the path to paths
            paths.append(".".join(current_path))
            
            # Add the key to required_params
            if key not in required_params:
                required_params.append(key)
            
            # Update the fields structure
            if path:
                # Navigate to the parent object
                parent_path = path[0]
                parent_obj = fields[parent_path]
                
                for i in range(1, len(path)):
                    parent_obj = parent_obj["parameter"][path[i]]
                
                # Add current key to parent's required_params if not there
                if key not in parent_obj["required_params"]:
                    parent_obj["required_params"].append(key)
                
                # Add the key to the parent's parameter object
                parent_obj["parameter"][key] = {
                    "description": "",
                    "type": "string",
                    "enum": [],
                    "required_params": [],
                    "parameter": {}
                }
            else:
                # We're at the root level
                fields[key] = {
                    "description": "",
                    "type": "string",
                    "enum": [],
                    "required_params": [],
                    "parameter": {}
                }
    
    return {
        "paths": paths,
        "fields": fields,
        "required_params": required_params
    }


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
    




