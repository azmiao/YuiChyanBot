import os
from collections.abc import Iterable
from typing import Any


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
