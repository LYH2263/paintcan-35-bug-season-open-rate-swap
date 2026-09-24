"""历史回读：只用写入时钉选在 input_json/result_json 内的口径原样返回。

季节窗配置属于"当场新测"的规则，不得在只读打开或保存窗口时重算旧记录，
因此这里不做任何 coverage/liters 的重新解析。
"""
import json


def _parse(raw):
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw or "{}")
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}


def decorate_history_row(conn, row):
    """返回库内钉选的原始结果；conn 不参与任何计算。"""
    item = dict(row)
    item["result"] = _parse(row.get("result_json"))
    item["input"] = _parse(row.get("input_json"))
    return item
