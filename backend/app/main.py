import logging
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.firebase import init_firebase
from app.core.logging_config import configure_logging
from app.api.routes import router as api_router


def create_app() -> FastAPI:
    # Load .env file (local dev)
    load_dotenv()
    configure_logging()
    init_firebase()

    app = FastAPI(title="DethiAI Backend", version="0.1.0")

    # Adjust CORS as needed for your frontend domains
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    app.include_router(api_router)
    logging.getLogger(__name__).info("Application startup complete")
    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
