import json

import pytest

from app import db, seed
from app.services.paint_service import PaintService

NET_M2 = 46.41  # 房间 1（客厅）的净面积，来自种子数据
COATS = 2


@pytest.fixture()
def svc(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "app.db")
    seed.init_db()
    with PaintService() as s:
        yield s


def _by_id(items):
    return {it["id"]: it for it in items}


def _stored_result(svc, run_id):
    row = svc._c.execute("SELECT result_json FROM calc_runs WHERE id=?", (run_id,)).fetchone()
    return json.loads(row["result_json"])


def test_in_window_write_pinned_after_window_change_and_disable(svc):
    svc.save_season_window(True, "06-01", "08-31", 6.0)
    r = svc.estimate(1, True, work_date="2026-07-15")
    assert r["coverage"] == 6.0 and r["coverage_source"] == "window"
    assert r["liters"] == round(NET_M2 * COATS / 6.0, 2)
    run_id = r["run_id"]

    # 改窗口覆盖率：旧条不得被带跑
    svc.save_season_window(True, "06-01", "08-31", 9.0)
    item = _by_id(svc.history())[run_id]
    assert item["result"]["coverage"] == 6.0
    assert item["result"]["coverage_source"] == "window"
    assert item["result"]["liters"] == round(NET_M2 * COATS / 6.0, 2)

    # 停用窗口：窗内写入的旧条仍是窗内口径
    svc.save_season_window(False, "06-01", "08-31", 9.0)
    item = _by_id(svc.history())[run_id]
    assert item["result"]["coverage"] == 6.0
    assert item["result"]["coverage_source"] == "window"


def test_outside_window_request_rate_pinned_after_disable(svc):
    svc.save_season_window(True, "06-01", "08-31", 6.0)
    r = svc.estimate(1, True, coverage=10.0, work_date="2026-05-01")
    assert r["coverage"] == 10.0 and r["coverage_source"] == "request"
    assert r["liters"] == round(NET_M2 * COATS / 10.0, 2)
    run_id = r["run_id"]

    # 旧实现会按当前默认率 8 重算成 11.6；钉选后必须仍是请求率口径
    svc.save_season_window(False, "06-01", "08-31", 6.0)
    item = _by_id(svc.history())[run_id]
    assert item["result"]["coverage"] == 10.0
    assert item["result"]["coverage_source"] == "request"
    assert item["result"]["liters"] == round(NET_M2 * COATS / 10.0, 2)


def test_saving_window_and_reading_history_do_not_rewrite_stored_rows(svc):
    svc.save_season_window(True, "06-01", "08-31", 6.0)
    run_id = svc.estimate(1, True, work_date="2026-07-15")["run_id"]
    before = _stored_result(svc, run_id)

    svc.save_season_window(True, "06-01", "08-31", 5.0)
    svc.save_season_window(False, "06-01", "08-31", 5.0)
    svc.history()  # 只读打开
    assert _stored_result(svc, run_id) == before


def test_new_estimate_follows_current_window_rules(svc):
    svc.save_season_window(True, "06-01", "08-31", 6.0)
    assert svc.estimate(1, False, work_date="2026-07-15")["coverage_source"] == "window"

    svc.save_season_window(False, "06-01", "08-31", 6.0)
    fresh = svc.estimate(1, False, work_date="2026-07-15")
    assert fresh["coverage"] == 8.0 and fresh["coverage_source"] == "default"
