from models.mongo_connection import db
from bson import ObjectId
from src.services.utils.logger import logger
from datetime import datetime
from typing import List, Dict, Optional

orchestrator_collection = db["orchestrator"]

async def create_orchestrator(data: Dict, org_id: str,folder_id: str, user_id:str   ) -> Optional[str]:
    """
    Create a new orchestrator in the database
    
    Args:
        data: Dictionary containing orchestrator data with agents, master_agent, status, and org_id
        
    Returns:
        String ID of created orchestrator or None if failed
    """
    try:
        # Insert the orchestrator, including org_id
        data["org_id"] = org_id
        if folder_id is not None: 
            data["folder_id"] = folder_id
        data['user_id'] = user_id
        result = await orchestrator_collection.insert_one(data)
        
        if result.inserted_id is not None:
            logger.info(f"Orchestrator created with ID: {result.inserted_id}")
            return str(result.inserted_id)
        else:
            logger.error("Failed to create orchestrator - no ID returned")
            return None
            
    except Exception as e:
        logger.error(f"Error creating orchestrator: {str(e)}")
        return None

async def get_all_orchestrators(query: Dict) -> List[Dict]:
    """
    Get all orchestrators for a specific organization
    
    Args:
        org_id: Organization ID to filter orchestrators
        
    Returns:
        List of orchestrator documents
    """
    try:
        # Find all orchestrators for the given org_id
        cursor = orchestrator_collection.find(query)
        orchestrators = []
        
        async for doc in cursor:
            # Convert ObjectId to string for JSON serialization
            doc['_id'] = str(doc['_id'])
            orchestrators.append(doc)
        
        logger.info(f"Retrieved {len(orchestrators)} orchestrators for org_id: {query['org_id']}")
        return orchestrators
        
    except Exception as e:
        logger.error(f"Error retrieving orchestrators for org_id {query['org_id']}: {str(e)}")
        return []

async def delete_orchestrator(orchestrator_id: str, org_id: str) -> bool:
    """
    Delete an orchestrator by ID and org_id
    
    Args:
        orchestrator_id: ID of the orchestrator to delete
        org_id: Organization ID for authorization check
        
    Returns:
        True if deleted successfully, False otherwise
    """
    try:
        # Validate ObjectId format
        if not ObjectId.is_valid(orchestrator_id):
            logger.error(f"Invalid orchestrator ID format: {orchestrator_id}")
            return False
        
        # Delete the orchestrator with both ID and org_id for security
        result = await orchestrator_collection.delete_one({
            "_id": ObjectId(orchestrator_id),
            "org_id": org_id
        })
        
        if result.deleted_count > 0:
            logger.info(f"Orchestrator {orchestrator_id} deleted successfully for org_id: {org_id}")
            return True
        else:
            logger.warning(f"Orchestrator {orchestrator_id} not found or not authorized for org_id: {org_id}")
            return False
            
    except Exception as e:
        logger.error(f"Error deleting orchestrator {orchestrator_id}: {str(e)}")
        return False

async def get_orchestrator_by_id(orchestrator_id: str, org_id: str) -> Optional[Dict]:
    """
    Get a specific orchestrator by ID and org_id
    
    Args:
        orchestrator_id: ID of the orchestrator to retrieve
        org_id: Organization ID for authorization check
        
    Returns:
        Orchestrator document or None if not found
    """
    try:
        # Validate ObjectId format
        if not ObjectId.is_valid(orchestrator_id):
            logger.error(f"Invalid orchestrator ID format: {orchestrator_id}")
            return None
        
        # Find the orchestrator with both ID and org_id for security
        doc = await orchestrator_collection.find_one({
            "_id": ObjectId(orchestrator_id),
            "org_id": org_id
        })
        
        if doc:
            # Convert ObjectId to string for JSON serialization
            doc['_id'] = str(doc['_id'])
            logger.info(f"Retrieved orchestrator {orchestrator_id} for org_id: {org_id}")
            return doc
        else:
            logger.warning(f"Orchestrator {orchestrator_id} not found for org_id: {org_id}")
            return None
            
    except Exception as e:
        logger.error(f"Error retrieving orchestrator {orchestrator_id}: {str(e)}")
        return None

async def update_orchestrator(orchestrator_id: str, org_id: str, new_data: Dict) -> bool:
    """
    Replace entire orchestrator data by ID and org_id (complete replacement)
    
    Args:
        orchestrator_id: ID of the orchestrator to replace
        org_id: Organization ID for authorization check
        new_data: Dictionary containing complete new data to replace with
        
    Returns:
        True if replaced successfully, False otherwise
    """
    try:
        # Validate ObjectId format
        if not ObjectId.is_valid(orchestrator_id):
            logger.error(f"Invalid orchestrator ID format: {orchestrator_id}")
            return False
        
        # Ensure org_id is preserved in the new data
        new_data['org_id'] = org_id
        
        # First check if the orchestrator exists and belongs to the org
        existing = await orchestrator_collection.find_one({
            "_id": ObjectId(orchestrator_id),
            "org_id": org_id
        })
        
        if not existing:
            logger.warning(f"Orchestrator {orchestrator_id} not found for org_id: {org_id}")
            return False
        
        # Replace the entire document while preserving _id
        result = await orchestrator_collection.replace_one(
            {"_id": ObjectId(orchestrator_id), "org_id": org_id},
            new_data
        )
        
        if result.modified_count > 0:
            logger.info(f"Orchestrator {orchestrator_id} replaced successfully for org_id: {org_id}")
            return True
        else:
            logger.warning(f"Orchestrator {orchestrator_id} replacement failed for org_id: {org_id}")
            return False
            
    except Exception as e:
        logger.error(f"Error replacing orchestrator {orchestrator_id}: {str(e)}")
        return False
