from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from src.services.utils.ai_call_util import get_ai_middleware_agent_data
from src.configs.constant import prebuilt_prompt_bridge_id
from src.services.prebuilt_prompt_service import get_prebuilt_prompts_service, update_prebuilt_prompt_service, get_specific_prebuilt_prompt_service
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
                    bridge_prompt = await get_ai_middleware_agent_data(prebuilt_prompt_bridge_id[prebuilt_prompt_id])
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

async def update_prebuilt_prompt_controller(request: Request):
    """Update prebuilt prompts for an organization"""
    try:
        org_id = request.state.profile['org']['id']
        body = await request.json()
        
        if not body:
            raise HTTPException(status_code=400, detail="Request body cannot be empty")

        prompt_id = list(body.keys())[0]
        prompt_text = body[prompt_id]
        
        if prompt_id not in prebuilt_prompt_bridge_id or not prompt_text:
            raise HTTPException(status_code=400, detail=f"Invalid prompt_id. Must be one of: {list(prebuilt_prompt_bridge_id.keys())}")
            
        try:
           # Update the prompt
            prompt_data = {"prompt": prompt_text}
            updated_prompt = await update_prebuilt_prompt_service(org_id, prompt_id, prompt_data)
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update prebuilt prompt: {str(e)}")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Prebuilt prompt updated successfully",
                "data": updated_prompt
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_prebuilt_prompt_controller: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

async def reset_prebuilt_prompts_controller(request: Request):
    """Reset a specific prebuilt prompt to its original AI middleware prompt"""
    try:
        org_id = request.state.profile['org']['id']
        body = await request.json()
        
        # Validate request body
        if not body or not body.get('prompt_id'):
            raise HTTPException(status_code=400, detail="prompt_id is required in request body")
        
        prompt_id = body.get('prompt_id')
        
        # Validate that prompt_id is one of the allowed prebuilt prompt IDs
        if prompt_id not in prebuilt_prompt_bridge_id:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid prompt_id. Must be one of: {list(prebuilt_prompt_bridge_id.keys())}"
            )
        
        try:
            # Get the bridge_id for this prompt
            bridge_id = prebuilt_prompt_bridge_id[prompt_id]
            
            # Fetch the original prompt from AI middleware
            bridge_prompt = await get_ai_middleware_agent_data(bridge_id)
            if bridge_prompt and bridge_prompt.get('bridge', {}).get('configuration', {}).get('prompt'):
                original_prompt = bridge_prompt['bridge']['configuration']['prompt']
                
                # Update the prompt with original value
                prompt_data = {"prompt": original_prompt}
                updated_prompt = await update_prebuilt_prompt_service(org_id, prompt_id, prompt_data)
                
                return JSONResponse(
                    status_code=200,
                    content={
                        "success": True,
                        "message": f"Successfully reset {prompt_id} to original value",
                        "data": updated_prompt
                    }
                )
            else:
                raise HTTPException(
                    status_code=404, 
                    detail="Failed to fetch original prompt from bridge configuration"
                )
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error resetting prompt {prompt_id}: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to reset prompt {prompt_id}: {str(e)}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in reset_prebuilt_prompts_controller: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

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
                detail=f"Invalid prompt_key. Must be one of: {list(prebuilt_prompt_bridge_id.keys())}"
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