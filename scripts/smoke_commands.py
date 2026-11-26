#!/usr/bin/env python3
"""Extract and optionally run commands documented in Markdown.

Reads fenced shell blocks from AGENTS.md, README.md and docs/**/*.md, tracks
`cd` lines inside each block, classifies commands, and optionally executes the
safe ones. Setup commands (venv/pip/install), tests, servers, and dangerous
commands are never executed unless their category is explicitly requested.

Usage:
    python smoke_commands.py --root .
    python smoke_commands.py --root . --run-safe
    python smoke_commands.py --root . --run safe,info,test --timeout 60
    python smoke_commands.py --root . --json
"""

from __future__ import annotations

import argparse
import json
import os
import posixpath
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


def configure_stdio() -> None:
    """Keep non-ASCII repository content from crashing output."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError):
            pass


configure_stdio()

SHELL_LANGS = {"bash", "sh", "shell", "console", "powershell", "ps1", "pwsh", "cmd", "bat"}
FENCE_RE = re.compile(r"^\s*(```|~~~)\s*([A-Za-z0-9_+.-]*)")
SKIP_DIRS = {
    ".git", "node_modules", "venv", ".venv", "dist", "build", "out", "target",
    ".next", ".nuxt", "coverage", "test-results", "playwright-report",
    "nworktree", "worktrees", ".worktrees", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", ".tox", ".nox",
}
PLACEHOLDER_RE = re.compile(r"(<[^>]+>|\{[^}]+\}|\.\.\.|YOUR_|your-|example\.com)")
INLINE_PYTHON_RE = re.compile(r"\bpython(?:3|\.exe)?\s+-c\b", re.IGNORECASE)
GRADLEW_RE = re.compile(r"(?:^|[/\\])gradlew(?:\.bat)?\b", re.IGNORECASE)
SCRIPT_SETUP_RE = re.compile(r"(?:^|[/\\])(?:setup|install|bootstrap|provision)\.sh\b", re.IGNORECASE)
SCRIPT_SERVER_RE = re.compile(r"(?:^|[/\\])(?:run|start|serve|dev)\.sh\b", re.IGNORECASE)
SETUP = (
    "python -m venv", "python3 -m venv", "py -m venv",
    "pip install", "python -m pip install", "python3 -m pip install",
    "poetry install", "uv sync", "pipenv install",
    "npm install", "npm ci", "pnpm install", "yarn install",
    "bundle install", "composer install", "go mod download",
    "cargo fetch", "dotnet restore",
    "choco install", "winget install", "scoop install", "brew install",
    "apt-get install", "apt install", "dnf install", "pacman -s", "apk add",
)

DANGEROUS = (
    "rm ", "rmdir", "del ", "erase ", "format ", "mkfs", "dd if=",
    "drop database", "drop table", "truncate ", "delete from",
    "git push", "git reset", "git clean", "git rebase",
    "npm publish", "pnpm publish", "yarn publish", "cargo publish", "twine upload",
    "build:backend", "deploy", "systemctl", "sudo ", "su ",
    "docker compose down", "docker system prune", "kubectl delete",
    "terraform apply", "terraform destroy", "helm uninstall",
    "fly deploy", "vercel --prod", "netlify deploy",
    "aws ", "gcloud ", "az ", "psql ", "mysql ",
    "createdb ", "dropdb ", "pg_ctl ", "initdb ",
)
SAFE_FLAGS = ("check:map-local", "config --format json")
SERVICE_CMD_RE = re.compile(
    r"(?:^|[;&|]\s*)service\s+[A-Za-z0-9_.-]+", re.IGNORECASE
)
SAFE_FLAG_RE = re.compile(
    r"(?:^|\s)--(?:help|version|dry-run|collect-only|list|list-tests"
    r"|showconfig|print-config|noemit)(?:\s|$)"
)
SERVER = (
    "uvicorn", "gunicorn", "flask run", "runserver", "npm run dev",
    "npm run start", "pnpm dev", "pnpm start", "yarn dev", "yarn start",
    "vite", "next dev", "nuxt dev", "nodemon", "go run", "cargo run",
    "dotnet run", "rails server", "php -s", "docker compose up",
)
TEST = (
    "pytest", "vitest", "jest", "playwright test", "cypress ", "go test",
    "cargo test", "dotnet test", "mvn test", "gradle test", "npm test",
    "npm run test", "pnpm test", "yarn test", "rspec", "phpunit", "ruby -itest",
)
INFO = (
    "pwd", "ls", "cat ", "git status", "git log", "git diff", "git branch",
    "node --version", "python --version", "python3 --version", "npm --version",
    "pnpm --version", "yarn --version", "go version", "cargo --version",
    "dotnet --version", "java -version", "php --version", "ruby --version",
)
BUILD = (
    "npm run build", "pnpm build", "pnpm run build", "yarn build",
    "vite build", "next build", "nuxt build", "go build", "cargo build",
    "dotnet build", "mvn package", "mvn verify", "docker build",
)

DOCKER_RE = re.compile(r"^docker(\s+compose)?\b", re.IGNORECASE)
DOCKER_READONLY = (
    "compose ps", "compose logs", "compose config", "compose images",
    "compose top", "compose version", "docker ps", "docker logs",
    "docker images", "docker version", "docker info", "docker inspect",
    "docker stats",
)
FRAGMENT_RE = re.compile(
    r"^(?:build|push|pull|up|down|logs|exec|ps|config|restart|stop|start"
    r"|images|top|version|rm)(?:\s+-{1,2}[A-Za-z0-9-]+)*$",
    re.IGNORECASE,
)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return ""


def rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def collect_markdown(root: Path) -> list[Path]:
    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            d for d in dirnames
            if d not in SKIP_DIRS and not (d.startswith(".") and d not in {
                ".github", ".gitlab", ".kilo", ".claude", ".cursor", ".agents",
            })
        )
        for name in sorted(filenames):
            path = Path(dirpath) / name
            relative = rel(path, root)
            if name in {"AGENTS.md", "README.md"} or (
                "docs" in Path(relative).parts and path.suffix.lower() in {".md", ".mdx"}
            ):
                files.append(path)
    return files


def normalize_cwd(current: str, target: str) -> str:
    target = target.strip().strip('"').strip("'")
    if target.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:", target):
        return target
    joined = posixpath.normpath(posixpath.join(current or ".", target.replace("\\", "/")))
    return "" if joined == "." else joined


def extract(path: Path, root: Path) -> list[dict[str, Any]]:
    commands: list[dict[str, Any]] = []
    in_fence = False
    lang = ""
    cwd = ""

    for number, line in enumerate(read_text(path).splitlines(), 1):
        fence = FENCE_RE.match(line)
        if fence:
            if not in_fence:
                in_fence = True
                lang = fence.group(2).lower()
                cwd = ""
            else:
                in_fence = False
                lang = ""
            continue
        if not in_fence or lang not in SHELL_LANGS:
            continue

        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.endswith("\\"):
            continue
        if stripped.startswith(("$ ", "> ", "PS> ")):
            stripped = re.sub(r"^(?:\$|>|PS>)\s+", "", stripped)

        if stripped.startswith("cd "):
            cwd = normalize_cwd(cwd, stripped[3:])
            continue
        if not stripped:
            continue

        commands.append({
            "file": rel(path, root),
            "line": number,
            "cwd": cwd or ".",
            "command": stripped,
        })
    return commands


def strip_shell_comment(command: str) -> str:
    """Drop an unquoted shell comment without touching quoted arguments."""
    quote = ""
    escaped = False
    for index, char in enumerate(command):
        if escaped:
            escaped = False
        elif char == "\\" and quote != "'":
            escaped = True
        elif quote:
            if char == quote:
                quote = ""
        elif char in "\"'":
            quote = char
        elif char == "#" and (index == 0 or command[index - 1].isspace()):
            return command[:index].rstrip()
    return command.rstrip()


def has_shell_operator(command: str) -> bool:
    """Detect unquoted shell operators without splitting quoted arguments."""
    command = strip_shell_comment(command)
    quote = ""
    escaped = False
    index = 0
    while index < len(command):
        char = command[index]
        if escaped:
            escaped = False
        elif char == "\\" and quote != "'":
            escaped = True
        elif quote:
            if char == quote:
                quote = ""
        elif char in "\"'":
            quote = char
        elif command.startswith(("&&", "||", "$(", "`"), index) or char in ";|<>":
            return True
        index += 1
    return False


def classify(item: dict[str, Any]) -> tuple[str, str]:
    command = item["command"]
    clean = strip_shell_comment(command)
    lower = clean.lower()
    cwd = item["cwd"]

    if cwd.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:", cwd):
        return "skip", "working directory outside repository"
    if has_shell_operator(clean):
        return "skip", "compound command or shell operator"
    if PLACEHOLDER_RE.search(clean):
        return "template", "contains a placeholder"
    if DOCKER_RE.match(clean):
        if any(token in lower for token in DOCKER_READONLY):
            return "info", "read-only docker query"
        return "dangerous", "docker command changes containers or host state"
    if FRAGMENT_RE.match(clean):
        return "skip", "fragment of a multi-line command block"
    if any(token in lower for token in DANGEROUS):
        if "systemctl" in lower and any(
            word in lower for word in ("status", "is-active", "list-units", "cat")
        ):
            return "info", "read-only systemctl query"
        return "dangerous", "mutating or destructive command"
    if SERVICE_CMD_RE.search(clean):
        return "dangerous", "mutates a system service"
    if INLINE_PYTHON_RE.search(clean):
        return "skip", "inline Python code"
    if SCRIPT_SETUP_RE.search(clean):
        return "setup", "runs an install/setup script"
    if SCRIPT_SERVER_RE.search(clean):
        return "server", "runs a long-running start script"
    if any(token in lower for token in SETUP):
        return "setup", "installs dependencies or creates an environment"
    if SAFE_FLAG_RE.search(lower) or any(token in lower for token in SAFE_FLAGS):
        return "safe", "read-only flag"
    if GRADLEW_RE.search(clean):
        if "test" in lower:
            return "test", "Gradle test task"
        return "build", "Gradle build/quality task"
    if any(token in lower for token in TEST):
        return "test", "test command"
    if any(token in lower for token in SERVER):
        return "server", "starts a long-running server"
    if any(token in lower for token in BUILD):
        return "build", "build command"
    if lower.startswith(INFO) or any(lower.startswith(token + " ") for token in INFO):
        return "info", "read-only information command"
    return "unknown", "not classified"


def run_one(item: dict[str, Any], root: Path, timeout: int) -> None:
    cwd = (root / item["cwd"]).resolve()
    started = time.monotonic()
    try:
        result = subprocess.run(
            item["command"],
            cwd=str(cwd),
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        item["exit_code"] = result.returncode
        output = (result.stdout or "") + (result.stderr or "")
        item["output"] = output.strip()[-1500:]
        item["status"] = "pass" if result.returncode == 0 else "fail"
    except subprocess.TimeoutExpired:
        item["status"] = "timeout"
        item["exit_code"] = None
        item["output"] = f"timed out after {timeout}s"
    except OSError as exc:
        item["status"] = "error"
        item["exit_code"] = None
        item["output"] = str(exc)
    item["seconds"] = round(time.monotonic() - started, 2)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="repository root (default: .)")
    parser.add_argument("--run-safe", action="store_true", help="run safe and info commands")
    parser.add_argument("--run-tests", action="store_true", help="also run test commands")
    parser.add_argument("--run", help="comma-separated categories to run, e.g. safe,info,test")
    parser.add_argument("--timeout", type=int, default=20, help="seconds per command (default: 20)")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument("--quiet", action="store_true", help="only show failures")
    parser.add_argument("--max-commands", type=int, default=300, help="stop after N commands")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2

    categories: set[str] = set()
    if args.run_safe:
        categories.update({"safe", "info"})
    if args.run_tests:
        categories.add("test")
    if args.run:
        categories.update(part.strip() for part in args.run.split(",") if part.strip())

    items: list[dict[str, Any]] = []
    for path in collect_markdown(root):
        items.extend(extract(path, root))
        if len(items) >= args.max_commands:
            break
    items = items[: args.max_commands]

    for item in items:
        category, reason = classify(item)
        item["category"] = category
        item["reason"] = reason

    if categories:
        for item in items:
            if item["category"] in categories:
                run_one(item, root, args.timeout)

    if args.json:
        print(json.dumps({
            "root": str(root),
            "commands": items,
            "summary": {
                "total": len(items),
                "by_category": {
                    category: sum(1 for item in items if item["category"] == category)
                    for category in sorted({item["category"] for item in items})
                },
                "executed": sum(1 for item in items if "status" in item),
                "failed": sum(
                    1 for item in items
                    if item.get("status") in {"fail", "timeout", "error"}
                ),
            },
        }, indent=2, ensure_ascii=False))
    else:
        print("Command smoke check")
        print(f"root: {root}")
        print(f"commands: {len(items)} | executed: {sum(1 for item in items if 'status' in item)}")
        counts: dict[str, int] = {}
        for item in items:
            counts[item["category"]] = counts.get(item["category"], 0) + 1
        print("categories: " + ", ".join(f"{key}={value}" for key, value in sorted(counts.items())))
        print("")
        for index, item in enumerate(items, 1):
            if args.quiet and item.get("status") not in {"fail", "timeout", "error"}:
                continue
            location = f"{item['file']}:{item['line']}"
            print(f"{index:>3}. [{item['category']}] {location} (cwd: {item['cwd']})")
            print(f"     {item['command']}")
            print(f"     {item['reason']}")
            if "status" in item:
                print(
                    f"     -> {item['status']} (exit {item['exit_code']}, "
                    f"{item['seconds']}s)"
                )
                if item.get("output"):
                    for line in item["output"].splitlines()[:8]:
                        print(f"        {line}")
            print("")

    if not categories and not args.json:
        print("No commands were executed. Use --run-safe or --run safe,info,test.")

    failed = any(item.get("status") in {"fail", "timeout", "error"} for item in items)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
