"""FastAPI application entrypoint for AI-Powered E-Commerce Data Analyst Agent."""

import logging
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.routes import router as api_router
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("data_analyst_agent")

app = FastAPI(
    title="AI-Powered E-Commerce Data Analyst Agent API",
    description="Deterministic and conversational business intelligence agent for e-commerce datasets.",
    version="1.0.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", tags=["Health"])
async def health_check():
    """Service health and LLM configuration status."""
    return {
        "status": "healthy",
        "llm_configured": settings.is_llm_configured(),
        "model": settings.llm_model,
        "max_upload_size_mb": settings.max_upload_size_mb,
    }


# Global Exception Handler to ensure consistent ErrorResponse structure
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception processing %s: %s", request.url.path, str(exc), exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred during analytics processing.",
            "error_code": "INTERNAL_SERVER_ERROR",
            "suggestions": ["Please verify the uploaded CSV data or retry the request."],
        },
    )


# Register API endpoints
app.include_router(api_router)


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting API server on %s:%s", settings.backend_host, settings.backend_port)
    uvicorn.run(
        "app.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True,
    )
