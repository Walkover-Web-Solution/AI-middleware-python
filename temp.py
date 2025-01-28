import asyncio
# from ..cache_service import find_in_cache_for_batch, delete_in_cache_for_batch
from openai import AsyncOpenAI

async def check_batch_status():
    # batch_ids = find_in_cache_for_batch()
    # for id in batch_ids:
    #     apikey = id.get('apikey')
    batch_id = 'batch_67987810a2d48190bdca1fdfd46001d0'  # id.get('batch_id')
    openAI = AsyncOpenAI(api_key='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')
    batch = await openAI.batches.retrieve(batch_id)
    return batch

async def main():
    batch_status = await check_batch_status()
    print(batch_status)

asyncio.run(main())
