import logging
import json
from ..cache_service import store_in_cache, find_in_cache
from src.configs.constant import redis_keys

logger = logging.getLogger(__name__)

def _build_limit_error(limit_type, current_usage, limit_value):
    """Helper to build a standard limit exceeded payload."""
    return {
        'success': False,
        'error': f"{limit_type.capitalize()} limit exceeded. Used: {current_usage}/{limit_value}",
        'error_code': f"{limit_type.upper()}_LIMIT_EXCEEDED",
        'limit_type': limit_type,
        'current_usage': current_usage,
        'limit_value': limit_value,
    }


async def _check_limit(limit_type, data):
    """Check a specific limit type against the provided data with Redis cache first."""
    limit_field = f"{limit_type}_limit"
    usage_field = f"{limit_type}_uses"
    
    # Get limit value from data
    try:
        limit_value = float(data.get(limit_field, 0) or 0)
    except (ValueError, TypeError):
        limit_value = 0.0
    
    # Skip if no limit is set
    if limit_value <= 0:
        return None
    
    # Create Redis key based on limit_type and identifier
    identifier = None
    if limit_type == 'bridge':
        identifier = data.get('parent_id') or data.get('bridge_id') or data.get('_id')
    elif limit_type == 'folder':
        identifier = data.get('folder_id')
    elif limit_type == 'apikey':
        identifier = data.get('apikey_id') or data.get('_id')
    
    usage_value = 0.0
    
    if identifier:
        # Try to get usage from Redis first bridgeusage_
        cache_key = f"{redis_keys[f'{limit_type}usedcost_']}{identifier}"
        try:
            cached_usage = await find_in_cache(cache_key)
            if cached_usage:
                usage_value = float(json.loads(cached_usage))
            else:
                # Fallback to data and update Redis
                try:
                    usage_value = float(data.get(usage_field, 0) or 0)
                except (ValueError, TypeError):
                    usage_value = 0.0
                
                # Store in Redis for future use
                await store_in_cache(cache_key, usage_value)
                logger.info(f"Updated Redis cache for {cache_key}: {usage_value}")
                
        except Exception as e:
            logger.error(f"Error accessing Redis for {cache_key}: {str(e)}")
            # Fallback to data
            try:
                usage_value = float(data.get(usage_field, 0) or 0)
            except (ValueError, TypeError):
                usage_value = 0.0
    else:
        # No identifier found, use data directly
        try:
            usage_value = float(data.get(usage_field, 0) or 0)
        except (ValueError, TypeError):
            usage_value = 0.0

    if usage_value >= limit_value:
        return _build_limit_error(limit_type, usage_value, limit_value)

    return None

async def check_bridge_api_folder_limits(result, bridge_data):
    """Validate folder, bridge, and API usage against their limits."""
    if not isinstance(bridge_data, dict):
        return None

    folder_identifier = result.get('folder_id')
    if folder_identifier:
        folder_error = await _check_limit('folder', data=result)
        if folder_error:
            return folder_error

    bridge_error = await _check_limit('bridge', data=bridge_data)
    if bridge_error:
        return bridge_error

    service_identifier = result.get('service')
    if service_identifier and result.get('apikeys') and service_identifier in result['apikeys']:
        api_error = await _check_limit('apikey', data=result['apikeys'][service_identifier])
        if api_error:
            return api_error

    return None
