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
