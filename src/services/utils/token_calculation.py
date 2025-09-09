import pydash as _
from src.configs.model_configuration import model_config_document

class TokenCalculator:
    def __init__(self, service, model_output_config):
        self.service = service
        self.model_output_config = model_output_config
        self.total_usage = {
            "total_tokens": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "cached_tokens":0,
            "cache_read_input_tokens":0,
            "cache_creation_input_tokens":0,
            "reasoning_tokens": 0
        }

    def calculate_usage(self, model_response):
        usage = {}
        match self.service:
            case 'open_router' | 'mistral' | 'ai_ml':
                usage["inputTokens"] = model_response['usage']['prompt_tokens']
                usage["outputTokens"] = model_response['usage']['completion_tokens']
                usage["totalTokens"] = model_response['usage']['total_tokens']
                # Handle optional token details with safe access
                usage["cachedTokens"] = model_response['usage'].get('prompt_tokens_details', {}).get('cached_tokens', 0)
                usage["reasoningTokens"] = model_response['usage'].get('completion_tokens_details', {}).get('reasoning_tokens', 0)
            
            case 'groq':
                usage["inputTokens"] = model_response['usage']['prompt_tokens']
                usage["outputTokens"] = model_response['usage']['completion_tokens']
                usage["totalTokens"] = model_response['usage']['total_tokens']
                # Groq doesn't have token details, set to 0
                usage["cachedTokens"] = 0
                usage["reasoningTokens"] = 0
            
            case 'gemini':
                usage["inputTokens"] = model_response['usage']['prompt_tokens']
                usage["outputTokens"] = model_response['usage']['completion_tokens']
                usage["totalTokens"] = model_response['usage']['total_tokens']
                # Gemini doesn't have cached/reasoning tokens
                usage["cachedTokens"] = 0
                usage["reasoningTokens"] = 0
            
            case 'openai':
                usage["inputTokens"] = model_response['usage']['input_tokens']
                usage["outputTokens"] = model_response['usage']['output_tokens']
                usage["totalTokens"] = model_response['usage']['total_tokens']
                usage["cachedTokens"] = model_response['usage'].get('input_tokens_details', {}).get('cached_tokens', 0)
                usage["reasoningTokens"] = model_response['usage'].get('output_tokens_details', {}).get('reasoning_tokens', 0)
            
            case 'anthropic':
                usage["inputTokens"] = model_response['usage']['input_tokens']
                usage["outputTokens"] = model_response['usage'].get('output_tokens', 0)
                usage["totalTokens"] = usage["inputTokens"] + usage["outputTokens"]
                usage['cachingReadTokens'] = model_response['usage'].get('cache_read_input_tokens', 0)
                usage['cachingCreationInputTokens'] = model_response['usage'].get('cache_creation_input_tokens', 0)
            
            case _:
                pass

        self._update_total_usage(usage)
        return usage

    def _update_total_usage(self, usage):
        self.total_usage["total_tokens"] += usage.get("totalTokens") or 0
        self.total_usage["input_tokens"] += usage.get("inputTokens") or  0
        self.total_usage["output_tokens"] += usage.get("outputTokens") or 0
        self.total_usage["cached_tokens"] += usage.get("cachedTokens") or  0
        self.total_usage["cache_read_input_tokens"] += usage.get("cachingReadTokens") or 0
        self.total_usage["cache_creation_input_tokens"] += usage.get("cachingCreationInputTokens") or 0
        self.total_usage["reasoning_tokens"] += usage.get("reasoningTokens") or 0


    def calculate_total_cost(self, model, service):
        """
        Calculate total cost in dollars using accumulated total_usage
        
        Args:
            model: model name
            service: service name
        
        Returns:
            Dictionary with cost breakdown using total_usage
        """
        model_obj = model_config_document[service][model]
        pricing = model_obj['outputConfig']['usage'][0]['total_cost']

        cost = {
            "input_cost": 0,
            "output_cost": 0, 
            "cached_cost": 0,
            "reasoning_cost": 0,
            "cache_read_cost": 0,
            "cache_creation_cost": 0,
            "total_cost": 0
        }
        
        # Calculate costs per million tokens using total_usage
        if self.total_usage["input_tokens"] and pricing.get("input_cost"):
            cost["input_cost"] = (self.total_usage["input_tokens"] / 1_000_000) * pricing["input_cost"]
            
        if self.total_usage["output_tokens"] and pricing.get("output_cost"):
            cost["output_cost"] = (self.total_usage["output_tokens"] / 1_000_000) * pricing["output_cost"]
            
        if self.total_usage["cached_tokens"] and pricing.get("cached_cost"):
            cost["cached_cost"] = (self.total_usage["cached_tokens"] / 1_000_000) * pricing["cached_cost"]
            
        if self.total_usage["reasoning_tokens"] and pricing.get("output_tokens"):
            cost["reasoning_cost"] = (self.total_usage["reasoning_tokens"] / 1_000_000) * pricing["output_tokens"]
            
        if self.total_usage["cache_read_input_tokens"] and pricing.get("caching_read_cost"):
            cost["cache_read_cost"] = (self.total_usage["cache_read_input_tokens"] / 1_000_000) * pricing["caching_read_cost"]
            
        if self.total_usage["cache_creation_input_tokens"] and pricing.get("caching_write_cost"):
            cost["cache_creation_cost"] = (self.total_usage["cache_creation_input_tokens"] / 1_000_000) * pricing["caching_write_cost"]
        
        # Calculate total cost
        cost["total_cost"] = (
            cost["input_cost"] + 
            cost["output_cost"] + 
            cost["cached_cost"] + 
            cost["reasoning_cost"] + 
            cost["cache_read_cost"] + 
            cost["cache_creation_cost"]
        )
        
        return cost

    def get_total_usage(self):
        return self.total_usage