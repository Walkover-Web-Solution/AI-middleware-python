from fastapi import Request
from fastapi.responses import JSONResponse
from src.db_services.ConfigurationServices import get_bridges
from src.db_services.ConfigurationServices import get_bridges_with_tools
from datetime import datetime, timezone
from src.controllers.configController import duplicate_create_bridges

import json

async def duplicate_bridge(request : Request):
    try:
        body = await request.json()
        org_id = request.state.profile.get("org",{}).get("id","")
        bridge_id = body.get('bridge_id')
        result = await get_bridges_with_tools(bridge_id, org_id)
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
            "apiCalls":bridge.get('apiCalls',{})
        })
        return JSONResponse(status_code=200, content={
            "success": True,
            "message": "Bridge duplicated successfully",
            "result" : json.loads(json.dumps(res, default=str))

        })
    except Exception as e:
        return {'error': str(e)}