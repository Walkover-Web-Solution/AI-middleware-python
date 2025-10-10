from models.mongo_connection import db
from src.services.utils.logger import logger
from fastapi import HTTPException


prebuilt_db  = db['preBuiltPrompts']
async def get_prebuilt_prompts_service(org_id: str):
    """
    Retrieve prebuilt prompts for an organization
    
    Args:
        org_id (str): Organization ID
        
    Returns:
        list: List of prebuilt prompts
    """
    try:        
        # Query prebuilt prompts for the organization
        query = {"org_id": org_id}
        document = await prebuilt_db.find_one(query, {"_id": 0})
        
        prompts = []
        if document and document.get("prebuilt_prompts"):
            # Convert the prebuilt_prompts object to a list format
            for prompt_id, prompt_text in document["prebuilt_prompts"].items():
                prompts.append({
                    prompt_id: prompt_text,
                })
        
        return prompts
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

async def update_prebuilt_prompt_service(org_id: str, prompt_id: str, prompt_data: dict):
    """
    Update a prebuilt prompt in the database
    
    Args:
        org_id (str): Organization ID
        prompt_id (str): Prompt ID to update
        prompt_data (dict): Updated prompt data
        
    Returns:
        dict: Updated prompt data
    """
    try:
        # Check if the document exists for this organization
        existing_document = await prebuilt_db.find_one({"org_id": org_id})
        
        if existing_document:
            # Update existing document - set the specific prompt_id within the prebuilt_prompts object
            update_data = {
                "$set": {
                    f"prebuilt_prompts.{prompt_id}": prompt_data.get("prompt")
                }
            }
            
            result = await prebuilt_db.update_one(
                {"org_id": org_id},
                update_data
            )
            
            if result.modified_count > 0 or result.matched_count > 0:
                return {
                    prompt_id: prompt_data.get("prompt"),
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to update prompt")
        else:
            # Create new document with the prompt
            new_prompt_data = {
                "org_id": org_id,
                "prebuilt_prompts": {
                    prompt_id: prompt_data.get("prompt")
                }
            }
            
            result = await prebuilt_db.insert_one(new_prompt_data)
            
            if result.inserted_id:
                return {
                    prompt_id: prompt_data.get("prompt"),
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to create prompt")
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

async def get_specific_prebuilt_prompt_service(org_id: str, prompt_key: str):
    """
    Retrieve a specific prebuilt prompt by prompt_key and org_id
    
    Args:
        org_id (str): Organization ID
        prompt_key (str): Prompt key to retrieve
        
    Returns:
        dict: Specific prompt data
    """
    try:
        # Query for the organization's document
        query = {"org_id": org_id}
        document = await prebuilt_db.find_one(query, {"_id": 0})
        
        if document and document.get("prebuilt_prompts") and prompt_key in document["prebuilt_prompts"]:
            prompt_text = document["prebuilt_prompts"][prompt_key]
            return {
                prompt_key: prompt_text
            }
        else:
            return None
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")