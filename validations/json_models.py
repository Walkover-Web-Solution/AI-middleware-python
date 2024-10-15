
def check_json_support(model, service):
     match service:
                case 'openai':
                    if model in ['gpt-4o']:
                          return True
                    else:
                          return False
                # case 'anthropic':
                #     if model in ['claude-3-5-sonnet-20240620']:
                #           return True
                # case  'groq':
                #     pass