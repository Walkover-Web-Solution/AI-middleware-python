import anthropic

async def anthropic_runmodel(configuration, apikey):
    try:
        antrophic_config = anthropic.Anthropic(api_key = apikey)
        # antrophic_config.api_key = apikey  # Set the API key separately
        Antrophic = antrophic_config.messages.create(**configuration)
        response = Antrophic.to_dict()
        print(response,"hiii")
        return {
                'success': True,
                'response': response
            }
    
    except Exception as e:
        print("Antrophic runmodel error=>", e)
        return {
            'success': False,
            'error': str(e)
        }