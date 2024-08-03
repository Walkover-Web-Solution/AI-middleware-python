ServiceKeys = {
    'gpt_keys': {
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
    },
    'anthropic_keys': {
        "creativity_level": "temperature",
        "probability_cutoff": "top_p",
        "token_selection_limit": "top_k",
        "additional_stop_sequences": "stop_sequence",
        "max_tokens": "max_tokens"
    }
}

# Export the service dictionary
__all__ = ['ServiceKeys']