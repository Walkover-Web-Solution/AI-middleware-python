from src.db_services.api_key_status_service import update_apikey_status

STATUS_BY_CODE = {
    "401": "invalid",
    "429": "exhuasted",
}

def classify_status_from_error(code) -> str:
    if code in STATUS_BY_CODE:
        return STATUS_BY_CODE[code]

    return code

async def mark_apikey_status_from_response(parsed_data, code=None):
    apikey_map = parsed_data.get("apikey_object_id") or {}
    status_map = parsed_data.get("apikey_status") or {}
    service = parsed_data.get("service")
    apikey_id = apikey_map.get(service)
    if not apikey_id:
        return

    new_status = "working" if not code else classify_status_from_error(
        code
    )
    if status_map.get(service) == new_status:
        return  # already up to date; skip DB write

    await update_apikey_status(apikey_id, new_status)