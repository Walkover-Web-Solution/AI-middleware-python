import anthropic
import json

async def anthropic_runmodel(configuration, apikey, execution_time_logs, bridge_id, timer):
    try:
        antrophic_config = anthropic.Anthropic(api_key = apikey)
        timer.start()
        Antrophic = antrophic_config.messages.create(**configuration)
        execution_time_logs[len(execution_time_logs) + 1] = timer.stop("Antrophic chat completion")
        response = Antrophic.to_dict()
        print(11, json.dumps(configuration), 22, bridge_id)
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