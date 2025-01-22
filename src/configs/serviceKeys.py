from .constant import service_name
ServiceKeys = {
    service_name['openai']: {
        "reasoning": {
            "max_tokens" : "max_completion_tokens"
        },
        "default" : {
            "creativity_level": "temperature",
            "probability_cutoff": "top_p",
            "repetition_penalty": "frequency_penalty",
            "novelty_penalty": "presence_penalty",
            "log_probability": "logprobs",
            "echo_input": "echo",
            "input_text": "input",
            "token_selection_limit": "topK",
            "response_count": "n",
            "additional_stop_sequences": "stopSequences",
            "best_response_count": "best_of",
            "response_suffix": "suffix",
            "response_type": "response_format", 
            "max_tokens" : "max_tokens"
        }
    },
    service_name['anthropic']: {
        "default" : {
            "creativity_level": "temperature",
            "probability_cutoff": "top_p",
            "token_selection_limit": "top_k",
            "additional_stop_sequences": "stop_sequence",
            "max_tokens": "max_tokens"
        }
    },
    service_name['groq']: {
        "default" : {
            "creativity_level": "temperature",
            "probability_cutoff": "top_p",
            "repetition_penalty": "frequency_penalty",
            "novelty_penalty": "presence_penalty",
            "log_probability": "logprobs",
            "echo_input": "echo",
            "input_text": "input",
            "token_selection_limit": "topK",
            "response_count": "n",
            "additional_stop_sequences": "stopSequences",
            "best_response_count": "best_of",
            "response_suffix": "suffix",
            "response_type": "response_format"
        }
    }
}

async def model_config_change(modelConfiguration, custom_config, service):
    new_custom_config = custom_config.copy()
    for key, value in custom_config.items():
        if value == 'default':
            if not (service == 'anthropic' and key == 'max_tokens'):
                del new_custom_config[key]
            else:
                new_custom_config[key] = modelConfiguration[key].get('default')
        elif value == 'max':
            max_value = modelConfiguration[key].get('max')
            new_custom_config[key] = max_value

        elif value == 'min':
            min_value = modelConfiguration[key].get('min')
            new_custom_config[key] = min_value 
    return new_custom_config

# Export the service dictionary
__all__ = ['ServiceKeys']