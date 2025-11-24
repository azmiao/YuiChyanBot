import datetime
from email.utils import parsedate_to_datetime

from dateutil import parser, tz


def parse_datetime(dt_str: str) -> datetime.datetime | None:
    """
    通用时间字符串解析 -> 返回北京时间(datetime)
    支持 ISO8601, RFC822, 常见日志时间、无时区时间
    """
    if not dt_str:
        return None

    dt_obj = None

    # 1. 尝试 ISO8601 / 自由格式解析
    try:
        dt_obj = parser.parse(dt_str)
    except (ValueError, OverflowError):
        pass

    # 2. 尝试 RFC822 格式解析（例如 RSS / Email 时间）
    if dt_obj is None:
        try:
            dt_obj = parsedate_to_datetime(dt_str)
        except (TypeError, ValueError):
            pass

    if dt_obj is None:
        return None

    # 3. 如果没有时区信息，默认为 UTC
    if dt_obj.tzinfo is None:
        dt_obj = dt_obj.replace(tzinfo=datetime.timezone.utc)

    # 4. 转换到北京时间（UTC+8）
    beijing_tz = tz.gettz("Asia/Shanghai")
    dt_obj_beijing = dt_obj.astimezone(beijing_tz)

    return dt_obj_beijing


def format_datetime(dt: datetime.datetime, fmt: str = "%Y-%m-%d %H:%M:%S", tz_name: str = "Asia/Shanghai") -> str:
    """
    将 datetime 转换为指定时区和格式的字符串
    :param dt: 输入 datetime 对象（可带时区或无时区）
    :param fmt: 输出格式字符串（默认: 年-月-日 时:分:秒）
    :param tz_name: 指定时区名称（默认: 北京时间 Asia/Shanghai）
    :return: 格式化的时间字符串
    """
    if not isinstance(dt, datetime.datetime):
        raise TypeError("dt 必须是 datetime.datetime 类型")

    # 如果没有时区信息，默认为 UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)

    # 转换到指定时区
    target_tz = tz.gettz(tz_name)
    dt_in_tz = dt.astimezone(target_tz)

    # 按指定格式输出
    return dt_in_tz.strftime(fmt)