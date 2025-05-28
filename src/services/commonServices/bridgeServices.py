from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from src.db_services.ConfigurationServices import get_bridges, get_bridges_with_tools
from datetime import datetime, timezone
from src.controllers.configController import duplicate_create_bridges
from src.configs.constant import bridge_ids
from src.services.utils.ai_call_util import call_ai_middleware

import json

async def duplicate_bridge(request : Request):
    try:
        body = await request.json()
        org_id = request.state.profile.get("org",{}).get("id","")
        bridge_id = body.get('bridge_id')
        result = await get_bridges(bridge_id, org_id)
        bridge = result.get('bridges')
        timestamp = datetime.now(timezone.utc).strftime('%d%H%S')
        name = bridge.get('name')
        new_name = f"{name}_{timestamp}"
        slugname = bridge.get('slugName')
        new_slugName = f"{slugname}_{timestamp}"
        # new_created_at = datetime.now(timezone.utc)
        res = await duplicate_create_bridges({
            "org_id": bridge.get('org_id'),
            "service": bridge.get('service'),
            "bridgeType": bridge.get('bridgeType'),
            "name": new_name,
            "configuration": bridge.get('configuration'),
            "apikey": bridge.get('apikey'),
            "slugName": new_slugName,
            "function_ids": bridge.get('function_ids'),
            "actions": bridge.get('actions',{}),
            "apikey_object_id": bridge.get('apikey_object_id',""),
        })
        return JSONResponse(status_code=200, content={
            "success": True,
            "message": "Bridge duplicated successfully",
            "result" : json.loads(json.dumps(res, default=str))

        })
    except Exception as e:
        return {'error': str(e)}
    

async def optimize_prompt_controller(request : Request, bridge_id: str):
    try:
        body = await request.json()
        version_id = body.get('version_id')
        org_id = request.state.profile.get("org",{}).get("id","")
        result = await get_bridges(bridge_id, org_id, version_id)
        bridge = result.get('bridges')
        prompt = bridge.get('configuration',{}).get('prompt',"")
        bridgeName = bridge.get('name')
        result = ""
        result = await call_ai_middleware(prompt, bridge_id = bridge_ids['optimze_prompt'], response_type='text', thread_id = bridgeName)
        return JSONResponse(status_code=200, content={
            "success": True,
            "message": "Prompt optimized successfully",
            "result" : result
        })
        
    except Exception as e:
        raise HTTPException(status_code=400, detail={"success": False, "error": "Error in optimizing prompt: "+ str(e)})
    
    



async def generate_summary(request):
    try:
        body = await request.json()
        org_id = request.state.profile.get("org",{}).get("id","")
        version_id = body.get('version_id')
        get_version_data = (await get_bridges_with_tools(None, org_id, version_id)).get("bridges")
        if not get_version_data:
            return {
                "success": False,
                "error": "Version data not found"
            }
        tools = {tool['endpoint_name']: tool['description'] for tool in get_version_data.get('apiCalls', {}).values()}
        system_prompt = get_version_data.get('configuration',{}).get('prompt')
        if tools:
            system_prompt += f'Available tool calls :-  {tools}'
        variables = {'prompt' : system_prompt}
        user = "generate summary from the user message provided in system prompt"
        summary = await call_ai_middleware(user, bridge_id = bridge_ids['generate_summary'],response_type='text', variables = variables)
        return JSONResponse(status_code=200, content={
            "success": True,
            "message": "Summary generated successfully",
            "result" : summary
        })
            
    except Exception as err:
        print("Error calling function=>", err)
async def function_agrs_using_ai(request):
    try:
        body = await request.json()
        data = body.get('example_json')
        user = f"geneate the json using the example json data : {data}"
        json = await call_ai_middleware(user, bridge_id = bridge_ids['function_agrs_using_ai'])
        return JSONResponse(status_code=200, content={
            "success": True,
            "message": "json generated successfully",
            "result" : json
        })
            
    except Exception as err:
        print("Error calling function=>", err)
    