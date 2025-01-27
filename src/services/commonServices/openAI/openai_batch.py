import pydash as _
from ..baseService.baseService import BaseService
from ..createConversations import ConversationService
from src.configs.constant import service_name
import json

class OpenaiBatch(BaseService):
    async def batch_execute(self):
       

        system_prompt = self.configuration.get('prompt', '')
        results = []

        # Assume "self.batch" is the list of messages we want to process
        for idx, message in enumerate(self.batch, start=1):
            # Copy all keys from self.customConfig into the body
            body_data = dict(self.customConfig)

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

        # Make these JSON lines accessible via self.batches
        self.batches = results
