from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
from contextlib import asynccontextmanager

from config import Config
from src.controllers.modelController import router as model_router
from src.routes.chatBot_routes import router as chatbot_router
from src.routes.apiCall_routes import router as apiCall_router
from src.routes.config_routes import router as config_router
from src.controllers.bridgeController import router as bridge_router
from src.routes.v2.modelRouter import router as v2_router
from src.services.utils.apiservice import fetch
from src.services.commonServices.queueService.queueService import queue_obj
from src.services.utils.logger import logger
from src.routes.bridge_version_routes import router as bridge_version
from src.routes.image_process_routes import router as image_process_routes
from src.routes.utils_routes import router as utils_routes
from src.services.utils.utils import healthcheck


async def consume_messages_in_executor():
    await queue_obj.consume_messages()
    
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    logger.info("Starting up...")
    # Run the consumer in the background without blocking the main event loop
    await queue_obj.connect()
    await queue_obj.create_queue_if_not_exists()
    
    consume_task = None
    if Config.CONSUMER_STATUS.lower() == "true":
        consume_task = asyncio.create_task(consume_messages_in_executor())
    
    yield  # Startup logic is complete
    # Shutdown logic
    logger.info("Shutting down...")
    if consume_task:
        consume_task.cancel()
    await queue_obj.disconnect()
    try:
        if consume_task:
            await consume_task
    except asyncio.CancelledError:
        print("Consumer task was cancelled during shutdown.")

# Initialize the FastAPI app
app = FastAPI(debug=True, lifespan=lifespan)
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
async def healthcheckConnection():
    return await healthcheck()
            

@app.get("/5-sec")
async def bloking():
    try:
        async def blocking_io_function():
            response = await fetch("https://flow.sokt.io/func/scriDLT6j3lB")
            return response
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
app.include_router(utils_routes, prefix="/utils" )


if __name__ == "__main__":
    PORT = int(Config.PORT)
    uvicorn.run(app, host="0.0.0.0", port=PORT)