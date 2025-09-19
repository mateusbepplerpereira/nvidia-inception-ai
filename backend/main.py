from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import startups, agents
from database.connection import engine
from database import models

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="NVIDIA Inception AI",
    description="AI Agent System for Startup Discovery and Analysis",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(startups.router, prefix="/api/startups", tags=["Startups"])
app.include_router(agents.router, prefix="/api/agents", tags=["Agents"])

@app.get("/")
async def root():
    return {
        "message": "NVIDIA Inception AI System",
        "version": "1.0.0",
        "endpoints": {
            "startups": "/api/startups",
            "agents": "/api/agents",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}