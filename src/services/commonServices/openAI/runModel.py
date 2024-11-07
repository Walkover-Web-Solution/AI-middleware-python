from .openAIInitializerService import OpenAIInitializer
import asyncio
from concurrent.futures import ThreadPoolExecutor
import traceback
import json
import copy
from ...utils.ai_middleware_format import send_alert

async def runModel(configuration, apiKey, execution_time_logs, bridge_id,timer,message_id=None):
    try:
        # Initialize OpenAI service
        OpenAIConfig = OpenAIInitializer(apiKey)
        openAI = OpenAIConfig.getOpenAIService()
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor(max_workers=2)

        # Function to execute the API call
        def api_call(config):
            try:
                chat_completion = openAI.chat.completions.create(**config)
                return {'success': True, 'response': chat_completion.to_dict()}
            except Exception as error:
                return {'success': False, 'error': str(error)}

      # Start timer  
        timer.start()

        # Start the first API call
        first_config = copy.deepcopy(configuration)
        first_task = loop.run_in_executor(executor, api_call, first_config)

        # Wait for the first task to complete or 40 seconds, whichever comes first
        done, pending = await asyncio.wait(
            [first_task],
            timeout=60,
            return_when=asyncio.FIRST_COMPLETED
        )

        if first_task in done:
            # First task completed within 60 seconds
            result = first_task.result()
            execution_time_logs[len(execution_time_logs) + 1] = timer.stop("OpenAI chat completion")
            print("First API call completed within 60 seconds.")
            if result['success']:
                print(11, json.dumps(first_config), 22, bridge_id)
            else:
                print("runmodel error=>", result['error'])
                traceback.print_exc()
            for task in pending:
                task.cancel()
            return result
        else:
            await send_alert(data={"configuration": configuration,"message_id":message_id, "bridge_id": bridge_id, "message": "retry mechanism started 2nd time"}),
            # First task did not complete within 60 seconds
            print("First API call did not complete within 60 seconds. Starting second API call.")
            # Start the second API call with 'gpt-4' model
            second_config = copy.deepcopy(configuration)
            second_config['model'] = 'gpt-4o-2024-08-06' if configuration['model'] == 'gpt-4o' else 'gpt-4o'
            second_task = loop.run_in_executor(executor, api_call, second_config)

            # Wait for either the first or second task to complete
            tasks = [first_task, second_task]
            done, pending = await asyncio.wait(
                tasks,
                timeout=240,
                return_when=asyncio.FIRST_COMPLETED
            )

            # Get the result from the task that completed first
            for task in done:
                result = task.result()
                execution_time_logs[len(execution_time_logs) + 1] = timer.stop("OpenAI chat completion")
                if task == first_task:
                    print("First API call completed first.")
                    config_used = first_config
                else:
                    print("Second API call completed first.")
                    config_used = second_config

                if result['success']:
                    print(11, json.dumps(config_used), 22, bridge_id)
                else:
                    print("runmodel error=>", result['error'])
                    traceback.print_exc()
                for task in pending:
                    task.cancel()
                return result

            # If no tasks completed successfully
            execution_time_logs[len(execution_time_logs) + 1] = timer.stop("OpenAI chat completion")
            return {
                'success': False,
                'error': 'No API call completed successfully.'
            }
    except Exception as error:
        execution_time_logs[len(execution_time_logs) + 1] = timer.stop("OpenAI chat completion")
        print("runmodel error=>", error)
        traceback.print_exc()
        return {
            'success': False,
            'error': str(error)
        }
