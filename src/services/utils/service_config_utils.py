
def tool_choice_function_name_formatter(service, configuration, toolchoice, found_choice):
    match service:
        case "openai" | "groq":
            configuration['tool_choice'] = found_choice if found_choice is not None else toolchoice
            return configuration['tool_choice']
        case "anthropic":
            if found_choice == 'default':
                default_choice = found_choice
            else:
                default_choice = {'type' : found_choice}
            user_choice = {'type' : 'tool', 'name' : toolchoice}
            configuration['tool_choice'] = default_choice if found_choice is not None else user_choice
            return configuration['tool_choice']
    return configuration['tool_choice']
