from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
import uvicorn
from starlette.exceptions import HTTPException as StarletteHTTPException
import os

from config import Config
from src.controllers.modelController import router as model_router
from src.routes.chatBot_routes import router as chatbot_router
from src.controllers.bridgeController import router as bridgeController
from src.routes.config_routes import router as configuration_router
# Initialize the FastAPI app
app = FastAPI(debug=True)

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
    return JSONResponse(status_code=200, content="OK running good...")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": "Custom error message", "errors": exc.errors()},
    )

# Include routers
app.include_router(model_router, prefix="/api/v1/model")
app.include_router(chatbot_router, prefix="/chatbot")
app.include_router(configuration_router, prefix="/api/v1/config")
app.include_router(bridgeController,prefix="/bridge")


if __name__ == "__main__":
    PORT = int(Config.PORT)
    uvicorn.run(app, host="0.0.0.0", port=PORT)
