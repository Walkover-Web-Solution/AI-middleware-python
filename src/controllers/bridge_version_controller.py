import json
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from ..db_services.bridge_version_services import get_bridge, create_bridge_version, update_bridge, get_version_with_tools, publish
from src.services.utils.helper import Helper
async def create_version(request):
    try:
       body = await request.json()
       version_id = body.get('version_id')
       org_id = request.state.profile['org']['id']
       bridge_data = await get_bridge(org_id, version_id)
       if bridge_data is None:
           return JSONResponse({"success": False, "message": "no version found"})
       parent_id = bridge_data.get('parent_id')
       create_new_version = await create_bridge_version(bridge_data)
       update_fields = {'versions' : [create_new_version]}
       await update_bridge(parent_id, update_fields)
       return {
           "success": True,
           "message" : "version created successfully",
           "version_id" : create_new_version
       }

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e)

async def get_version(request, version_id: str):
    try:

        bridge = await get_version_with_tools(version_id,request.state.profile['org']['id'])
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
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e)
