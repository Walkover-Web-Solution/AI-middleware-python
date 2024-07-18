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
# from openAI.openaiCall import UnifiedOpenAICase
from .openAI.openaiCall import UnifiedOpenAICase

from ..utils.customRes import ResponseSender
from .Google.geminiCall import GeminiHandler
import pydash as _
from ..utils.helper import Helper
import asyncio
from prompts import mui_prompt
app = FastAPI()

# responseSender = ResponseSender()

@app.post("/getchat/{bridge_id}")
async def getchat(request: Request, bridge_id):
    try:
        body = await request.json()##
        apikey = body.get("apikey")##
        configuration = body.get("configuration")##
        service = body.get("service")
        variables = body.get("variables", {})


        customConfig = {}
        bridge_id = request.path_params['bridge_id']
        getconfig = await getConfiguration(configuration, service, bridge_id, apikey)
        if not getconfig["success"]:
            return JSONResponse(status_code=400, content={"success": False, "error": getconfig["error"]})
        configuration = getconfig["configuration"]
        service = getconfig["service"]
        apikey = getconfig["apikey"]
        model = configuration.get("model")
        bridge = getconfig["bridge"]
        service = service.lower() if service else ""
    

        if not (service in services and model in services[service]["chat"]):
            return JSONResponse(status_code=400, content={"success": False, "error": "model or service does not exist!"})

        modelname = model.replace("-", "_").replace(".", "_") 
        modelfunc = getattr(ModelsConfig, modelname, None)
        #modelfunc = ModelsConfig.get(modelname, None) ## does it work the same ? then remove above one
        modelObj = modelfunc()
        modelConfig, modelOutputConfig = modelObj['configuration'], modelObj['outputConfig']



        for key in modelConfig: ## this code should not work properly, key should be index not value
            if modelConfig[key]["level"] == 2 or key in configuration:
                customConfig[key] = configuration.get(key, modelConfig[key]["default"])
        
        params = {
            "customConfig": customConfig,
            "configuration": configuration,
            "apikey": apikey,
            "variables": variables,
            "user": configuration.get("user", ""),
            "startTime": int(time.time() * 1000),
            "org_id": None,
            "bridge_id": bridge_id, # bridge_id is not like it is in js code,
            "bridge": bridge,
            "model": model,
            "service": service,
            "modelOutputConfig": modelOutputConfig,
            "playground": True,
            "req": request
        }
        
        if service == "openai":
            openAIInstance = UnifiedOpenAICase(params)
            result = await openAIInstance.execute()
            if not result["success"]:
                return JSONResponse(status_code=400, content=result)
        elif service == "google":
            geminiHandler = GeminiHandler(params)
            result = await geminiHandler.handle_gemini()
            if not result["success"]:
                return JSONResponse(status_code=400, content=result)  
            
        return JSONResponse(status_code=200, content={"success": True, "response": result["modelResponse"]})
    
    except Exception as error:
        print("hello error!!!")  
        traceback.print_exc()
        print("common error=>", error)
        return JSONResponse(status_code=400, content={"success": False, "error": str(error)})


@app.post("/prochat")
async def prochat(request: Request):
    startTime = int(time.time() * 1000)
    body = await request.json()
    if(hasattr(request.state, 'body')): 
        body.update(request.state.body) 

    apikey = body.get("apikey")
    bridge_id = body.get("bridge_id")
    configuration = body.get("configuration")
    thread_id = body.get("thread_id")
    org_id = request.state.org_id
    user = body.get("user")
    tool_call = body.get("tool_call")
    service = body.get("service")
    variables = body.get("variables", {})
    RTLayer = body.get("RTLayer")
    bridgeType = body.get('chatbot')
    template = body.get('template')
    usage = {}
    customConfig = {}
    model = configuration.get("model") if configuration else None
    rtlLayer = RTLayer if RTLayer else configuration.get("RTLayer")
    webhook = body.get('webhook')
    headers = body.get('headers')
    bridge = body.get('bridge')

    try:
        modelname = model.replace("-", "_").replace(".", "_")
        modelfunc = getattr(ModelsConfig, modelname, None)
        modelObj = modelfunc()
        modelConfig, modelOutputConfig = modelObj['configuration'], modelObj['outputConfig']

        for key in modelConfig:
            if modelConfig[key]["level"] == 2 or key in configuration:
                customConfig[key] = configuration.get(key, modelConfig[key]["default"])

        if thread_id:
            thread_id = thread_id.strip()
            result = await getThread(thread_id, org_id, bridge_id)
            if result["success"]:
                configuration["conversation"] = result.get("data", [])
        else:
            thread_id = str(uuid.uuid1())
        
        params = {
            "customConfig": customConfig,
            "configuration": configuration,
            "apikey": apikey,
            "variables": variables,
            "user": user,
            "tool_call": tool_call,
            "startTime": startTime,
            "org_id": org_id,
            "bridge_id": bridge_id,
            "bridge": bridge,
            "thread_id": thread_id,
            "model": model,
            "service": service,
            "req": request,
            "modelOutputConfig": modelOutputConfig,
            "playground": False,
            "rtlayer": rtlLayer,
            "webhook": webhook,
            "template": template
        }
        if service == "openai":
            openAIInstance = UnifiedOpenAICase(params)
            result = await openAIInstance.execute()
            if not result["success"]:
                if rtlLayer or webhook:
                    return
                return JSONResponse(status_code=400, content=result)
        elif service == "google":
            geminiHandler = GeminiHandler(params)
            result = await geminiHandler.handle_gemini()
            if not result["success"]:
                if rtlLayer or webhook:
                    return
                return JSONResponse(status_code=400, content=result)

        if bridgeType:
            parsedJson = Helper.parse_json(_.get(result["modelResponse"], modelOutputConfig["message"]))
            if not parsedJson.get("json", {}).get("isMarkdown"):
                params["configuration"]["prompt"] = {"role": "system", "content": mui_prompt.responsePrompt}
                params["user"] = _.get(result["modelResponse"],(modelOutputConfig["message"]))
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
        asyncio.create_task(ResponseSender.sendResponse(
            rtl_layer = rtlLayer,
            webhook= webhook,
            data= {"response": result["modelResponse"], "success": True},
            req_body= body,
            headers= headers or {}
        ))
        if rtlLayer or webhook:
            return JSONResponse(status_code=200, content = {"success" : True, "message" : "Your data will be send through the configured means."})
        return JSONResponse(status_code=200, content={"success": True, "response": result["modelResponse"]})
    
    except Exception as error:
        traceback.print_exc()
        
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
        asyncio.create_task( metrics_service.create([usage],{ 
                "thread_id": thread_id,
                "user": user,
                "message": "",
                "org_id": org_id,
                "bridge_id": bridge_id,
                "model": configuration.get("model", None),
                "channel": 'chat',
                "type": "error",
                "actor": "user"
            }))
        print("prochats common error=>", error)
        asyncio.create_task(ResponseSender.sendResponse({
            "rtlLayer": rtlLayer,
            "webhook": webhook,
            "data": {"error": str(error), "success": False},
            "reqBody": body,
            "headers": headers or {}
        }))
        if rtlLayer or webhook:
            return
        return JSONResponse(status_code=400, content={"success": False, "error": str(error)})
