from pathlib import Path
from collections.abc import Callable
from inspect import signature
from typing import Any, cast

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import inspect as sqlalchemy_inspect
from starlette.responses import Response

from trading_assistant.db.base import Base
from trading_assistant.db.models import FocusStockORM
from trading_assistant.db.repositories import FocusImportMode, FocusStockRepository
from trading_assistant.db.session import build_engine, build_session_factory
from trading_assistant.pools.focus_pool import (
    FocusPoolImportError,
    FocusStockImportRow,
    FocusStockStatus,
    parse_focus_pool_csv_text,
)
from trading_assistant.settings import Settings
from trading_assistant.web.view_models import (
    build_backtest_view,
    build_candidates_view,
    build_dashboard_view,
    build_focus_pool_view,
    build_holdings_view,
    build_intraday_monitor_view,
    build_market_view,
)

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request) -> Response:
    focus_stocks = _load_focus_stocks_for_web()
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "request": request,
            "view": _build_focus_aware_view(build_dashboard_view, focus_stocks),
        },
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
    focus_stocks = _load_focus_stocks_for_web()
    return templates.TemplateResponse(
        request=request,
        name="candidates.html",
        context={
            "request": request,
            "view": _build_focus_aware_view(build_candidates_view, focus_stocks),
        },
    )


@router.get("/market", response_class=HTMLResponse)
def market(request: Request) -> Response:
    return templates.TemplateResponse(
        request=request,
        name="market.html",
        context={"request": request, "view": build_market_view()},
    )


@router.get("/intraday", response_class=HTMLResponse)
def intraday(request: Request) -> Response:
    focus_stocks = _load_focus_stocks_for_web()
    return templates.TemplateResponse(
        request=request,
        name="intraday.html",
        context={
            "request": request,
            "view": _build_focus_aware_view(build_intraday_monitor_view, focus_stocks),
        },
    )


@router.get("/focus-pool", response_class=HTMLResponse)
def focus_pool(request: Request) -> Response:
    focus_stocks = _load_focus_stocks_for_web()
    return templates.TemplateResponse(
        request=request,
        name="focus_pool.html",
        context={"request": request, "view": build_focus_pool_view(focus_stocks=focus_stocks)},
    )


@router.post("/focus-pool/import", response_class=HTMLResponse)
async def import_focus_pool(
    request: Request,
    mode: str = Form("merge"),
    file: UploadFile = File(...),
) -> Response:
    if mode not in ("merge", "replace"):
        return _focus_import_response(
            request,
            import_error="mode must be merge or replace",
            status_code=400,
        )
    _ensure_focus_table()
    raw_content = await file.read()
    try:
        csv_text = raw_content.decode("utf-8-sig")
        rows = parse_focus_pool_csv_text(csv_text)
    except (UnicodeDecodeError, FocusPoolImportError) as exc:
        return _focus_import_response(
            request,
            import_error=str(exc),
            status_code=400,
        )

    imported_count = _import_focus_rows(rows, mode=cast(FocusImportMode, mode))

    return _focus_import_response(
        request,
        import_result=f"已导入 {imported_count} 只关注股票",
        status_code=200,
    )


@router.get("/backtest", response_class=HTMLResponse)
def backtest(request: Request) -> Response:
    return templates.TemplateResponse(
        request=request,
        name="backtest.html",
        context={"request": request, "view": build_backtest_view()},
    )


def _focus_import_response(
    request: Request,
    *,
    import_result: str | None = None,
    import_error: str | None = None,
    status_code: int,
) -> Response:
    focus_stocks = _load_focus_stocks_for_web()
    return templates.TemplateResponse(
        request=request,
        name="focus_pool.html",
        context={
            "request": request,
            "view": build_focus_pool_view(
                focus_stocks=focus_stocks,
                import_result=import_result,
                import_error=import_error,
            ),
        },
        status_code=status_code,
    )


def _load_focus_stocks_for_web() -> list[FocusStockImportRow] | None:
    settings = Settings()
    engine = build_engine(settings.database_url)
    try:
        if not sqlalchemy_inspect(engine).has_table(FocusStockORM.__tablename__):
            return None
        session_factory = build_session_factory(engine)
        with session_factory() as session:
            repo = FocusStockRepository(session)
            return [_focus_row_from_orm(row) for row in repo.list_focus_stocks()]
    finally:
        engine.dispose()


def _build_focus_aware_view(
    builder: Callable[..., dict[str, Any]],
    focus_stocks: list[FocusStockImportRow] | None,
) -> dict[str, Any]:
    if "focus_stocks" in signature(builder).parameters:
        return builder(focus_stocks=focus_stocks)
    return builder()


def _ensure_focus_table() -> None:
    settings = Settings()
    engine = build_engine(settings.database_url)
    try:
        Base.metadata.create_all(engine)
    finally:
        engine.dispose()


def _import_focus_rows(rows: list[FocusStockImportRow], *, mode: FocusImportMode) -> int:
    settings = Settings()
    engine = build_engine(settings.database_url)
    try:
        Base.metadata.create_all(engine)
        session_factory = build_session_factory(engine)
        with session_factory() as session:
            repo = FocusStockRepository(session)
            return repo.upsert_many(rows, mode=mode)
    finally:
        engine.dispose()


def _focus_row_from_orm(row: FocusStockORM) -> FocusStockImportRow:
    return FocusStockImportRow(
        symbol=row.symbol,
        name=row.name,
        focus_reason=row.focus_reason,
        tags=tuple(tag.strip() for tag in row.tags.split("|") if tag.strip()),
        priority=row.priority,
        status=FocusStockStatus(row.status),
    )
