import logging
import asyncio
import json
from ..cache_service import store_in_cache, find_in_cache

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


def _check_limit(limit_type, data):
    """Check a specific limit type against the provided data."""
    limit_field = f"{limit_type}_limit"
    usage_field = f"{limit_type}_uses"
    
    # Safely convert string values to float, handle None and invalid values
    try:
        limit_value = float(data.get(limit_field, 0) or 0)
    except (ValueError, TypeError):
        limit_value = 0.0
    
    try:
        usage_value = float(data.get(usage_field, 0) or 0)
    except (ValueError, TypeError):
        usage_value = 0.0

    if limit_value > 0 and usage_value >= limit_value:
        return _build_limit_error(limit_type, usage_value, limit_value)

    return None

def _check_limit_from_cache_data(limit_type, cache_data):
    """Check limit using cache data structure {limit: x, uses: y}"""
    if not cache_data:
        return None
        
    try:
        limit_value = float(cache_data.get('limit', 0) or 0)
        usage_value = float(cache_data.get('uses', 0) or 0)
        
        if limit_value > 0 and usage_value >= limit_value:
            return _build_limit_error(limit_type, usage_value, limit_value)
            
    except (ValueError, TypeError) as e:
        logger.error(f"Error checking limit from cache data: {str(e)}")
        
    return None

async def check_bridge_api_folder_limits(result, bridge_data):
    """Validate folder, bridge, and API usage against their limits."""
    if not isinstance(bridge_data, dict):
        return None

    folder_identifier = bridge_data.get('folder_id') or bridge_data.get('folder_limit')
    if folder_identifier:
        folder_error = _check_limit('folder', data=bridge_data)
        if folder_error:
            return folder_error

    bridge_error = _check_limit('bridge', data=bridge_data)
    if bridge_error:
        return bridge_error

    service_identifier = bridge_data.get('service')
    if service_identifier and result.get('apikeys') and service_identifier in result['apikeys']:
        api_error = _check_limit('apikey', data=result['apikeys'][service_identifier])
        if api_error:
            return api_error

    return None

async def check_bridge_api_folder_limits_with_cache(result, bridge_data):
    """Validate folder, bridge, and API usage against their limits using Redis cache first."""
    if not isinstance(bridge_data, dict):
        return None

    try:
        # Extract identifiers
        folder_id = bridge_data.get('folder_id')
        bridge_id = bridge_data.get('parent_id')
        service = bridge_data.get('service')
        apikey_object_id = result.get('apikey_object_id', {}).get(service)

        # Check folder limits
        if folder_id:
            folder_key = f"folderlimit_{folder_id}"
            folder_cache = await find_in_cache(folder_key)
            if folder_cache:
                folder_data = json.loads(folder_cache)
                folder_error = _check_limit_from_cache_data('folder', folder_data)
                if folder_error:
                    return folder_error
            else:
                # Cache miss - check from data and store in cache
                folder_error = _check_limit('folder', data=bridge_data)
                if folder_error:
                    return folder_error
                # Store in cache
                cache_data = {"limit": bridge_data.get('folder_limit', 0), "uses": bridge_data.get('folder_uses', 0)}
                await store_in_cache(folder_key, cache_data, 172800)  # 2 days TTL

        # Check bridge limits
        if bridge_id:
            bridge_key = f"bridgelimit_{bridge_id}"
            bridge_cache = await find_in_cache(bridge_key)
            if bridge_cache:
                bridge_data_cache = json.loads(bridge_cache)
                bridge_error = _check_limit_from_cache_data('bridge', bridge_data_cache)
                if bridge_error:
                    return bridge_error
            else:
                # Cache miss - check from data and store in cache
                bridge_error = _check_limit('bridge', data=bridge_data)
                if bridge_error:
                    return bridge_error
                # Store in cache
                cache_data = {"limit": bridge_data.get('bridge_limit', 0), "uses": bridge_data.get('bridge_uses', 0)}
                await store_in_cache(bridge_key, cache_data, 172800)  # 2 days TTL

        # Check API limits
        if service and apikey_object_id and result.get('apikeys', {}).get(service):
            api_key = f"apilimit_{apikey_object_id}"
            api_cache = await find_in_cache(api_key)
            if api_cache:
                api_data_cache = json.loads(api_cache)
                api_error = _check_limit_from_cache_data('apikey', api_data_cache)
                if api_error:
                    return api_error
            else:
                # Cache miss - check from data and store in cache
                api_error = _check_limit('apikey', data=result['apikeys'][service])
                if api_error:
                    return api_error
                # Store in cache
                api_data = result['apikeys'][service]
                cache_data = {"limit": api_data.get('apikey_limit', 0), "uses": api_data.get('apikey_uses', 0)}
                await store_in_cache(api_key, cache_data, 172800)  # 2 days TTL
        
        return None
        
    except Exception as e:
        logger.error(f"Error in cached limit check: {str(e)}")
        # Fallback to original method on error
        return await check_bridge_api_folder_limits(result, bridge_data)

async def update_limit_cache_usage(bridge_id, folder_id, service, apikey_object_id, usage_delta):
    """Update usage in Redis limit cache"""
    try:
        tasks = []
        
        # Update bridge cache
        if bridge_id:
            bridge_key = f"bridgelimit_{bridge_id}"
            bridge_cache = await find_in_cache(bridge_key)
            if bridge_cache:
                data = json.loads(bridge_cache)
                data["uses"] = float(data.get("uses", 0)) + float(usage_delta)
                tasks.append(store_in_cache(bridge_key, data, 172800))
        
        # Update folder cache
        if folder_id:
            folder_key = f"folderlimit_{folder_id}"
            folder_cache = await find_in_cache(folder_key)
            if folder_cache:
                data = json.loads(folder_cache)
                data["uses"] = float(data.get("uses", 0)) + float(usage_delta)
                tasks.append(store_in_cache(folder_key, data, 172800))
        
        # Update API cache
        if service and apikey_object_id:
            api_key = f"apilimit_{apikey_object_id}"
            api_cache = await find_in_cache(api_key)
            if api_cache:
                data = json.loads(api_cache)
                data["uses"] = float(data.get("uses", 0)) + float(usage_delta)
                tasks.append(store_in_cache(api_key, data, 172800))
        
        # Execute all updates
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info(f"Limit cache usage updated by {usage_delta}")
            
    except Exception as e:
        logger.error(f"Error updating limit cache usage: {str(e)}")
