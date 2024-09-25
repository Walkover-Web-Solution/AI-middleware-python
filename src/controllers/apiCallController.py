from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from src.db_services.apiCallDbService import get_all_api_calls_by_org_id
from src.db_services.apiCallDbService import update_api_call_by_function_id
from src.db_services.apiCallDbService import get_function_by_id


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
    

async def validate_data_to_update(data_to_update, db_data):
    def recursive_check(data, expected):
        for key in expected:
            if key not in data:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Missing key: '{key}' in data_to_update")

            if isinstance(expected[key], dict):
                recursive_check(data[key], expected[key])

    recursive_check(data_to_update, db_data)
    return True


async def update_apicalls_controller(request):
    try:
        org_id = request.state.profile['org']['id']
        body = await request.json()
        
        function_id = body.get('function_id')
        data_to_update = body.get('dataToSend')

        if not function_id or not data_to_update:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing function_id or data to update")
        
        db_data = await get_function_by_id(function_id)
        
        if not db_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Function not found")
        
        data = db_data.get('data', {})
        del data['_id']

        await validate_data_to_update(data_to_update, data)
      
        updated_function = await update_api_call_by_function_id(
            org_id=org_id, function_id=function_id, data_to_update=data_to_update
        )
        
        return JSONResponse(status_code=200, content={
            "success": True,
            "message": "Function updated successfully",
            "data": updated_function
        })
    
    except HTTPException as e:
        print(f"HTTP Error updating function: {e}")
        raise e  # Re-raise the HTTPException since it has already been handled
    
    except Exception as e:
        print(f"General Error updating function: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred")