from config import Config
from src.services.utils.apiservice import fetch
from src.services.cache_service import find_in_cache, store_in_cache
from src.configs.constant import redis_keys
from typing import Optional, Any, Dict


async def get_timezone_and_org_name(org_id: str) -> Dict[str, Any]:
    """Fetch org timezone and name from MSG91 and cache the result.

    Cache key format: timezone_and_org_{org_id}
    """
    cache_key = f"{redis_keys['timezone_and_org_']}{org_id}"
    cached_data = await find_in_cache(cache_key)
    if cached_data:
        return __safe_json(cached_data)

    response, _ = await fetch(
        f"https://routes.msg91.com/api/{Config.PUBLIC_REFERENCEID}/getCompanies?id={org_id}",
        "GET",
        {"Authkey": Config.ADMIN_API_KEY},
        None,
        None,
    )
    data = (response or {}).get('data', {}).get('data', [{}])[0]
    await store_in_cache(cache_key, data)
    return data


async def validate_proxy_pauthkey(pauthkey: str) -> Dict[str, Any]:
    """Validate MSG91 pauthkey via proxy validation endpoint."""
    if not pauthkey:
        raise ValueError("pauthkey is required for validation")
    headers = {
        "authkey": Config.ADMIN_API_KEY
    }
    response, _ = await fetch(
        "https://routes.msg91.com/api/validateCauthKey",
        "POST",
        headers,
        None,
        {
            "cAuthKey": pauthkey
        },
    )
    return response


async def get_user_org_mapping(user_id: Optional[str], org_id: Optional[str]):
    """Get user details for embed alert enrichment using MSG91 admin token.

    Cached under key: userOrgMapping-{user_id}-{org_id}
    """
    if not user_id:
        return None

    cache_key = f"userOrgMapping-{user_id}-{org_id}"
    cached_data = await find_in_cache(cache_key)
    if cached_data:
        return __safe_json(cached_data)

    url = f"https://routes.msg91.com/api/{Config.PUBLIC_REFERENCEID}/getDetails"
    params = {"user_id": user_id}
    headers = {"Authkey": Config.ADMIN_API_KEY}
    response, _ = await fetch(url, "GET", headers, None, params)

    if response and response.get('status') == 'success':
        user_data = response.get('data', {})
        await store_in_cache(cache_key, user_data, ttl=3600)
        return user_data
    return None


def __safe_json(data):
    """Parse cached JSON string to object if needed."""
    if isinstance(data, (dict, list)):
        return data
    try:
        import json
        return json.loads(data)
    except Exception:
        return data


async def get_proxy_details_by_token(proxy_auth_token: str) -> Dict[str, Any]:
    """Validate proxy_auth_token and fetch user/org details from MSG91.

    Endpoint: GET https://routes.msg91.com/api/c/getDetails
    Header: { 'proxy_auth_token': <token> }
    """
    if not proxy_auth_token:
        raise ValueError("proxy_auth_token is required")

    headers = { 'proxy_auth_token': proxy_auth_token }
    response_data, rs_header = await fetch(
        "https://routes.msg91.com/api/c/getDetails", "GET", headers
    )
    return response_data


async def update_user_role(proxy_auth_token: str, user_id: str, role_id: int) -> Dict[str, Any]:
    """Update user role via MSG91 API.

    Endpoint: POST https://routes.msg91.com/api/c/updateCuserRole
    Header: { 'proxy_auth_token': <token> }
    Body: { 'user_id': <user_id>, 'role_id': <role_id> }
    """
    if not proxy_auth_token:
        raise ValueError("proxy_auth_token is required")
    if not user_id:
        raise ValueError("user_id is required")
    if role_id is None:
        raise ValueError("role_id is required")

    headers = {
        'proxy_auth_token': proxy_auth_token,
        'Content-Type': 'application/json'
    }
    json_body = {
        'user_id': user_id,
        'role_id': role_id
    }
    response_data, rs_header = await fetch(
        "https://routes.msg91.com/api/c/updateCuserRole", "POST", headers, None, json_body
    )
    return response_data

