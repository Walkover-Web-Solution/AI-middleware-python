from src.db_services.conversationDbService import calculate_average_response_time
from src.services.utils.logger import logger
from src.services.cache_service import store_in_cache, find_in_cache


async def get_bridge_avg_response_time(org_id, bridge_id):
    """Compute and cache the bridge's average response time."""
    try:
        cache_key = f"AVG_{org_id}_{bridge_id}"
        cached_avg_response_time = await find_in_cache(cache_key)
        
        if cached_avg_response_time is not None:
            return float(cached_avg_response_time)
        
        avg_response_time = await calculate_average_response_time(org_id, bridge_id)
        await store_in_cache(cache_key, avg_response_time, 86400)  # 1 day TTL (24 hours * 60 minutes * 60 seconds)
        return avg_response_time

    except Exception as e:
        logger.error(f"Error in getting bridge average response time: {str(e)}")
        return 0
