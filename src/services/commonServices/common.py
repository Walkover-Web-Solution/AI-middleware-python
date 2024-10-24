from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import traceback
import uuid
import time
from config import Config
from src.configs.models import services
from src.configs.modelConfiguration import ModelsConfig
from ...controllers.conversationController import getThread 
from operator import itemgetter
from ...db_services import metrics_service as metrics_service
from .openAI.openaiCall import UnifiedOpenAICase
from .baseService.baseService import BaseService
from .Google.geminiCall import GeminiHandler
import pydash as _
from ..utils.helper import Helper
import asyncio
from .anthrophic.antrophicCall import Antrophic
from .groq.groqCall import Groq
from prompts import mui_prompt
from .baseService.utils import sendResponse
from ..utils.ai_middleware_format import Response_formatter
app = FastAPI()
from src.services.commonServices.baseService.utils import axios_work
from ...configs.constant import service_name
import src.db_services.ConfigurationServices as ConfigurationService
from ..utils.send_error_webhook import send_error_to_webhook
from copy import deepcopy
import json
from ..utils.time import Timer
from src.handler.executionHandler import handle_exceptions
from src.configs.serviceKeys import model_config_change

async def create_service_handler(params, service):
    if service == service_name['openai']:
        class_obj = UnifiedOpenAICase(params)
    elif service == service_name['gemini']:
        class_obj = GeminiHandler(params)
    elif service == service_name['anthropic']:
        class_obj = Antrophic(params)
    elif service == service_name['groq']:
        class_obj = Groq(params)
        
    return class_obj


@app.post("/chat/{bridge_id}")
@handle_exceptions
async def chat(request: Request):
    body = await request.json()
    if(hasattr(request.state, 'body')): 
        body.update(request.state.body) 

    apikey = body.get("apikey")
    bridge_id = request.path_params.get('bridge_id') or body.get("bridge_id")
    configuration = body.get("configuration")
    thread_id = body.get("thread_id")
    org_id = request.state.profile.get('org',{}).get('id','')
    user = body.get("user")
    tools =  configuration.get('tools')
    service = body.get("service")
    variables = body.get("variables", {})
    bridgeType = body.get('chatbot')
    template = body.get('template')
    usage = {}
    customConfig = {}
    response_format = configuration.get("response_format")
    model = configuration.get('model')
    is_playground = request.state.is_playground
    bridge = body.get('bridge')
    pre_tools = body.get('pre_tools')
    version = request.state.version
    fine_tune_model = configuration.get('fine_tune_model', {}).get('current_model', {})
    is_rich_text = configuration.get('is_rich_text',True)   
    actions = body.get('actions',{})
    execution_time_logs = body.get('execution_time_logs')
    user_reference = body.get("user_reference", "")
    user_contains = ""
    timer = request.state.timer
    variables_path = body.get('variables_path')
    names = body.get('names')
    suggest = body.get('suggest',False)
    message_id = str(uuid.uuid1())
    result = {}
    suggestions = []
    suggestions_flag =False
    if isinstance(variables, list):
        variables = {}

    try:
        modelname = model.replace("-", "_").replace(".", "_")
        modelfunc = getattr(ModelsConfig, modelname, None)
        modelObj = modelfunc()
        modelConfig, modelOutputConfig = modelObj['configuration'], modelObj['outputConfig']

        for key in modelConfig:
            if key == 'type' and key in configuration:
                continue
            if  modelConfig[key]["level"] == 2 or key in configuration:
                customConfig[key] = configuration.get(key, modelConfig[key]["default"])
        if fine_tune_model is not None and len(fine_tune_model) and model in {'gpt-4o-mini-2024-07-18', 'gpt-4o-2024-08-06', 'gpt-4-0613'}:
            customConfig['model'] = fine_tune_model
            del customConfig['creativity_level'] # [?] to be removed
        if pre_tools:
            pre_function_response = await axios_work(pre_tools.get('args', {}), pre_tools.get('name', ''))
            if pre_function_response.get('status') == 0:
                variables['pre_function'] = "Error while calling prefunction. Error message: " + pre_function_response.get('response')
            else:
                variables['pre_function'] = pre_function_response.get('response')

        if thread_id:
            thread_id = thread_id.strip()
            result = await getThread(thread_id, org_id, bridge_id,bridgeType)
            if result["success"]:
                configuration["conversation"] = result.get("data", [])
        else:
            thread_id = str(uuid.uuid1())

        configuration['prompt'], missing_vars  = Helper.replace_variables_in_prompt(configuration['prompt'] , variables)
        if len(missing_vars) > 0:
            await send_error_to_webhook(bridge_id, org_id, missing_vars, type = 'Variable')

        if template:
            system_prompt = template
            configuration['prompt'], missing_vars = Helper.replace_variables_in_prompt(system_prompt, {"system_prompt": configuration['prompt'], **variables})

        if bridgeType and modelConfig.get('response_type') and suggest:
            template_content = (await ConfigurationService.get_template_by_id(Config.CHATBOT_OPTIONS_TEMPLATE_ID)).get('template', '')
            configuration['prompt'], missing_vars = Helper.replace_variables_in_prompt(template_content, {"system_prompt": configuration['prompt']})
            customConfig['response_type'] = {"type": "json_object"}
            suggestions_flag = True

        customConfig = await model_config_change(modelObj['configuration'], customConfig)
            
        params = {
            "customConfig": customConfig,
            "configuration": configuration,
            "apikey": apikey,
            "variables": variables,
            "user": user,
            "tools": tools,
            "org_id": org_id if is_playground else None,
            "bridge_id": bridge_id,
            "bridge": bridge,
            "thread_id": thread_id,
            "model": model,
            "service": service,
            "req": request, 
            "modelOutputConfig": modelOutputConfig,
            "playground": is_playground,
            "template": template,
            "response_format" : response_format,
            "org_id" : org_id,
            "execution_time_logs" : execution_time_logs,
            "timer" : timer,
            "variables_path" : variables_path,
            "message_id" : message_id,
            "bridgeType": bridgeType,
            "names":names
        }

        class_obj = await create_service_handler(params,service)
        result = await class_obj.execute()
        
        if not result["success"]:
            raise ValueError(result)

        if is_rich_text and bridgeType:
                try:
                    try:
                        # validation for the check response
                        parsedJson = Helper.parse_json(_.get(result["modelResponse"], modelOutputConfig["message"]))
                    except Exception as e:
                        if _.get(result["modelResponse"], modelOutputConfig["tools"]):
                            raise RuntimeError("Function calling has been done 6 times, limit exceeded.")
                        raise RuntimeError(e)
                    system_prompt =  (await ConfigurationService.get_template_by_id(Config.MUI_TEMPLATE_ID)).get('template', '')
                    if user_reference: 
                        user_reference = f"\"user reference\": \"{user_reference}\""
                        user_contains = "on the base of user reference"
                    params["configuration"]["prompt"], missing_vars = Helper.replace_variables_in_prompt(system_prompt, { "actions" : actions, "user_reference": user_reference, "user_contains": user_contains})
                    params["user"] = f"user: {user}, \n Answer: {_.get(result['modelResponse'], modelOutputConfig['message'])}"
                    params["template"] = None
                    tools = result.get('historyParams').get('tools')
                    if 'customConfig' in params and 'tools' in params['customConfig']:
                        del params['customConfig']['tools']
                    model_response_content = result.get('historyParams').get('message')
                    obj = await create_service_handler(params,service)
                    newresult = await obj.execute()
                    tokens = obj.calculate_usage(newresult["modelResponse"])
                    if service == "anthropic":
                        _.set_(result['usage'], "totalTokens", _.get(result['usage'], "totalTokens") + tokens['totalTokens'])
                        _.set_(result['usage'], "inputTokens", _.get(result['usage'], "inputTokens") + tokens['inputTokens'])
                        _.set_(result['usage'], "outputTokens", _.get(result['usage'], "outputTokens") + tokens['outputTokens'])
                    elif service == 'openai' or service == 'groq':
                        _.set_(result['usage'], "totalTokens", _.get(result['usage'], "totalTokens") + tokens['totalTokens'])
                        _.set_(result['usage'], "inputTokens", _.get(result['usage'], "inputTokens") + tokens['inputTokens'])
                        _.set_(result['usage'], "outputTokens", _.get(result['usage'], "outputTokens") + tokens['outputTokens'])
                        _.set_(result['usage'], "expectedCost", _.get(result['usage'], "expectedCost") + tokens['expectedCost'])
                    _.set_(result['modelResponse'], modelOutputConfig['message'], _.get(newresult['modelResponse'], modelOutputConfig['message']))
                    result['historyParams'] = deepcopy(newresult.get('historyParams',{}))
                    result['historyParams']['message'] = model_response_content
                    result['historyParams']['chatbot_message'] = newresult['historyParams']['message']
                    result['historyParams']['user'] = user
                    result['historyParams']['tools'] = tools
                except Exception as e:
                    print(f"error in chatbot : {e}")
                    raise RuntimeError(f"error in chatbot : {e}")
        
        if bridgeType and suggestions_flag:
                suggestions = class_obj.extract_response_from_model(model_response=result['modelResponse'])
                message = json.loads(result['historyParams']['message'])
                result["historyParams"]["message"] = message.get('response','')
                
        if version == 2:
            result['modelResponse'] = await Response_formatter(result["modelResponse"],service)
        if bridgeType and suggestions:
                result['modelResponse']['options'] = suggestions
        latency = {
            "over_all_time" : timer.stop("Api total time") or "",
            "model_execution_time": sum(execution_time_logs.values()) or "",
            "execution_time_logs" : execution_time_logs or {}
        }
        if not is_playground:
            usage.update({
                **result.get("usage", {}),
                "service": service,
                "model": model,
                "orgId": org_id,
                "latency": json.dumps(latency),
                "success": True,
                "variables": variables,
                "prompt": configuration["prompt"]
            })
            if result.get('modelResponse') and result['modelResponse'].get('data'):
                result['modelResponse']['data']['message_id'] = message_id
            # Optimize task creation and gathering
            await asyncio.gather(
                sendResponse(response_format, result["modelResponse"], success=True),
                metrics_service.create([usage], result["historyParams"]),
                return_exceptions=True
            )
        return JSONResponse(status_code=200, content={"success": True, "response": result["modelResponse"]})
    except Exception as error:
        traceback.print_exc()
        if not is_playground:
            latency = {
                "over_all_time": timer.stop("Api total time") or "",
                "model_execution_time": sum(execution_time_logs.values()) or "",
                "execution_time_logs": execution_time_logs or {}
            }
            usage.update({
                **usage,
                "service": service,
                "model": model,
                "orgId": org_id,
                "latency": json.dumps(latency),
                "success": False,
                "error": str(error)
            })
            # Combine the tasks into a single asyncio.gather call
            await asyncio.gather(
                metrics_service.create([usage], {
                    "thread_id": thread_id,
                    "user": user,
                    "message": "",
                    "org_id": org_id,
                    "bridge_id": bridge_id,
                    "model": model or configuration.get("model", None),
                    "channel": 'chat',
                    "type": "error",
                    "actor": "user"
                }),
                sendResponse(response_format, error_message),
                # Only send the second response if the type is not 'default'
                sendResponse(response_format, result.get("modelResponse", str(error))) if response_format['type'] != 'default' else None,
                return_exceptions=True
            )
            print("chat common error=>", error)
            error_message = str(error)
            if not result.get('success'):
                error_message = result.get("modelResponse", str(error))
        raise ValueError(error)
        
