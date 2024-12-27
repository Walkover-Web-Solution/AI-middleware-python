import pydash as _

class TokenCalculator:
    def __init__(self, service, model_output_config):
        self.service = service
        self.model_output_config = model_output_config
        self.total_usage = {
            "totalTokens": 0,
            "inputTokens": 0,
            "outputTokens": 0,
            "cachedTokens":0,
            "expectedCost": 0.0
        }

    def calculate_usage(self, model_response):
        usage = {}
        match self.service:
            case 'openai' | 'groq':
                usage["totalTokens"] = _.get(model_response, self.model_output_config['usage'][0]['total_tokens'])
                usage["inputTokens"] = _.get(model_response, self.model_output_config['usage'][0]['prompt_tokens'])
                usage["outputTokens"] = _.get(model_response, self.model_output_config['usage'][0]['completion_tokens'])
                usage["cachedTokens"] = _.get(model_response, self.model_output_config['usage'][0].get('cached_tokens', 0))
            case 'anthropic':
                usage["inputTokens"] = _.get(model_response, self.model_output_config['usage'][0]['prompt_tokens'])
                usage["outputTokens"] = _.get(model_response, self.model_output_config['usage'][0]['completion_tokens'])
                usage['cachingReadTokens'] = _.get(model_response,self.model_output_config['usage'][0]['caching_read_tokens'])
                usage['cachingWriteTokens'] = _.get(model_response,self.model_output_config['usage'][0]['caching_write_tokens'])
                usage["totalTokens"] = usage["inputTokens"] + usage["outputTokens"]
                
            case _:
                pass

        self._update_total_usage(usage)
        return usage

    def _update_total_usage(self, usage):
        self.total_usage["totalTokens"] += usage.get("totalTokens", 0)
        self.total_usage["inputTokens"] += usage.get("inputTokens", 0)
        self.total_usage["outputTokens"] += usage.get("outputTokens", 0)
        self.total_usage["expectedCost"] += usage.get("expectedCost", 0.0)

    def get_total_usage(self):
        return self.total_usage