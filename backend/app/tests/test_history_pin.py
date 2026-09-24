"""钉选回归：写入时确定的涂布率/升数，打开与改窗都不得变动。"""
import pytest

import app.db as db_mod
from app.seed import init_db
from app.services.paint_service import PaintService


@pytest.fixture
def svc(tmp_path, monkeypatch):
    monkeypatch.setattr(db_mod, "DB_PATH", tmp_path / "test.db")
    init_db()
    with PaintService() as s:
        yield s


def _by_id(items):
    return {h["id"]: h for h in items}


def _raw_results():
    with db_mod.connect() as c:
        return {r["id"]: r["result_json"] for r in c.execute("SELECT id, result_json FROM calc_runs").fetchall()}


def test_write_pins_window_and_request_rates(svc):
    # 窗内率 6 压过请求率 10；窗外按请求率 10。
    svc.save_season_window(True, "06-01", "08-31", 6.0)
    r_in = svc.estimate(1, True, coverage=10.0, work_date="2026-07-15")
    r_out = svc.estimate(1, True, coverage=10.0, work_date="2026-05-01")

    assert (r_in["coverage"], r_in["coverage_source"], r_in["liters"]) == (6.0, "window", 15.47)
    assert (r_out["coverage"], r_out["coverage_source"], r_out["liters"]) == (10.0, "request", 9.28)

    items = _by_id(svc.history())
    assert (items[r_in["run_id"]]["result"]["coverage"],
            items[r_in["run_id"]]["result"]["coverage_source"],
            items[r_in["run_id"]]["result"]["liters"]) == (6.0, "window", 15.47)
    assert (items[r_out["run_id"]]["result"]["coverage"],
            items[r_out["run_id"]]["result"]["coverage_source"],
            items[r_out["run_id"]]["result"]["liters"]) == (10.0, "request", 9.28)


def test_changing_window_does_not_move_old_rows(svc):
    svc.save_season_window(True, "06-01", "08-31", 6.0)
    r_in = svc.estimate(1, True, coverage=10.0, work_date="2026-07-15")
    r_out = svc.estimate(1, True, coverage=10.0, work_date="2026-05-01")
    pinned_before = {rid: txt for rid, txt in _raw_results().items() if rid in (r_in["run_id"], r_out["run_id"])}

    # 若仍按现行窗重算，两条都会被带成窗内率 3、30.94 升。
    svc.save_season_window(True, "01-01", "12-31", 3.0)
    items = _by_id(svc.history())
    assert (items[r_in["run_id"]]["result"]["coverage"], items[r_in["run_id"]]["result"]["liters"]) == (6.0, 15.47)
    assert (items[r_out["run_id"]]["result"]["coverage"], items[r_out["run_id"]]["result"]["liters"]) == (10.0, 9.28)
    # 停用窗口同样不得带跑旧条。
    svc.save_season_window(False, "01-01", "12-31", 3.0)
    items = _by_id(svc.history())
    assert (items[r_in["run_id"]]["result"]["coverage_source"],
            items[r_in["run_id"]]["result"]["coverage"],
            items[r_in["run_id"]]["result"]["liters"]) == ("window", 6.0, 15.47)
    assert (items[r_out["run_id"]]["result"]["coverage_source"],
            items[r_out["run_id"]]["result"]["coverage"],
            items[r_out["run_id"]]["result"]["liters"]) == ("request", 10.0, 9.28)
    pinned_after = _raw_results()
    assert pinned_after[r_in["run_id"]] == pinned_before[r_in["run_id"]]
    assert pinned_after[r_out["run_id"]] == pinned_before[r_out["run_id"]]


def test_saving_window_and_reading_history_never_rewrites_stored_rows(svc):
    svc.save_season_window(True, "06-01", "08-31", 6.0)
    svc.estimate(1, True, coverage=10.0, work_date="2026-07-15")
    snapshot = _raw_results()

    svc.save_season_window(False, "06-01", "08-31", 99.0)
    svc.history()
    svc.history(limit=5)

    assert _raw_results() == snapshot


def test_fresh_estimate_still_uses_current_window_rules(svc):
    # 改窗后的当场新测走现行规则，不影响旧条。
    svc.save_season_window(True, "06-01", "08-31", 6.0)
    old = svc.estimate(1, True, coverage=10.0, work_date="2026-07-15")
    svc.save_season_window(True, "06-01", "08-31", 5.0)
    new = svc.estimate(1, True, coverage=10.0, work_date="2026-07-15")
    assert new["coverage"] == 5.0
    assert _by_id(svc.history())[old["run_id"]]["result"]["coverage"] == 6.0
