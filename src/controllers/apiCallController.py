from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from src.db_services.apiCallDbService import get_all_api_calls_by_org_id
from src.db_services.apiCallDbService import update_api_call_by_function_id
from pydantic import ValidationError
from validations.validation import DataToSendModel

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

async def update_apicalls_controller(request):
    try:
        org_id = request.state.profile['org']['id']
        body = await request.json()  
        
        function_id = body.get('function_id')  
        data_to_update = body.get('dataToSend')  

        if not function_id or not data_to_update:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing function_id or data to update")

        try:
            validated_data_to_send = DataToSendModel(**data_to_update)
        except ValidationError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Validation Failed while Updating the Function")
        updated_function = await update_api_call_by_function_id(org_id=org_id, function_id=function_id, data_to_update=data_to_update)
        
        return JSONResponse(status_code=200, content={
            "success": True,
            "data": updated_function
        })
    
    except HTTPException as e:
        print(f"Error updating function: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        print(f"Error updating function: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))