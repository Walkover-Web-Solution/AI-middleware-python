from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from src.configs.constant import bridge_ids, prebuilt_prompt_bridge_id
from src.services.prebuilt_prompt_service import get_specific_prebuilt_prompt_service
from src.services.utils.logger import logger



async def get_specific_prebuilt_prompt_controller(request: Request):
    """Get a specific prebuilt prompt by prompt_key"""
    try:
        body = await request.json()
        org_id = request.state.profile['org']['id']
        
        # Validate request body
        if not body or not body.get('prompt_key'):
            raise HTTPException(status_code=400, detail="prompt_key is required in request body")
        
        prompt_key = body.get('prompt_key')
        
        # Validate that prompt_key is one of the allowed prebuilt prompt IDs
        if prompt_key not in prebuilt_prompt_bridge_id:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid prompt_key. Must be one of: {prebuilt_prompt_bridge_id}"
            )
        
        # Get the specific prompt
        specific_prompt = await get_specific_prebuilt_prompt_service(org_id, prompt_key)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Retrieved prompt '{prompt_key}' successfully",
                "data": specific_prompt
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_specific_prebuilt_prompt_controller: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")