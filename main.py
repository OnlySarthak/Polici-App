from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.chatbot import router as chatbot_router
from app.routers.dashboard import router as dashboard_router
from app.routers.admin import router as admin_router
from app.database.init_db import init_database

def create_app() -> FastAPI:
    """
    Factory function to initialize and configure the FastAPI application.
    """
    # Sync database schema (create tables / add missing columns)
    init_database()

    app = FastAPI(
        title="Insurance Intelligence Engine",
        description="Production-grade asynchronous FastAPI architecture for Insurance Intelligence Engine.",
        version="1.0.0"
    )

    # Mount CORS middleware for cross-origin requests
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Incorporate structural sub-routers
    app.include_router(chatbot_router)
    app.include_router(dashboard_router)
    app.include_router(admin_router)

    return app

app = create_app()

@app.get("/")
async def health_check():
    """
    Health check endpoint for the Insurance Intelligence Engine.
    """
    return {"status": "ok", "service": "Insurance Intelligence Engine"}
