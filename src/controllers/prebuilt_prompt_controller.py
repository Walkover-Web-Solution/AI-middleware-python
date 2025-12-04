from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from src.services.utils.ai_call_util import get_ai_middleware_agent_data
from src.configs.constant import bridge_ids, prebuilt_prompt_bridge_id
from src.services.prebuilt_prompt_service import get_prebuilt_prompts_service
from src.services.utils.logger import logger

async def get_prebuilt_prompts_controller(request: Request):
    """Get all prebuilt prompts for an organization"""
    try:
        org_id = request.state.profile['org']['id']
        prebuilt_prompts = await get_prebuilt_prompts_service(org_id)
        
        # Create a set of existing prompt IDs for quick lookup
        existing_prompt_ids = set()
        for prompt in prebuilt_prompts:
            existing_prompt_ids.update(prompt.keys())
        
        # Check for missing prebuilt prompts and add them from bridge configuration
        for prebuilt_prompt_id in prebuilt_prompt_bridge_id:
            if prebuilt_prompt_id not in existing_prompt_ids:
                try:
                    bridge_prompt = await get_ai_middleware_agent_data(bridge_ids[prebuilt_prompt_id])
                    if bridge_prompt:
                       prebuilt_prompts.append({prebuilt_prompt_id:bridge_prompt['bridge']['configuration']['prompt']})
                except Exception as e:
                    logger.warning(f"Failed to fetch bridge prompt {prebuilt_prompt_id}: {str(e)}")
                    continue
                
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Prebuilt prompts retrieved successfully",
                "data": prebuilt_prompts
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_prebuilt_prompts_controller: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


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