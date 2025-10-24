from ...db_services.webhook_alert_Dbservice import get_webhook_data
from ..commonServices.baseService.baseService import sendResponse
from .helper import Helper
from globals import *

async def send_error_to_webhook(bridge_id, org_id, error_log, error_type, bridge_name=None, is_embed=None, user_id=None):
    """
    Sends error logs to a webhook if the specified conditions are met.

    Args:
        bridge_id (str): Identifier for the bridge.
        org_id (str): Identifier for the organization.
        error_log (dict): Error log details.
        error_type (str): Type of the error (e.g., 'Variable', 'Error', 'metrix_limit_reached').
        bridge_name (str): Name of the bridge.
        is_embed (bool): Whether the bridge is embedded.
        user_id (str): User ID from bridge data for alert management.

    Returns:
        None
    """
    try:
        # Fetch webhook data for the organization
        result = await get_webhook_data(org_id)
        if not result or 'webhook_data' not in result:
            raise BadRequestException("Webhook data is missing in the response.")

        webhook_data = result['webhook_data']

        # Add default alert configuration if necessary
        webhook_data.append({
            "org_id": org_id,
            "name": "default alert",
            "webhookConfiguration": {
                "url": "https://flow.sokt.io/func/scriSmH2QaBH",
                "headers": {}
            },
            "alertType": ["Error", "Variable", "retry_mechanism"],
            "bridges": ["all"]
        })

        # Generate the appropriate payload based on the error type
        
        if error_type == 'Variable': 
            details_payload = create_missing_vars(error_log)
        elif error_type == 'metrix_limit_reached':
            details_payload = metrix_limit_reached(error_log)
        elif error_type == 'retry_mechanism':
            details_payload = create_retry_mechanism_payload(error_log, bridge_name, is_embed)
        else:
            details_payload = create_error_payload(error_log)
        

        # Iterate through webhook configurations and send responses
        for entry in webhook_data:
            webhook_config = entry.get('webhookConfiguration')
            bridges = entry.get('bridges', [])

            if error_type in entry.get('alertType', []) and (bridge_id in bridges or 'all' in bridges):
                if(error_type == 'metrix_limit_reached' and entry.get('limit', 500) == error_log): 
                    continue
                webhook_url = webhook_config['url']
                headers = webhook_config.get('headers', {})

                # Prepare details for the webhook
                payload = {
                    "details": details_payload,  # Use details_payload directly to avoid nesting
                    "bridge_id": bridge_id,
                    "org_id": org_id,
                    "user_id": user_id,
                }
                
                # Add bridge_name and is_embed to payload if available
                if bridge_name is not None:
                    payload["bridge_name"] = bridge_name
                if is_embed is not None:
                    payload["is_embed"] = is_embed

                # Fetch user org mapping only if user_id is available
                if user_id:
                    user_org_mapping = await Helper.get_user_org_mapping(user_id, org_id)
                    if user_org_mapping:
                        payload["user_org_mapping"] = user_org_mapping
                # Send the response
                response_format = create_response_format(webhook_url, headers)
                await sendResponse(response_format, data=payload)

    except Exception as error:
        logger.error(f'Error in send_error_to_webhook: %s, {str(error)}')

def create_missing_vars(details):
    return {
        "alert" : "variables missing",
        "Variables" : details
    }

def metrix_limit_reached(details):
    return {
        "alert" : "limit_reached",
        "Limit Size" : details
    }

def create_error_payload(details):
    return {
        "alert" : "Unexpected Error",
        "error_message" : details['error_message']
    }

def create_retry_mechanism_payload(details, bridge_name=None, is_embed=None):
    payload = {
        "alert" : "Retry Mechanism Started due to error.",
        "error_message" : details
    }
    
    # Add bridge_name and is_embed to the details if available
    if bridge_name is not None:
        payload["bridge_name"] = bridge_name
    if is_embed is not None:
        payload["is_embed"] = is_embed
        
    return payload

def create_response_format(url, headers):
    return {
        "type": "webhook",
        "cred": {
            "url": url,
            "headers": headers
        }
    }
