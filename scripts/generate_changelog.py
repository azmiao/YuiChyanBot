"""根据正式版本标签生成项目 Changelog。"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


VERSION_TAG_PATTERN = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")
COMMIT_PATTERN = re.compile(
    r"^(?P<type>[A-Za-z]+)(?:[^\w\s:(]+)?"
    r"(?:\((?P<scope>[^)]+)\))?\s*:\s*(?P<message>.+)$"
)
GITHUB_NOREPLY_PATTERN = re.compile(
    r"^(?:\d+\+)?(?P<username>[^@]+)@users\.noreply\.github\.com$",
    re.IGNORECASE,
)

CATEGORY_BY_TYPE = {
    "feat": "✨ 新功能",
    "fix": "🐛 Bug 修复",
    "patch": "🐛 Bug 修复",
    "perf": "🚀 性能优化",
    "refactor": "🎨 代码重构",
    "docs": "📚 文档",
    "deps": "🧩 依赖变更",
    "build": "🧩 依赖变更",
    "test": "🧪 测试",
    "ci": "⚙️ 持续集成",
    "chore": "🧹 日常维护",
    "style": "🧹 日常维护",
    "format": "🧹 日常维护",
    "config": "🧹 日常维护",
}
CATEGORY_ORDER = tuple(dict.fromkeys(CATEGORY_BY_TYPE.values())) + ("其他变更",)


@dataclass(frozen=True)
class Commit:
    subject: str
    author_name: str
    author_email: str
    category: str


def run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    return result.stdout


def parse_version_tag(tag: str) -> tuple[int, int, int] | None:
    match = VERSION_TAG_PATTERN.fullmatch(tag)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def get_release_tags() -> list[str]:
    tags = [line.strip() for line in run_git("tag", "--list").splitlines()]
    versions = [
        (version, tag)
        for tag in tags
        if (version := parse_version_tag(tag)) is not None
    ]
    return [tag for _, tag in sorted(versions, reverse=True)]


def get_previous_tag(tag: str, tags: list[str]) -> str | None:
    index = tags.index(tag)
    return tags[index + 1] if index + 1 < len(tags) else None


def read_commit_records(tag: str, previous_tag: str | None) -> list[str]:
    revision = f"{previous_tag}..{tag}" if previous_tag else tag
    output = run_git(
        "log",
        "--no-merges",
        "--format=%an%x1f%ae%x1f%s%x1e",
        revision,
    )
    return [record.strip() for record in output.split("\x1e") if record.strip()]


def format_author(name: str, email: str) -> str:
    match = GITHUB_NOREPLY_PATTERN.fullmatch(email.strip())
    return f"@{match.group('username')}" if match else name.strip()


def parse_commit_record(record: str) -> Commit:
    fields = record.split("\x1f", maxsplit=2)
    if len(fields) != 3:
        raise ValueError("Git 提交记录格式损坏")

    author_name, author_email, raw_subject = (field.strip() for field in fields)
    match = COMMIT_PATTERN.fullmatch(raw_subject)
    if not match:
        return Commit(raw_subject, author_name, author_email, "其他变更")

    commit_type = match.group("type").lower()
    scope = match.group("scope")
    message = match.group("message").strip()
    subject = f"*({scope})* {message}" if scope else message
    category = CATEGORY_BY_TYPE.get(commit_type, "其他变更")
    return Commit(subject, author_name, author_email, category)


def render_version(tag: str, tags: list[str]) -> str:
    if parse_version_tag(tag) is None:
        raise ValueError(f"不是正式版本标签：{tag}")
    if tag not in tags:
        raise ValueError(f"正式版本标签不存在：{tag}")

    run_git("rev-parse", "--verify", f"refs/tags/{tag}")
    previous_tag = get_previous_tag(tag, tags)
    commits = [parse_commit_record(record) for record in read_commit_records(tag, previous_tag)]
    grouped: dict[str, list[Commit]] = defaultdict(list)
    for commit in commits:
        grouped[commit.category].append(commit)

    date = run_git("log", "-1", "--format=%cs", tag).strip()
    lines = [f"## {tag.removeprefix('v')} ({date})"]
    for category in CATEGORY_ORDER:
        category_commits = grouped.get(category)
        if not category_commits:
            continue
        lines.extend(("", f"### {category}", ""))
        lines.extend(
            f"- {commit.subject} {format_author(commit.author_name, commit.author_email)}"
            for commit in category_commits
        )
    return "\n".join(lines) + "\n"


def render_changelog(tags: list[str]) -> str:
    if not tags:
        raise ValueError("仓库中没有正式版本标签")
    sections = [render_version(tag, tags).rstrip() for tag in tags]
    return "# 更新日志\n\n" + "\n\n".join(sections) + "\n"


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="根据正式版本标签生成项目 Changelog")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--tag", help="只生成指定正式版本的发布说明")
    mode.add_argument("--all", action="store_true", help="生成全部正式版本的 Changelog")
    parser.add_argument("--output", type=Path, help="将结果写入指定文件")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        tags = get_release_tags()
        content = render_changelog(tags) if args.all else render_version(args.tag, tags)
        if args.output:
            args.output.write_text(content, encoding="utf-8", newline="\n")
        else:
            sys.stdout.write(content)
        return 0
    except (subprocess.CalledProcessError, ValueError, OSError) as error:
        detail = error.stderr.strip() if isinstance(error, subprocess.CalledProcessError) else str(error)
        print(f"生成 Changelog 失败：{detail}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
