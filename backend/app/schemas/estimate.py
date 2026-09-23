from pydantic import BaseModel

class EstimateRequest(BaseModel):
    room_id: int
    coats: int | None = None
    coverage: float | None = None
    work_date: str | None = None
    persist: bool = True

class SeasonWindowRequest(BaseModel):
    enabled: bool
    start_md: str
    end_md: str
    coverage: float
