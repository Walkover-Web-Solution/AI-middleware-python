from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from src.db_services.apiCallDbService import get_all_api_calls_by_org_id, update_api_call_by_function_id, get_function_by_id, delete_function_from_apicalls_db
from globals import *
from src.services.utils.apicallUtills import validate_required_params

async def get_all_apicalls_controller(request):
    try:
        org_id = request.state.profile['org']['id']
        folder_id = request.state.folder_id if hasattr(request.state, 'folder_id') else None
        user_id = request.state.user_id
        isEmbedUser = request.state.embed
        functions = await get_all_api_calls_by_org_id(org_id=org_id, folder_id=folder_id, user_id=user_id, isEmbedUser=isEmbedUser)
        return JSONResponse(status_code=200, content={
                "success": True,
                "message": "Get all functions of a org successfully",
                "data" : functions,
                "org_id": org_id # [?] is it really needed
            })
    except Exception as e:
        logger.error(f"Error in get_all_apicalls_controller: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    

async def update_apicalls_controller(request, function_id):
    try:
        org_id = request.state.profile['org']['id']
        body = await request.json()  
        data_to_update = validate_required_params(body.get('dataToSend'))  

        if not function_id or not data_to_update:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing function_id or data to update")
        
        data = await get_function_by_id(function_id)
        del data['_id']

        data_to_update['old_fields'] = data.get('fields',{})
        data_to_update = {**data_to_update, "version": "v2"}
        updated_function = await update_api_call_by_function_id(
            org_id=org_id, function_id=function_id, data_to_update=data_to_update
        )
        
        return JSONResponse(status_code=200, content={
            "success": True,
            "data": updated_function
        })
    
    except Exception as e:
        logger.error(f"Error updating function: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

async def delete_function(request):
    try:
        org_id = request.state.profile['org']['id']
        body = await request.json()
        function_name = body.get('function_name')
        if not function_name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing endpoint_name")
        return await delete_function_from_apicalls_db(org_id, function_name)
    
    except Exception as e:
        logger.error(f"Error deleting function: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))