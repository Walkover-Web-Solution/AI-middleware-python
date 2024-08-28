from ...db_services.webhook_alert_Dbservice import get_webhook_data
from ..commonServices.baseService.baseService import sendResponse
import asyncio
async def send_error_to_webhook(bridge_id, org_id, error_details):
    try:
        result = await get_webhook_data(org_id)
        data = result.get('webhook_data', [])

        for entry in data:
            webhook_config = entry.get('webhookConfiguration')
            bridges = entry.get('bridges', [])
            
            if not webhook_config:
                continue
            if bridge_id in bridges or "all" in bridges:
                webhook_url = webhook_config.get('url')
                if webhook_url:
                    response_format = {
                        "type": "webhook",
                        "cred": {
                            "url": webhook_url,
                            "headers": webhook_config.get('headers', {})
                        }
                    }
                    asyncio.ensure_future(sendResponse(response_format, data=error_details))

    except Exception as error:
        print(f"send_error_to_webhook => {error}")
