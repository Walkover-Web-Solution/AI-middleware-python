import traceback
import httpx
from ..api_executor import execute_api_call
from globals import *

XAI_CHAT_COMPLETIONS_URL = "https://api.x.ai/v1/chat/completions"

async def grok_runmodel(configuration, api_key, execution_time_logs, bridge_id, timer, message_id, org_id, name="", org_name="", service="", count=0, token_calculator=None):
    """Execute a chat completion call against the xAI Grok API."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    timeout = httpx.Timeout(3600.0, connect=30.0)

    async def api_call(config):
        try:
            print(config)
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(XAI_CHAT_COMPLETIONS_URL, json=config, headers=headers)
            response.raise_for_status()
            return {
                "success": True,
                "response": response.json()
            }
        except httpx.HTTPStatusError as error:
            return {
                "success": False,
                "error": error.response.text,
                "status_code": error.response.status_code
            }
        except Exception as error:
            return {
                "success": False,
                "error": str(error),
                "status_code": None
            }

    try:
        return await execute_api_call(
            configuration=configuration,
            api_call=api_call,
            execution_time_logs=execution_time_logs,
            timer=timer,
            bridge_id=bridge_id,
            message_id=message_id,
            org_id=org_id,
            alert_on_retry=False,
            name=name,
            org_name=org_name,
            service=service,
            count=count,
            token_calculator=token_calculator
        )
    except Exception as error:
        execution_time_logs.append({"step": f"{service} Processing time for call :- {count + 1}", "time_taken": timer.stop("API chat completion")})
        logger.error("Grok runmodel error=>", error)
        traceback.print_exc()
        return {
            "success": False,
            "error": str(error)
        }


async def grok_test_model(configuration, api_key):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    timeout = httpx.Timeout(3600.0, connect=30.0)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(XAI_CHAT_COMPLETIONS_URL, json=configuration, headers=headers)
        response.raise_for_status()
        return {
            "success": True,
            "response": response.json()
        }
    except httpx.HTTPStatusError as error:
        return {
            "success": False,
            "error": error.response.text,
            "status_code": error.response.status_code
        }
    except Exception as error:
        return {
            "success": False,
            "error": str(error),
            "status_code": None
        }
