from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError  # Import RequestValidationError
from app.routes import endpoints


app = FastAPI(title="ML Service API")

app.include_router(endpoints.router, prefix="", tags=["Endpoints"])
