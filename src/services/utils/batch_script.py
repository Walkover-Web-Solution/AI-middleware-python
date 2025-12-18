from ..cache_service import find_in_cache_with_prefix, delete_in_cache
from openai import AsyncOpenAI
from ..utils.send_error_webhook import create_response_format
from ..commonServices.baseService.baseService import sendResponse
import asyncio
import json
import httpx
import certifi
from .ai_middleware_format import  Batch_Response_formatter
from src.configs.constant import redis_keys
from globals import *

async def repeat_function():
    while True:
        await check_batch_status()
        await asyncio.sleep(900)



async def check_batch_status():
    try:
        print("Batch Script running...")
        batch_ids = await find_in_cache_with_prefix('openai_batch_')
        if batch_ids is None:
            return
        for id in batch_ids:
            apikey = id.get('apikey')
            webhook = id.get('webhook')
            batch_id = id.get('id')
            batch_variables = id.get('batch_variables')  # Retrieve batch_variables from cache
            custom_id_mapping = id.get('custom_id_mapping', {})  # Get mapping of custom_id to index
            
            if webhook.get('url') is not None:
                response_format = create_response_format(webhook.get('url'), webhook.get('headers'))
            
            # Create httpx client with proper production configuration
            limits = httpx.Limits(
                max_keepalive_connections=5,
                max_connections=10,
                keepalive_expiry=30.0
            )
            
            http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(60.0, connect=10.0),
                transport=httpx.AsyncHTTPTransport(
                    retries=3,
                    verify=certifi.where()
                ),
                limits=limits,
                follow_redirects=True
            )
            
            try:
                openAI = AsyncOpenAI(api_key=apikey, http_client=http_client)
                batch = await openAI.batches.retrieve(batch_id)
                if batch.status == "completed":
                    file = batch.output_file_id or batch.error_file_id
                    file_response = None
                    if file is not None:
                        file_response = await openAI.files.content(file)
                        file_content = await asyncio.to_thread(file_response.read)
                        try:
                            # Split the data by newline and parse each JSON object separately
                            file_content = [json.loads(line) for line in file_content.decode('utf-8').splitlines() if line.strip()]
                        except json.JSONDecodeError as e:
                            print(f"JSON decoding error: {e}")
                            file_content = None
                        for index, content in enumerate(file_content):
                            response = content.get("response", {})
                            response_body = response.get("body", {})
                            status_code = response.get("status_code", 200)
                            custom_id = content.get("custom_id", None)
                            
                            # Check if response contains an error (status_code >= 400 or error in body)
                            if status_code >= 400 or "error" in response_body:
                                # Handle error response
                                formatted_content = {
                                    "custom_id": custom_id,
                                    "batch_id": batch_id,
                                    "error": response_body.get("error", response_body),
                                    "status_code": status_code
                                }
                            else:
                                # Handle successful response
                                formatted_content = await Batch_Response_formatter(response=response_body, service='openai_batch', tools={}, type='chat', images=None, batch_id=batch_id, custom_id=custom_id)
                            
                            # Add batch_variables to response if available
                            if batch_variables is not None and custom_id in custom_id_mapping:
                                variable_index = custom_id_mapping[custom_id]
                                if variable_index < len(batch_variables):
                                    formatted_content["variables"] = batch_variables[variable_index]
                            
                            file_content[index] = formatted_content
                        
                        # Check if all responses are errors
                        has_success = any(item.get("status_code") is None or item.get("status_code", 200) < 400 for item in file_content)
                        
                        await sendResponse(response_format, data=file_content, success=has_success)
                    cache_key = f"{redis_keys['openai_batch_']}{batch_id}"
                    await delete_in_cache(cache_key)
            finally:
                # Ensure http_client is properly closed
                await http_client.aclose()
    except Exception as error:
        logger.error(f"An error occurred while checking the batch status: {str(error)}")
        
    
    