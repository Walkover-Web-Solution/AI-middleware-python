from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config import Config
from src.controllers.modelController import router as model_router
from src.routes.chatBot_routes import router as chatbot_router
from src.routes.config_routes import router as config_router
from src.controllers.bridgeController import router as bridge_router
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
    return JSONResponse(status_code=200, content="OK running good... v1")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"detail": "Custom error message", "errors": exc.errors()},
    )

# Include routers
app.include_router(model_router, prefix="/api/v1/model")
app.include_router(chatbot_router, prefix="/chatbot")
app.include_router(bridge_router, prefix="/bridge")
app.include_router(config_router, prefix="/api/v1/config")

if __name__ == "__main__":
    PORT = int(Config.PORT)
    uvicorn.run(app, host="0.0.0.0", port=PORT)
