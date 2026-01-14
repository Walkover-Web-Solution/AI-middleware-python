import pydash as _
from ..baseService.baseService import BaseService
from ..createConversations import ConversationService
from src.configs.constant import service_name
import json
import uuid
from ...cache_service import store_in_cache
from src.configs.constant import redis_keys
from src.services.commonServices.Mistral.mistral_run_batch import create_batch_file, process_batch_file


class MistralBatch(BaseService):
    async def batch_execute(self):
        batch_requests = []
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
        
        # Get processed prompts from params (processed in common.py)
        processed_prompts = self.processed_prompts if hasattr(self, 'processed_prompts') and self.processed_prompts else []

        # Construct batch requests in Mistral JSONL format
        for idx, message in enumerate(self.batch, start=1):
            # Generate a unique custom_id for each request
            custom_id = str(uuid.uuid4())

            # Get the processed prompt for this message (idx-1 because enumerate starts at 1)
            current_system_prompt = self.configuration.get('prompt', '')
            
            if processed_prompts and idx - 1 < len(processed_prompts):
                current_system_prompt = processed_prompts[idx - 1]

            # Construct Mistral batch request body
            request_body = {
                "messages": [],
                "max_tokens": self.customConfig.get("max_tokens", 1024)
            }
            
            # Add system message
            request_body["messages"].append({
                "role": "system",
                "content": current_system_prompt
            })
            
            # Add user message
            request_body["messages"].append({
                "role": "user",
                "content": message
            })
            
            # Add other config from customConfig
            if self.customConfig:
                for key in ['temperature', 'top_p', 'random_seed', 'safe_prompt']:
                    if key in self.customConfig:
                        request_body[key] = self.customConfig[key]

            # Create JSONL entry with custom_id and body
            batch_entry = {
                "custom_id": custom_id,
                "body": request_body
            }
            batch_requests.append(json.dumps(batch_entry))
            
            # Store message mapping for response
            mapping_item = {
                "message": message,
                "custom_id": custom_id
            }
            
            # Add batch_variables to mapping if provided
            if batch_variables is not None:
                mapping_item["variables"] = batch_variables[idx - 1]
            
            message_mappings.append(mapping_item)

        # Upload batch file and create batch job
        uploaded_file = await create_batch_file(batch_requests, self.apikey)
        batch_job = await process_batch_file(uploaded_file, self.apikey, self.model)
        
        batch_id = batch_job.id
        batch_json = {
            "id": batch_job.id,
            "status": batch_job.status,
            "created_at": batch_job.created_at,
            "model": self.model,
            "apikey": self.apikey,
            "webhook": self.webhook,
            "batch_variables": batch_variables,
            "custom_id_mapping": {item["custom_id"]: idx for idx, item in enumerate(message_mappings)},
            "service": self.service,
            "uploaded_file_id": uploaded_file.id
        }
        cache_key = f"{redis_keys['batch_']}{batch_job.id}"
        await store_in_cache(cache_key, batch_json, ttl = 86400)
        return {
            "success": True,
            "message": "Response will be successfully sent to the webhook within 24 hrs.",
            "batch_id": batch_id,
            "messages": message_mappings
        }
