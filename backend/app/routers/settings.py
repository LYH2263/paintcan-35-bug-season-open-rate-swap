from fastapi import APIRouter, HTTPException
from app.engines.season import WindowError
from app.schemas.estimate import SeasonWindowRequest
from app.services.paint_service import PaintService
router = APIRouter()
@router.get("/settings")
def settings():
    with PaintService() as s: return s.settings()
@router.get("/settings/season-window")
def get_season_window():
    with PaintService() as s: return s.season_window()
@router.post("/settings/season-window")
def post_season_window(body: SeasonWindowRequest):
    with PaintService() as s:
        try:
            return s.save_season_window(body.enabled, body.start_md, body.end_md, body.coverage)
        except WindowError as e:
            raise HTTPException(status_code=400, detail=str(e))
