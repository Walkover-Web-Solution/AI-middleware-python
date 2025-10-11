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


def _check_limit(limit_type, bridges_data):
    """Check a specific limit type against the provided data."""
    limit_field = f"{limit_type}_limit"
    usage_field = f"{limit_type}_uses"

    # Safely convert string values to float, handle None and invalid values
    try:
        limit_value = float(bridges_data.get(limit_field, 0) or 0)
    except (ValueError, TypeError):
        limit_value = 0.0
    
    try:
        usage_value = float(bridges_data.get(usage_field, 0) or 0)
    except (ValueError, TypeError):
        usage_value = 0.0

    if limit_value > 0 and usage_value >= limit_value:
        return _build_limit_error(limit_type, usage_value, limit_value)

    return None

async def check_bridge_api_folder_limits(bridges_data):
    """Validate folder, bridge, and API usage against their limits."""
    if not isinstance(bridges_data, dict):
        return None

    folder_identifier = bridges_data.get('folder_id') or bridges_data.get('folder_limit')
    if folder_identifier:
        folder_error = _check_limit('folder', bridges_data)
        if folder_error:
            return folder_error

    bridge_error = _check_limit('bridge', bridges_data)
    if bridge_error:
        return bridge_error

    api_error = _check_limit('apikey', bridges_data)
    if api_error:
        return api_error

    return None
