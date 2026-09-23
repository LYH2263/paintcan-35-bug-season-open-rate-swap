import sqlite3

def get_map(conn): return {r["key"]: r["value"] for r in conn.execute("SELECT * FROM settings").fetchall()}
def coverage_coats(conn):
    m = get_map(conn)
    return float(m.get("coverage", "8")), int(m.get("coats", "2"))

def season_window(conn):
    """从 settings 键拼装窗口；窗内率缺失或非正视为未配置（仅停用状态可返回）。"""
    m = get_map(conn)
    enabled = m.get("season_window_enabled", "0") == "1"
    try:
        return {
            "enabled": enabled,
            "start_md": m["season_window_start_md"],
            "end_md": m["season_window_end_md"],
            "coverage": float(m["season_window_coverage"]),
        }
    except (KeyError, TypeError, ValueError):
        return {"enabled": False, "start_md": None, "end_md": None, "coverage": None}

def save_season_window(conn, enabled, start_md, end_md, coverage):
    values = {
        "season_window_enabled": "1" if enabled else "0",
        "season_window_start_md": start_md,
        "season_window_end_md": end_md,
        "season_window_coverage": str(coverage),
    }
    conn.executemany(
        "INSERT INTO settings(key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        list(values.items()),
    )
    conn.commit()
