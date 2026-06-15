from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.responses import Response

from trading_assistant.web.view_models import (
    build_backtest_view,
    build_candidates_view,
    build_dashboard_view,
    build_holdings_view,
)

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request) -> Response:
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"request": request, "view": build_dashboard_view()},
    )


@router.get("/holdings", response_class=HTMLResponse)
def holdings(request: Request) -> Response:
    return templates.TemplateResponse(
        request=request,
        name="holdings.html",
        context={"request": request, "view": build_holdings_view()},
    )


@router.get("/candidates", response_class=HTMLResponse)
def candidates(request: Request) -> Response:
    return templates.TemplateResponse(
        request=request,
        name="candidates.html",
        context={"request": request, "view": build_candidates_view()},
    )


@router.get("/backtest", response_class=HTMLResponse)
def backtest(request: Request) -> Response:
    return templates.TemplateResponse(
        request=request,
        name="backtest.html",
        context={"request": request, "view": build_backtest_view()},
    )
