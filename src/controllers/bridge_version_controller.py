import json
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from ..db_services.bridge_version_services import get_bridge, create_bridge_version, update_bridge
async def create_version(request):
    try:
       body = await request.json()
       version_id = body.get('version_id')
       org_id = request.state.profile['org']['id']
       bridge_data = await get_bridge(org_id, version_id)
       parent_id = bridge_data.get('parent_id')
       create_new_version = await create_bridge_version(bridge_data)
       update_fields = {'versions' : [create_new_version]}
       await update_bridge(parent_id, update_fields)
       return {
           "success": True,
           "message" : "version created successfully"
       }

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e)