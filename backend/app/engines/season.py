"""季节性涂布率窗口：按施工日的月日判定是否落在窗内。"""

class WindowError(ValueError):
    """窗口配置非法（月日格式错、顺序非法、窗内率非正）。"""

def parse_md(value) -> tuple[int, int]:
    """接受 'MM-DD' 字符串，或 (month, day) 整数序列。"""
    if isinstance(value, str):
        parts = value.split("-")
        if len(parts) != 2:
            raise WindowError(f"月日格式须为 MM-DD: {value!r}")
        try:
            month, day = int(parts[0]), int(parts[1])
        except ValueError:
            raise WindowError(f"月日格式须为 MM-DD: {value!r}")
    else:
        try:
            month, day = int(value[0]), int(value[1])
        except (TypeError, ValueError, IndexError):
            raise WindowError(f"月日格式须为 MM-DD: {value!r}")
    if not 1 <= month <= 12 or not 1 <= day <= 31:
        raise WindowError(f"月日越界: {month:02d}-{day:02d}")
    return month, day

def md_key(value) -> int:
    month, day = parse_md(value)
    return month * 100 + day

def validate_window(start_md, end_md, coverage):
    """非正窗内率或起止顺序非法即抛 WindowError；返回规整后的 (start, end, coverage)。"""
    start = parse_md(start_md)
    end = parse_md(end_md)
    cov = float(coverage)
    if cov <= 0:
        raise WindowError("窗内涂布率须为正数")
    if md_key(start) > md_key(end):
        raise WindowError("起止顺序非法：起月日不得晚于止月日（暂不支持跨年窗口）")
    return f"{start[0]:02d}-{start[1]:02d}", f"{end[0]:02d}-{end[1]:02d}", cov

def in_window(work_date: str, start_md: str, end_md: str) -> bool:
    """work_date 为 ISO 日期（YYYY-MM-DD），仅按月日比较；start<=end，不支持跨年。"""
    date_part = work_date.strip()[:10]
    try:
        cur = md_key(date_part[5:7] + "-" + date_part[8:10])
    except WindowError:
        raise WindowError(f"施工日格式须为 YYYY-MM-DD: {work_date!r}")
    return md_key(start_md) <= cur <= md_key(end_md)

def resolve_coverage(work_date, window, request_coverage, default_coverage):
    """窗内率 > 请求体覆盖值 > 系统默认率。window 停用或缺字段时跳过窗内判定。"""
    if work_date and window and window.get("enabled"):
        try:
            if in_window(work_date, window["start_md"], window["end_md"]):
                return float(window["coverage"]), "window"
        except (KeyError, WindowError):
            pass
    if request_coverage is not None:
        return float(request_coverage), "request"
    return float(default_coverage), "default"


def resolve_coverage_for_work_date(work_date, window, default_coverage):
    """Alias used by history replay paths."""
    return resolve_coverage(work_date, window, None, default_coverage)
