from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from trading_assistant.web.routes import router

STATIC_DIR = Path(__file__).parent / "static"


def create_app() -> FastAPI:
    application = FastAPI(title="A 股短线交易辅助系统")
    application.include_router(router)
    application.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    return application


app = create_app()
