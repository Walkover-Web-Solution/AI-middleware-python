from datetime import datetime, timezone
from typing import Optional, Dict, Any
from models.mongo_connection import db
from src.services.utils.logger import logger
import traceback

# Collections
embed_user_limits_collection = db["embed_user_limits"]
embed_user_usage_collection = db["embed_user_usage"]

# Default limits
DEFAULT_COST_LIMIT = 10.00  # $10 default limit

class EmbedUserLimitService:
    
    @staticmethod
    async def get_user_limits(org_id: str, user_id: str) -> Dict[str, Any]:
        """Get user's cost limits and current usage"""
        try:
            # Get user's limits
            limits_doc = await embed_user_limits_collection.find_one({
                "org_id": org_id,
                "user_id": user_id
            })
            
            if not limits_doc:
                # Create default limits for new user
                limits_doc = {
                    "org_id": org_id,
                    "user_id": user_id,
                    "cost_limit": DEFAULT_COST_LIMIT,
                    "cost_used": 0.0,
                    "remaining_cost": DEFAULT_COST_LIMIT,
                    "reset_frequency": "monthly",
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                }
                await embed_user_limits_collection.insert_one(limits_doc)
                logger.info(f"Created default limits for embed user {org_id}:{user_id}")
            
            return limits_doc
            
        except Exception as e:
            logger.error(f"Error getting user limits: {str(e)}")
            traceback.print_exc()
            return None
    
    @staticmethod
    async def check_cost_limit(org_id: str, user_id: str, estimated_cost: float = 0.0) -> Dict[str, Any]:
        """Check if user can make API call within cost limits"""
        try:
            limits_doc = await EmbedUserLimitService.get_user_limits(org_id, user_id)
            
            if not limits_doc:
                return {"allowed": False, "reason": "Unable to fetch user limits"}
            
            current_used = limits_doc.get("cost_used", 0.0)
            cost_limit = limits_doc.get("cost_limit", DEFAULT_COST_LIMIT)
            
            # Check if adding estimated cost would exceed limit
            projected_cost = current_used + estimated_cost
            
            if projected_cost > cost_limit:
                return {
                    "allowed": False,
                    "reason": f"Cost limit exceeded. Used: ${current_used:.4f}, Limit: ${cost_limit:.2f}, Estimated: ${estimated_cost:.4f}",
                    "current_used": current_used,
                    "limit": cost_limit,
                    "remaining": max(0, cost_limit - current_used)
                }
            
            return {
                "allowed": True,
                "current_used": current_used,
                "limit": cost_limit,
                "remaining": cost_limit - current_used
            }
            
        except Exception as e:
            logger.error(f"Error checking cost limit: {str(e)}")
            traceback.print_exc()
            return {"allowed": False, "reason": "Error checking limits"}
    
    @staticmethod
    async def record_api_usage(org_id: str, user_id: str, api_cost: float, 
                              api_endpoint: str, metadata: Dict[str, Any] = None) -> bool:
        """Record API usage and update cost totals"""
        try:
            current_period = datetime.now(timezone.utc).strftime("%Y-%m")
            
            # Record individual usage
            usage_doc = {
                "org_id": org_id,
                "user_id": user_id,
                "folder_id": metadata.get("folder_id") if metadata else None,
                "api_cost": api_cost,
                "api_endpoint": api_endpoint,
                "timestamp": datetime.now(timezone.utc),
                "period": current_period,
                "metadata": metadata or {}
            }
            
            await embed_user_usage_collection.insert_one(usage_doc)
            
            # Update user's total cost
            await embed_user_limits_collection.update_one(
                {"org_id": org_id, "user_id": user_id},
                {
                    "$inc": {"cost_used": api_cost},
                    "$set": {
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            # Recalculate remaining cost properly
            limits_doc = await embed_user_limits_collection.find_one({"org_id": org_id, "user_id": user_id})
            if limits_doc:
                new_remaining = max(0, limits_doc["cost_limit"] - limits_doc["cost_used"])
                await embed_user_limits_collection.update_one(
                    {"org_id": org_id, "user_id": user_id},
                    {"$set": {"remaining_cost": new_remaining}}
                )
            
            logger.info(f"Recorded API usage for {org_id}:{user_id} - Cost: ${api_cost:.4f}, Endpoint: {api_endpoint}")
            return True
            
        except Exception as e:
            logger.error(f"Error recording API usage: {str(e)}")
            traceback.print_exc()
            return False
    
    @staticmethod
    async def get_usage_history(org_id: str, user_id: str, limit: int = 50) -> list:
        """Get user's API usage history"""
        try:
            cursor = embed_user_usage_collection.find(
                {"org_id": org_id, "user_id": user_id}
            ).sort("timestamp", -1).limit(limit)
            
            usage_history = []
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])  # Convert ObjectId to string
                usage_history.append(doc)
            
            return usage_history
            
        except Exception as e:
            logger.error(f"Error getting usage history: {str(e)}")
            traceback.print_exc()
            return []
    
    @staticmethod
    async def update_user_limits(org_id: str, user_id: str, new_cost_limit: float) -> bool:
        """Update user's cost limits (admin function)"""
        try:
            result = await embed_user_limits_collection.update_one(
                {"org_id": org_id, "user_id": user_id},
                {
                    "$set": {
                        "cost_limit": new_cost_limit,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            # Recalculate remaining cost
            limits_doc = await embed_user_limits_collection.find_one({"org_id": org_id, "user_id": user_id})
            if limits_doc:
                new_remaining = max(0, new_cost_limit - limits_doc.get("cost_used", 0))
                await embed_user_limits_collection.update_one(
                    {"org_id": org_id, "user_id": user_id},
                    {"$set": {"remaining_cost": new_remaining}}
                )
            
            logger.info(f"Updated cost limit for {org_id}:{user_id} to ${new_cost_limit:.2f}")
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error updating user limits: {str(e)}")
            traceback.print_exc()
            return False

# Helper function to extract cost from API response
def extract_cost_from_response(response_data: Dict[str, Any], api_endpoint: str) -> float:
    """Extract cost from API response based on endpoint"""
    try:
        # Common cost extraction patterns
        if isinstance(response_data, dict):
            # Try common cost fields
            cost_fields = ["cost", "total_cost", "usage_cost", "price", "amount"]
            for field in cost_fields:
                if field in response_data:
                    return float(response_data[field])
            
            # Try nested usage object
            if "usage" in response_data and isinstance(response_data["usage"], dict):
                usage = response_data["usage"]
                for field in cost_fields:
                    if field in usage:
                        return float(usage[field])
        
        # Default cost if not found (you can customize per endpoint)
        logger.warning(f"Could not extract cost from response for {api_endpoint}, using default 0.01")
        return 0.01
        
    except Exception as e:
        logger.error(f"Error extracting cost from response: {str(e)}")
        return 0.01
