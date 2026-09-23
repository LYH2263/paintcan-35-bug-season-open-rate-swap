"""Re-resolve seasonal coverage for history rows and window saves."""
import json
from app.engines.estimate import estimate_room
from app.engines.paint_volume import paint_liters
from app.engines.season import resolve_coverage
from app.repositories import openings, rooms, settings


def _parse(raw):
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw or "{}")
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}


def resolve_for_row(conn, row):
    inp = _parse(row.get("input_json") if "input_json" in row else row.get("input"))
    res = _parse(row.get("result_json") if "result_json" in row else row.get("result"))
    work_date = inp.get("work_date") or res.get("work_date")
    def_cov, def_ct = settings.coverage_coats(conn)
    window = settings.season_window(conn)
    cov, source = resolve_coverage(work_date, window, None, def_cov)
    ct = int(inp.get("coats") or res.get("coats") or def_ct)
    net = res.get("net_m2")
    if net is None:
        return res
    vol = paint_liters(float(net), float(cov), ct)
    out = dict(res)
    out["coverage"] = vol["coverage"]
    out["coats"] = vol["coats"]
    out["liters"] = vol["liters"]
    out["coverage_source"] = source
    return out


def decorate_history_row(conn, row):
    item = dict(row)
    item["result"] = resolve_for_row(conn, row)
    item["input"] = _parse(row.get("input_json"))
    return item


def rewrite_runs_with_window(conn):
    rows = conn.execute("SELECT * FROM calc_runs").fetchall()
    for row in rows:
        d = dict(row)
        fresh = resolve_for_row(conn, d)
        conn.execute(
            "UPDATE calc_runs SET result_json=? WHERE id=?",
            (json.dumps(fresh, ensure_ascii=False), d["id"]),
        )
    conn.commit()
