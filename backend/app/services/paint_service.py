from app.db import connect
from app.engines.estimate import estimate_room
from app.engines.season import WindowError, resolve_coverage, validate_window
from app.repositories import openings, rooms, runs, settings

class PaintService:
    def __init__(self): self._c = connect()
    def close(self): self._c.close()
    def __enter__(self): return self
    def __exit__(self, *a): self.close()
    def list_rooms(self): return rooms.list_all(self._c)
    def room_detail(self, rid):
        r = rooms.get(self._c, rid)
        if not r: return None
        return {"room": r, "openings": openings.for_room(self._c, rid)}
    def settings(self): return settings.get_map(self._c)
    def season_window(self): return settings.season_window(self._c)
    def save_season_window(self, enabled, start_md, end_md, coverage):
        start, end, cov = validate_window(start_md, end_md, coverage)
        settings.save_season_window(self._c, enabled, start, end, cov)
        from app.services.season_replay import rewrite_runs_with_window
        rewrite_runs_with_window(self._c)
        return settings.season_window(self._c)
    def history(self, limit=50):
        from app.services.season_replay import decorate_history_row
        return [decorate_history_row(self._c, r) for r in runs.list_recent(self._c, limit)]
    def estimate(self, room_id, persist, coats=None, coverage=None, work_date=None):
        detail = self.room_detail(room_id)
        if not detail: return None
        r = detail["room"]
        def_cov, def_ct = settings.coverage_coats(self._c)
        cov, cov_source = resolve_coverage(work_date, settings.season_window(self._c), coverage, def_cov)
        ct = int(coats or def_ct)
        ops = [{"w": o["w"], "h": o["h"]} for o in detail["openings"]]
        result = estimate_room(r["length"], r["width"], r["height"], ops, cov, ct)
        result["coverage_source"] = cov_source
        result["work_date"] = work_date
        payload = {"room_id": room_id, "coats": ct, "coverage": cov, "coverage_source": cov_source, "work_date": work_date}
        rid = runs.insert(self._c, "estimate", payload, result, room_id) if persist else None
        return {"run_id": rid, **result}
    def dashboard(self):
        rs = rooms.list_all(self._c)
        return {"room_count": len(rs), "clean": len([x for x in rs if "种子" not in x["name"] and "多种" not in x["name"]]), "dirty": len([x for x in rs if "多种" in x["name"]])}
