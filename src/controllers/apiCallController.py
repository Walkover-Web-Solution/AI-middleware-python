from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from src.db_services.apiCallDbService import get_all_api_calls_by_org_id
from src.db_services.apiCallDbService import update_api_call_by_function_id



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
        # Extract org_id from the request state (assuming it comes from middleware)
        org_id = request.state.profile['org']['id']
        
        # Extract the request body as JSON
        body = await request.json()  # Use await since request.body() is a coroutine
        
        # Extract functionId and the data to update
        function_id = body.get('function_id')  # Ensure that 'function_id' exists in the body
        data_to_update = body.get('dataToSend')  # Get the fields to be updated

        # Print the data_to_update to the terminal
        # print(f"Data to update: {data_to_update}")
        
        if not function_id or not data_to_update:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing function_id or data to update")

        # Call the update function with org_id, function_id, and data_to_update
        updated_function = await update_api_call_by_function_id(org_id=org_id, function_id=function_id, data_to_update=data_to_update)
        
        # Return a successful response
        return JSONResponse(status_code=200, content={
            "success": True,
            "message": "Function updated successfully",
            "data": updated_function
        })
    
    except HTTPException as e:
        raise e  # Propagate HTTPExceptions
    except Exception as e:
        print(f"Error updating function: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

