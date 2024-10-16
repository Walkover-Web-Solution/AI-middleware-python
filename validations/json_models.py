
def check_json_support(model, service):
     match service:
                case 'openai':
                    if model in ['gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo', 'gpt-4-turbo', 'gpt-4o-2024-08-06', 'chatgpt-4o-latest', 'gpt-4o-mini-2024-07-18' ]:
                          return True
                    else:
                          return False
                case  'groq': 
                    if model in ['llama-3.1-70b-versatile', 'llama-3.1-8b-instant', 'llama3-groq-70b-8192-tool-use-preview','llama3-groq-8b-8192-tool-use-preview','llama3-70b-8192','llama3-8b-8192','mixtral-8x7b-32768','gemma-7b-it','gemma2-9b-it']:
                          return True
                    else:
                          return False
                # case 'anthropic':
                #     if model in ['claude-3-5-sonnet-20240620']:
                #           return True
                
