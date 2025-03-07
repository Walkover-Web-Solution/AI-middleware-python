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
                 "usecase": [
                "The gpt_3_5_turbo model can be used for building conversational agents and chatbots, providing fast and efficient responses in customer support scenarios.",
                "It can also be employed in content generation tools, helping writers produce high-quality blog posts, articles, and social media content."
               ]
            
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
                "usecase": [
                "The gpt_4 model can be used for complex problem-solving tasks, such as assisting in research and development for scientific studies or technical innovations.",
                "It can also be utilized in creating detailed, personalized content for marketing campaigns, including tailored emails, landing pages, and product descriptions."
                ]
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
                "usecase": [
               "The gpt_4_0613 model can be used for advanced data analysis and predictive modeling, assisting in decision-making processes for industries like finance or healthcare.",
               "It can also be employed in automated content creation for dynamic platforms, producing high-quality content that adapts to audience preferences and trends."
              ]

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
                 "usecase": [
                "The gpt_4_turbo model can be used to enhance customer service platforms by providing fast, accurate, and context-aware responses in live chat interactions.",
               "It can also be leveraged in content generation applications, delivering high-quality articles, reports, and creative writing pieces with improved speed and efficiency."
            ]

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
                "usecase": [
                "The chatgpt_4o_latest model can be used for developing advanced conversational agents that provide personalized customer service and support across multiple industries.",
                "It can also be applied in content creation tools, assisting writers by generating high-quality, context-aware content for blogs, articles, and marketing materials."
                ]
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
                "usecase": [
                 "The gpt_4o_mini model can be used in low-resource environments to perform text generation and summarization tasks in applications with constrained computational power.",
                 "It can also be applied in mobile applications to provide conversational AI capabilities, offering quick, responsive interactions for users on the go."
              ]

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
                "usecase": [
                "The gpt_4o_mini_2024_07_18 model can be used in resource-constrained devices, enabling efficient text generation and summarization for applications in fields like healthcare or finance.",
               "It can also serve in educational tools, providing personalized tutoring and feedback to students, especially in mobile or lightweight learning environments."
             ]
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
                "usecase": [
                "The o1 model can be used in real-time language translation applications, enabling seamless communication across different languages for global teams.",
               "It can also be applied in automated content moderation systems, detecting inappropriate language or harmful content across social media and online platforms."
              ]
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
            },
            "specification" : {
                "input_cost": 1.10,
                "output_cost": 4.40,
                "description" : "O3 Mini is likely a smaller, more optimized version of a model from the O3 series, designed for efficiency and faster processing. The Mini designation typically indicates a compact model with fewer parameters, making it suitable for environments with limited resources or for applications requiring lower latency.",
                "knowledge_cutoff" : "October 2023",
                "usecase": [
                "The o3_mini model can be used for efficient text classification tasks in applications with limited computational resources.",
                "It can also be utilized for real-time sentiment analysis on social media posts or product reviews with fast response times."
  ]
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
                 "usecase": [
                 "The o1_preview model can be used in early-stage content generation tools to create drafts for articles, blogs, or creative writing projects, streamlining the writing process.",
                  "It can also be applied in beta testing environments for AI-based chatbots, providing initial feedback and interactions to optimize conversational flows before full deployment."
                ]
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
            "specification" : {
                "input_cost": "",
                "output_cost": "",
                "description" : "text-embedding-3-small is our improved, more performant version of our ada embedding model. Embeddings are a numerical representation of text that can be used to measure the relatedness between two pieces of text. Embeddings are useful for search, clustering, recommendations, anomaly detection, and classification tasks.",
                "knowledge_cutoff" : "",
                "usecase": [
                "The o1_mini model can be used in mobile applications to provide lightweight and efficient natural language processing for tasks like text summarization and simple query responses.",
               "It can also serve in voice assistant devices, offering quick, accurate responses with lower computational requirements, ideal for devices with limited resources."
               ]
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
            "specification" : {
                "input_cost": 30.00,
                "output_cost": 60.00,
                "description" : "Claude 3.5 Sonnet is an advanced AI model designed for real-world software engineering tasks, featuring enhanced reasoning capabilities and state-of-the-art coding skills. It allows for sophisticated interaction with computer environments, making it suitable for a wide range of applications.",
                "knowledge_cutoff" : "June 2023 ",
                "usecase": [
                "The claude_3_5_sonnet_20241022 model can be used for generating creative poetry and sonnets, making it ideal for artistic content creation.",
                "It can also be employed for educational purposes, helping students analyze and understand classical poetry structures in literature classes."
                 ]
            }

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
            "specification" : {
                "input_cost": 3.00,
                "output_cost": 15.00,
                "description" : "LLaDE 3.5 Sonnet Latest is a version of the LLaDE (Large Language and Domain-specific Engine) model, optimized for creating and understanding sonnets. The 3.5 suggests it is an updated iteration, improving upon earlier versions with refined capabilities in natural language generation, particularly for structured forms like sonnets. This model is designed to generate poetry with a focus on artistic qualities, such as rhyme, meter, and thematic depth, making it well-suited for creative applications in literature",
                "knowledge_cutoff" : "April 2024",
                "usecase": [
                "The claude_3_5_sonnet_latest model can generate personalized sonnets based on user input, offering unique, creative experiences for digital storytelling.",
                "It can also be used in AI-driven writing assistants, helping writers compose poetic content or find inspiration for their creative projects."
  ]
            }

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
            "specification" : {
                "input_cost": 15.00,
                "output_cost": 75.00,
                "description" : "Claude 3 Opus 20240229 is a version of the Claude model, which is part of the family of language models developed by Anthropic. The Opus label suggests it may be an enhanced or specialized version of the model, possibly optimized for specific tasks or features. The 20240229 indicates its release date, February 29, 2024, making it a relatively recent update. This model is likely designed to offer improvements in areas like natural language understanding, generation, and safety, with a focus on producing high-quality",
                "knowledge_cutoff" : " August 2023",
                 "usecase": [
                 "The claude_3_opus_20240229 model can be used for advanced natural language understanding tasks, such as summarization and content extraction in legal or research documents.",
                 "It can also serve in customer support applications, providing more accurate and contextually aware responses in chatbot interactions."
                 ]
            }

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
            "specification" : {
                "input_cost": 15.00,
                "output_cost": 75.00,
                "description" : "Claude 3 Opus Latest is the most recent iteration of the Claude 3 model developed by Anthropic. The Opus designation suggests it may be a more advanced or specialized version, potentially optimized for improved performance, safety, and versatility in natural language tasks. The Latest label indicates that this version includes the most up-to-date features and enhancements, aiming to provide high-quality, contextually relevant, and reliable responses across a wide range of applications.",
                "knowledge_cutoff" : " October 2024",
                "usecase": [
                "The claude_3_opus_latest model can be utilized in real-time multilingual translation systems, offering fast and accurate translations across various languages.",
                "It can also enhance interactive voice assistants by enabling more natural, context-aware conversations and improved user engagement."
               ]
            }

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
            "specification" : {
                "input_cost": 3.00,
                "output_cost": 15.00,
                "description" : "Claude 3 Sonnet 20240229 is a version of the Claude 3 model developed by Anthropic, specifically tailored for generating and understanding sonnets. The Sonnet designation indicates that this model has been fine-tuned or optimized for tasks involving poetic forms, especially the structured and rhythmic style of sonnets",
                "knowledge_cutoff" : "",
                "usecase": [
                "The claude_3_sonnet_20240229 model can be used to generate artistic sonnets and poems, helping writers and creators with poetic content for books, blogs, or performances.",
                "It can also serve in educational settings to teach students about poetic structures, analyzing and generating examples of sonnets for literature courses."
  ]
            }

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
            "specification" : {
                "input_cost": 0.25,
                "output_cost": 1.25,
                "description" : "Claude 3 Haiku 20240307 is a version of the Claude 3 model developed by Anthropic, specifically optimized for generating and understanding haikus. The Haiku designation indicates that this model is fine-tuned to produce short, structured poems typically consisting of 3 lines with a 5-7-5 syllable pattern. The 20240307 refers to the release date, March 7, 2024. This version likely focuses on creating concise, evocative, and thematically rich haikus, adhering to the traditional style while maintaining the model's natural language generation capabilities",
                "knowledge_cutoff" : "",
                "usecase": [
                "The claude_3_haiku_20240307 model can be used to generate personalized haikus for greeting cards, gifts, or special occasions.",
                 "It can also serve in language learning apps, helping students explore the structure and beauty of traditional Japanese poetry while practicing creative writing."
                ]
            }

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
            "specification" : {
                "input_cost": 0.80,
                "output_cost":4.00,
                "description" : "Claude 3.5 Haiku 20241022 is an updated version of the Claude 3 model, specifically fine-tuned for generating and understanding haikus. The 3.5 indicates an iteration with improvements over previous versions, offering enhanced performance and accuracy in producing poetic forms. The Haiku label signifies that the model is optimized for generating 3-line poems with a 5-7-5 syllable structure",
                "knowledge_cutoff" : "July 2024",
                "usecase": [
                "The claude_3_5_haiku_20241022 model can be used to generate short, expressive haikus for creative writing projects, greeting cards, or social media posts.",
                "It can also be applied in wellness and meditation apps, providing calming haikus to help users relax and reflect during mindfulness sessions."
             ]
            }

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
            "specification" : {
                "input_cost": 3.00,
                "output_cost": 15.00,
                "description" : "Claude 3.7 Sonnet Latest is a refined version of the Claude 3 model, specifically optimized for generating and understanding sonnets. The 3.7 designation suggests it is a more advanced iteration, offering enhancements in performance, creativity, and accuracy. The Sonnet label indicates that it is fine-tuned to handle the structure, rhythm, and themes typically associated with sonnets",
                "knowledge_cutoff" : "October 2024",
                "usecase": [
                "The claude_3_7_sonnet_latest model can be used to create original and emotional sonnets, making it ideal for writers, poets, and content creators seeking inspiration.",
                "It can also be applied in digital marketing campaigns, generating poetic and captivating content for advertisements, social media posts, or branded experiences."
                ]
            }

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
            },
            "specification" : {
                "input_cost":  0.59,
                "output_cost":  0.79,
                "description" : "LLaMA 3.3 70B Versatile is a version of Meta's LLaMA (Large Language Model Meta AI) model, with 70 billion parameters. It is designed to be highly versatile, offering improvements in natural language processing tasks such as text generation, summarization, translation, and question answering. This model excels at understanding complex queries and producing coherent, contextually relevant responses. With its large scale, LLaMA 3.3 70B Versatile provides high-quality language understanding and generation across a wide range of applications.",
                "knowledge_cutoff" : "December 2023",
                 "usecase": [
                 "The llama_3_3_70b_versatile model can be used for large-scale natural language understanding tasks, such as document classification, sentiment analysis, and summarization in enterprise settings.",
                 "It can also be applied in advanced research applications, helping scientists and engineers generate insights from complex datasets and scientific papers."
                 ]
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
            },
            "specification" : {
                "input_cost": 0.05,
                "output_cost": 0.08,
                "description" : "LLaMA 3.1 8B Instant is a version of Meta’s LLaMA (Large Language Model Meta AI) with 8 billion parameters. It is designed to be highly efficient and capable of performing a variety of natural language processing tasks like text generation, summarization, and question answering. The Instant designation likely implies an optimized version for faster, low-latency inference, making it suitable for real-time applications. Despite being smaller than other models in the LLaMA series, LLaMA 3.1 8B Instant balances performance with speed, making it versatile for a wide range of use cases.",
                "knowledge_cutoff" : "",
                "usecase": [
                "The llama_3_1_8b_instant model can be used in real-time chat applications, providing quick and accurate responses for customer support, virtual assistants, or interactive learning.",
                "It can also be applied in dynamic content generation tools, rapidly producing text for blogs, social media, and e-commerce platforms."
               ]
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
            },
            "specification" : {
                "input_cost": 0.05,
                "output_cost": 08.00,
                "description" : "Qwen 2.5 32B is a version of the Qwen (Quantum-enhanced Neural Engine) model with 32 billion parameters. The 2.5 likely indicates an updated or intermediate iteration, offering improvements over previous versions. With 32 billion parameters, it is a large model capable of handling a variety of complex natural language tasks such as text generation, summarization, and question answering",
                "knowledge_cutoff" : "",
                "usecase": [
                "The qwen_2_5_32b model can be used in large-scale language processing tasks, such as translating documents, extracting information, and answering complex queries in research and enterprise environments.",
                "It can also be applied in AI-driven writing assistants, helping to generate high-quality, contextually relevant content for marketing campaigns, reports, and creative projects."
               ]
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
            },
            "specification" : {
                "input_cost": 0.05,
                "output_cost": 0.08,
                "description" : "DeepSeek R1 Distill Qwen 32B is a distilled version of the Qwen 32B model, optimized for efficiency and performance. It retains strong reasoning, comprehension, and generation capabilities while being more lightweight. Designed for AI applications requiring high-quality responses with reduced computational cost. Ideal for chatbots, content generation, and various NLP tasks.",
                "knowledge_cutoff" : "",
                 "usecase": [
                 "The deepseek_r1_distill_qwen_32b model can be used for fast and efficient document retrieval systems, enabling quick access to relevant information from large datasets in research and legal industries.",
                 "It can also be applied in AI-powered chatbots for customer service, offering precise and contextually aware answers to user inquiries while reducing response time."
                ]
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
            },
            "specification" : {
                "input_cost": 0.05,
                "output_cost": 0.08,
                "description" : "DeepSeek R1 Distill LLaMA 70B is a compressed version of the LLaMA model with 70 billion parameters. It has been distilled to reduce size while maintaining much of its original performance. The model is optimized for efficient and fast processing of complex language tasks. It provides high-quality natural language understanding and generation with reduced computational requirements.",
                "knowledge_cutoff" : "",
                 "usecase": [
                 "The deepseek_r1_distill_llama_70b model can be used for advanced information retrieval systems, providing fast, accurate, and context-aware searches through large data repositories in industries like finance or healthcare.",
                 "It can also be applied in personalized recommendation systems, helping businesses deliver tailored content or product suggestions based on user preferences and behaviors."
                ]
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
            },
            "specification" : {
                "input_cost": 0.05,
                "output_cost": 0.08,
                "description" : "LLaMA 3 8B 8192 is a version of Meta’s LLaMA (Large Language Model Meta AI) with 8 billion parameters. The 3 suggests it is part of the third iteration of the LLaMA model series. The 8B indicates that the model has 8 billion parameters, which allows it to handle a variety of natural language processing tasks effectively. The 8192 refers to the model's context window or token limit, which represents the maximum number of tokens (words or pieces of words) the model can process in a single input",
                "knowledge_cutoff" : "",
                "usecase": [
                "The llama3_8b_8192 model can be used for high-performance language generation tasks, such as creating long-form articles, reports, or creative content with detailed context and coherence.",
                "It can also be applied in real-time natural language understanding for virtual assistants, enabling smooth, conversational interactions with users across a variety of platforms."
                ]
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
            },
            "specification" : {
                "input_cost": 0.24,
                "output_cost": 0.24,
                "description" : "Mixtral 8x7B 32768 is a version of a language model with a unique architecture. The 8x7B suggests that the model consists of 8 components, each with 7 billion parameters, totaling 56 billion parameters. The 32768 refers to the model's context window or token limit, which is 32,768 tokens — an exceptionally large context window that allows the model to process long text inputs effectively",
                "knowledge_cutoff" : "",
                "usecase": [
                "The mixtral_8x7b_32768 model can be used for large-scale language understanding tasks, such as processing complex legal, medical, or scientific documents to extract key insights and summarize information.",
                "It can also be applied in real-time AI-powered translation systems, providing high-quality translations with the ability to handle extensive vocabulary and varied contexts across multiple languages."
  ]
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
            },
            "specification" : {
                "input_cost":  0.20,
                "output_cost":  0.20,
                "description" : "Gemma2 9B IT refers to a language model named Gemma2 with 9 billion parameters. The IT likely indicates that this version is specialized or fine-tuned for tasks related to Information Technology (IT), such as technical support, coding, system administration, and other IT-related domains.",
                "knowledge_cutoff" : "",
                "usecase": [
               "The gemma2_9b_it model can be used in Italian language processing tasks, such as translation, sentiment analysis, and content generation, making it ideal for businesses targeting Italian-speaking audiences.",
               "It can also be applied in conversational AI for Italian language chatbots, enabling more natural, context-aware interactions in customer support or virtual assistant applications."
             ]
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
            },
            "specification" : {
                "input_cost":  0.20,
                "output_cost": 0.20,
                "description" : "LLaMA Guard 3 8B is a version of the LLaMA (Large Language Model Meta AI) model with 8 billion parameters, specifically designed with added safety or moderation features. The Guard in its name suggests that it may have additional safety mechanisms to help prevent harmful or biased outputs, making it more suitable for use in sensitive applications.",
                "knowledge_cutoff" : "March 2023",
                "usecase": [
                "The llama_guard_3_8b model can be used for advanced cybersecurity applications, detecting and responding to potential threats in real-time through anomaly detection and pattern recognition.",
                "It can also be applied in data privacy tools, helping to ensure sensitive information is safeguarded by identifying and blocking any potential data breaches or leaks."
                 ]
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
            },
            "specification" : {
                "input_cost": 0.01,
                "output_cost": 0.03,
                "description" : "DALL·E 3 is OpenAI's advanced image-generation model capable of creating highly detailed and realistic images from text prompts. It understands complex descriptions, generating accurate compositions with improved coherence, lighting, and textures. The model is designed to follow user instructions closely, making it ideal for creative design, concept art, and visual storytelling. It excels in producing high-quality images with fewer artifacts compared to its predecessors.",
                "knowledge_cutoff" : "",
                "usecase": [
                "The dall_e_3 model can be used for creating high-quality, customized images from textual descriptions, making it ideal for digital artists, graphic designers, and marketing teams.",
                "It can also be applied in augmented reality and virtual reality applications, generating realistic and contextually relevant visual assets for immersive experiences."
             ]
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
               "usecase": [
               "The dall_e_2 model can be used in creative industries to generate unique, high-quality images from textual descriptions, helping artists and designers with visual inspiration.",
               "It can also be applied in e-commerce platforms to create product mockups or advertisements, providing businesses with visually appealing content generated automatically."
               ]
=======
            
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
            },
            "specification" : {
                "input_cost": null,
                "output_cost": null,
                "description" : "Text-Embedding-3-Large is a high-performance embedding model from OpenAI, designed for converting text into dense vector representations. It excels in tasks like semantic search, clustering, and text similarity. The model offers improved accuracy and efficiency over previous versions. It is ideal for applications requiring deep contextual understanding and large-scale text processing.",
                "knowledge_cutoff" : "",
                "usecase": [
                "The text_embedding_3_large model can be used for semantic search applications, improving the relevance and accuracy of search results by understanding the meaning behind user queries.",
                "It can also be applied in recommendation systems, helping to match users with personalized content, products, or services based on their preferences and behavior."
  ]
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
            },
            "specification" : {
                "input_cost": null,
                "output_cost": null,
                "description" : "Text-Embedding-3-Small is a lightweight embedding model from OpenAI, optimized for efficiency and speed while maintaining strong performance. It converts text into dense vector representations for tasks like semantic search, text similarity, and clustering. With lower computational requirements, it is well-suited for real-time and large-scale applications",
                "knowledge_cutoff" : "",
                "usecase": [
                "The text_embedding_3_small model can be used for efficient text classification tasks in environments with limited computational resources, such as mobile devices or edge computing.",
                "It can also be applied in real-time sentiment analysis, quickly processing user feedback and social media content to identify trends and public sentiment."
                ]
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
            },
            "specification" : {
                "input_cost": 30.00,
                "output_cost": 60.00,
                "description" : "text-embedding-ada-002 is an OpenAI embedding model designed for converting text into dense vector representations. It is optimized for tasks like semantic search, clustering, and text similarity. Known for its balance of efficiency and accuracy, it provides high-quality embeddings at a lower computational cost. It is widely used in NLP applications, including recommendation systems and knowledge retrieval.",
                "knowledge_cutoff" : "",
                "usecase": [
               "The text_embedding_ada_002 model can be used for document clustering, grouping similar pieces of content based on their semantic meaning for better organization in databases or knowledge management systems.",
               "It can also be applied in improving search engine capabilities by enhancing keyword matching with semantic understanding, offering more relevant results for user queries."
              ]
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