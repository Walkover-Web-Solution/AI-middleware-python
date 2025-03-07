class ModelsConfig:
    @staticmethod
    def gpt_3_5_turbo():
        configuration = {
            "model": {
                "field": "dropdown",
                "default": "gpt-3.5-turbo",
                "level": 1
            },
            "creativity_level": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.1,
                "default": 0,
                "level": 2
            },
            "max_tokens": {
                "field": "slider",
                "min": 256,
                "max": 4096,
                "step": 1,
                "default": 256,
                "level": 2
            },
            "probability_cutoff": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 1,
                "level": 2
            },
            "log_probability": {
                "field": "boolean",
                "default": False,
                "level": 0
            },
            "repetition_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "novelty_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "response_count": {
                "field": "number",
                "default": 1,
                "level": 0
            },
            "stream": {
                "field": "boolean",
                "default": False,
                "level": 0
            },
            "type" : {
                "default" : ["chat"]
            },
            "response_type": {
                "field": "select",
                "options" : [{"type" : "text"},{"type" : "json_object"}],
                "default": {
                "type" : "text",
                },
                "level": 0
            },
            "specification" : {
                "input_cost": 3.00,
                "output_cost": 6.00,
                "description" : "GPT-3.5 Turbo models can understand and generate natural language or code and have been optimized for chat using the Chat Completions API but work well for non-chat tasks as well. As of July 2024, use gpt-4o-mini in place of GPT-3.5 Turbo, as it is cheaper, more capable, multimodal, and just as fast",
                "knowledge_cutoff" : "Sep 01, 2021",
                "usecase" : [""]
            
            }
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.prompt_tokens",
                "completion_tokens": "usage.completion_tokens",
                "total_tokens": "usage.total_tokens",
                "total_cost": {
                    "input_cost": 3.00,
                    "output_cost": 6.00
                }
            }],
            "message": "choices[0].message.content",
            "tools": "choices[0].message.tool_calls",
            "id": "id"
        }
        inputConfig = {
            "system": {
                "default": {
                    "role": "system",
                    "content": ""
                },
                "contentKey": "content",
                "type": "json"
            },
            "content_location": "prompt[0].content"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }

    @staticmethod
    def gpt_3_5_turbo_0613():
        configuration = {
            "model": {
                "field": "dropdown",
                "default": "gpt-3.5-turbo-0613",
                "level": 1
            },
            "creativity_level": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.1,
                "default": 0,
                "level": 2
            },
            "max_tokens": {
                "field": "slider",
                "min": 256,
                "max": 4096,
                "step": 1,
                "default": 256,
                "level": 2
            },
            "probability_cutoff": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 1,
                "level": 2
            },
            "log_probability": {
                "field": "boolean",
                "default": False,
                "level": 0
            },
            "repetition_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "novelty_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "response_count": {
                "field": "number",
                "default": 1,
                "level": 0
            },
            "additional_stop_sequences": {
                "field": "text",
                "default": "",
                "level": 0
            },
            "stream": {
                "field": "boolean",
                "default": False,
                "level": 0
            },
            "type" : {
                "default" : ["chat"]
            }
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.prompt_tokens",
                "completion_tokens": "usage.completion_tokens",
                "total_tokens": "usage.total_tokens",
                "total_cost": {
                    "input_cost": 1.50,
                    "output_cost": 2.00
                }
            }],
            "message": "choices[0].message.content",
            "tools": "choices[0].message.tool_calls",
            "assistant": "choices[0].message",
            "id": "id"
        }
        inputConfig = {
            "system": {
                "default": {
                    "role": "system",
                    "content": ""
                },
                "contentKey": "content",
                "type": "json"
            },
            "content_location": "prompt[0].content"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }

    @staticmethod
    def gpt_3_5_turbo_0125():
        configuration = {
            "model": {
                "field": "dropdown",
                "default": "gpt-3.5-turbo-0125",
                "level": 1
            },
            "creativity_level": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.1,
                "default": 0,
                "level": 2
            },
            "max_tokens": {
                "field": "slider",
                "min": 256,
                "max": 4096,
                "step": 1,
                "default": 256,
                "level": 2
            },
            "probability_cutoff": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 1,
                "level": 2
            },
            "log_probability": {
                "field": "boolean",
                "default": False,
                "level": 0
            },
            "repetition_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "novelty_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "response_count": {
                "field": "number",
                "default": 1,
                "level": 0
            },
            "additional_stop_sequences": {
                "field": "text",
                "default": "",
                "level": 0
            },
            "stream": {
                "field": "boolean",
                "default": False,
                "level": 0
            },
            "tools": {
                "field": "array",
                "level": 0,
                "default": []
            },
            "tool_choice": {
                "field": "dropdown",
                "options" : ["auto", "none", "required"],
                "default": "auto",
                "level": 0
            },
            "response_type": {
                "field": "select",
                "options" : [{"type" : "text"},{"type" : "json_object"}],
                "default": {
                "type" : "text",
                },
                "level": 0
            },
             "type" : {
                "default" : ["chat"]
            }
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.prompt_tokens",
                "completion_tokens": "usage.completion_tokens",
                "total_tokens": "usage.total_tokens",
                "total_cost": {
                    "input_cost": 0.50,
                    "output_cost": 1.50
                }
            }],
            "message": "choices[0].message.content",
            "tools": "choices[0].message.tool_calls",
            "assistant": "choices[0].message",
            "id": "id"
        }
        inputConfig = {
            "system": {
                "default": {
                    "role": "system",
                    "content": ""
                },
                "contentKey": "content",
                "type": "json"
            },
            "content_location": "prompt[0].content"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }

    @staticmethod
    def gpt_3_5_turbo_0301():
        configuration = {
            "model": {
                "field": "dropdown",
                "default": "gpt-3.5-turbo-0301",
                "level": 1
            },
            "creativity_level": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.1,
                "default": 1,
                "level": 2
            },
            "max_tokens": {
                "field": "slider",
                "min": 256,
                "max": 4096,
                "step": 1,
                "default": 256,
                "level": 2
            },
            "probability_cutoff": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 1,
                "level": 2
            },
            "log_probability": {
                "field": "boolean",
                "default": False,
                "level": 0
            },
            "repetition_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "novelty_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "response_count": {
                "field": "number",
                "default": 1,
                "level": 0
            },
            "additional_stop_sequences": {
                "field": "text",
                "default": "",
                "level": 0
            },
            "stream": {
                "field": "boolean",
                "default": False,
                "level": 0
            },
            "tools": {
                "field": "array",
                "level": 0,
                "default": []
            },
            "tool_choice": {
                "field": "dropdown",
                 "options" : ["auto", "none", "required"],
                "default": "auto",
                "level": 0
            },
            "response_type": {
                "field": "select",
                "options" : [{"type" : "text"},{"type" : "json_object"}],
                "default": {
                "type" : "text",
                },
                "level": 0
            },
            "type" : {
                "default" : ["chat"]
            }
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.prompt_tokens",
                "completion_tokens": "usage.completion_tokens",
                "total_tokens": "usage.total_tokens",
                "total_cost": {
                    "input_cost": 1.50,
                    "output_cost": 2.00
                }
            }],
            "message": "choices[0].message.content",
            "tools": "choices[0].message.tool_calls",
            "assistant": "choices[0].message",
            "id": "id"
        }
        inputConfig = {
            "system": {
                "default": {
                    "role": "system",
                    "content": ""
                },
                "contentKey": "content",
                "type": "json"
            },
            "content_location": "prompt[0].content"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }

    @staticmethod
    def gpt_3_5_turbo_1106():
        configuration = {
            "model": {
                "field": "dropdown",
                "default": "gpt-3.5-turbo-1106",
                "level": 1
            },
            "creativity_level": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.1,
                "default": 0,
                "level": 2
            },
            "max_tokens": {
                "field": "slider",
                "min": 256,
                "max": 4096,
                "step": 1,
                "default": 256,
                "level": 2
            },
            "probability_cutoff": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 1,
                "level": 2
            },
            "log_probability": {
                "field": "boolean",
                "default": False,
                "level": 0
            },
            "repetition_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "novelty_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "response_count": {
                "field": "number",
                "default": 1,
                "level": 0
            },
            "additional_stop_sequences": {
                "field": "text",
                "default": "",
                "level": 0
            },
            "stream": {
                "field": "boolean",
                "default": False,
                "level": 0
            },
            "tools": {
                "field": "array",
                "level": 0,
                "default": []
            },
            "tool_choice": {
                "field": "dropdown",
                "options" : ["auto", "none", "required"],
                "default": "auto",
                "level": 0
            },
            "response_type": {
                "field": "select",
                "options" : [{"type" : "text"},{"type" : "json_object"}],
                "default": {
                "type" : "text",
                },
                "level": 0
            },
            "type" : {
                "default" : ["chat"]
            }
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.prompt_tokens",
                "completion_tokens": "usage.completion_tokens",
                "total_tokens": "usage.total_tokens",
                "total_cost": {
                    "input_cost": 1.00,
                    "output_cost": 2.00
                }
            }],
            "message": "choices[0].message.content",
            "tools": "choices[0].message.tool_calls",
            "assistant": "choices[0].message",
            "id": "id"
        }
        inputConfig = {
            "system": {
                "default": {
                    "role": "system",
                    "content": ""
                },
                "contentKey": "content",
                "type": "json"
            },
            "content_location": "prompt[0].content"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }

    @staticmethod
    def gpt_3_5_turbo_16k():
        configuration = {
            "model": {
                "field": "dropdown",
                "default": "gpt-3.5-turbo-16k",
                "level": 1
            },
            "creativity_level": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.1,
                "default": 0,
                "level": 2
            },
            "max_tokens": {
                "field": "slider",
                "min": 256,
                "max": 16384,
                "step": 1,
                "default": 256,
                "level": 2
            },
            "probability_cutoff": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 1,
                "level": 2
            },
            "log_probability": {
                "field": "boolean",
                "default": False,
                "level": 0
            },
            "repetition_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "novelty_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "response_count": {
                "field": "number",
                "default": 1,
                "level": 0
            },
            "additional_stop_sequences": {
                "field": "text",
                "default": "",
                "level": 0
            },
            "stream": {
                "field": "boolean",
                "default": False,
                "level": 0
            },
            "tools": {
                "field": "array",
                "level": 0,
                "default": []
            },
            "tool_choice": {
                "field": "dropdown",
                "options" : ["auto", "none", "required"],
                "default": "auto",
                "level": 0
            },
            "response_type": {
                "field": "select",
                "options" : [{"type" : "text"},{"type" : "json_object"}],
                "default": {
                "type" : "text",
                },
                "level": 0
            },
            "type" : {
                "default" : ["chat"]
            }
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.prompt_tokens",
                "completion_tokens": "usage.completion_tokens",
                "total_tokens": "usage.total_tokens",
                "total_cost": {
                    "input_cost": 3.00,
                    "output_cost": 4.00
                }
            }],
            "message": "choices[0].message.content",
            "tools": "choices[0].message.tool_calls",
            "assistant": "choices[0].message",
            "id": "id"
        }
        inputConfig = {
            "system": {
                "default": {
                    "role": "system",
                    "content": ""
                },
                "contentKey": "content",
                "type": "json"
            },
            "content_location": "prompt[0].content"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }

    @staticmethod
    def gpt_3_5_turbo_16k_0613():
        configuration = {
            "model": {
                "field": "dropdown",
                "default": "gpt-3.5-turbo-16k-0613",
                "level": 1
            },
            "creativity_level": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.1,
                "default": 0,
                "level": 2
            },
            "max_tokens": {
                "field": "slider",
                "min": 256,
                "max": 16384,
                "step": 1,
                "default": 256,
                "level": 2
            },
            "probability_cutoff": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 1,
                "level": 2
            },
            "log_probability": {
                "field": "boolean",
                "default": False,
                "level": 0
            },
            "repetition_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "novelty_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "response_count": {
                "field": "number",
                "default": 1,
                "level": 0
            },
            "additional_stop_sequences": {
                "field": "text",
                "default": "",
                "level": 0
            },
            "stream": {
                "field": "boolean",
                "default": False,
                "level": 0
            },
            "tools": {
                "field": "array",
                "level": 0,
                "default": []
            },
            "tool_choice": {
                "field": "dropdown",
                "options" : ["auto", "none", "required"],
                "default": "auto",
                "level": 0
            },
            "response_type": {
                "field": "select",
                "options" : [{"type" : "text"},{"type" : "json_object"}],
                "default": {
                "type" : "text",
                },
                "level": 0
            },
            "type" : {
                "default" : ["chat"]
            }
        }

        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.prompt_tokens",
                "completion_tokens": "usage.completion_tokens",
                "total_tokens": "usage.total_tokens",
                "total_cost": {
                    "input_cost": 3.00,
                    "output_cost": 4.00
                }
            }],
            "message": "choices[0].message.content",
            "tools": "choices[0].message.tool_calls",
            "assistant": "choices[0].message",
            "id": "id"
        }
        inputConfig = {
            "system": {
                "default": {
                    "role": "system",
                    "content": ""
                },
                "contentKey": "content",
                "type": "json"
            },
            "content_location": "prompt[0].content"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }

    @staticmethod
    def gpt_4():
        configuration = {
            "model": {
                "field": "dropdown",
                "default": "gpt-4",
                "level": 1
            },
            "creativity_level": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.1,
                "default": 0,
                "level": 2
            },
            "max_tokens": {
                "field": "slider",
                "min": 256,
                "max": 8192,
                "step": 1,
                "default": 256,
                "level": 2
            },
            "probability_cutoff": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 1,
                "level": 2
            },
            "log_probability": {
                "field": "boolean",
                "default": False,
                "level": 0
            },
            "repetition_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "novelty_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "response_count": {
                "field": "number",
                "default": 1,
                "level": 0
            },
            "stream": {
                "field": "boolean",
                "default": False,
                "level": 0
            },
            "tools": {
                "field": "array",
                "level": 0,
                "default": []
            },
            "tool_choice": {
                "field": "dropdown",
                "options" : ["auto", "none", "required"],
                "default": "auto",
                "level": 0
            },
             "type" : {
                "default" : ["chat"]
            },
            "specification" : {
                "input_cost": 30.00,
                "output_cost": 60.00,
                "description" : "GPT-4 is an advanced AI language model by OpenAI, capable of understanding and generating human-like text with improved reasoning, creativity, and context retention. It supports both text and image inputs, making it highly versatile. With enhanced problem-solving skills, it excels in writing, coding, and complex queries.",
                "knowledge_cutoff" : "Dec 01, 2023",
                "usecase" : [""]
            }
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.prompt_tokens",
                "completion_tokens": "usage.completion_tokens",
                "total_tokens": "usage.total_tokens",
                "total_cost": {
                    "input_cost": 30.00,
                    "output_cost": 60.00
                }
            }],
            "message": "choices[0].message.content",
            "tools": "choices[0].message.tool_calls",
            "assistant": "choices[0].message",
            "id": "id"
        }
        inputConfig = {
            "system": {
                "default": {
                    "role": "system",
                    "content": ""
                },
                "contentKey": "content",
                "type": "json"
            },
            "content_location": "prompt[0].content"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }

    @staticmethod
    def gpt_4_0613():
        configuration = {
            "model": {
                "field": "dropdown",
                "default": "gpt-4-0613",
                "level": 1
            },
            "creativity_level": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.1,
                "default": 0,
                "level": 2
            },
            "max_tokens": {
                "field": "slider",
                "min": 256,
                "max": 8192,
                "step": 1,
                "default": 256,
                "level": 2
            },
            "probability_cutoff": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 1,
                "level": 2
            },
            "log_probability": {
                "field": "boolean",
                "default": False,
                "level": 0
            },
            "repetition_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "novelty_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "response_count": {
                "field": "number",
                "default": 1,
                "level": 0
            },
            "stop": {
                "field": "text",
                "default": "",
                "level": 0
            },
            "stream": {
                "field": "boolean",
                "default": False,
                "level": 0
            },
            "tools": {
                "field": "array",
                "level": 0,
                "default": []
            },
            "tool_choice": {
                "field": "dropdown",
                "options" : ["auto", "none", "required"],
                "default": "auto",
                "level": 0
            },
             "type" : {
                "default" : ["chat"]
            },
            "specification" : {
                "input_cost": 30.00,
                "output_cost": 60.00,
                "description" : "GPT-4o-2024-08-06 is a version of OpenAI's GPT-4 model released in August 2024. It likely includes optimizations and updates for better performance. The model excels in tasks like natural language understanding, creative writing, and problem-solving. It does not have real-time data access, relying on its pre-existing knowledge base.",
                "knowledge_cutoff" : "Oct 01, 2023",
                "usecase" : [""]
            }

        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.prompt_tokens",
                "completion_tokens": "usage.completion_tokens",
                "total_tokens": "usage.total_tokens",
                "total_cost": {
                    "input_cost": 30.00,
                    "output_cost": 60.00
                }
            }],
            "message": "choices[0].message.content",
            "tools": "choices[0].message.tool_calls",
            "assistant": "choices[0].message",
            "id": "id"
        }
        inputConfig = {
            "system": {
                "default": {
                    "role": "system",
                    "content": ""
                },
                "contentKey": "content",
                "type": "json"
            },
            "content_location": "prompt[0].content"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }

    @staticmethod
    def gpt_4_1106_preview():
        configuration = {
            "model": {
                "field": "dropdown",
                "default": "gpt-4-1106-preview",
                "level": 1
            },
            "creativity_level": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.1,
                "default": 0,
                "level": 2
            },
            "max_tokens": {
                "field": "slider",
                "min": 256,
                "max": 4096,
                "step": 1,
                "default": 256,
                "level": 2
            },
            "probability_cutoff": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 1,
                "level": 2
            },
            "log_probability": {
                "field": "boolean",
                "default": False,
                "level": 0
            },
            "repetition_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "novelty_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "response_count": {
                "field": "number",
                "default": 1,
                "level": 0
            },
            "stop": {
                "field": "text",
                "default": "",
                "level": 0
            },
            "stream": {
                "field": "boolean",
                "default": False,
                "level": 0
            },
            "tools": {
                "field": "array",
                "level": 0,
                "default": []
            },
            "tool_choice": {
                "field": "dropdown",
                "options" : ["auto", "none", "required"],
                "default": "auto",
                "level": 0
            },
            # "response_type": {
            #     "field": "boolean",
            #     "default": {
            #         "type" : "text",
            #      },
            #     "level": 0
            # },
            "type" : {
                "default" : ["chat"]
            }
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.prompt_tokens",
                "completion_tokens": "usage.completion_tokens",
                "total_tokens": "usage.total_tokens",
                "total_cost": {
                    "input_cost": 10.00,
                    "output_cost": 30.00
                }
            }],
            "message": "choices[0].message.content",
            "tools": "choices[0].message.tool_calls",
            "assistant": "choices[0].message",
            "id": "id"
        }
        inputConfig = {
            "system": {
                "default": {
                    "role": "system",
                    "content": ""
                },
                "contentKey": "content",
                "type": "json"
            },
            "content_location": "prompt[0].content"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }

    @staticmethod
    def gpt_4_turbo_preview():
        configuration = {
            "model": {
                "field": "dropdown",
                "default": "gpt-4-turbo-preview",
                "level": 1
            },
            "creativity_level": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.1,
                "default": 0,
                "level": 2
            },
            "max_tokens": {
                "field": "slider",
                "min": 256,
                "max": 4096,
                "step": 1,
                "default": 256,
                "level": 2
            },
            "probability_cutoff": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 1,
                "level": 2
            },
            "log_probability": {
                "field": "boolean",
                "default": False,
                "level": 0
            },
            "repetition_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "novelty_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "response_count": {
                "field": "number",
                "default": 1,
                "level": 0
            },
            "stop": {
                "field": "text",
                "default": "",
                "level": 0
            },
            "stream": {
                "field": "boolean",
                "default": False,
                "level": 0
            },
            "tools": {
                "field": "array",
                "level": 0,
                "default": []
            },
            "tool_choice": {
                "field": "dropdown",
                "options" : ["auto", "none", "required"],
                "default": "auto",
                "level": 0
            },
            # "response_type": {
            #     "field": "boolean",
            #     "default": {
            #         "type" : "text",
            #      },
            #     "level": 0
            # },
            "type" : {
                "default" : ["chat"]
            }
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.prompt_tokens",
                "completion_tokens": "usage.completion_tokens",
                "total_tokens": "usage.total_tokens",
                "total_cost": {
                    "input_cost": 10.00,
                    "output_cost": 30.00
                }
            }],
            "message": "choices[0].message.content",
            "tools": "choices[0].message.tool_calls",
            "assistant": "choices[0].message",
            "id": "id"
        }
        inputConfig = {
            "system": {
                "default": {
                    "role": "system",
                    "content": ""
                },
                "contentKey": "content",
                "type": "json"
            },
            "content_location": "prompt[0].content"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }

    @staticmethod
    def gpt_4_0125_preview():
        configuration = {
            "model": {
                "field": "dropdown",
                "default": "gpt-4-0125-preview",
                "level": 1
            },
            "creativity_level": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.1,
                "default": 0,
                "level": 2
            },
            "max_tokens": {
                "field": "slider",
                "min": 256,
                "max": 4096,
                "step": 1,
                "default": 256,
                "level": 2
            },
            "probability_cutoff": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 1,
                "level": 2
            },
            "log_probability": {
                "field": "boolean",
                "default": False,
                "level": 0
            },
            "repetition_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "novelty_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "response_count": {
                "field": "number",
                "default": 1,
                "level": 0
            },
            "stop": {
                "field": "text",
                "default": "",
                "level": 0
            },
            "stream": {
                "field": "boolean",
                "default": False,
                "level": 0
            },
            "tools": {
                "field": "array",
                "level": 0,
                "default": []
            },
            "tool_choice": {
                "field": "dropdown",
                "options" : ["auto", "none", "required"],
                "default": "auto",
                "level": 0
            },
            # "response_type": {
            #     "field": "boolean",
            #     "default": {
            #         "type" : "text",
            #      },
            #     "level": 0
            # },
            "type" : {
                "default" : ["chat"]
            }
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.prompt_tokens",
                "completion_tokens": "usage.completion_tokens",
                "total_tokens": "usage.total_tokens",
                "total_cost": {
                    "input_cost": 10.00,
                    "output_cost": 30.00
                }
            }],
            "message": "choices[0].message.content",
            "tools": "choices[0].message.tool_calls",
            "assistant": "choices[0].message",
            "id": "id"
        }
        inputConfig = {
            "system": {
                "default": {
                    "role": "system",
                    "content": ""
                },
                "contentKey": "content",
                "type": "json"
            },
            "content_location": "prompt[0].content"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }

    @staticmethod
    def gpt_4_turbo_2024_04_09():
        configuration = {
            "model": {
                "field": "drop",
                "default": "gpt-4-turbo-2024-04-09",
                "level": 1
            },
            "creativity_level": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.1,
                "default": 0,
                "level": 2
            },
            "max_tokens": {
                "field": "slider",
                "min": 256,
                "max": 4096,
                "step": 1,
                "default": 256,
                "level": 2
            },
            "probability_cutoff": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 1,
                "level": 2
            },
            "log_probability": {
                "field": "boolean",
                "default": False,
                "level": 0,
                "typeOf": "boolean"
            },
            "repetition_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "novelty_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "response_count": {
                "field": "number",
                "default": 1,
                "typeOf": "number",
                "level": 0
            },
            "stop": {
                "field": "text",
                "default": "",
                "level": 0
            },
            "stream": {
                "field": "boolean",
                "default": False,
                "level": 0,
                "typeOf": "boolean"
            },
            "tools": {
                "field": "array",
                "level": 0,
                "default": [],
                "typeOf": "array"
            },
            "tool_choice": {
                "field": "dropdown",
                "options" : ["auto", "none", "required"],
                "default": "auto",
                "level": 0,
                "typeOf": "string"
            },
            # "response_type": {
            #     "field": "boolean",
            #     "default": {
            #         "type" : "text",
            #      },
            #     "level": 0
            # },
            "type" : {
                "default" : ["chat"]
            }
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.prompt_tokens",
                "completion_tokens": "usage.completion_tokens",
                "total_tokens": "usage.total_tokens",
                "total_cost": {
                    "input_cost": 10.00,
                    "output_cost": 30.00
                }
            }],
            "message": "choices[0].message.content",
            "tools": "choices[0].message.tool_calls",
            "assistant": "choices[0].message",
            "id": "id"
        }
        inputConfig = {
            "system": {
                "default": {
                    "role": "system",
                    "content": ""
                },
                "contentKey": "content",
                "type": "json"
            },
            "content_location": "prompt[0].content"
        }
        return {
            "configuration": configuration,
            "inputConfig": inputConfig,
            "outputConfig": outputConfig
        }

    @staticmethod
    def gpt_4_turbo():
        configuration = {
            "model": {
                "field": "drop",
                "default": "gpt-4-turbo",
                "level": 1
            },
            "creativity_level": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.1,
                "default": 0,
                "level": 2
            },
            "max_tokens": {
                "field": "slider",
                "min": 256,
                "max": 4096,
                "step": 1,
                "default": 256,
                "level": 2
            },
            "probability_cutoff": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 1,
                "level": 2
            },
            "log_probability": {
                "field": "boolean",
                "default": False,
                "level": 0,
                "typeOf": "boolean"
            },
            "repetition_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "novelty_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "response_count": {
                "field": "number",
                "default": 1,
                "typeOf": "number",
                "level": 0
            },
            "stop": {
                "field": "text",
                "default": "",
                "level": 0
            },
            "stream": {
                "field": "boolean",
                "default": False,
                "level": 0,
                "typeOf": "boolean"
            },
            "tools": {
                "field": "array",
                "level": 0,
                "default": [],
                "typeOf": "array"
            },
            "tool_choice": {
                "field": "dropdown",
                "options" : ["auto", "none", "required"],
                "default": "auto",
                "level": 0,
                "typeOf": "string"
            },
           "response_type": {
                "field": "select",
                "options" : [{"type" : "text"},{"type" : "json_object"},{"type" : "json_schema"}],
                "default": {
                "type" : "text",
                },
                "level": 0
            },
            "type" : {
                "default" : ["chat"]
            },"specification" : {
                "input_cost": 10.00,
                "output_cost": 30.00,
                "description" : ["GPT-4 Turbo is a faster, more efficient, and cost-effective version of GPT-4, optimized for speed and scalability. It offers improved reasoning, longer context handling, and better performance in coding and complex tasks. Designed for high responsiveness, it balances power with efficiency for seamless interactions"],
                "knowledge_cutoff" : "Dec 01, 2023",
                "usecase" : [""]
            }
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.prompt_tokens",
                "completion_tokens": "usage.completion_tokens",
                "total_tokens": "usage.total_tokens",
                "total_cost": {
                    "input_cost": 10.00,
                    "output_cost": 30.00
                }
            }],
            "message": "choices[0].message.content",
            "tools": "choices[0].message.tool_calls",
            "assistant": "choices[0].message",
            "id": "id"
        }
        inputConfig = {
            "system": {
                "role": "system",
                "content": "",
                "contentKey": "content",
                "type": "json"
            }
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }
    
    @staticmethod
    def gpt_4o():
        configuration = {
            "model": {
                "field": "drop",
                "default": "gpt-4o",
                "level": 1
            },
            "creativity_level": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.1,
                "default": 0,
                "level": 2
            },
            "max_tokens": {
                "field": "slider",
                "min": 256,
                "max": 16384,
                "step": 1,
                "default": 256,
                "level": 2
            },
            "probability_cutoff": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 1,
                "level": 2
            },
            "log_probability": {
                "field": "boolean",
                "default": False,
                "level": 0,
                "typeOf": "boolean"
            },
            "repetition_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "novelty_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "response_count": {
                "field": "number",
                "default": 1,
                "typeOf": "number",
                "level": 0
            },
            "stop": {
                "field": "text",
                "default": "",
                "level": 0
            },
            "stream": {
                "field": "boolean",
                "default": False,
                "level": 0,
                "typeOf": "boolean"
            },
            "tools": {
                "field": "array",
                "level": 0,
                "default": [],
                "typeOf": "array"
            },
            "tool_choice": {
                "field": "dropdown",
                "options" : ["auto", "none", "required"],
                "default": "auto",
                "level": 0,
                "typeOf": "string"
            },
            "response_type": {
                "field": "select",
                "options" : [{"type" : "text"},{"type" : "json_object"},{"type" : "json_schema"}],
                "default": {
                "type" : "text",
                },
                "level": 0
            },
            "vision": {
                "support": True,
                 "level": 0,
                 "default" : False
            },
            "parallel_tool_calls": {
                "field": "boolean",
                "default": True,
                "level": 0,
                "typeOf": "boolean"  
            }
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.prompt_tokens",
                "completion_tokens": "usage.completion_tokens",
                "total_tokens": "usage.total_tokens",
                "cached_tokens": "usage.prompt_tokens_details.cached_tokens",
                "total_cost": {
                    "input_cost": 2.50,
                    "output_cost": 10.00,
                    "cached_cost": 1.25
                }
            }],
            "message": "choices[0].message.content",
            "tools": "choices[0].message.tool_calls",
            "assistant": "choices[0].message",
            "id": "id"
        }
        inputConfig = {
            "system": {
                "role": "system",
                "content": "",
                "contentKey": "content",
                "type": "json"
            },
            "content_location": "prompt[0].content"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }
    
    @staticmethod
    def gpt_4_5_preview():
        configuration = {
            "model": {
                "field": "drop",
                "default": "gpt-4.5-preview",
                "level": 1
            },
            "creativity_level": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.1,
                "default": 0,
                "level": 2
            },
            "max_tokens": {
                "field": "slider",
                "min": 256,
                "max": 16384,
                "step": 1,
                "default": 256,
                "level": 2
            },
            "probability_cutoff": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 1,
                "level": 2
            },
            "log_probability": {
                "field": "boolean",
                "default": False,
                "level": 0,
                "typeOf": "boolean"
            },
            "repetition_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "novelty_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "response_count": {
                "field": "number",
                "default": 1,
                "typeOf": "number",
                "level": 0
            },
            "stop": {
                "field": "text",
                "default": "",
                "level": 0
            },
            "stream": {
                "field": "boolean",
                "default": False,
                "level": 0,
                "typeOf": "boolean"
            },
            "tools": {
                "field": "array",
                "level": 0,
                "default": [],
                "typeOf": "array"
            },
            "tool_choice": {
                "field": "dropdown",
                "options" : ["auto", "none", "required"],
                "default": "auto",
                "level": 0,
                "typeOf": "string"
            },
            "response_type": {
                "field": "select",
                "options" : [{"type" : "text"},{"type" : "json_object"},{"type" : "json_schema"}],
                "default": {
                "type" : "text",
                },
                "level": 0
            },
            "vision": {
                "support": True,
                 "level": 0,
                 "default" : False
            },
            "parallel_tool_calls": {
                "field": "boolean",
                "default": True,
                "level": 0,
                "typeOf": "boolean"  
            }
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.prompt_tokens",
                "completion_tokens": "usage.completion_tokens",
                "total_tokens": "usage.total_tokens",
                "cached_tokens": "usage.prompt_tokens_details.cached_tokens",
                "total_cost": {
                    "input_cost": 2.50,
                    "output_cost": 10.00,
                    "cached_cost": 1.25
                }
            }],
            "message": "choices[0].message.content",
            "tools": "choices[0].message.tool_calls",
            "assistant": "choices[0].message",
            "id": "id"
        }
        inputConfig = {
            "system": {
                "role": "system",
                "content": "",
                "contentKey": "content",
                "type": "json"
            },
            "content_location": "prompt[0].content"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }
    
    @staticmethod
    def gpt_4o_2024_08_06():
        configuration = {
            "model": {
                "field": "drop",
                "default": "gpt-4o-2024-08-06",
                "level": 1
            },
            "creativity_level": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.1,
                "default": 0,
                "level": 2
            },
            "max_tokens": {
                "field": "slider",
                "min": 256,
                "max": 16384,
                "step": 1,
                "default": 256,
                "level": 2
            },
            "probability_cutoff": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 1,
                "level": 2
            },
            "log_probability": {
                "field": "boolean",
                "default": False,
                "level": 0,
                "typeOf": "boolean"
            },
            "repetition_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "novelty_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "response_count": {
                "field": "number",
                "default": 1,
                "typeOf": "number",
                "level": 0
            },
            "stop": {
                "field": "text",
                "default": "",
                "level": 0
            },
            "stream": {
                "field": "boolean",
                "default": False,
                "level": 0,
                "typeOf": "boolean"
            },
            "tools": {
                "field": "array",
                "level": 0,
                "default": [],
                "typeOf": "array"
            },
            "tool_choice": {
                "field": "dropdown",
                "options" : ["auto", "none", "required"],
                "default": "auto",
                "level": 0,
                "typeOf": "string"
            },
            "response_type": {
                "field": "select",
                "options" : [{"type" : "text"},{"type" : "json_object"},{"type" : "json_schema"}],
                "default": {
                "type" : "text",
                },
                "level": 0
            },
            "vision": {
                "support": True,
                 "level": 0,
                 "default" : False
            },
            "parallel_tool_calls": {
                "field": "boolean",
                "default": True,
                "level": 0,
                "typeOf": "boolean"  
            }
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.prompt_tokens",
                "completion_tokens": "usage.completion_tokens",
                "total_tokens": "usage.total_tokens",
                "cached_tokens": "usage.prompt_tokens_details.cached_tokens",
                "total_cost": {
                    "input_cost": 2.50,
                    "output_cost": 10.00,
                    "cached_cost": 1.25
                }
            }],
            "message": "choices[0].message.content",
            "tools": "choices[0].message.tool_calls",
            "assistant": "choices[0].message",
            "id": "id"
        }
        inputConfig = {
            "system": {
                "role": "system",
                "content": "",
                "contentKey": "content",
                "type": "json"
            },
            "content_location": "prompt[0].content"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }
    @staticmethod
    def chatgpt_4o_latest():
        configuration = {
            "model": {
                "field": "drop",
                "default": "chatgpt-4o-latest",
                "level": 1
            },
            "creativity_level": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.1,
                "default": 0,
                "level": 2
            },
            "max_tokens": {
                "field": "slider",
                "min": 256,
                "max": 16384,
                "step": 1,
                "default": 256,
                "level": 2
            },
            "probability_cutoff": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 1,
                "level": 2
            },
            "log_probability": {
                "field": "boolean",
                "default": False,
                "level": 0,
                "typeOf": "boolean"
            },
            "repetition_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "novelty_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "response_count": {
                "field": "number",
                "default": 1,
                "typeOf": "number",
                "level": 0
            },
            "stop": {
                "field": "text",
                "default": "",
                "level": 0
            },
            "stream": {
                "field": "boolean",
                "default": False,
                "level": 0,
                "typeOf": "boolean"
            },
            "response_type": {
                "field": "select",
                "options" : [{"type" : "text"},{"type" : "json_object"},{"type" : "json_schema"}],
                "default": {
                "type" : "text",
                },
                "level": 0
            },
            "vision": {
                "support": True,
                 "level": 0,
                 "default" : False
            },
            "parallel_tool_calls": {
                "field": "boolean",
                "default": True,
                "level": 0,
                "typeOf": "boolean"  
            },
            "specification" : {
                "input_cost": 5.00,
                "output_cost": 15.00,
                "description" : [""],
                "knowledge_cutoff" : "",
                "usecase" : [""]
            }
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.prompt_tokens",
                "completion_tokens": "usage.completion_tokens",
                "total_tokens": "usage.total_tokens",
                "total_cost": {
                    "input_cost": 5.00,
                    "output_cost": 15.00
                }
            }],
            "message": "choices[0].message.content",
            "tools": "choices[0].message.tool_calls",
            "assistant": "choices[0].message",
            "id": "id"
        }
        inputConfig = {
            "system": {
                "role": "system",
                "content": "",
                "contentKey": "content",
                "type": "json"
            },
            "content_location": "prompt[0].content"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }
    @staticmethod
    def gpt_4o_mini():
        configuration = {
            "model": {
                "field": "dropdown",
                "default": "gpt-4o-mini",
                "level": 1
            },
            "creativity_level": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.1,
                "default": 0,
                "level": 2
            },
            "max_tokens": {
                "field": "slider",
                "min": 256,
                "max": 8192,
                "step": 1,
                "default": 256,
                "level": 2
            },
            "probability_cutoff": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 1,
                "level": 2
            },
            "log_probability": {
                "field": "boolean",
                "default": False,
                "level": 0
            },
            "repetition_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "novelty_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "response_count": {
                "field": "number",
                "default": 1,
                "level": 0
            },
            "stop": {
                "field": "text",
                "default": "",
                "level": 0
            },
            "stream": {
                "field": "boolean",
                "default": False,
                "level": 0
            },
            "tools": {
                "field": "array",
                "level": 0,
                "default": []
            },
            "tool_choice": {
                "field": "dropdown",
                "options" : ["auto", "none", "required"],
                "default": "auto",
                "level": 0
            },
             "type" : {
                "default" : ["chat"]
            },
            "response_type": {
                "field": "select",
                "options" : [{"type" : "text"},{"type" : "json_object"}],
                "default": {
                "type" : "text",
                },
                "level": 0
            },
            "vision": {
                "support": True,
                 "level": 0,
                 "default" : False
            },
            "parallel_tool_calls": {
                "field": "boolean",
                "default": True,
                "level": 0,
                "typeOf": "boolean"  
            },
            "specification" : {
                "input_cost": 0.150,
                "output_cost": 0.600,
                "description" : "GPT-4o mini (“o” for “omni”) is a fast, affordable small model for focused tasks. It accepts both text and image inputs, and produces text outputs (including Structured Outputs). It is ideal for fine-tuning, and model outputs from a larger model like GPT-4o can be distilled to GPT-4o-mini to produce similar results at lower cost and latency",
                "knowledge_cutoff" : "Oct 01, 2023",
                "usecase" : [""]
            }
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.prompt_tokens",
                "completion_tokens": "usage.completion_tokens",
                "total_tokens": "usage.total_tokens",
                "cached_tokens": "usage.prompt_tokens_details.cached_tokens",
                "total_cost": {
                    "input_cost": 0.150,
                    "output_cost": 0.600,
                    "cached_cost": 0.075
                }
            }],
            "message": "choices[0].message.content",
            "tools": "choices[0].message.tool_calls",
            "assistant": "choices[0].message",
            "id": "id"
        }
        inputConfig = {
            "system": {
                "default": {
                    "role": "system",
                    "content": ""
                },
                "contentKey": "content",
                "type": "json"
            },
            "content_location": "prompt[0].content"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }
    
    @staticmethod
    def gpt_4o_mini_2024_07_18():
        configuration = {
            "model": {
                "field": "dropdown",
                "default": "gpt-4o-mini-2024-07-18",
                "level": 1
            },
            "creativity_level": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.1,
                "default": 0,
                "level": 2
            },
            "max_tokens": {
                "field": "slider",
                "min": 256,
                "max": 8192,
                "step": 1,
                "default": 256,
                "level": 2
            },
            "probability_cutoff": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 1,
                "level": 2
            },
            "log_probability": {
                "field": "boolean",
                "default": False,
                "level": 0
            },
            "repetition_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "novelty_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "response_count": {
                "field": "number",
                "default": 1,
                "level": 0
            },
            "stop": {
                "field": "text",
                "default": "",
                "level": 0
            },
            "stream": {
                "field": "boolean",
                "default": False,
                "level": 0
            },
            "tools": {
                "field": "array",
                "level": 0,
                "default": []
            },
            "tool_choice": {
                "field": "dropdown",
                "options" : ["auto", "none", "required"],
                "default": "auto",
                "level": 0
            },
             "type" : {
                "default" : ["chat"]
            },
            "response_type": {
                "field": "select",
                "options" : [{"type" : "text"},{"type" : "json_object"}],
                "default": {
                "type" : "text",
                },
                "level": 0
            },
            "vision": {
                "support": True,
                 "level": 0,
                 "default" : False
            },
            "parallel_tool_calls": {
                "field": "boolean",
                "default": True,
                "level": 0,
                "typeOf": "boolean"  
            },
            "specification" : {
                "input_cost":  0.150,
                "output_cost": 0.600,
                "description" : "GPT-4o-mini-2024-07-18 is a smaller, optimized version of GPT-4 released in July 2024. It offers improved efficiency with faster processing and lower resource usage. The model excels in natural language understanding and generation tasks. It’s ideal for applications with resource constraints while maintaining strong performance",
                "knowledge_cutoff" : "Oct 01, 2023",
                "usecase" : [""]
            }

        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.prompt_tokens",
                "completion_tokens": "usage.completion_tokens",
                "total_tokens": "usage.total_tokens",
                "cached_tokens": "usage.prompt_tokens_details.cached_tokens",
                "total_cost": {
                    "input_cost": 0.150,
                    "output_cost": 0.600,
                    "cached_cost" : 0.075
                }
            }],
            "message": "choices[0].message.content",
            "tools": "choices[0].message.tool_calls",
            "assistant": "choices[0].message",
            "id": "id"
        }
        inputConfig = {
            "system": {
                "default": {
                    "role": "system",
                    "content": ""
                },
                "contentKey": "content",
                "type": "json"
            },
            "content_location": "prompt[0].content"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }
    
    @staticmethod
    def o1():
        configuration = {
            "model": {
                "field": "drop",
                "default": "o1",
                "level": 1,
            },
            "tools": {
                "field": "array",
                "level": 0,
                "default": [],
                "typeOf": "array"
            },
            "tool_choice": {
                "field": "dropdown",
                "options" : ["auto", "none", "required"],
                "default": "auto",
                "level": 0,
                "typeOf": "string"
            },
            "response_type": {
                "field": "select",
                "options" : [{"type" : "text"},{"type" : "json_object"},{"type" : "json_schema"}],
                "default": {
                "type" : "text",
                },
                "level": 0
            },
            "vision": {
                "support": True,
                 "level": 0,
                 "default" : False
            },
            "max_tokens": {
                "field": "slider",
                "min": 1,
                "max": 100_000,
                "step": 1,
                "default": 256,
                "level": 2
            },
            "vision": {
                "support": True,
                 "level": 0,
                 "default" : False
            },
            "specification" : {
                "input_cost": 15.00,
                "output_cost": 60.00,
                "description" : "The o1 series of models are trained with reinforcement learning to perform complex reasoning. o1 models think before they answer, producing a long internal chain of thought before responding to the user.",
                "knowledge_cutoff" : "Oct 01, 2023",
                "usecase" : [""]
            },
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.prompt_tokens",
                "completion_tokens": "usage.completion_tokens",
                "total_tokens": "usage.total_tokens",
                "cached_tokens": "usage.prompt_tokens_details.cached_tokens",
                "reasoning_tokens": "usage.completion_tokens_details.cached_tokens",
                "total_cost": {
                    "input_cost": 15.00,
                    "output_cost": 60.00,
                    "cached_cost": 7.50
                }
            }],
            "message": "choices[0].message.content",
            "assistant": "choices[0].message",
            "tools": "choices[0].message.tool_calls",
            "id": "id"
        }
        inputConfig = {
            "system": {
                "role": "system",
                "content": "",
                "contentKey": "content",
                "type": "json"
            },
            "content_location": "prompt[0].content"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }
    
    @staticmethod
    def o3_mini():
        configuration = {
            "model": {
                "field": "drop",
                "default": "o3-mini",
                "level": 1,
            },
            "tools": {
                "field": "array",
                "level": 0,
                "default": [],
                "typeOf": "array"
            },
            "tool_choice": {
                "field": "text",
                "options" : ["auto", "none", "required"],
                "default": "auto",
                "level": 0,
                "typeOf": "string"
            },
            "response_type": {
                "field": "select",
                "options" : [{"type" : "text"},{"type" : "json_object"},{"type" : "json_schema"}],
                "default": {
                "type" : "text",
                },
                "level": 0
            }, 
            "max_tokens": {
                "field": "slider",
                "min": 256,
                "max": 100_000,
                "step": 1,
                "default": 256,
                "level": 2
            }
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.prompt_tokens",
                "completion_tokens": "usage.completion_tokens",
                "total_tokens": "usage.total_tokens",
                "cached_tokens": "usage.prompt_tokens_details.cached_tokens",
                "reasoning_tokens": "usage.completion_tokens_details.cached_tokens",
                "total_cost": {
                    "input_cost": 1.10,
                    "output_cost": 4.40,
                    "cached_cost": 0.55
                }
            }],
            "message": "choices[0].message.content",
            "assistant": "choices[0].message",
            "tools": "choices[0].message.tool_calls",
            "id": "id"
        }
        inputConfig = {
            "system": {
                "role": "system",
                "content": "",
                "contentKey": "content",
                "type": "json"
            },
            "content_location": "prompt[0].content"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }
    
    @staticmethod
    def o1_preview():
        configuration = {
            "model": {
                "field": "drop",
                "default": "o1-preview",
                "level": 1
            },
            "specification" : {
                "input_cost": 3.00,
                "output_cost": 12.00,
                "description" : "o3-mini is our newest small reasoning model, providing high intelligence at the same cost and latency targets of o1-mini. o3-mini supports key developer features, like Structured Outputs, function calling, and Batch API",
                "knowledge_cutoff" : "Oct 01, 2023",
                "usecase" : [""]
            },
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.prompt_tokens",
                "completion_tokens": "usage.completion_tokens",
                "total_tokens": "usage.total_tokens",
                "cached_tokens": "usage.prompt_tokens_details.cached_tokens",
                "reasoning_tokens": "usage.completion_tokens_details.cached_tokens",
                "total_cost": {
                    "input_cost": 15.00,
                    "output_cost": 60.00,
                    "cached_cost": 7.50
                }
            }],
            "message": "choices[0].message.content",
            "assistant": "choices[0].message",
            "id": "id"
        }
        inputConfig = {
            "system": {
                "role": "system",
                "content": "",
                "contentKey": "content",
                "type": "json"
            },
            "content_location": "prompt[0].content"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }
    

    @staticmethod
    def o1_mini():
        configuration = {
            "model": {
                "field": "drop",
                "default": "o1-mini",
                "level": 1
            },
            "encoding_format": {
                "field": "dropdown",
                "values": ["float", "base64"],
                "default": "float",
                "level": 2
            },
            "dimensions": {
                "field": "number",
                "level": 0
            },
            "type" : {
                "default" : ["embedding"]
            },
            "specification" : {
                "input_cost": "",
                "output_cost": "",
                "description" : "text-embedding-3-small is our improved, more performant version of our ada embedding model. Embeddings are a numerical representation of text that can be used to measure the relatedness between two pieces of text. Embeddings are useful for search, clustering, recommendations, anomaly detection, and classification tasks.",
                "knowledge_cutoff" : "",
                "usecase" : [""]
            },
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.prompt_tokens",
                "completion_tokens": "usage.completion_tokens",
                "total_tokens": "usage.total_tokens",
                "cached_tokens": "usage.prompt_tokens_details.cached_tokens",
                "reasoning_tokens": "usage.completion_tokens_details.cached_tokens",
                "total_cost": {
                    "input_cost": 3.00,
                    "output_cost": 12.00,
                    "cached_cost" : 1.50,
                }
            }],
            "message": "choices[0].message.content",
            "assistant": "choices[0].message",
            "id": "id"
        }
        inputConfig = {
            "system": {
                "role": "system",
                "content": "",
                "contentKey": "content",
                "type": "json"
            },
            "content_location": "prompt[0].content"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }
    
    @staticmethod
    def gpt_3_5_turbo_instruct():
        configuration = {
            "model": {
                "field": "drop",
                "default": "gpt-3.5-turbo-instruct",
                "level": 1
            },
            "additional_stop_sequences": {
                "field": "slider",
                "min": 1,
                "max": 20,
                "default": 1,
                "level": 2,
                "step": 1
            },
            "echo_input": {
                "field": "text",
                "default": False,
                "typeOf": "boolean",
                "level": 2
            },
            "repetition_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "log_probability": {
                "field": "boolean",
                "default": False,
                "level": 0
            },
            "max_tokens": {
                "field": "slider",
                "min": 256,
                "max": 4096,
                "step": 1,
                "default": 256,
                "level": 2
            },
            "response_count": {
                "field": "number",
                "default": 1,
                "level": 0
            },
            "novelty_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "seed": {
                "field": "number",
                "default": 0,
                "level": 0
            },
            "stop": {
                "field": "text",
                "default": "",
                "level": 0
            },
            "stream": {
                "field": "boolean",
                "default": False,
                "level": 0
            },
            "response_suffix": {
                "field": "text",
                "default": "",
                "level": 2
            },
            "creativity_level": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.1,
                "default": 0,
                "level": 2
            },
            "probability_cutoff": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 1,
                "level": 2
            },
            "response_type": {
                "field": "select",
                "options" : [{"type" : "text"},{"type" : "json_object"}],
                "default": {
                "type" : "text",
                },
                "level": 0
            },
            "type" :  {
                "default" : ["completion"]
            }
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.prompt_tokens",
                "completion_tokens": "usage.completion_tokens",
                "total_tokens": "usage.total_tokens",
                "total_cost": {
                    "input_cost": 1.50,
                    "output_cost": 2.00
                }
            }],
            "message": "choices[0].text",
            "assistant": "choices",
            "id": "id"
        }
        inputConfig = {
            "prompt": {
                "prompt": "",
                "contentKey": "prompt",
                "type": "text"
            },
            "content_location": "prompt"
        }
        chatmessage = {
            "chat": {
                "role": "user",
                "content": ""
            },
            "chatpath": "content"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig,
            "chatmessage": chatmessage
        }
    
    @staticmethod
    def gemini_1_5_pro():
        configuration = {
            "model": {
                "field": "drop",
                "default": "gemini-1.5-pro",
                "level": 1
            },
            "creativity_level": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.1,
                "default": 1,
                "level": 2
            },
            "token_selection_limit": {
                "field": "slider",
                "min": 1,
                "max": 40,
                "step": 1,
                "default": 40,
                "level": 2
            },
            "topP": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 1,
                "level": 2
            },
            "maxOutputTokens": {
                "field": "slider",
                "min": 1,
                "max": 8192,
                "step": 1,
                "default": 2048,
                "level": 0
            },
            "additional_stop_sequences": {
                "field": "text",
                "default": "",
                "level": 0
            },
            "type" : {
                "default" : ["completion","chat"]
            }
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.input_tokens",
                "output_tokens": "usage.output_tokens",
                "total_tokens": "usage.total_tokens",
                "total_cost": 0
            }],
            "message": "candidates[0].content.parts[0].text",
            "role": "model"
        }
        inputConfig = {
            "model": {
                "default": {
                    "role": "model",
                    "parts": [{
                        "text": ""
                    }]
                },
                "contentKey": "parts[0].text",
                "type": "json"
            },
            "content_location": "prompt"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }
    
    
    @staticmethod
    def gemini_pro():
        configuration = {
            "model": {
                "field": "drop",
                "default": "gemini-pro",
                "level": 1
            },
            "creativity_level": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.1,
                "default": 1,
                "level": 2
            },
            "token_selection_limit": {
                "field": "slider",
                "min": 1,
                "max": 40,
                "step": 1,
                "default": 40,
                "level": 2
            },
            "topP": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 1,
                "level": 2
            },
            "maxOutputTokens": {
                "field": "slider",
                "min": 1,
                "max": 30720,
                "step": 1,
                "default": 2048,
                "level": 0
            },
            "additional_stop_sequences": {
                "field": "text",
                "default": "",
                "level": 0
            },
             "type" : {
                "default" : ["completion","chat"]
            }
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.input_tokens",
                "output_tokens": "usage.output_tokens",
                "total_tokens": "usage.total_tokens",
                "total_cost": 0
            }],
            "message": "candidates[0].content.parts[0].text",
            "role": "model"
        }
        inputConfig = {
            "model": {
                "default": {
                    "role": "model",
                    "parts": [{
                        "text": ""
                    }]
                },
                "contentKey": "parts[0].text",
                "type": "json"
            },
            "content_location": "prompt"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }
    
    @staticmethod
    def gemini_1_5_Flash():
        configuration = {
            "model": {
                "field": "drop",
                "default": "gemini-1.5-Flash",
                "level": 1
            },
            "creativity_level": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.1,
                "default": 1,
                "level": 2
            },
            "token_selection_limit": {
                "field": "slider",
                "min": 1,
                "max": 40,
                "step": 1,
                "default": 40,
                "level": 2
            },
            "topP": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 1,
                "level": 2
            },
            "maxOutputTokens": {
                "field": "slider",
                "min": 1,
                "max": 8192,
                "step": 1,
                "default": 2048,
                "level": 0
            },
            "additional_stop_sequences": {
                "field": "text",
                "default": "",
                "level": 0
            },
             "type" : {
                "default" : ["completion","chat"]
            }
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.input_tokens",
                "output_tokens": "usage.output_tokens",
                "total_tokens": "usage.total_tokens",
                "total_cost": 0
            }],
            "message": "candidates[0].content.parts[0].text",
            "role": "model"
        }
        inputConfig = {
            "model": {
                "default": {
                    "role": "model",
                    "parts": [{
                        "text": ""
                    }]
                },
                "contentKey": "parts[0].text",
                "type": "json"
            },
            "content_location": "prompt"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }
    
    @staticmethod
    def gemini_1_0_pro():
        configuration = {
            "model": {
                "field": "drop",
                "default": "gemini-1.0-pro",
                "level": 1
            },
            "creativity_level": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.1,
                "default": 1,
                "level": 2
            },
            "token_selection_limit": {
                "field": "slider",
                "min": 1,
                "max": 40,
                "step": 1,
                "default": 40,
                "level": 2
            },
            "topP": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 1,
                "level": 2
            },
            "maxOutputTokens": {
                "field": "slider",
                "min": 1,
                "max": 8192,
                "step": 1,
                "default": 2048,
                "level": 0
            },
            "additional_stop_sequences": {
                "field": "text",
                "default": "",
                "level": 0
            },
             "type" : {
                "default" : ["completion","chat"]
            }
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.input_tokens",
                "output_tokens": "usage.output_tokens",
                "total_tokens": "usage.total_tokens",
                "total_cost": 0
            }],
            "message": "candidates[0].content.parts[0].text",
            "role": "model"
        }
        inputConfig = {
            "model": {
                "default": {
                    "role": "model",
                    "parts": [{
                        "text": ""
                    }]
                },
                "contentKey": "parts[0].text",
                "type": "json"
            },
            "content_location": "prompt"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }
    
    @staticmethod
    def gemini_1_0_pro_vision():
        configuration = {
            "model": {
                "field": "drop",
                "default": "gemini-1.0-pro-vision",
                "level": 1
            },
            "creativity_level": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.1,
                "default": 1,
                "level": 2
            },
            "token_selection_limit": {
                "field": "slider",
                "min": 1,
                "max": 40,
                "step": 1,
                "default": 40,
                "level": 2
            },
            "topP": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 1,
                "level": 2
            },
            "maxOutputTokens": {
                "field": "slider",
                "min": 1,
                "max": 4096,
                "step": 1,
                "default": 2048,
                "level": 0
            },
            "additional_stop_sequences": {
                "field": "text",
                "default": "",
                "level": 0
            },
             "type" : {
                "default" : ["completion","chat"]
            }
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.input_tokens",
                "output_tokens": "usage.output_tokens",
                "total_tokens": "usage.total_tokens",
                "total_cost": 0
            }],
            "message": "candidates[0].content.parts[0].text",
            "role": "model"
        }
        inputConfig = {
            "model": {
                "default": {
                    "role": "model",
                    "parts": [{
                        "text": ""
                    }]
                },
                "contentKey": "parts[0].text",
                "type": "json"
            },
            "content_location": "prompt"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }
    @staticmethod
    def claude_3_5_sonnet_20241022():
        configuration = {
            "model": {
                "field": "drop",
                "default": "claude-3-5-sonnet-20241022",
                "level": 1
            },
            "creativity_level": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 0,
                "level": 2
            },
            "max_tokens": {
                "field": "slider",
                "min": 1,
                "max": 8192,
                "step": 1,
                "default": 1046,
                "level": 2
            },
            "top_p": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 0.9,
                "level": 2
            },
            # "stream": {
            #     "field": "boolean",
            #     "default": False,
            #     "level": 0,
            #     "typeOf": "boolean"
            # },
            "tools": {
                "field": "array",
                "level": 0,
                "default": [],
                "typeOf": "array"
            },
            # "tool_choice": {
            #     "field": "text",
            #     "default": "auto",
            #     "level": 0,
            #     "typeOf": "string"
            # },
             "vision": {
                "support": True,
                 "level": 0,
                 "default" : False
            },
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.input_tokens",
                "completion_tokens": "usage.output_tokens",
                "cache_read_input_tokens": "usage.cache_read_input_tokens",
                "cache_creation_input_tokens": "usage.cache_creation_input_tokens",
                "total_cost": {
                    "input_cost": 3.00,
                    "output_cost": 15.00,
                    "caching_read_cost":0.30,
                    "caching_write_cost":3.75
                }
            }],
            "message": "content[0].text", # find from modelResponse
            "tools": "content[1].text", # find from functionResponse.modelResposne
            "assistant": "role",
            "id": "id"
        }
        inputConfig = {
            "system": {
                "role": "system",
                "content": "",
                "contentKey": "content",
                "type": "json"
            },
            "content_location": "prompt[0].content"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }
    
    @staticmethod
    def claude_3_5_sonnet_20240620():
        configuration = {
            "model": {
                "field": "drop",
                "default": "claude-3-5-sonnet-20240620",
                "level": 1
            },
            "creativity_level": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 0,
                "level": 2
            },
            "max_tokens": {
                "field": "slider",
                "min": 1,
                "max": 8192,
                "step": 1,
                "default": 1046,
                "level": 2
            },
            "top_p": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 0.9,
                "level": 2
            },
            # "stream": {
            #     "field": "boolean",
            #     "default": False,
            #     "level": 0,
            #     "typeOf": "boolean"
            # },
            "tools": {
                "field": "array",
                "level": 0,
                "default": [],
                "typeOf": "array"
            },
            # "tool_choice": {
            #     "field": "text",
            #     "default": "auto",
            #     "level": 0,
            #     "typeOf": "string"
            # },
             "vision": {
                "support": True,
                 "level": 0,
                 "default" : False
            },
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.input_tokens",
                "completion_tokens": "usage.output_tokens",
                "cache_read_input_tokens": "usage.cache_read_input_tokens",
                "cache_creation_input_tokens": "usage.cache_creation_input_tokens",
                "total_cost": {
                    "input_cost": 3.00,
                    "output_cost": 15.00,
                    "caching_read_cost":0.30,
                    "caching_write_cost":3.75
                }
            }],
            "message": "content[0].text", # find from modelResponse
            "tools": "content[1].text", # find from functionResponse.modelResposne
            "assistant": "role",
            "id": "id"
        }
        inputConfig = {
            "system": {
                "role": "system",
                "content": "",
                "contentKey": "content",
                "type": "json"
            },
            "content_location": "prompt[0].content"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }
    
    @staticmethod
    def claude_3_5_sonnet_latest():
        configuration = {
            "model": {
                "field": "drop",
                "default": "claude-3-5-sonnet-latest",
                "level": 1
            },
            "creativity_level": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 0,
                "level": 2
            },
            "max_tokens": {
                "field": "slider",
                "min": 1,
                "max": 8192,
                "step": 1,
                "default": 1046,
                "level": 2
            },
            "top_p": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 1,
                "level": 2
            },
            # "stream": {
            #     "field": "boolean",
            #     "default": False,
            #     "level": 0,
            #     "typeOf": "boolean"
            # },
            "tools": {
                "field": "array",
                "level": 0,
                "default": [],
                "typeOf": "array"
            },
            # "tool_choice": {
            #     "field": "text",
            #     "default": "auto",
            #     "level": 0,
            #     "typeOf": "string"
            # },
             "vision": {
                "support": True,
                 "level": 0,
                 "default" : False
            },
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.input_tokens",
                "completion_tokens": "usage.output_tokens",
                "cache_read_input_tokens": "usage.cache_read_input_tokens",
                "cache_creation_input_tokens": "usage.cache_creation_input_tokens",
                "total_cost": {
                    "input_cost": 3.00,
                    "output_cost": 15.00,
                    "caching_read_cost":0.30,
                    "caching_write_cost":3.75
                }
            }],
            "message": "content[0].text", # find from modelResponse
            "tools": "content[1].text", # find from functionResponse.modelResposne
            "assistant": "role",
            "id": "id"
        }
        inputConfig = {
            "system": {
                "role": "system",
                "content": "",
                "contentKey": "content",
                "type": "json"
            },
            "content_location": "prompt[0].content"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }
        
    @staticmethod
    def claude_3_opus_20240229(): 
        configuration = {
            "model": {
                "field": "drop",
                "default": "claude-3-opus-20240229",
                "level": 1
            },
            "creativity_level": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 0,
                "level": 2
            },
            "max_tokens": {
                "field": "slider",
                "min": 1,
                "max": 4096,
                "step": 1,
                "default": 1046,
                "level": 2
            },
            "top_p": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 0.9,
                "level": 2
            },
            # "stream": {
            #     "field": "boolean",
            #     "default": False,
            #     "level": 0,
            #     "typeOf": "boolean"
            # },
            "tools": {
                "field": "array",
                "level": 0,
                "default": [],
                "typeOf": "array"
            },
            # "tool_choice": {
            #     "field": "text",
            #     "default": "auto",
            #     "level": 0,
            #     "typeOf": "string"
            # },
             "vision": {
                "support": True,
                 "level": 0,
                 "default" : False
            },
        }
        outputConfig = {
        "usage": [{
                "prompt_tokens": "usage.input_tokens",
                "completion_tokens": "usage.output_tokens",
                "cache_read_input_tokens": "usage.cache_read_input_tokens",
                "cache_creation_input_tokens": "usage.cache_creation_input_tokens",
                "total_cost": {
                    "input_cost": 15.00,
                    "output_cost": 75.00,
                    "caching_read_cost":1.50,
                    "caching_write_cost":18.75
                }
            }],
            "message": "content[0].text",
            "tools": "content[1].type",
            "assistant": "role",
            "id": "id"
        }
        inputConfig = {
            "system": {
                "role": "system",
                "content": "",
                "contentKey": "content",
                "type": "json"
            },
            "content_location": "prompt[0].content"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }
    @staticmethod
    def claude_3_opus_latest(): 
        configuration = {
            "model": {
                "field": "drop",
                "default": "claude-3-opus-latest",
                "level": 1
            },
            "creativity_level": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 0,
                "level": 2
            },
            "max_tokens": {
                "field": "slider",
                "min": 1,
                "max": 4096,
                "step": 1,
                "default": 1046,
                "level": 2
            },
            "top_p": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 1,
                "level": 2
            },
            # "stream": {
            #     "field": "boolean",
            #     "default": False,
            #     "level": 0,
            #     "typeOf": "boolean"
            # },
            "tools": {
                "field": "array",
                "level": 0,
                "default": [],
                "typeOf": "array"
            },
            # "tool_choice": {
            #     "field": "text",
            #     "default": "auto",
            #     "level": 0,
            #     "typeOf": "string"
            # },
             "vision": {
                "support": True,
                 "level": 0,
                 "default" : False
            },
        }
        outputConfig = {
        "usage": [{
                "prompt_tokens": "usage.input_tokens",
                "completion_tokens": "usage.output_tokens",
                "cache_read_input_tokens": "usage.cache_read_input_tokens",
                "cache_creation_input_tokens": "usage.cache_creation_input_tokens",
                "total_cost": {
                    "input_cost": 15.00,
                    "output_cost": 75.00,
                    "caching_read_cost":1.50,
                    "caching_write_cost":18.75
                }
            }],
            "message": "content[0].text",
            "tools": "content[1].type",
            "assistant": "role",
            "id": "id"
        }
        inputConfig = {
            "system": {
                "role": "system",
                "content": "",
                "contentKey": "content",
                "type": "json"
            },
            "content_location": "prompt[0].content"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }
        
    @staticmethod
    def claude_3_sonnet_20240229(): 
        configuration = {
            "model": {
                "field": "drop",
                "default": "claude-3-sonnet-20240229",
                "level": 1
            },
            "creativity_level": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 0,
                "level": 2
            },
            "max_tokens": {
                "field": "slider",
                "min": 1,
                "max": 4096,
                "step": 1,
                "default": 1046,
                "level": 2
            },
            "top_p": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 0.9,
                "level": 2
            },
            # "stream": {
            #     "field": "boolean",
            #     "default": False,
            #     "level": 0,
            #     "typeOf": "boolean"
            # },
            "tools": {
                "field": "array",
                "level": 0,
                "default": [],
                "typeOf": "array"
            },
            # "tool_choice": {
            #     "field": "text",
            #     "default": "auto",
            #     "level": 0,
            #     "typeOf": "string"
            # },
             "vision": {
                "support": True,
                 "level": 0,
                 "default" : False
            },
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.input_tokens",
                "completion_tokens": "usage.output_tokens",
                "total_cost": {
                    "input_cost": 3.00,
                    "output_cost": 15.00
                }
            }],
            "message": "content[0].text",
            "tools": "content[1].type",
            "assistant": "role",
            "id": "id"
        }
        inputConfig = {
            "system": {
                "role": "system",
                "content": "",
                "contentKey": "content",
                "type": "json"
            },
            "content_location": "prompt[0].content"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }
    
    @staticmethod
    def claude_3_haiku_20240307(): 
        configuration = {
            "model": {
                "field": "drop",
                "default": "claude-3-haiku-20240307",
                "level": 1
            },
            "creativity_level": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 0,
                "level": 2
            },
            "max_tokens": {
                "field": "slider",
                "min": 1,
                "max": 4096,
                "step": 1,
                "default": 1046,
                "level": 2
            },
            "top_p": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 0.9,
                "level": 2
            },
            # "stream": {
            #     "field": "boolean",
            #     "default": False,
            #     "level": 0,
            #     "typeOf": "boolean"
            # },
            "tools": {
                "field": "array",
                "level": 0,
                "default": [],
                "typeOf": "array"
            },
            # "tool_choice": {
            #     "field": "text",
            #     "default": "auto",
            #     "level": 0,
            #     "typeOf": "string"
            # },
             "vision": {
                "support": True,
                 "level": 0,
                 "default" : False
            },
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.input_tokens",
                "completion_tokens": "usage.output_tokens",
                "cache_read_input_tokens": "usage.cache_read_input_tokens",
                "cache_creation_input_tokens": "usage.cache_creation_input_tokens",
                "total_cost": {
                    "input_cost": 0.25,
                    "output_cost": 1.25,
                    "caching_read_cost":0.03,
                    "caching_write_cost":0.30
                }
            }],
            "message": "content[0].text",
            "tools": "content[1].type",
            "assistant": "role",
            "id": "id"
        }
        inputConfig = {
            "system": {
                "role": "system",
                "content": "",
                "contentKey": "content",
                "type": "json"
            },
            "content_location": "prompt[0].content"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }
    @staticmethod
    def claude_3_5_haiku_20241022(): 
        configuration = {
            "model": {
                "field": "drop",
                "default": "claude-3-5-haiku-20241022",
                "level": 1
            },
            "creativity_level": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 0,
                "level": 2
            },
            "max_tokens": {
                "field": "slider",
                "min": 1,
                "max": 4096,
                "step": 1,
                "default": 1046,
                "level": 2
            },
            "top_p": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 1,
                "level": 2
            },
            # "stream": {
            #     "field": "boolean",
            #     "default": False,
            #     "level": 0,
            #     "typeOf": "boolean"
            # },
            "tools": {
                "field": "array",
                "level": 0,
                "default": [],
                "typeOf": "array"
            },
            # "tool_choice": {
            #     "field": "text",
            #     "default": "auto",
            #     "level": 0,
            #     "typeOf": "string"
            # },
             "vision": {
                "support": True,
                 "level": 0,
                 "default" : False
            },
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.input_tokens",
                "completion_tokens": "usage.output_tokens",
                "cache_read_input_tokens": "usage.cache_read_input_tokens",
                "cache_creation_input_tokens": "usage.cache_creation_input_tokens",
                "total_cost": {
                    "input_cost": 0.80,
                    "output_cost": 4.00,
                    "caching_read_cost":0.08,
                    "caching_write_cost":1.00
                }
            }],
            "message": "content[0].text",
            "tools": "content[1].type",
            "assistant": "role",
            "id": "id"
        }
        inputConfig = {
            "system": {
                "role": "system",
                "content": "",
                "contentKey": "content",
                "type": "json"
            },
            "content_location": "prompt[0].content"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }

    @staticmethod
    def claude_3_7_sonnet_latest(): 
        configuration = {
            "model": {
                "field": "drop",
                "default": "claude-3-7-sonnet-latest",
                "level": 1
            },
            "creativity_level": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 0,
                "level": 2
            },
            "max_tokens": {
                "field": "slider",
                "min": 1,
                "max": 8192,
                "step": 1,
                "default": 1046,
                "level": 2
            },
            "top_p": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 0.9,
                "level": 2
            },
            # "stream": {
            #     "field": "boolean",
            #     "default": False,
            #     "level": 0,
            #     "typeOf": "boolean"
            # },
            "tools": {
                "field": "array",
                "level": 0,
                "default": [],
                "typeOf": "array"
            },
            # "tool_choice": {
            #     "field": "text",
            #     "default": "auto",
            #     "level": 0,
            #     "typeOf": "string"
            # },
             "vision": {
                "support": True,
                 "level": 0,
                 "default" : False
            },
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.input_tokens",
                "completion_tokens": "usage.output_tokens",
                "total_cost": {
                    "input_cost": 3.00,
                    "output_cost": 15.00
                }
            }],
            "message": "content[0].text",
            "tools": "content[1].type",
            "assistant": "role",
            "id": "id"
        }
        inputConfig = {
            "system": {
                "role": "system",
                "content": "",
                "contentKey": "content",
                "type": "json"
            },
            "content_location": "prompt[0].content"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }

    @staticmethod
    def llama_3_3_70b_versatile():
        configuration = {
            "model": {
                "field": "drop",
                "default": "llama-3.3-70b-versatile",
                "level": 1
            },
            "creativity_level": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.1,
                "default": 0,
                "level": 2
            },
            "max_tokens": {
                "field": "slider",
                "min": 1,
                "max": 32768,
                "step": 1,
                "default": 256,
                "level": 2
            },
            "probability_cutoff": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 1,
                "level": 2
            },
            "log_probability": {
                "field": "boolean",
                "default": False,
                "level": 0,
                "typeOf": "boolean"
            },
            "repetition_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "novelty_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "response_count": {
                "field": "number",
                "default": 1,
                "typeOf": "number",
                "level": 0
            },
            "stop": {
                "field": "text",
                "default": "",
                "level": 0
            },
            "stream": {
                "field": "boolean",
                "default": False,
                "level": 0,
                "typeOf": "boolean"
            },
            "tools": {
                "field": "array",
                "level": 0,
                "default": [],
                "typeOf": "array"
            },
            "tool_choice": {
                "field": "dropdown",
                "options" : ["auto", "none", "required"],
                "default": "auto",
                "level": 0,
                "typeOf": "string"
            },
            "response_type": {
                "field": "select",
                "options" : [{"type" : "text"},{"type" : "json_object"}],
                "default": {
                "type" : "text",
                },
                "level": 0
            }
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.prompt_tokens",
                "completion_tokens": "usage.completion_tokens",
                "total_tokens": "usage.total_tokens",
                "total_cost": {
                    "input_cost": 0.59,
                    "output_cost": 0.79
                }
            }],
            "message": "choices[0].message.content",
            "tools": "choices[0].message.tool_calls",
            "assistant": "choices[0].message",
            "id": "id"
        }
        inputConfig = {
            "system": {
                "role": "system",
                "content": "",
                "contentKey": "content",
                "type": "json"
            },
            "content_location": "prompt[0].content"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }
    
    @staticmethod
    def llama_3_1_8b_instant():
        configuration = {
            "model": {
                "field": "drop",
                "default": "llama-3.1-8b-instant",
                "level": 1
            },
            "creativity_level": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.1,
                "default": 0,
                "level": 2
            },
            "max_tokens": {
                "field": "slider",
                "min": 1,
                "max": 8000,
                "step": 1,
                "default": 256,
                "level": 2
            },
            "probability_cutoff": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 1,
                "level": 2
            },
            "log_probability": {
                "field": "boolean",
                "default": False,
                "level": 0,
                "typeOf": "boolean"
            },
            "repetition_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "novelty_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "response_count": {
                "field": "number",
                "default": 1,
                "typeOf": "number",
                "level": 0
            },
            "stop": {
                "field": "text",
                "default": "",
                "level": 0
            },
            "stream": {
                "field": "boolean",
                "default": False,
                "level": 0,
                "typeOf": "boolean"
            },
            "tools": {
                "field": "array",
                "level": 0,
                "default": [],
                "typeOf": "array"
            },
            "tool_choice": {
                "field": "dropdown",
                "options" : ["auto", "none", "required"],
                "default": "auto",
                "level": 0,
                "typeOf": "string"
            },
            "response_type": {
                "field": "select",
                "options" : [{"type" : "text"},{"type" : "json_object"}],
                "default": {
                "type" : "text",
                },
                "level": 0
            }
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.prompt_tokens",
                "completion_tokens": "usage.completion_tokens",
                "total_tokens": "usage.total_tokens",
                "total_cost": {
                    "input_cost": 0.05,
                    "output_cost": 0.08
                }
            }],
            "message": "choices[0].message.content",
            "tools": "choices[0].message.tool_calls",
            "assistant": "choices[0].message",
            "id": "id"
        }
        inputConfig = {
            "system": {
                "role": "system",
                "content": "",
                "contentKey": "content",
                "type": "json"
            },
            "content_location": "prompt[0].content"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }
    
    @staticmethod
    def llama3_70b_8192():
        configuration = {
            "model": {
                "field": "drop",
                "default": "llama3-70b-8192",
                "level": 1
            },
            "creativity_level": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.1,
                "default": 0,
                "level": 2
            },
            "max_tokens": {
                "field": "slider",
                "min": 1,
                "max": 8192,
                "step": 1,
                "default": 256,
                "level": 2
            },
            "probability_cutoff": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 1,
                "level": 2
            },
            "log_probability": {
                "field": "boolean",
                "default": False,
                "level": 0,
                "typeOf": "boolean"
            },
            "repetition_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "novelty_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "response_count": {
                "field": "number",
                "default": 1,
                "typeOf": "number",
                "level": 0
            },
            "stop": {
                "field": "text",
                "default": "",
                "level": 0
            },
            "stream": {
                "field": "boolean",
                "default": False,
                "level": 0,
                "typeOf": "boolean"
            },
            "tools": {
                "field": "array",
                "level": 0,
                "default": [],
                "typeOf": "array"
            },
            "tool_choice": {
                "field": "dropdown",
                "options" : ["auto", "none", "required"],
                "default": "auto",
                "level": 0,
                "typeOf": "string"
            },
            "response_type": {
                "field": "select",
                "options" : [{"type" : "text"},{"type" : "json_object"}],
                "default": {
                "type" : "text",
                },
                "level": 0
            }
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.prompt_tokens",
                "completion_tokens": "usage.completion_tokens",
                "total_tokens": "usage.total_tokens",
                "total_cost": {
                    "input_cost": 0.59,
                    "output_cost": 0.79
                }
            }],
            "message": "choices[0].message.content",
            "tools": "choices[0].message.tool_calls",
            "assistant": "choices[0].message",
            "id": "id"
        }
        inputConfig = {
            "system": {
                "role": "system",
                "content": "",
                "contentKey": "content",
                "type": "json"
            },
            "content_location": "prompt[0].content"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }
    
    @staticmethod
    def qwen_2_5_coder_32b():
        configuration = {
            "model": {
                "field": "drop",
                "default": "qwen-2.5-coder-32b",
                "level": 1
            },
            "tools": {
                "field": "array",
                "level": 0,
                "default": [],
                "typeOf": "array"
            },
            "tool_choice": {
                "field": "dropdown",
                "options" : ["auto", "none", "required"],
                "default": "auto",
                "level": 0,
                "typeOf": "string"
            },
            "response_type": {
                "field": "select",
                "options" : [{"type" : "text"},{"type" : "json_object"}],
                "default": {
                "type" : "text",
                },
                "level": 0
            }
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.prompt_tokens",
                "completion_tokens": "usage.completion_tokens",
                "total_tokens": "usage.total_tokens",
                "total_cost": {
                    "input_cost": 0.05,
                    "output_cost": 0.08
                }
            }],
            "message": "choices[0].message.content",
            "tools": "choices[0].message.tool_calls",
            "assistant": "choices[0].message",
            "id": "id"
        }
        inputConfig = {
            "system": {
                "role": "system",
                "content": "",
                "contentKey": "content",
                "type": "json"
            },
            "content_location": "prompt[0].content"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }
    
    @staticmethod
    def qwen_2_5_32b():
        configuration = {
            "model": {
                "field": "drop",
                "default": "qwen-2.5-32b",
                "level": 1
            },
            "tools": {
                "field": "array",
                "level": 0,
                "default": [],
                "typeOf": "array"
            },
            "tool_choice": {
                "field": "dropdown",
                "options" : ["auto", "none", "required"],
                "default": "auto",
                "level": 0,
                "typeOf": "string"
            },
            "response_type": {
                "field": "select",
                "options" : [{"type" : "text"},{"type" : "json_object"}],
                "default": {
                "type" : "text",
                },
                "level": 0
            }
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.prompt_tokens",
                "completion_tokens": "usage.completion_tokens",
                "total_tokens": "usage.total_tokens",
                "total_cost": {
                    "input_cost": 0.05,
                    "output_cost": 0.08
                }
            }],
            "message": "choices[0].message.content",
            "tools": "choices[0].message.tool_calls",
            "assistant": "choices[0].message",
            "id": "id"
        }
        inputConfig = {
            "system": {
                "role": "system",
                "content": "",
                "contentKey": "content",
                "type": "json"
            },
            "content_location": "prompt[0].content"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }
    
    @staticmethod
    def deepseek_r1_distill_qwen_32b():
        configuration = {
            "model": {
                "field": "drop",
                "default": "deepseek-r1-distill-qwen-32b",
                "level": 1
            },
            "max_tokens": {
                "field": "slider",
                "min": 1,
                "max": 16384,
                "step": 1,
                "default": 256,
                "level": 2
            },
            "tools": {
                "field": "array",
                "level": 0,
                "default": [],
                "typeOf": "array"
            },
            "tool_choice":{
                "field": "dropdown",
                "options" : ["auto", "none", "required"],
                "default": "auto",
                "level": 0,
                "typeOf": "string"
            },
            "response_type": {
                "field": "select",
                "options" : [{"type" : "text"},{"type" : "json_object"}],
                "default": {
                "type" : "text",
                },
                "level": 0
            }
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.prompt_tokens",
                "completion_tokens": "usage.completion_tokens",
                "total_tokens": "usage.total_tokens",
                "total_cost": {
                    "input_cost": 0.05,
                    "output_cost": 0.08
                }
            }],
            "message": "choices[0].message.content",
            "tools": "choices[0].message.tool_calls",
            "assistant": "choices[0].message",
            "id": "id"
        }
        inputConfig = {
            "system": {
                "role": "system",
                "content": "",
                "contentKey": "content",
                "type": "json"
            },
            "content_location": "prompt[0].content"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }
    
    @staticmethod
    def deepseek_r1_distill_llama_70b_specdec():
        configuration = {
            "model": {
                "field": "drop",
                "default": "deepseek-r1-distill-llama-70b-specdec",
                "level": 1
            },
            "max_tokens": {
                "field": "slider",
                "min": 1,
                "max": 16384,
                "step": 1,
                "default": 256,
                "level": 2
            },
            "tools": {
                "field": "array",
                "level": 0,
                "default": [],
                "typeOf": "array"
            },
            "tool_choice": {
                "field": "dropdown",
                "options" : ["auto", "none", "required"],
                "default": "auto",
                "level": 0,
                "typeOf": "string"
            },
            "response_type": {
                "field": "select",
                "options" : [{"type" : "text"},{"type" : "json_object"}],
                "default": {
                "type" : "text",
                },
                "level": 0
            }
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.prompt_tokens",
                "completion_tokens": "usage.completion_tokens",
                "total_tokens": "usage.total_tokens",
                "total_cost": {
                    "input_cost": 0.05,
                    "output_cost": 0.08
                }
            }],
            "message": "choices[0].message.content",
            "tools": "choices[0].message.tool_calls",
            "assistant": "choices[0].message",
            "id": "id"
        }
        inputConfig = {
            "system": {
                "role": "system",
                "content": "",
                "contentKey": "content",
                "type": "json"
            },
            "content_location": "prompt[0].content"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }
    
    @staticmethod
    def deepseek_r1_distill_llama_70b():
        configuration = {
            "model": {
                "field": "drop",
                "default": "deepseek-r1-distill-llama-70b",
                "level": 1
            },
            "tools": {
                "field": "array",
                "level": 0,
                "default": [],
                "typeOf": "array"
            },
            "tool_choice": {
                "field": "dropdown",
                "options" : ["auto", "none", "required"],
                "default": "auto",
                "level": 0,
                "typeOf": "string"
            },
            "response_type": {
                "field": "select",
                "options" : [{"type" : "text"},{"type" : "json_object"}],
                "default": {
                "type" : "text",
                },
                "level": 0
            }
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.prompt_tokens",
                "completion_tokens": "usage.completion_tokens",
                "total_tokens": "usage.total_tokens",
                "total_cost": {
                    "input_cost": 0.05,
                    "output_cost": 0.08
                }
            }],
            "message": "choices[0].message.content",
            "tools": "choices[0].message.tool_calls",
            "assistant": "choices[0].message",
            "id": "id"
        }
        inputConfig = {
            "system": {
                "role": "system",
                "content": "",
                "contentKey": "content",
                "type": "json"
            },
            "content_location": "prompt[0].content"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }
    
    @staticmethod
    def llama3_8b_8192():
        configuration = {
            "model": {
                "field": "drop",
                "default": "llama3-8b-8192",
                "level": 1
            },
            "creativity_level": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.1,
                "default": 0,
                "level": 2
            },
            "max_tokens": {
                "field": "slider",
                "min": 1,
                "max": 8192,
                "step": 1,
                "default": 256,
                "level": 2
            },
            "log_probability": {
                "field": "boolean",
                "default": False,
                "level": 0,
                "typeOf": "boolean"
            },
            "repetition_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "novelty_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "response_count": {
                "field": "number",
                "default": 1,
                "typeOf": "number",
                "level": 0
            },
            "stop": {
                "field": "text",
                "default": "",
                "level": 0
            },
            "stream": {
                "field": "boolean",
                "default": False,
                "level": 0,
                "typeOf": "boolean"
            },
            "tools": {
                "field": "array",
                "level": 0,
                "default": [],
                "typeOf": "array"
            },
            "tool_choice": {
                "field": "dropdown",
                "options" : ["auto", "none", "required"],
                "default": "auto",
                "level": 0,
                "typeOf": "string"
            },
            "response_type": {
                "field": "select",
                "options" : [{"type" : "text"},{"type" : "json_object"}],
                "default": {
                "type" : "text",
                },
                "level": 0
            }
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.prompt_tokens",
                "completion_tokens": "usage.completion_tokens",
                "total_tokens": "usage.total_tokens",
                "total_cost": {
                    "input_cost": 0.05,
                    "output_cost": 0.08
                }
            }],
            "message": "choices[0].message.content",
            "tools": "choices[0].message.tool_calls",
            "assistant": "choices[0].message",
            "id": "id"
        }
        inputConfig = {
            "system": {
                "role": "system",
                "content": "",
                "contentKey": "content",
                "type": "json"
            },
            "content_location": "prompt[0].content"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }
    
    @staticmethod
    def mixtral_8x7b_32768():
        configuration = {
            "model": {
                "field": "drop",
                "default": "mixtral-8x7b-32768",
                "level": 1
            },
            "creativity_level": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.1,
                "default": 0,
                "level": 2
            },
            "max_tokens": {
                "field": "slider",
                "min": 1,
                "max": 32768,
                "step": 1,
                "default": 256,
                "level": 2
            },
            "probability_cutoff": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 1,
                "level": 2
            },
            "log_probability": {
                "field": "boolean",
                "default": False,
                "level": 0,
                "typeOf": "boolean"
            },
            "repetition_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "novelty_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "response_count": {
                "field": "number",
                "default": 1,
                "typeOf": "number",
                "level": 0
            },
            "stop": {
                "field": "text",
                "default": "",
                "level": 0
            },
            "stream": {
                "field": "boolean",
                "default": False,
                "level": 0,
                "typeOf": "boolean"
            },
            "tools": {
                "field": "array",
                "level": 0,
                "default": [],
                "typeOf": "array"
            },
            "tool_choice": {
                "field": "dropdown",
                "options" : ["auto", "none", "required"],
                "default": "auto",
                "level": 0,
                "typeOf": "string"
            },
            "response_type": {
                "field": "select",
                "options" : [{"type" : "text"},{"type" : "json_object"}],
                "default": {
                "type" : "text",
                },
                "level": 0
            }
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.prompt_tokens",
                "completion_tokens": "usage.completion_tokens",
                "total_tokens": "usage.total_tokens",
                "total_cost": {
                    "input_cost": 0.24,
                    "output_cost": 0.24
                }
            }],
            "message": "choices[0].message.content",
            "tools": "choices[0].message.tool_calls",
            "assistant": "choices[0].message",
            "id": "id"
        }
        inputConfig = {
            "system": {
                "role": "system",
                "content": "",
                "contentKey": "content",
                "type": "json"
            },
            "content_location": "prompt[0].content"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }
    
    @staticmethod
    def gemma2_9b_it():
        configuration = {
            "model": {
                "field": "drop",
                "default": "gemma2-9b-it",
                "level": 1
            },
            "creativity_level": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.1,
                "default": 0,
                "level": 2
            },
            "max_tokens": {
                "field": "slider",
                "min": 1,
                "max": 8192,
                "step": 1,
                "default": 256,
                "level": 2
            },
            "probability_cutoff": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 1,
                "level": 2
            },
            "log_probability": {
                "field": "boolean",
                "default": False,
                "level": 0,
                "typeOf": "boolean"
            },
            "repetition_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "novelty_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "response_count": {
                "field": "number",
                "default": 1,
                "typeOf": "number",
                "level": 0
            },
            "stop": {
                "field": "text",
                "default": "",
                "level": 0
            },
            "stream": {
                "field": "boolean",
                "default": False,
                "level": 0,
                "typeOf": "boolean"
            },
            "tools": {
                "field": "array",
                "level": 0,
                "default": [],
                "typeOf": "array"
            },
            "tool_choice": {
                "field": "dropdown",
                "options" : ["auto", "none", "required"],
                "default": "auto",
                "level": 0,
                "typeOf": "string"
            },
            "response_type": {
                "field": "select",
                "options" : [{"type" : "text"},{"type" : "json_object"}],
                "default": {
                "type" : "text",
                },
                "level": 0
            }
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.prompt_tokens",
                "completion_tokens": "usage.completion_tokens",
                "total_tokens": "usage.total_tokens",
                "total_cost": {
                    "input_cost": 0.20,
                    "output_cost": 0.20
                }
            }],
            "message": "choices[0].message.content",
            "tools": "choices[0].message.tool_calls",
            "assistant": "choices[0].message",
            "id": "id"
        }
        inputConfig = {
            "system": {
                "role": "system",
                "content": "",
                "contentKey": "content",
                "type": "json"
            },
            "content_location": "prompt[0].content"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }
    
    @staticmethod
    def llama_guard_3_8b():
        configuration = {
            "model": {
                "field": "drop",
                "default": "llama-guard-3-8b",
                "level": 1
            },
            "creativity_level": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.1,
                "default": 0,
                "level": 2
            },
            "max_tokens": {
                "field": "slider",
                "min": 1,
                "max": 8192,
                "step": 1,
                "default": 256,
                "level": 2
            },
            "probability_cutoff": {
                "field": "slider",
                "min": 0,
                "max": 1,
                "step": 0.1,
                "default": 1,
                "level": 2
            },
            "log_probability": {
                "field": "boolean",
                "default": False,
                "level": 0,
                "typeOf": "boolean"
            },
            "repetition_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "novelty_penalty": {
                "field": "slider",
                "min": 0,
                "max": 2,
                "step": 0.01,
                "default": 0,
                "level": 2
            },
            "response_count": {
                "field": "number",
                "default": 1,
                "typeOf": "number",
                "level": 0
            },
            "stop": {
                "field": "text",
                "default": "",
                "level": 0
            },
            "stream": {
                "field": "boolean",
                "default": False,
                "level": 0,
                "typeOf": "boolean"
            },
            "tools": {
                "field": "array",
                "level": 0,
                "default": [],
                "typeOf": "array"
            },
            "tool_choice": {
                "field": "dropdown",
                "options" : ["auto", "none", "required"],
                "default": "auto",
                "level": 0,
                "typeOf": "string"
            },
            "response_type": {
                "field": "select",
                "options" : [{"type" : "text"},{"type" : "json_object"}],
                "default": {
                "type" : "text",
                },
                "level": 0
            }
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.prompt_tokens",
                "completion_tokens": "usage.completion_tokens",
                "total_tokens": "usage.total_tokens",
                "total_cost": {
                    "input_cost": 0.20,
                    "output_cost": 0.20
                }
            }],
            "message": "choices[0].message.content",
            "tools": "choices[0].message.tool_calls",
            "assistant": "choices[0].message",
            "id": "id"
        }
        inputConfig = {
            "system": {
                "role": "system",
                "content": "",
                "contentKey": "content",
                "type": "json"
            },
            "content_location": "prompt[0].content"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }
    
    @staticmethod
    def dall_e_3():
        configuration = {
            "model": {
                "field": "drop",
                "default": "dall-e-3",
                "level": 1
            },
            "size": {
                "field": "select",
                "options": ['1024x1024', '1024x1792', '1729x1024'],
                "default": '1024x1024',
                "level": 0
            },
            "quality": {
                "field": "select",
                "options": ['standard','hd'],
                "default": 'standard',
                "level": 0
            },
            "style": {
                "field": "select",
                "options": ['vivid', 'natural'],
                "default": 'vivid',
                "level": 0
            }
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.prompt_tokens",
                "completion_tokens": "usage.completion_tokens",
                "total_tokens": "usage.total_tokens",
                "total_cost": {
                    "input_cost": 0.01,
                    "output_cost": 0.03
                }
            }],
            "message": "choices[0].message.content",
            "tools": "choices[0].message.tool_calls",
            "assistant": "choices[0].message",
            "id": "id"
        }
        inputConfig = {
            "system": {
                "role": "system",
                "content": "",
                "contentKey": "content",
                "type": "json"
            },
            "content_location": "prompt[0].content"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }
    
    @staticmethod
    def dall_e_2():
        configuration = {
            "model": {
                "field": "drop",
                "default": "dall-e-2",
                "level": 1
            },
            "size": {
                "field": "select",
                "options": ['256x256', '512x512', '1024x1024'],
                "default": '1024x1024',
                "level": 0
            },
            "quality": {
                "field": "select",
                "options": ['standard','hd'],
                "default": 'standard',
                "level": 0
            },
            "specification" : {
                "input_cost":  0.01,
                "output_cost":  0.03,
                "description" : "DALL-E 2 is an AI model by OpenAI that generates high-quality images from text descriptions. It improves upon the original DALL-E with higher resolution and more accurate image generation. The model uses a neural network and transformer architecture. It is designed for creative applications, producing detailed visuals based on written prompts.",
                "knowledge_cutoff" : "",
                "usecase" : [""]
            },
            # "response_format": {
            #     "field": "select",
            #     "options": ['url', 'b64_json'],
            #     "default": 'url',
            #     "level": 0
            # }
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.prompt_tokens",
                "completion_tokens": "usage.completion_tokens",
                "total_tokens": "usage.total_tokens",
                "total_cost": {
                    "input_cost": 0.01,
                    "output_cost": 0.03
                }
            }],
            "message": "choices[0].message.content",
            "tools": "choices[0].message.tool_calls",
            "assistant": "choices[0].message",
            "id": "id"
        }
        inputConfig = {
            "system": {
                "role": "system",
                "content": "",
                "contentKey": "content",
                "type": "json"
            },
            "content_location": "prompt[0].content"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }
    
    @staticmethod
    def text_embedding_3_large():
        configuration = {
            "model": {
                "field": "dropdown",
                "default": "text-embedding-3-large",
                "level": 1
            },
            # "encoding_format": {
            #     "field": "select",
            #     "typeOf": "string",
            #     "level": 2
            # },
            # "dimensions": {
            #     "field": "number",
            #     "level": 0
            # },
             "type" : {
                "default" : ["embedding"]
            }
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.prompt_tokens",
                "total_tokens": "usage.total_tokens",
                "total_cost": 0.130
            }],
            "message": "data[0].embedding"
        }
        inputConfig = {
            "input": {
                "input": "",
                "contentKey": "input",
                "type": "text"
            },
            "content_location": "input"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }
    
    @staticmethod
    def text_embedding_3_small():
        configuration = {
            "model": {
                "field": "dropdown",
                "default": "text-embedding-3-small",
                "level": 1
            },
            "encoding_format": {
                "field": "select",
                "options": ["float", "base64"],
                "default": "float",
                "level": 2
            },
            # "dimensions": {
            #     "field": "number",
            #     "level": 0
            # },
            "type" : {
                "default" : ["embedding"]
            }
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.prompt_tokens",
                "total_tokens": "usage.total_tokens",
                "total_cost": 0.020
            }],
            "message": "data[0].embedding"
        }
        inputConfig = {
            "input": {
                "input": "",
                "contentKey": "input",
                "type": "text"
            },
            "content_location": "input"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }
    
    @staticmethod
    def text_embedding_ada_002():
        configuration = {
            "model": {
                "field": "dropdown",
                "default": "text-embedding-ada-002",
                "level": 1
            },
            "encoding_format": {
                "field": "select",
                "options": ["float", "base64"],
                "default": "float",
                "level": 2
            },
            "type" : {
                "default" : ["embedding"]
            }
        }
        outputConfig = {
            "usage": [{
                "prompt_tokens": "usage.prompt_tokens",
                "total_tokens": "usage.total_tokens",
                "total_cost": 0.100
            }],
            "message": "data[0].embedding"
        }
        inputConfig = {
            "input": {
                "input": "",
                "contentKey": "input",
                "type": "text"
            },
            "content_location": "input"
        }
        return {
            "configuration": configuration,
            "outputConfig": outputConfig,
            "inputConfig": inputConfig
        }