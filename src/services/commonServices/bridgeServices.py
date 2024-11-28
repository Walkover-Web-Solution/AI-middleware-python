from fastapi import Request
from fastapi.responses import JSONResponse
from src.db_services.ConfigurationServices import get_bridges
from datetime import datetime, timezone
from src.services.utils.apiservice import fetch
from src.controllers.configController import duplicate_create_bridges

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
        purpose = body.get('purpose', "optimize")
        prompt_description = body.get('prompt_description', "")
        org_id = request.state.profile.get("org",{}).get("id","")
        result = await get_bridges(bridge_id, org_id)
        bridge = result.get('bridges')
        prompt = bridge.get('configuration',{}).get('prompt',"")
        bridgeName = bridge.get('name')
        result = ""
        try:    
            response, rs_headers = await fetch(f"https://flow.sokt.io/func/scrivbjJBCa3","POST", None,None, {"prompt": prompt, "threadId": bridgeName, "purpose": purpose, "promptDescription": prompt_description}) # required is not send then it will still hit the curl
            if response.get('success') == False:
                raise Exception(response.get('message'))
            else:
                result = response.get('response',{}).get('data',{}).get('content',"")
                
        except Exception as err:
            print("Error calling function=>", err)
        return JSONResponse(status_code=200, content={
            "success": True,
            "message": "Prompt optimized successfully",
            "result" : result
        })
        
    except Exception as e:
        return {'error': str(e)}