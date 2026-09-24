"""历史记录读取：升数与所用涂布率在写入时即钉选，只读打开不得重算或改写。"""
import json


def _parse(raw):
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw or "{}")
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}


def pinned_result(row):
    """返回写入时落库的结果（coverage/coverage_source/liters 已钉选）。

    不按当前季节窗或默认设置重新解析——改窗口、停用窗口都不得带跑旧条。
    """
    res = _parse(row.get("result_json") if "result_json" in row else row.get("result"))
    inp = _parse(row.get("input_json") if "input_json" in row else row.get("input"))
    # 仅在老数据缺字段时用落库入参补齐展示口径，仍不做任何重算。
    if "coverage_source" not in res and "coverage_source" in inp:
        res["coverage_source"] = inp["coverage_source"]
    if "work_date" not in res and "work_date" in inp:
        res["work_date"] = inp["work_date"]
    return res


def decorate_history_row(conn, row):
    item = dict(row)
    item["result"] = pinned_result(row)
    item["input"] = _parse(row.get("input_json"))
    return item
