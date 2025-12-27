import pydash as _
from ..baseService.baseService import BaseService
from ..createConversations import ConversationService
from src.configs.constant import service_name
import json
import uuid
from ...cache_service import store_in_cache
from src.configs.constant import redis_keys
from src.services.commonServices.AiMl.aiml_run_batch import create_batch


class AiMlBatch(BaseService):
    async def batch_execute(self):
        system_prompt = self.configuration.get('prompt', '')
        results = []
        message_mappings = []
        
        # Validate batch_variables if provided
        batch_variables = self.batch_variables if hasattr(self, 'batch_variables') and self.batch_variables else None
        if batch_variables is not None:
            if not isinstance(batch_variables, list):
                return {
                    "success": False,
                    "message": "batch_variables must be an array"
                }
            if len(batch_variables) != len(self.batch):
                return {
                    "success": False,
                    "message": f"batch_variables array length ({len(batch_variables)}) must match batch array length ({len(self.batch)})"
                }

        # Construct batch requests in AIML native format
        for idx, message in enumerate(self.batch, start=1):
            # Generate a unique ID for each request
            custom_id = str(uuid.uuid4())

            # Construct AIML-native request (uses 'params' instead of 'body')
            request_obj = {
                "custom_id": custom_id,
                "params": {
                    "model": self.model,
                    "messages": []
                }
            }
            
            # Add system prompt to 'system' field (AIML-specific format)
            if system_prompt:
                request_obj["params"]["system"] = system_prompt
            
            # Add user message (only user messages go in the messages array for AIML)
            request_obj["params"]["messages"].append({
                "role": "user",
                "content": message
            })
            
            # Add other config from customConfig (like temperature, max_tokens, etc.)
            if self.customConfig:
                for key, value in self.customConfig.items():
                    if key not in ['messages', 'prompt', 'model']:
                        request_obj["params"][key] = value

            # Add request object to results (no JSON serialization needed)
            results.append(request_obj)
            
            # Store message mapping for response
            mapping_item = {
                "message": message,
                "custom_id": custom_id
            }
            
            # Add batch_variables to mapping if provided (idx-1 because enumerate starts at 1)
            if batch_variables is not None:
                mapping_item["variables"] = batch_variables[idx - 1]
            
            message_mappings.append(mapping_item)

        # Create batch job using AIML native batch API (no file upload needed)
        batch_response = await create_batch(results, self.apikey)
        
        batch_id = batch_response.get("id")
        batch_json = {
            "id": batch_response.get("id"),
            "status": batch_response.get("status"),
            "created_at": batch_response.get("created_at"),
            "model": self.model,
            "apikey": self.apikey,
            "webhook": self.webhook,
            "batch_variables": batch_variables,
            "custom_id_mapping": {item["custom_id"]: idx for idx, item in enumerate(message_mappings)},
            "service": self.service
        }
        cache_key = f"{redis_keys['batch_']}{batch_file.id}"
        await store_in_cache(cache_key, batch_json, ttl = 86400)
        return {
            "success": True,
            "message": "Response will be successfully sent to the webhook within 24 hrs.",
            "batch_id": batch_id,
            "messages": message_mappings
        }
