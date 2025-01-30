import json
import os
from openai import AsyncOpenAI
import io

async def create_batch_file(data, apiKey):
    try:
        file_content = "\n".join(data)
        filelike_obj = io.BytesIO(file_content.encode("utf-8"))
        openAI = AsyncOpenAI(api_key=apiKey)
        batch_input_file = await openAI.files.create(
            file=filelike_obj,
            purpose="batch"
        )
        return batch_input_file
    except Exception as e:
        print(f"Error in create_batch_file: {e}")
        raise

async def process_batch_file(batch_input_file, apiKey):
    try:
        openAI = AsyncOpenAI(api_key=apiKey)
        batch_input_file_id = batch_input_file.id

        result = await openAI.batches.create(
            input_file_id=batch_input_file_id,
            endpoint="/v1/chat/completions",
            completion_window="24h"
        )
        print(result)
        return result
    except Exception as e:
        print(f"Error in process_batch_file: {e}")
        raise


async def retrieve_batch_status(batch_id, apiKey):
    try:
        openAI = AsyncOpenAI(api_key=apiKey)
        batch = await openAI.batches.retrieve(batch_id)
        print(batch)
        return batch
    except Exception as e:
        print(f"Error in retrieve_batch_status: {e}")
        raise