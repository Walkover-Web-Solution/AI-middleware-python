from ...db_services.webhook_alert_Dbservice import get_webhook_data
from ..commonServices.baseService.baseService import sendResponse

async def send_error_to_webhook(bridge_id, org_id, details, type):
    try:
        result = await get_webhook_data(org_id)
        data = result.get('webhook_data')
        data.append({
                    "org_id": org_id,
                    "name": "default alert",
                    "webhookConfiguration": {
                        "url": "https://flow.sokt.io/func/scriSmH2QaBH",
                        "headers": {}
                    },
                    "alertType": [
                        "Error",
                        "Variable"
                    ],
                    "bridges": [
                        "all"
                    ],
                })
        if type == 'Variable':
                details = create_missing_vars(details)
        for entry in data:
            webhook_config = entry.get('webhookConfiguration')
            bridges = entry.get('bridges', [])
            details = {
                 "details":details,
                 "bridge_id":bridge_id,
                 "org_id":org_id
            }
            if type in entry['alertType'] and (bridge_id in bridges or 'all' in bridges):
                    webhook_url = webhook_config.get('url')
                    if webhook_url:
                        response_format = create_response_format(webhook_url, webhook_config.get('headers', {}))
                        await sendResponse(response_format, data=details)

    except Exception as error:
        print(f"send_error_to_webhook => {error}")

def create_missing_vars(details):
    return {
        "alert" : "variables missing",
        "Variables" : details
    }

def create_response_format(url, headers):
    return {
        "type": "webhook",
        "cred": {
            "url": url,
            "headers": headers
        }
    }
