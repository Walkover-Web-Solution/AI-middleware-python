from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from src.middlewares.middleware import JWTMiddleware
import uvicorn
import os

from config import Config
from src.controllers.modelController import router as model_router



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

# Include routers
# app.add_middleware(JWTMiddleware)
app.include_router(model_router, prefix="/api/v1/model")

if __name__ == "__main__":
    PORT = int(Config.PORT)
    uvicorn.run(app, host="0.0.0.0", port=PORT)
