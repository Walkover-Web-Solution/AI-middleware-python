import anthropic

async def anthropic_runmodel(configuration, apikey):
    try:
        antrophic_config = anthropic.Anthropic(api_key = apikey)
        Antrophic = antrophic_config.messages.create(**configuration)
        response = Antrophic.to_dict()
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