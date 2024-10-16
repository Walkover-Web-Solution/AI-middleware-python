
def check_json_support(model, service):
     match service:
                case 'openai':
                    if model in ['gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo', 'gpt-4-turbo', 'gpt-4o-2024-08-06', 'chatgpt-4o-latest', 'gpt-4o-mini-2024-07-18' ]:
                          return True
                    else:
                          return False
                # case 'anthropic':
                #     if model in ['claude-3-5-sonnet-20240620']:
                #           return True
                # case  'groq':
                #     pass