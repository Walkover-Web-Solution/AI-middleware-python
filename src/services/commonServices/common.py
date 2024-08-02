from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import traceback
import uuid
import time
from src.configs.models import services
from src.configs.modelConfiguration import ModelsConfig
from ...controllers.conversationController import getThread 
from ..utils.getConfiguration import getConfiguration
from operator import itemgetter
from ...db_services import metrics_service as metrics_service
from .openAI.openaiCall import UnifiedOpenAICase
from ..utils.customRes import ResponseSender
from .Google.geminiCall import GeminiHandler
import pydash as _
from ..utils.helper import Helper
import asyncio
from prompts import mui_prompt
app = FastAPI()

@app.post("/chat/{bridge_id}")
async def chat(request: Request):
    startTime = int(time.time() * 1000)
    body = await request.json()
    if(hasattr(request.state, 'body')): 
        body.update(request.state.body) 

    apikey = body.get("apikey")
    bridge_id = request.path_params.get('bridge_id') or body.get("bridge_id")
    configuration = body.get("configuration")
    thread_id = body.get("thread_id")
    org_id = request.state.org_id
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
    # if hasattr(request.state, 'playground'): # change according to ui ka playground
    #     is_playground = request.state.playground
    is_playground = body.get('is_playground', False)
    bridge = body.get('bridge')

    try:
        modelname = model.replace("-", "_").replace(".", "_")
        modelfunc = getattr(ModelsConfig, modelname, None)
        modelObj = modelfunc()
        modelConfig, modelOutputConfig = modelObj['configuration'], modelObj['outputConfig']

        #todo :: will not work if level is nor present in key
        for key in modelConfig:
            if modelConfig[key]["level"] == 2 or key in configuration: # may be not required
                customConfig[key] = configuration.get(key, modelConfig[key]["default"])

        if thread_id:
            thread_id = thread_id.strip()
            result = await getThread(thread_id, org_id, bridge_id)
            if result["success"]:
                configuration["conversation"] = result.get("data", [])
        else:
            thread_id = str(uuid.uuid1())
        configuration['prompt']  = Helper.replace_variables_in_prompt(configuration['prompt'] , variables)

        if template:
            system_prompt = [{"role": "system", "content": template}]
            configuration['prompt'] = Helper.replace_variables_in_prompt(system_prompt, {"system_prompt": configuration['prompt'][0].get('content'), **variables})

        params = {
            "customConfig": customConfig,
            "configuration": configuration,
            "apikey": apikey,
            "variables": variables,
            "user": user,
            "tools": tools,
            "startTime": startTime,
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
        }

        if service == "openai":
            openAIInstance = UnifiedOpenAICase(params)
            result = await openAIInstance.execute()
            if not result["success"]:
                if response_format['type'] != 'default':
                    return
                return JSONResponse(status_code=400, content=result)
        elif service == "google":
            geminiHandler = GeminiHandler(params)
            result = await geminiHandler.handle_gemini()
            if not result["success"]:
                if response_format['type'] != 'default':
                    return
                return JSONResponse(status_code=400, content=result)

        if bridgeType:
            parsedJson = Helper.parse_json(_.get(result["modelResponse"], modelOutputConfig["message"]))
            if not parsedJson.get("json", {}).get("isMarkdown"):
                params["configuration"]["prompt"] = {"role": "system", "content": mui_prompt.responsePrompt}
                params["user"] = _.get(result["modelResponse"], (modelOutputConfig["message"]))
                params["template"] = None
                openAIInstance = UnifiedOpenAICase(params)
                newresult = await openAIInstance.execute()
                if not newresult["success"]:
                    return

                _.set_(result['modelResponse'], modelOutputConfig['usage'][0]['total_tokens'], _.get(result['modelResponse'], modelOutputConfig['usage'][0]['total_tokens']) + _.get(newresult['modelResponse'], modelOutputConfig['usage'][0]['total_tokens']))
                _.set_(result['modelResponse'], modelOutputConfig['message'], _.get(newresult['modelResponse'], modelOutputConfig['message']))
                _.set_(result['modelResponse'], modelOutputConfig['usage'][0]['prompt_tokens'], _.get(result['modelResponse'], modelOutputConfig['usage'][0]['prompt_tokens']) + _.get(newresult['modelResponse'], modelOutputConfig['usage'][0]['prompt_tokens']))
                _.set_(result['modelResponse'], modelOutputConfig['usage'][0]['completion_tokens'], _.get(result['modelResponse'], modelOutputConfig['usage'][0]['completion_tokens']) + _.get(newresult['modelResponse'], modelOutputConfig['usage'][0]['completion_tokens']))
                result['historyParams'] = newresult['historyParams']
                _.set_(result['usage'], "totalTokens", _.get(result['usage'], "totalTokens") + _.get(newresult['usage'], "totalTokens"))
                _.set_(result['usage'], "inputTokens", _.get(result['usage'], "inputTokens") + _.get(newresult['usage'], "inputTokens"))
                _.set_(result['usage'], "outputTokens", _.get(result['usage'], "outputTokens") + _.get(newresult['usage'], "outputTokens"))
                _.set_(result['usage'], "expectedCost", _.get(result['usage'], "expectedCost") + _.get(newresult['usage'], "expectedCost"))
                result['historyParams']['user'] = user

        endTime = int(time.time() * 1000)
        if not is_playground:
            usage.update({
                **result.get("usage", {}),
                "service": service,
                "model": model,
                "orgId": org_id,
                "latency": endTime - startTime,
                "success": True,
                "variables": variables,
                "prompt": configuration["prompt"]
            })
            asyncio.create_task(metrics_service.create([usage], result["historyParams"]))
            asyncio.create_task(ResponseSender.sendResponse(response_format, result["modelResponse"],success=True))
            if response_format['type'] != 'default':
                return
        return JSONResponse(status_code=200, content={"success": True, "response": result["modelResponse"]})

    except Exception as error:
        traceback.print_exc()
        if not is_playground:
            endTime = int(time.time() * 1000)
            latency = endTime - startTime
            usage.update({
                **usage,
                "service": service,
                "model": model,
                "orgId": org_id,
                "latency": latency,
                "success": False,
                "error": str(error)
            })
            asyncio.create_task(metrics_service.create([usage], {
                "thread_id": thread_id,
                "user": user,
                "message": "",
                "org_id": org_id,
                "bridge_id": bridge_id,
                "model": model or configuration.get("model", None),
                "channel": 'chat',
                "type": "error",
                "actor": "user"
            }))
            print("chat common error=>", error)
            asyncio.create_task(ResponseSender.sendResponse(response_format, result["modelResponse"]))
            if response_format['type'] != 'default':
                return
        return JSONResponse(status_code=400, content={"success": False, "error": str(error)})
