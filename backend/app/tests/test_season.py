import pytest
from app.engines.season import WindowError, in_window, parse_md, resolve_coverage, validate_window

WIN = {"enabled": True, "start_md": "06-01", "end_md": "08-31", "coverage": 6.0}

def test_parse_md_string_and_tuple():
    assert parse_md("06-01") == (6, 1)
    assert parse_md((7, 15)) == (7, 15)

def test_parse_md_rejects_bad_format():
    with pytest.raises(WindowError): parse_md("6/1")
    with pytest.raises(WindowError): parse_md("13-01")
    with pytest.raises(WindowError): parse_md("06-32")

def test_in_window_boundaries():
    assert in_window("2026-06-01", "06-01", "08-31")
    assert in_window("2026-08-31", "06-01", "08-31")
    assert in_window("2026-07-15", "06-01", "08-31")
    assert not in_window("2026-05-31", "06-01", "08-31")
    assert not in_window("2026-09-01", "06-01", "08-31")

def test_in_window_bad_date():
    with pytest.raises(WindowError): in_window("not-a-date", "06-01", "08-31")

def test_validate_window_ok():
    assert validate_window("6-1", "08-31", 6) == ("06-01", "08-31", 6.0)
    assert validate_window("06-01", "06-01", 6.5) == ("06-01", "06-01", 6.5)

def test_validate_window_rejects_nonpositive():
    with pytest.raises(WindowError): validate_window("06-01", "08-31", 0)
    with pytest.raises(WindowError): validate_window("06-01", "08-31", -2)

def test_validate_window_rejects_bad_order():
    with pytest.raises(WindowError): validate_window("08-31", "06-01", 6)

def test_resolve_window_hit_overrides_request_and_default():
    cov, source = resolve_coverage("2026-07-01", WIN, 10.0, 8.0)
    assert (cov, source) == (6.0, "window")

def test_resolve_outside_window_uses_request_override():
    cov, source = resolve_coverage("2026-05-01", WIN, 10.0, 8.0)
    assert (cov, source) == (10.0, "request")

def test_resolve_outside_window_uses_default():
    cov, source = resolve_coverage("2026-05-01", WIN, None, 8.0)
    assert (cov, source) == (8.0, "default")

def test_resolve_disabled_window_ignores_window():
    off = {**WIN, "enabled": False}
    cov, source = resolve_coverage("2026-07-01", off, None, 8.0)
    assert (cov, source) == (8.0, "default")

def test_resolve_no_work_date_skips_window():
    cov, source = resolve_coverage(None, WIN, None, 8.0)
    assert (cov, source) == (8.0, "default")

def test_resolve_request_override_takes_precedence_without_date():
    cov, source = resolve_coverage(None, WIN, 9.5, 8.0)
    assert (cov, source) == (9.5, "request")
