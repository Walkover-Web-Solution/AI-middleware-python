import json
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from ..db_services.bridge_version_services import create_bridge_version, update_bridges, get_version_with_tools, publish
from src.services.utils.helper import Helper
from ..db_services.ConfigurationServices import get_bridges_with_tools, update_bridge, get_bridges_without_tools
from bson import ObjectId
async def create_version(request):
   try:
      body = await request.json()
      version_id = body.get('version_id')
      version_description = body.get('version_description') or ""
      org_id = request.state.profile['org']['id']
      bridge_data = await get_bridges_without_tools(org_id=org_id, version_id= version_id)
      if bridge_data is None:
          return JSONResponse({"success": False, "message": "no version found"})
      parent_id = bridge_data.get('bridges').get('parent_id')
      bridge_data['bridges']['version_description'] = version_description
      create_new_version = await create_bridge_version(bridge_data.get('bridges'), parent_id=parent_id)
      update_fields = {'versions' : [create_new_version]}
      await update_bridges(parent_id, update_fields)
      return {
          "success": True,
          "message" : "version created successfully",
          "version_id" : create_new_version
      }
   
   except Exception as e:
       raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e)

async def get_version(request, version_id: str):
    try:
        org_id = request.state.profile.get("org",{}).get("id","")
        bridge = await get_version_with_tools(version_id, org_id)
        prompt = bridge.get('bridges').get('configuration',{}).get('prompt')
        variables = []
        if prompt is not None:
            variables = Helper.find_variables_in_string(prompt)
        variables_path = bridge.get('bridges').get('variables_path',{})
        path_variables = []
        for script_id, vars_dict in variables_path.items():
            if isinstance(vars_dict, dict):
                path_variables.extend(vars_dict.keys())
            else:
                path_variables.append(vars_dict)
        all_variables = variables + path_variables
        bridge.get('bridges')['all_varaibles'] = all_variables
        return Helper.response_middleware_for_bridge({"succcess": True,"message": "bridge get successfully","bridge":bridge.get("bridges", {})})
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e,)
    

async def publish_version(request, version_id):
    try:
        org_id = request.state.profile['org']['id']
        result = await publish(org_id, version_id)
        if result['success']:
            return JSONResponse({"success": True, "message": "version published successfully", "version_id": version_id})
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e)


async def discard_version(request, version_id):
    org_id = request.state.profile['org']['id']
    body = await request.json()
    bridge_id = body.get('bridge_id')
    cache_key = f"{version_id}"
    bridge_data = await get_bridges_with_tools(bridge_id, org_id)
    bridge_data['bridges'] = {key: value for key, value in bridge_data['bridges'].items() if key not in ['name', 'slugName', 'bridgeType', '_id', 'versions','status']}
    bridge_data['bridges']['is_drafted'] = False
    function_ids = bridge_data['bridges'].get('function_ids', [])
    if function_ids is not None:
        bridge_data['bridges']['function_ids'] = [ObjectId(fid) for fid in function_ids]
    result = await update_bridge(version_id=version_id, update_fields=bridge_data['bridges'], cache_key=cache_key)
    if 'success' in result:
        return JSONResponse({"success": True, "message": "version changes discarded successfully", "version_id": version_id})
    return result
    
    