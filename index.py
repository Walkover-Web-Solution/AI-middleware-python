from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import atatus
from atatus.contrib.starlette import create_client, Atatus
from contextlib import asynccontextmanager
import src.services.utils.batch_script
from src.services.utils.batch_script import repeat_function
from config import Config
from src.controllers.modelController import router as model_router
from src.routes.chatBot_routes import router as chatbot_router
from src.routes.apiCall_routes import router as apiCall_router
from src.routes.config_routes import router as config_router
from src.controllers.bridgeController import router as bridge_router
from src.routes.v2.modelRouter import router as v2_router
from src.services.commonServices.queueService.queueService import queue_obj
from src.services.commonServices.queueService.queueLogService import sub_queue_obj
from src.services.utils.logger import logger
from src.routes.bridge_version_routes import router as bridge_version
from src.routes.image_process_routes import router as image_process_routes
from src.routes.utils_router import router as utils_router
from src.routes.rag_routes import router as rag_routes
from src.routes.Internal_routes import router as Internal_routes
from src.routes.testcase_routes import router as testcase_routes
from models.Timescale.connections import init_async_dbservice
from src.routes.runagents_routes import router as runagents_routes
from src.configs.model_configuration import init_model_configuration, background_listen_for_changes
from globals import *


atatus_client = atatus.get_client()
if atatus_client is None and (Config.ENVIROMENT == 'PRODUCTION'):
    logger.info("Initializing Atatus client...")
    atatus_client = create_client({
        'APP_NAME': 'Python - GTWY - Backend - PROD',
        'LICENSE_KEY': Config.ATATUS_LICENSE_KEY,
        'ANALYTICS': True,
        'ANALYTICS_CAPTURE_OUTGOING': True,
        'LOG_BODY': 'all'
    })

    
async def consume_messages_in_executor():
    await queue_obj.consume_messages()

async def consume_sub_messages_in_executor():
    await sub_queue_obj.consume_messages()
    
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    logger.info("Starting up...")
    await init_model_configuration()
    # Run the consumer in the background without blocking the main event loop
    await queue_obj.connect()
    await queue_obj.create_queue_if_not_exists()
    await sub_queue_obj.connect()
    await sub_queue_obj.create_queue_if_not_exists()
    
    consume_task = None
    consume_sub_task = None
    if Config.CONSUMER_STATUS.lower() == "true":
        consume_task = asyncio.create_task(consume_messages_in_executor())
        consume_sub_task = asyncio.create_task(consume_sub_messages_in_executor())
    
    asyncio.create_task(init_async_dbservice()) if Config.ENVIROMENT == 'LOCAL' else await init_async_dbservice()
    
    asyncio.create_task(repeat_function())

    logger.info("Starting MongoDB change stream listener as a background task.")
    change_stream_task = asyncio.create_task(background_listen_for_changes())
    
    yield  # Startup logic is complete
    
    # Shutdown logic
    logger.info("Shutting down...")
    
    logger.info("Shutting down MongoDB change stream listener.")
    change_stream_task.cancel()

    if consume_task:
        consume_task.cancel()
    if consume_sub_task:
        consume_sub_task.cancel()

    await queue_obj.disconnect()
    await sub_queue_obj.disconnect()

    try:
        if consume_task:
            await consume_task
        if consume_sub_task:
            await consume_sub_task
    except asyncio.CancelledError:
        logger.error("Consumer task was cancelled during shutdown.")
    
    try:
        await change_stream_task
    except asyncio.CancelledError:
        logger.info("MongoDB change stream listener task successfully cancelled.")

# Initialize the FastAPI app
app = FastAPI(debug=True, lifespan=lifespan)

app.add_middleware(Atatus, client=atatus_client)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=86400
)

# Healthcheck route
@app.get("/healthcheck")
async def healthcheck():
    return JSONResponse(status_code=200, content={
            "status": "OK running good... v1.2",
    })
            

@app.get("/90-sec")
async def bloking():
    try:
        async def blocking_io_function():
            await asyncio.sleep(90)  # Sleep for 2 minutes
            # response = await fetch("https://flow.sokt.io/func/scriDLT6j3lB")
            # return response
        result = await blocking_io_function()
        return JSONResponse(status_code=200, content={
                "status": "OK running good... v1.1",
                "api_result": result
            })
    except Exception as e:
        return JSONResponse(status_code=500, content={
            "status": "Error",
            "error": str(e)
        })
        


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"detail": "Custom error message", "errors": exc.errors()},
    )

# New route for streaming data
@app.get("/stream")
async def stream_data():
    async def generate():
        for i in range(100):
            yield f"data: {i}\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(generate(), media_type="text/event-stream")

# Include routers
app.include_router(model_router, prefix="/api/v1/model")
app.include_router(v2_router, prefix="/api/v2/model")
app.include_router(chatbot_router, prefix="/chatbot")
app.include_router(bridge_router, prefix="/bridge")
app.include_router(config_router, prefix="/api/v1/config")
app.include_router(apiCall_router, prefix="/functions")
app.include_router(bridge_version, prefix="/bridge/versions" )
app.include_router(image_process_routes, prefix="/image/processing" )
app.include_router(image_process_routes, prefix="/files" )
app.include_router(utils_router, prefix="/utils" )
app.include_router(rag_routes,prefix="/rag")
app.include_router(Internal_routes,prefix="/internal")
app.include_router(testcase_routes, prefix='/testcases')
app.include_router(runagents_routes, prefix='/publicAgent')


if __name__ == "__main__":
    PORT = int(Config.PORT)
    uvicorn.run(app, host="0.0.0.0", port=PORT)