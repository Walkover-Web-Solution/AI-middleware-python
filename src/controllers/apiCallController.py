from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from src.db_services.apiCallDbService import get_all_api_calls_by_org_id
from src.db_services.apiCallDbService import update_api_call_by_function_id
from pydantic import ValidationError
from validations.update_tools_call_validation import data_to_update_model
from validations.update_tools_call_validation import update_tool_call_body_data
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
        
   

        try:
            validate_function_id = update_tool_call_body_data(**{
            "function_id" : function_id,
            "data_to_update": data_to_update
        })
            validated_data_to_update = data_to_update_model(**data_to_update)
        except ValidationError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        
        updated_function = await update_api_call_by_function_id(org_id=org_id, function_id=function_id, data_to_update=data_to_update)
        
        return JSONResponse(status_code=200, content={
            "success": True,
            "data": updated_function
        })
    
    except Exception as e:
        print(f"Error updating function: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))