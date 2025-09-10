from fastapi import HTTPException
from fastapi.responses import JSONResponse
from src.db_services.OrchestratorServices import (
    create_orchestrator,
    get_all_orchestrators,
    delete_orchestrator,
    update_orchestrator
)
from src.services.utils.logger import logger
import json

async def create_orchestrator_controller(request):
    """
    Create a new orchestrator configuration.
    
    Request Body Structure:
    {
        "agents": {
            "agent_id_1": {
                "name": "Agent Name",
                "description": "Agent Description",
                "parentAgents": ["parent_agent_id"],
                "childAgents": ["child_agent_id"]
            },
            "agent_id_2": { ... }
        },
        "master_agent": "agent_id_1",
        "status": "publish" | "draft"
    }
    """
    try:
        data = await request.json()
        org_id = request.state.profile['org']['id']
        folder_id = request.state.folder_id if hasattr(request.state, 'folder_id') else None
        user_id = request.state.user_id
        
        # Validate required fields
        required_fields = ['status', 'bridge_type', 'flow_name','flow_description']
        for field in required_fields:
            if field not in data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Validate status
        if data['status'] not in ['publish', 'draft']:
            raise HTTPException(status_code=400, detail="Status must be 'publish' or 'draft'")  
        result = await create_orchestrator(data,org_id,folder_id,user_id)
        
        if result:
            logger.info(f"Orchestrator created successfully for org_id: {data['org_id']}")
            return JSONResponse(
                status_code=201,
                content={
                    "success": True,
                    "message": "Orchestrator created successfully",
                    "data": {"orchestrator_id": str(result)}
                }
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to create orchestrator")
            
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in create_orchestrator_controller: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

async def get_all_orchestrators_controller(request):
    """
    Retrieve all orchestrators for the organization.
    """
    try:
        # Extract org_id from query parameters
        org_id = request.state.profile['org']['id']
        folder_id = request.state.folder_id if hasattr(request.state, 'folder_id') else None
        user_id = request.state.user_id
        isEmbedUser = request.state.embed
        query = {"org_id": org_id}
        if folder_id:
            query["folder_id"] = folder_id
        if user_id and isEmbedUser:
            query["user_id"] = user_id
        orchestrators = await get_all_orchestrators(query)
        
        logger.info(f"Retrieved {len(orchestrators)} orchestrators for org_id: {org_id}")
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Orchestrators retrieved successfully",
                "data": orchestrators
            }
        ) 
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_all_orchestrators_controller: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

async def delete_orchestrator_controller(orchestrator_id: str, request):
    """
    Delete an orchestrator by ID.
    """
    try:
        # Extract org_id from query parameters for additional validation
        org_id = request.state.profile['org']['id']
        
        result = await delete_orchestrator(orchestrator_id, org_id)
        
        if result:
            logger.info(f"Orchestrator {orchestrator_id} deleted successfully for org_id: {org_id}")
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Orchestrator deleted successfully",
                    "data": {"orchestrator_id": orchestrator_id}
                }
            )
        else:
            raise HTTPException(status_code=404, detail="Orchestrator not found or not authorized to delete")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in delete_orchestrator_controller: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

async def update_orchestrator_controller(orchestrator_id: str, request):
    """    
    Path Parameters:
    - orchestrator_id: str - The ID of the orchestrator to update
    
    Request Body Structure:
    {
        "agents": {
            "agent_id_1": {
                "name": "Updated Agent Name",
                "description": "Updated Agent Description",
                "parentAgents": ["parent_agent_id"],
                "childAgents": ["child_agent_id"]
            },
            "agent_id_2": { ... }
        },
        "master_agent": "agent_id_1",
        "status": "publish" | "draft"
    }
    """
    try:
        data = await request.json()
        org_id = request.state.profile['org']['id']
        
        # Validate required fields
        required_fields = ['agents', 'master_agent', 'status']
        for field in required_fields:
            if field not in data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Validate status
        if data['status'] not in ['publish', 'draft']:
            raise HTTPException(status_code=400, detail="Status must be 'publish' or 'draft'")
        
        # Validate agents structure
        if not isinstance(data['agents'], dict):
            raise HTTPException(status_code=400, detail="Agents must be a dictionary")
        
        # Validate each agent
        for agent_id, agent_data in data['agents'].items():
            required_agent_fields = ['name', 'description', 'parentAgents', 'childAgents']
            for field in required_agent_fields:
                if field not in agent_data:
                    raise HTTPException(status_code=400, detail=f"Agent {agent_id} missing required field: {field}")
        
        # Validate master_agent exists in agents
        if data['master_agent'] not in data['agents']:
            raise HTTPException(status_code=400, detail="Master agent must exist in agents dictionary")
        
        result = await update_orchestrator(orchestrator_id, org_id, data)
        
        if result:
            logger.info(f"Orchestrator {orchestrator_id} updated successfully for org_id: {org_id}")
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Orchestrator updated successfully",
                    "data": {"orchestrator_id": orchestrator_id}
                }
            )
        else:
            raise HTTPException(status_code=404, detail="Orchestrator not found or not authorized to update")
            
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_orchestrator_controller: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
