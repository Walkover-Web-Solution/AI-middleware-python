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
            "reasoning_tokens": 0,
            "image_count": 0,
            "input_image_tokens": 0,
            "output_image_tokens": 0
        }

    def calculate_usage(self, model_response):
        usage = {}
        match self.service:
            case 'open_router' | 'mistral' | 'ai_ml' | 'openai_completion':
                usage["inputTokens"] = model_response['usage']['prompt_tokens']
                usage["outputTokens"] = model_response['usage']['completion_tokens']
                usage["totalTokens"] = model_response['usage']['total_tokens']
                # Handle optional token details with safe access
                usage["cachedTokens"] = (model_response['usage'].get('prompt_tokens_details') or {}).get('cached_tokens', 0)
                usage["reasoningTokens"] = (model_response['usage'].get('completion_tokens_details') or {}).get('reasoning_tokens', 0)
            
            case 'groq':
                usage["inputTokens"] = model_response['usage']['prompt_tokens']
                usage["outputTokens"] = model_response['usage']['completion_tokens']
                usage["totalTokens"] = model_response['usage']['total_tokens']
                # Groq doesn't have token details, set to 0
                usage["cachedTokens"] = 0
                usage["reasoningTokens"] = 0
            
            case 'grok':
                # Support both dicts (HTTP response) and SDK objects
                usage_obj = model_response.get('usage') or {}
                def _get_usage_value(key, default=0):
                    if isinstance(usage_obj, dict):
                        return usage_obj.get(key, default)
                    return getattr(usage_obj, key, default)

                usage["inputTokens"] = _get_usage_value('prompt_tokens')
                usage["outputTokens"] = _get_usage_value('completion_tokens')
                usage["totalTokens"] = _get_usage_value('total_tokens')
                # Grok may return cached/reasoning tokens under different keys, prefer documented ones
                usage["cachedTokens"] = _get_usage_value('cached_prompt_text_tokens') or _get_usage_value('cached_tokens')
                usage["reasoningTokens"] = _get_usage_value('reasoning_tokens')
            
            case 'gemini':
                # Handle both chat and image models
                if 'usage' in model_response and 'image_count' in model_response.get('usage', {}):
                    # Image model response
                    usage["inputTokens"] = model_response.get('usage', {}).get('input_tokens', 0)
                    usage["outputTokens"] = model_response.get('usage', {}).get('output_tokens', 0)
                    usage["totalTokens"] = usage["inputTokens"] + usage["outputTokens"]
                    usage["cachedTokens"] = 0
                    usage["reasoningTokens"] = 0
                    usage["imageCount"] = model_response.get('usage', {}).get('image_count', 0)
                    usage["inputImageTokens"] = model_response.get('usage', {}).get('input_image_tokens', 0)
                    usage["outputImageTokens"] = model_response.get('usage', {}).get('output_image_tokens', 0)
                else:
                    # Chat model response
                    usage["inputTokens"] = model_response.get('usage', {}).get('prompt_tokens', 0)
                    usage["outputTokens"] = model_response.get('usage', {}).get('completion_tokens', 0)
                    usage["totalTokens"] = model_response.get('usage', {}).get('total_tokens', 0)
                    usage["cachedTokens"] = 0
                    usage["reasoningTokens"] = 0
            
            case 'openai':
                # Handle both chat and image models
                if 'usage' in model_response and 'image_count' in model_response.get('usage', {}):
                    # Image model response
                    usage_data = model_response.get('usage', {})
                    
                    # Extract text tokens from details if available, otherwise use top-level
                    input_details = usage_data.get('input_tokens_details', {})
                    output_details = usage_data.get('output_tokens_details', {})
                    
                    # Check if detailed breakdown is available
                    has_detailed_breakdown = bool(output_details)
                    
                    if has_detailed_breakdown:
                        # gpt-image-1.5: Has detailed breakdown
                        input_text_tokens = input_details.get('text_tokens', usage_data.get('input_tokens', 0))
                        output_text_tokens = output_details.get('text_tokens', 0)
                        input_image_tokens = input_details.get('image_tokens', 0)
                        output_image_tokens = output_details.get('image_tokens', 0)
                    else:
                        # gpt-image-1, gpt-image-1-mini: No detailed breakdown
                        # Treat all input tokens as text, all output tokens as image tokens
                        input_text_tokens = usage_data.get('input_tokens', 0)
                        output_text_tokens = 0  # No text output
                        input_image_tokens = 0  # No image input
                        output_image_tokens = usage_data.get('output_tokens', 0)  # All output = image tokens
                    
                    usage["inputTokens"] = input_text_tokens
                    usage["outputTokens"] = output_text_tokens
                    usage["totalTokens"] = usage_data.get('total_tokens', input_text_tokens + output_text_tokens + output_image_tokens)
                    usage["cachedTokens"] = usage_data.get('cached_tokens', 0)
                    usage["reasoningTokens"] = output_details.get('reasoning_tokens', 0) if has_detailed_breakdown else 0
                    usage["imageCount"] = usage_data.get('image_count', 0)
                    
                    # Image tokens
                    usage["inputImageTokens"] = input_image_tokens
                    usage["outputImageTokens"] = output_image_tokens
                else:
                    # Chat model response
                    usage["inputTokens"] = model_response.get('usage', {}).get('input_tokens', 0)
                    usage["outputTokens"] = model_response.get('usage', {}).get('output_tokens', 0)
                    usage["totalTokens"] = model_response.get('usage', {}).get('total_tokens', 0)
                    usage["cachedTokens"] = (model_response.get('usage', {}).get('input_tokens_details') or {}).get('cached_tokens', 0)
                    usage["reasoningTokens"] = (model_response.get('usage', {}).get('output_tokens_details') or {}).get('reasoning_tokens', 0)
            
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
        self.total_usage["image_count"] += usage.get("imageCount") or 0
        self.total_usage["input_image_tokens"] += usage.get("inputImageTokens") or 0
        self.total_usage["output_image_tokens"] += usage.get("outputImageTokens") or 0


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

    def calculate_image_cost(self, model, service, config=None):
        """
        Calculate cost for image generation models
        
        Args:
            model: model name
            service: service name
            config: configuration dict containing quality, size, aspect_ratio, image_size, etc.
        
        Returns:
            Dictionary with cost breakdown for image generation
        """
        try:
            model_obj = model_config_document[service][model]
        except KeyError as e:
            # Model not found in config, return zero cost
            return {
                "text_token_cost": 0,
                "image_token_cost": 0,
                "image_generation_cost": 0,
                "total_cost": 0
            }
        
        # Image models have pricing under outputConfig['usage'][0]
        # Some models have it directly (OpenAI), others nest it under 'total_cost' (Imagen)
        pricing_raw = model_obj['outputConfig']['usage'][0]
        
        # Extract actual pricing - handle both direct and nested under 'total_cost'
        if 'total_cost' in pricing_raw and isinstance(pricing_raw['total_cost'], dict):
            pricing = pricing_raw['total_cost']
        else:
            pricing = pricing_raw
        
        config = config or {}
        
        cost = {
            "text_token_cost": 0,
            "image_token_cost": 0,
            "image_generation_cost": 0,
            "total_cost": 0
        }
        
        # Handle OpenAI image models (gpt-image-*)
        if service == 'openai' and 'gpt-image' in model:
            # Text tokens cost (input/output)
            if 'text_tokens' in pricing:
                text_pricing = pricing['text_tokens']
                permillion = 1_000_000
                
                if self.total_usage["input_tokens"] and text_pricing.get('input'):
                    cost["text_token_cost"] += (self.total_usage["input_tokens"] / permillion) * text_pricing['input']
                
                if self.total_usage["output_tokens"] and text_pricing.get('output'):
                    cost["text_token_cost"] += (self.total_usage["output_tokens"] / permillion) * text_pricing['output']
                
                if self.total_usage["cached_tokens"] and text_pricing.get('cached_input'):
                    cost["text_token_cost"] += (self.total_usage["cached_tokens"] / permillion) * text_pricing['cached_input']
            
            # Image tokens cost (input/output)
            if 'image_tokens' in pricing:
                image_token_pricing = pricing['image_tokens']
                permillion = 1_000_000
                
                if self.total_usage["input_image_tokens"] and image_token_pricing.get('input'):
                    cost["image_token_cost"] += (self.total_usage["input_image_tokens"] / permillion) * image_token_pricing['input']
                
                if self.total_usage["output_image_tokens"] and image_token_pricing.get('output'):
                    cost["image_token_cost"] += (self.total_usage["output_image_tokens"] / permillion) * image_token_pricing['output']
                
                if self.total_usage["cached_tokens"] and image_token_pricing.get('cached_input'):
                    cost["image_token_cost"] += (self.total_usage["cached_tokens"] / permillion) * image_token_pricing['cached_input']
        
        # Handle Gemini image models (gemini-*-image, imagen-*)
        elif service == 'gemini':
            # Gemini 2.5 Flash Image
            if 'gemini-2.5-flash-image' in model or 'gemini-3-pro-image' in model:
                permillion = 1_000_000
                
                # Input text/image tokens
                if 'input_text/image' in pricing:
                    input_cost_per_million = float(pricing['input_text/image'])
                    total_input_tokens = self.total_usage["input_tokens"] + self.total_usage["input_image_tokens"]
                    if total_input_tokens:
                        cost["text_token_cost"] = (total_input_tokens / permillion) * input_cost_per_million
                
                # Input image cost (for gemini-3-pro-image)
                if 'input_image' in pricing:
                    input_image_cost = float(pricing['input_image'])
                    if self.total_usage["image_count"] > 0:
                        cost["image_token_cost"] = self.total_usage["image_count"] * input_image_cost
                
                # Output image cost
                if 'output_image' in pricing:
                    if isinstance(pricing['output_image'], dict):
                        # gemini-3-pro-image has different pricing for 1K/2K vs 4K
                        image_size = config.get('image_size', '1K')
                        if image_size == '4K':
                            per_image_cost = float(pricing['output_image']['4K'])
                        else:
                            per_image_cost = float(pricing['output_image']['1K/2K'])
                    else:
                        # Simple per-image pricing
                        per_image_cost = float(pricing['output_image'])
                    
                    if self.total_usage["image_count"] > 0:
                        cost["image_generation_cost"] = self.total_usage["image_count"] * per_image_cost
            
            # Imagen models (imagen-4.0-*)
            elif 'imagen' in model:
                # Imagen models only have output_image cost
                if 'output_image' in pricing and self.total_usage["image_count"] > 0:
                    per_image_cost = float(pricing['output_image'])
                    cost["image_generation_cost"] = self.total_usage["image_count"] * per_image_cost
        
        # Calculate total cost
        cost["total_cost"] = (
            cost["text_token_cost"] + 
            cost["image_token_cost"] + 
            cost["image_generation_cost"]
        )
        
        return cost

    def get_total_usage(self):
        return self.total_usage
