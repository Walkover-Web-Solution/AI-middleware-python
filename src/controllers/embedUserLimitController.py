from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import JSONResponse
from ..middlewares.middleware import jwt_middleware
from ..db_services.embedUserLimitService import EmbedUserLimitService
from typing import Optional
from datetime import datetime
import traceback

router = APIRouter()

@router.get('/limits', dependencies=[Depends(jwt_middleware)])
async def get_embed_user_limits(request: Request):
    """Get current limits and usage for embed user"""
    try:
        # Check if user is an embed user
        if not getattr(request.state, 'is_embed_user', False):
            raise HTTPException(status_code=403, detail="Access denied. Only embed users can view limits.")
        
        org_id = request.state.org_id
        user_id = str(request.state.user_id)
        
        # Get user limits and usage
        limits_data = await EmbedUserLimitService.get_user_limits(org_id, user_id)
        usage_history = await EmbedUserLimitService.get_usage_history(org_id, user_id, limit=10)
        
        if not limits_data:
            raise HTTPException(status_code=404, detail="User limits not found")
        
        # Convert datetime objects to strings for JSON serialization
        def serialize_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return obj
        
        # Clean limits data
        clean_limits = {
            "cost_limit": limits_data.get("cost_limit", 0),
            "cost_used": limits_data.get("cost_used", 0),
            "remaining_cost": limits_data.get("remaining_cost", 0),
            "reset_frequency": limits_data.get("reset_frequency", "monthly"),
            "created_at": serialize_datetime(limits_data.get("created_at")),
            "updated_at": serialize_datetime(limits_data.get("updated_at"))
        }
        
        # Clean usage history
        clean_usage = []
        for usage in usage_history[:5]:
            clean_usage.append({
                "api_endpoint": usage.get("api_endpoint"),
                "api_cost": usage.get("api_cost"),
                "timestamp": serialize_datetime(usage.get("timestamp")),
                "metadata": usage.get("metadata", {})
            })
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {
                    "limits": clean_limits,
                    "usage_summary": {
                        "total_api_calls": len(usage_history),
                        "recent_usage": clean_usage
                    },
                    "user_info": {
                        "org_id": org_id,
                        "user_id": user_id,
                        "folder_id": getattr(request.state, 'folder_id', None)
                    }
                }
            }
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get('/usage', dependencies=[Depends(jwt_middleware)])
async def get_embed_user_usage(request: Request, limit: Optional[int] = 50):
    """Get detailed usage history for embed user"""
    try:
        # Check if user is an embed user
        if not getattr(request.state, 'is_embed_user', False):
            raise HTTPException(status_code=403, detail="Access denied. Only embed users can view usage.")
        
        org_id = request.state.org_id
        user_id = str(request.state.user_id)
        
        # Get usage history
        usage_history = await EmbedUserLimitService.get_usage_history(org_id, user_id, limit=limit)
        
        # Convert datetime objects to strings for JSON serialization
        def serialize_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return obj
        
        # Clean usage history
        clean_usage_history = []
        for usage in usage_history:
            clean_usage = {
                "org_id": usage.get("org_id"),
                "user_id": usage.get("user_id"),
                "folder_id": usage.get("folder_id"),
                "api_cost": usage.get("api_cost"),
                "api_endpoint": usage.get("api_endpoint"),
                "timestamp": serialize_datetime(usage.get("timestamp")),
                "period": usage.get("period"),
                "metadata": usage.get("metadata", {})
            }
            clean_usage_history.append(clean_usage)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {
                    "usage_history": clean_usage_history,
                    "total_records": len(usage_history)
                }
            }
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.put('/limits', dependencies=[Depends(jwt_middleware)])
async def update_embed_user_limits(request: Request):
    """Update embed user limits (admin only)"""
    try:
        body = await request.json()
        
        # This should be restricted to admin users only
        # For now, we'll allow any authenticated user to update their own limits
        # You can add admin role checking here
        
        org_id = request.state.org_id
        user_id = str(request.state.user_id)
        new_cost_limit = body.get('cost_limit')
        
        if not new_cost_limit or new_cost_limit <= 0:
            raise HTTPException(status_code=400, detail="Invalid cost limit. Must be greater than 0.")
        
        # Update limits
        success = await EmbedUserLimitService.update_user_limits(org_id, user_id, float(new_cost_limit))
        
        if not success:
            raise HTTPException(status_code=404, detail="User not found or update failed")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Cost limit updated to ${new_cost_limit:.2f}",
                "data": {
                    "org_id": org_id,
                    "user_id": user_id,
                    "new_cost_limit": new_cost_limit
                }
            }
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get('/check', dependencies=[Depends(jwt_middleware)])
async def check_embed_user_limits(request: Request):
    """Check if embed user can make API calls within limits"""
    try:
        # Check if user is an embed user
        if not getattr(request.state, 'is_embed_user', False):
            raise HTTPException(status_code=403, detail="Access denied. Only embed users can check limits.")
        
        org_id = request.state.org_id
        user_id = str(request.state.user_id)
        
        # Check limits
        limit_check = await EmbedUserLimitService.check_cost_limit(org_id, user_id)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {
                    "can_make_api_calls": limit_check.get('allowed', False),
                    "current_used": limit_check.get('current_used', 0),
                    "limit": limit_check.get('limit', 0),
                    "remaining": limit_check.get('remaining', 0),
                    "reason": limit_check.get('reason', 'Within limits') if not limit_check.get('allowed', True) else None
                }
            }
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
