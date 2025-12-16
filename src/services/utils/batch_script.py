from ..cache_service import find_in_cache_with_prefix, delete_in_cache
from openai import AsyncOpenAI
from ..utils.send_error_webhook import create_response_format
from ..commonServices.baseService.baseService import sendResponse
import asyncio
import json
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
        batch_ids = await find_in_cache_with_prefix('batch_')
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
            openAI = AsyncOpenAI(api_key=apikey)
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
                        response_body = content["response"]["body"]
                        custom_id = content.get("custom_id", None)
                        formatted_content = await Batch_Response_formatter(response=response_body, service='openai_batch', tools={}, type='chat', images=None, batch_id=batch_id, custom_id=custom_id) # changes
                        
                        # Add batch_variables to response if available
                        if batch_variables is not None and custom_id in custom_id_mapping:
                            variable_index = custom_id_mapping[custom_id]
                            if variable_index < len(batch_variables):
                                formatted_content["variables"] = batch_variables[variable_index]
                        
                        file_content[index] = formatted_content
                        
                    await sendResponse(response_format, data=file_content, success = True)
                cache_key = f"{redis_keys['batch_']}{batch_id}"
                await delete_in_cache(cache_key)
    except Exception as error:
        logger.error(f"An error occurred while checking the batch status: {str(error)}")
        
    
    