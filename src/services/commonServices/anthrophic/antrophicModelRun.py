import anthropic
from ...utils.time import Timer

async def anthropic_runmodel(configuration, apikey, execution_time_logs):
    try:
        timer = Timer()
        antrophic_config = anthropic.Anthropic(api_key = apikey)
        timer.start()
        Antrophic = antrophic_config.messages.create(**configuration)
        execution_time_logs[len(execution_time_logs) + 1] = timer.stop("Antrophic chat completion")
        response = Antrophic.to_dict()
        return {
                'success': True,
                'response': response
            }
    
    except Exception as e:
        execution_time_logs[len(execution_time_logs) + 1] = timer.stop("Antrophic chat completion")
        print("Antrophic runmodel error=>", e)
        return {
            'success': False,
            'error': str(e)
        }