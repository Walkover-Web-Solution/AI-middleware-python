import pydash as _

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
            "cache_creation_input_tokens":0
        }

    def calculate_usage(self, model_response):
        usage = {}
        match self.service:
            case 'openai' | 'groq' | 'open_router' | 'mistral':
                usage["totalTokens"] = _.get(model_response, self.model_output_config['usage'][0]['total_tokens']) or 0
                usage["inputTokens"] = _.get(model_response, self.model_output_config['usage'][0]['prompt_tokens']) or 0 
                usage["outputTokens"] = _.get(model_response, self.model_output_config['usage'][0]['completion_tokens']) or 0
                usage["cachedTokens"] = _.get(model_response, self.model_output_config['usage'][0].get('cached_tokens')) or 0
            
            case 'openai_response':
                usage["totalTokens"] = _.get(model_response, self.model_output_config['usage'][0]['total_tokens'])
                usage["cachedTokens"] = _.get(model_response, self.model_output_config['usage'][0].get('cached_tokens')) or 0
            
            case 'anthropic':
                usage["inputTokens"] = _.get(model_response, self.model_output_config['usage'][0]['prompt_tokens']) or 0
                usage["outputTokens"] = _.get(model_response, self.model_output_config['usage'][0]['completion_tokens']) or 0
                usage['cachingReadTokens'] = _.get(model_response, self.model_output_config['usage'][0].get('cache_read_input_tokens')) or 0
                usage['cachingCreationInputTokens'] = _.get(model_response, self.model_output_config['usage'][0].get('cache_creation_input_tokens')) or 0
                usage["totalTokens"] = usage["inputTokens"] + usage["outputTokens"]
                
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

    def get_total_usage(self):
        return self.total_usage