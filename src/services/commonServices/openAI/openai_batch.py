import pydash as _
from ..baseService.baseService import BaseService
from ..createConversations import ConversationService
from src.configs.constant import service_name
import json
from ...cache_service import store_in_cache
from src.services.commonServices.openAI.openai_run_batch import create_batch_file, process_batch_file

class OpenaiBatch(BaseService):
    async def batch_execute(self):
        """Create a batch job for chat completions and cache its metadata."""
        system_prompt = self.configuration.get('prompt', '')
        results = []

        # Assume "self.batch" is the list of messages we want to process
        for idx, message in enumerate(self.batch, start=1):
            # Copy all keys from self.customConfig into the body
            body_data = self.customConfig

            # Add messages array with system prompt and user message
            body_data["messages"] = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]

            # Construct one JSONL line for each message
            request_obj = {
                "custom_id": f"request-{idx}",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": body_data
            }

            # Serialize to JSON string
            results.append(json.dumps(request_obj))

        batch_input_file = await create_batch_file(results, self.apikey)
        batch_file = await process_batch_file(batch_input_file, self.apikey)
        batch_id = batch_file.id
        batch_json = {
            "id": batch_file.id,
            "completion_window": batch_file.completion_window,
            "created_at": batch_file.created_at,
            "endpoint": batch_file.endpoint,
            "input_file_id": batch_file.input_file_id,
            "object": batch_file.object,
            "status": batch_file.status,
            "cancelled_at": batch_file.cancelled_at,
            "cancelling_at": batch_file.cancelling_at,
            "completed_at": batch_file.completed_at,
            "error_file_id": batch_file.error_file_id,
            "errors": batch_file.errors,
            "expires_at": batch_file.expires_at,
            "metadata": batch_file.metadata,
            "request_counts": {
                "completed": batch_file.request_counts.completed,
                "failed": batch_file.request_counts.failed,
                "total": batch_file.request_counts.total
            },
            "apikey": self.apikey,
            "webhook" : self.webhook
        }
        await store_in_cache(batch_id, batch_json)
        return {
            "success": True,
            "message": "Response will be successfully sent to the webhook wihtin 24 hrs."
        }
