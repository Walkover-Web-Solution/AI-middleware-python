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
import asyncio

app = FastAPI()

@app.post("/getchat/{bridge_id}")
async def getchat(request: Request, bridge_id):
    try:
        body = await request.json()
        apikey = body.get("apikey")
        configuration = body.get("configuration")
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
        modelObj = modelfunc()
        modelConfig, modelOutputConfig = modelObj['configuration'], modelObj['outputConfig']

        for key in modelConfig:
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
            "bridge_id": bridge_id,
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
        traceback.print_exc()
        print("common error=>", error)
        return JSONResponse(status_code=400, content={"success": False, "error": str(error)})


@app.post("/prochat")
async def prochat(request: Request):
    startTime = int(time.time() * 1000)
    
    body = await request.json()
    apikey = body.get("apikey")
    bridge_id = body.get("bridge_id", None)
    configuration = body.get("configuration")
    thread_id = body.get("thread_id", None)
    org_id = request.state.org_id
    user = body.get("user", None)
    tool_call = body.get("tool_call", None)
    service = body.get("service")
    variables = body.get("variables", {})
    RTLayer = body.get("RTLayer", None)
    template_id = body.get("template_id", None)
    bridgeType = request.get("chatbot", None)

    usage = {}
    customConfig = {}
    model = configuration.get("model") if configuration else None
    rtlLayer = False
    webhook = None
    headers = None
    try:
        getconfig = await getConfiguration(configuration, service, bridge_id, apikey, template_id)
        if not getconfig["success"]:
            return JSONResponse(status_code=400, content={"success": False, "error": getconfig["error"]})

        configuration = getconfig["configuration"]
        service = getconfig["service"]
        apikey = getconfig["apikey"]
        template = getconfig["template"]
        model = model or configuration.get("model")
        rtlLayer = RTLayer or getconfig["RTLayer"]
        bridge = getconfig["bridge"]

        if not (service in services and model in services[service]["chat"]):
            return JSONResponse(status_code=400, content={"success": False, "error": "model or service does not exist!"})

        webhook = configuration.get("webhook")
        headers = configuration.get("headers")
        # if rtlLayer or webhook:
        #     response = JSONResponse(status_code=200, content={"success": True, "message": "Will got response over your configured means."})
        #     await response(request.scope, request.receive, request._send)

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

    #     if bridgeType:
    #         parsedJson = Helper.parseJson(result["modelResponse"].get(modelOutputConfig["message"]))
    #         if not parsedJson.get("json", {}).get("isMarkdown"):
    #             params["configuration"]["prompt"] = {"role": "system", "content": responsePrompt}
    #             params["user"] = result["modelResponse"].get(modelOutputConfig["message"])
    #             params["template"] = None
    #             openAIInstance = UnifiedOpenAICase(params)
    #             newresult = await openAIInstance.execute()
    #             if not newresult["success"]:
    #                 return

    #             result["modelResponse"][modelOutputConfig["message"]] = newresult["modelResponse"].get(modelOutputConfig["message"])
    #             result["modelResponse"][modelOutputConfig["usage"][0]["total_tokens"]] += newresult["modelResponse"].get(modelOutputConfig["usage"][0]["total_tokens"])
    #             result["modelResponse"][modelOutputConfig["usage"][0]["prompt_tokens"]] += newresult["modelResponse"].get(modelOutputConfig["usage"][0]["prompt_tokens"])
    #             result["modelResponse"][modelOutputConfig["usage"][0]["completion_tokens"]] += newresult["modelResponse"].get(modelOutputConfig["usage"][0]["completion_tokens"])
    #             result["historyParams"] = newresult["historyParams"]
    #             result["usage"]["totalTokens"] += newresult["usage"]["totalTokens"]
    #             result["usage"]["inputTokens"] += newresult["usage"]["inputTokens"]
    #             result["usage"]["outputTokens"] += newresult["usage"]["outputTokens"]
    #             result["usage"]["expectedCost"] += newresult["usage"]["expectedCost"]
    #             result["historyParams"]["user"] = user

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
            return
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
                "model": model or configuration.get("model", None),
                "channel": 'chat',
                "type": "error",
                "actor": "user"
            }))
        ResponseSender.sendResponse({
            "rtlLayer": rtlLayer,
            "webhook": webhook,
            "data": {"error": str(error), "success": False},
            "reqBody": body,
            "headers": headers or {}
        })
        if rtlLayer or webhook:
            return
        return JSONResponse(status_code=400, content={"success": False, "error": str(error)})
