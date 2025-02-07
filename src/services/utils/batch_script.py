from ..cache_service import find_in_cache_with_prefix, delete_in_cache_for_batch
from openai import AsyncOpenAI
from ..utils.send_error_webhook import create_response_format
from ..commonServices.baseService.baseService import sendResponse
import asyncio
import json

async def repeat_function():
    while True:
        await check_batch_status()
        await asyncio.sleep(900)

asyncio.ensure_future(repeat_function())


async def check_batch_status():
    try:

        batch_ids = await find_in_cache_with_prefix('batch_')
        for id in batch_ids:
            apikey = id.get('apikey')
            webhook = id.get('webhook')
            batch_id = id.get('id')
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
                    await sendResponse(response_format, data=file_content, success = True)
                await delete_in_cache_for_batch(f'AIMIDDLEWARE_{batch_id}')
    except Exception as error:
        print(f"An error occurred while checking the batch status: {error}")
        
    
    