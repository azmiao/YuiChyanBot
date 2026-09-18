import os
from collections.abc import Iterable
from datetime import datetime
from typing import Any


def build_auth_view(expiration: Any, now: datetime | None = None) -> dict:
    """把群授权到期时间转换为模板展示所需的标签信息。

    - 无授权记录：state = none
    - 已过期：state = expired，仅保留“已到期”标签，不再展示剩余时间和到期日期
    - 剩余不足 3 天：state = danger（红色）
    - 剩余不足 7 天：state = warning（橙色）
    - 其余：state = valid（蓝色）
    """
    if not expiration:
        return {"state": "none", "label": "未授权", "expires_at": "", "days_left": None}
    now = now or datetime.now()
    remaining = expiration - now
    if remaining.total_seconds() <= 0:
        return {"state": "expired", "label": "已到期", "expires_at": "", "days_left": None}
    days_left = max(remaining.days, 0)
    if days_left < 3:
        state = "danger"
    elif days_left < 7:
        state = "warning"
    else:
        state = "valid"
    return {
        "state": state,
        "label": f"剩余 {days_left} 天",
        "expires_at": expiration.strftime("%Y-%m-%d"),
        "days_left": days_left,
    }


def _service_directory(file_path: str) -> str:
    return os.path.normcase(os.path.normpath(os.path.dirname(file_path)))


def _command_list(help_cmd: Any) -> list[str]:
    if not help_cmd:
        return []
    if isinstance(help_cmd, str):
        return [help_cmd]
    if isinstance(help_cmd, Iterable):
        return [str(command) for command in help_cmd if str(command).strip()]
    return [str(help_cmd)]


def attach_help_commands(help_list: list[dict], services: Iterable[Any]) -> list[dict]:
    commands_by_directory: dict[str, list[str]] = {}
    for service in services:
        service_directory = _service_directory(service.file_path)
        commands = commands_by_directory.setdefault(service_directory, [])
        for command in _command_list(service.help_cmd):
            if command not in commands:
                commands.append(command)

    result = []
    for help_body in help_list:
        item = dict(help_body)
        item["help_commands"] = commands_by_directory.get(
            _service_directory(os.fspath(help_body["path"])), []
        )
        result.append(item)
    return result
