from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from src.db_services.apiCallDbService import get_all_api_calls_by_org_id

async def get_all_apicalls_controller(request):
    try:
        org_id = request.state.profile['org']['id']
        functions = await get_all_api_calls_by_org_id(org_id=org_id)
        return JSONResponse(status_code=200, content={
                "success": True,
                "message": "Get all functions of a org successfully",
                "data" : functions,
                "org_id": org_id # [?] is it really needed
            })
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e,)