class ServiceKeys:
    
    @staticmethod
    def gpt_keys():
        configuration = {
            "creativity_level" : "temprature",
            "probability_cutoff" : "top_p",
            "repetition_penalty" : "frequency_penalty",
            "novelty_penalty" : "presence_penalty",
            "log_probability" : "logprobs",
            "echo_input" :"echo",
            "input_text" : "input",
            "token_selection_limit" : "topK",
            "response_count" : "n",
            "additional_stop_sequences" : "stopSequences",
            "best_response_count" : "best_of",
            "response_suffix" : "suffix",
        }
        return {
            "configuration": configuration,
        }
