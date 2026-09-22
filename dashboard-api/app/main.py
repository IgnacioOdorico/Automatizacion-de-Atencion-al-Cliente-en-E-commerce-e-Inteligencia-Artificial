from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import (
    auth,
    connections,
    dashboard,
    metrics,
    monitoring_conversations,
    monitoring_feed,
    monitoring_workflows,
    orders,
    products,
    tickets,
)

def create_app() -> FastAPI:
    docs = settings.dashboard_enable_docs
    application = FastAPI(
        title=settings.app_name,
        docs_url="/docs" if docs else None,
        redoc_url="/redoc" if docs else None,
        openapi_url="/openapi.json" if docs else None,
    )

    # Whitelist explícita de orígenes, métodos y headers: nunca `*`.
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "Accept"],
    )

    @application.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    application.include_router(auth.router)
    application.include_router(connections.router)
    application.include_router(dashboard.router)
    application.include_router(metrics.router)
    application.include_router(orders.router)
    application.include_router(tickets.router)
    application.include_router(products.router)
    application.include_router(monitoring_feed.router)
    application.include_router(monitoring_conversations.router)
    application.include_router(monitoring_workflows.router)
    return application


app = create_app()