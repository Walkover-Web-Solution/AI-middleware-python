from ..cache_service import find_in_cache_for_batch, delete_in_cache_for_batch
from openai import AsyncOpenAI
from ..utils.send_error_webhook import create_response_format
from ..commonServices.baseService.baseService import sendResponse
import asyncio

async def repeat_function():
    while True:
        await check_batch_status()
        await asyncio.sleep(900)

asyncio.ensure_future(repeat_function())


async def check_batch_status():
    batch_ids = await find_in_cache_for_batch()
    for id in batch_ids:
        apikey = id.get('apikey')
        webhook = id.get('webhook')
        response_format = create_response_format(webhook.get('url'), webhook.get('headers'))
        batch_id = id.get('batch_id')
        openAI = AsyncOpenAI(api_key= apikey)
        batch = openAI.batches.retrieve(batch_id)
        if batch.status=="completed":
            file = batch.output_file_id or batch.error_file_id
            file_response = None
            if file is not None:
                file_response = openAI.files.content(file)
                await sendResponse(response_format, data=file_response)
            await delete_in_cache_for_batch(batch_id)
        
        


    
    