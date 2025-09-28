from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import startups, agents, jobs, notifications, logs
from database.connection import engine
from database import models
from services.scheduler_service import scheduler_service

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
app.include_router(jobs.router, prefix="/api/jobs", tags=["Scheduled Jobs"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(logs.router, prefix="/api/logs", tags=["Task Logs"])

@app.get("/")
async def root():
    return {
        "message": "NVIDIA Inception AI System",
        "version": "1.0.0",
        "endpoints": {
            "startups": "/api/startups",
            "agents": "/api/agents",
            "jobs": "/api/jobs",
            "notifications": "/api/notifications",
            "logs": "/api/logs",
            "docs": "/docs"
        }
    }

@app.on_event("startup")
async def startup_event():
    """Inicia o scheduler quando a aplicação sobe"""
    scheduler_service.start()

@app.on_event("shutdown")
async def shutdown_event():
    """Para o scheduler quando a aplicação para"""
    scheduler_service.stop()

@app.get("/health")
async def health_check():
    return {"status": "healthy"}