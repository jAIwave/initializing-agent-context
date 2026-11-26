#!/usr/bin/env python3
"""Read-only repository inventory for agent-context initialization.

Builds a fact sheet about the repository: state, units, stacks, manifests,
commands, entry points, tests, docs, CI, deploy, hazards, and warnings.

The script never writes to the repository and never reads .env contents.
It only lists environment file names.

Usage:
    python scan_repo.py --root .
    python scan_repo.py --root . --json > repo-fact-sheet.json
    python scan_repo.py --root . --depth 3 --skip nworktree --skip tools
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone


def configure_stdio() -> None:
    """Keep non-ASCII repository content from crashing output."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError):
            pass


configure_stdio()
from pathlib import Path
from typing import Any, Iterable

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SKIP_DIRS = {
    ".git", ".hg", ".svn",
    "node_modules", "bower_components", "jspm_packages",
    "venv", ".venv", "env", ".env.d", "virtualenv",
    "dist", "build", "out", "target", "bin", "obj",
    ".next", ".nuxt", ".svelte-kit", ".output", ".vite-cache", ".vite",
    ".rsbuild", ".angular", ".expo", ".webpack",
    "coverage", ".nyc_output", "htmlcov",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox", ".nox",
    "__pycache__", ".ipynb_checkpoints",
    "test-results", "playwright-report", "blob-report", "cypress/videos", "cypress/screenshots",
    ".cache", ".parcel-cache", ".turbo", ".eslintcache", ".stylelintcache",
    ".gradle", ".idea", ".vscode", ".fleet",
    "vendor", "Pods", "DerivedData", ".terraform", ".terragrunt-cache",
    "nworktree", "worktrees", ".worktrees",
    ".yarn", ".pnpm-store", ".npm",
}

# Hidden directories worth inspecting for agent/CI configuration.
ALLOWED_HIDDEN = {
    ".github", ".gitlab", ".kilo", ".claude", ".cursor", ".agents",
    ".devcontainer", ".config",
}

# Hidden directories that hold tool configuration, not deployable units.
TOOLING_DIRS = {
    ".github", ".gitlab", ".kilo", ".claude", ".cursor", ".agents",
    ".devcontainer", ".config", ".vscode", ".idea",
}

CODE_EXTS = {
    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
    ".go", ".rs", ".java", ".kt", ".kts", ".scala", ".cs", ".fs", ".vb",
    ".php", ".rb", ".swift", ".dart", ".ex", ".exs", ".lua", ".r", ".jl",
    ".c", ".h", ".cc", ".cpp", ".cxx", ".hpp", ".m", ".mm",
    ".vue", ".svelte", ".astro", ".html", ".css", ".scss", ".sass", ".less",
    ".sh", ".bash", ".zsh", ".ps1", ".sql", ".tf", ".tfvars",
}

LANG_BY_EXT = {
    ".py": "Python", ".pyi": "Python",
    ".js": "JavaScript", ".jsx": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript",
    ".go": "Go", ".rs": "Rust",
    ".java": "Java", ".kt": "Kotlin", ".kts": "Kotlin", ".scala": "Scala",
    ".cs": "C#", ".fs": "F#", ".vb": "VB.NET",
    ".php": "PHP", ".rb": "Ruby", ".swift": "Swift", ".dart": "Dart",
    ".ex": "Elixir", ".exs": "Elixir", ".lua": "Lua", ".r": "R", ".jl": "Julia",
    ".c": "C", ".h": "C/C++", ".cc": "C++", ".cpp": "C++", ".cxx": "C++",
    ".hpp": "C++", ".m": "Objective-C", ".mm": "Objective-C",
    ".vue": "Vue", ".svelte": "Svelte", ".astro": "Astro",
    ".html": "HTML", ".css": "CSS", ".scss": "CSS", ".sass": "CSS", ".less": "CSS",
    ".sh": "Shell", ".bash": "Shell", ".zsh": "Shell", ".ps1": "PowerShell",
    ".sql": "SQL", ".tf": "Terraform", ".tfvars": "Terraform",
}

MANIFEST_STACK = {
    "package.json": "Node/JavaScript",
    "tsconfig.json": "TypeScript",
    "pnpm-workspace.yaml": "pnpm workspace",
    "pyproject.toml": "Python",
    "requirements.txt": "Python",
    "setup.py": "Python",
    "setup.cfg": "Python",
    "Pipfile": "Python",
    "poetry.lock": "Python/Poetry",
    "uv.lock": "Python/uv",
    "go.mod": "Go",
    "go.work": "Go workspace",
    "Cargo.toml": "Rust",
    "pom.xml": "Java/Maven",
    "build.gradle": "JVM/Gradle",
    "build.gradle.kts": "JVM/Gradle",
    "settings.gradle": "JVM/Gradle",
    "settings.gradle.kts": "JVM/Gradle",
    "composer.json": "PHP",
    "Gemfile": "Ruby",
    "Package.swift": "Swift",
    "pubspec.yaml": "Dart/Flutter",
    "mix.exs": "Elixir",
    "build.sbt": "Scala",
    "CMakeLists.txt": "C/C++",
    "Makefile": "Make",
    "makefile": "Make",
    "justfile": "Just",
    "Taskfile.yml": "Task",
    "Taskfile.yaml": "Task",
    "Dockerfile": "Container",
    "docker-compose.yml": "Container",
    "docker-compose.yaml": "Container",
    "compose.yml": "Container",
    "compose.yaml": "Container",
    "Procfile": "Deploy",
    "fly.toml": "Deploy",
    "vercel.json": "Deploy",
    "netlify.toml": "Deploy",
    "render.yaml": "Deploy",
    "serverless.yml": "Deploy",
    "app.yaml": "Deploy",
    ".github/workflows": "CI",
    ".gitlab-ci.yml": "CI",
    "Jenkinsfile": "CI",
    "azure-pipelines.yml": "CI",
    ".circleci/config.yml": "CI",
    "bitbucket-pipelines.yml": "CI",
}

LOCKFILES = {
    "package-lock.json": "npm",
    "pnpm-lock.yaml": "pnpm",
    "yarn.lock": "yarn",
    "bun.lockb": "bun",
    "bun.lock": "bun",
    "poetry.lock": "poetry",
    "uv.lock": "uv",
    "Pipfile.lock": "pipenv",
    "Gemfile.lock": "bundler",
    "composer.lock": "composer",
    "Cargo.lock": "cargo",
    "go.sum": "go modules",
    "packages.lock.json": "nuget",
}

ENTRY_NAMES = {
    "main.py", "app.py", "server.py", "__main__.py", "manage.py", "wsgi.py", "asgi.py",
    "index.js", "index.mjs", "index.cjs", "index.ts",
    "main.js", "main.mjs", "main.ts", "server.js", "server.ts",
    "app.js", "app.ts", "app.jsx", "app.tsx",
    "main.go", "Program.cs", "Startup.cs", "Application.java", "Main.java",
    "main.rs", "lib.rs", "config.ru", "index.php", "artisan",
    "vite.config.js", "vite.config.ts", "next.config.js", "next.config.mjs",
    "next.config.ts", "nuxt.config.ts", "svelte.config.js", "astro.config.mjs",
    "playwright.config.ts", "playwright.config.js",
    "vitest.config.ts", "vitest.config.js", "jest.config.ts", "jest.config.js",
    "pytest.ini", "tox.ini", "conftest.py",
}

ENTRY_GLOBS = (
    "cmd/*/main.go",
    "src/main.*",
    "src/index.*",
    "src/app.*",
    "src/App.*",
    "app/main.*",
    "apps/*/src/main.*",
    "services/*/app.py",
    "services/*/main.py",
    "services/*/app/main.py",
)

TEST_DIR_NAMES = {
    "test", "tests", "__tests__", "spec", "specs", "e2e",
    "integration-tests", "unit-tests", "cypress", "playwright",
}

TEST_CONFIG_NAMES = {
    "pytest.ini", "tox.ini", "conftest.py", "noxfile.py",
    "vitest.config.js", "vitest.config.ts", "jest.config.js", "jest.config.ts",
    "playwright.config.js", "playwright.config.ts", "cypress.config.js",
    "cypress.config.ts", "karma.conf.js", ".mocharc.json", ".mocharc.yml",
    "phpunit.xml", "phpunit.xml.dist", ".rspec", "jest-puppeteer.config.js",
    "codecov.yml", ".coveragerc",
}

TEST_FILE_RE = re.compile(
    r"(^test_.*\.py$|.*_test\.py$|.*\.(test|spec)\.(js|jsx|mjs|cjs|ts|tsx)$|"
    r".*_test\.go$|.*Tests?\.(cs|fs|vb)$|.*Test\.(java|kt)$)",
    re.IGNORECASE,
)

DOC_DIR_NAMES = {"docs", "doc", "documentation"}

DB_DIR_NAMES = {
    "migrations", "migration", "alembic", "prisma", "schema", "db", "database",
    "flyway", "liquibase", "knex", "sequelize",
}
DB_FILE_NAMES = {
    "schema.sql", "schema.prisma", "alembic.ini", "flyway.conf", "liquibase.properties",
}

CI_NAMES = {
    ".gitlab-ci.yml", "Jenkinsfile", "azure-pipelines.yml", "bitbucket-pipelines.yml",
}

DEPLOY_NAMES = {
    "Dockerfile", "docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml",
    "Procfile", "fly.toml", "vercel.json", "netlify.toml", "render.yaml",
    "serverless.yml", "app.yaml", "now.json", "railway.json",
}

ENV_NAMES = {".env", ".env.example", ".env.sample", ".env.template", ".env.local",
             ".env.development", ".env.production", ".env.test"}

HAZARD_WORDS = ("auth", "security", "payment", "billing", "secret", "credential",
                "token", "crypto", "permission", "rbac", "session")

# ---------------------------------------------------------------------------
# Filesystem helpers
# ---------------------------------------------------------------------------


def should_skip_dir(name: str, extra_skip: set[str]) -> bool:
    if name in SKIP_DIRS or name in extra_skip:
        return True
    if name.startswith(".") and name not in ALLOWED_HIDDEN:
        return True
    return False


def walk_files(root: Path, max_files: int, extra_skip: set[str]) -> list[Path]:
    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        current = Path(dirpath)
        dirnames[:] = sorted(
            d for d in dirnames if not should_skip_dir(d, extra_skip)
        )
        for name in sorted(filenames):
            path = current / name
            try:
                if path.is_symlink():
                    continue
            except OSError:
                continue
            files.append(path)
            if len(files) >= max_files:
                return files
    return files


def rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def read_text(path: Path, limit: int = 200_000) -> str:
    try:
        with path.open("r", encoding="utf-8-sig", errors="replace") as handle:
            return handle.read(limit)
    except OSError:
        return ""


def read_json(path: Path) -> Any:
    try:
        return json.loads(read_text(path))
    except (OSError, json.JSONDecodeError):
        return None


def count_lines(path: Path) -> int:
    text = read_text(path)
    return len(text.splitlines()) if text else 0


def git(root: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True, text=True, timeout=5, check=False,
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def git_info(root: Path) -> dict[str, Any]:
    branch = git(root, "rev-parse", "--abbrev-ref", "HEAD")
    commit = git(root, "rev-parse", "--short", "HEAD")
    dirty = bool(git(root, "status", "--porcelain"))
    worktrees = git(root, "worktree", "list", "--porcelain")
    worktree_count = max(1, worktrees.count("worktree ")) if worktrees else 1
    submodules: list[str] = []
    gitmodules = root / ".gitmodules"
    if gitmodules.exists():
        for line in read_text(gitmodules).splitlines():
            match = re.match(r"\s*path\s*=\s*(.+)", line)
            if match:
                submodules.append(match.group(1).strip())
    return {
        "branch": branch,
        "commit": commit,
        "dirty": dirty,
        "worktrees": worktree_count,
        "submodules": submodules,
    }


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------


def detect_languages(files: Iterable[Path]) -> list[dict[str, Any]]:
    counts: Counter[str] = Counter()
    for path in files:
        language = LANG_BY_EXT.get(path.suffix.lower())
        if language:
            counts[language] += 1
    return [{"name": name, "files": count} for name, count in counts.most_common()]


def detect_manifests(root: Path, files: Iterable[Path]) -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    for path in files:
        name = path.name
        stack = MANIFEST_STACK.get(name)
        if path.parent.name == "workflows" and path.parent.parent.name == ".github":
            stack = "CI"
        if name in {"Dockerfile", "docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"}:
            stack = MANIFEST_STACK.get(name)
        if stack:
            found.append({"path": rel(path, root), "stack": stack})
    return sorted(found, key=lambda item: item["path"])


def detect_agent_files(root: Path, files: Iterable[Path]) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for path in files:
        name = path.name
        relative = rel(path, root)
        if name in {"AGENTS.md", "CLAUDE.md", "CLAUDE.local.md", "GEMINI.md",
                    "copilot-instructions.md", ".aider.conf.yml"}:
            found.append({
                "path": relative,
                "kind": name,
                "lines": count_lines(path),
            })
        elif relative.startswith(".cursor/rules/") and name.endswith(".mdc"):
            found.append({"path": relative, "kind": "cursor-rule", "lines": count_lines(path)})
        elif name == "SKILL.md" and ("skills" in Path(relative).parts or path.parent == root):
            found.append({"path": relative, "kind": "skill", "lines": count_lines(path)})
        elif relative.startswith(".kilo/command/") and name.endswith(".md"):
            found.append({"path": relative, "kind": "kilo-command", "lines": count_lines(path)})
        elif relative.startswith(".kilo/agent/") and name.endswith(".md"):
            found.append({"path": relative, "kind": "kilo-agent", "lines": count_lines(path)})
        elif name == "kilo.json" and path.parent == root:
            found.append({"path": relative, "kind": "kilo-config", "lines": count_lines(path)})
    return sorted(found, key=lambda item: item["path"])


def detect_docs(root: Path, files: Iterable[Path]) -> dict[str, Any]:
    readme = root / "README.md"
    docs_files = [
        p for p in files
        if any(part.lower() in DOC_DIR_NAMES for part in p.relative_to(root).parts[:-1])
        and p.suffix.lower() == ".md"
    ]
    plans = [p for p in files if "plans" in p.relative_to(root).parts and p.suffix.lower() == ".md"]
    adr = [p for p in files if "adr" in p.relative_to(root).parts and p.suffix.lower() == ".md"]
    return {
        "readme": rel(readme, root) if readme.exists() else None,
        "readme_lines": count_lines(readme) if readme.exists() else 0,
        "docs_dir": any((root / name).is_dir() for name in DOC_DIR_NAMES),
        "docs_markdown": len(docs_files),
        "plans_markdown": len(plans),
        "adr_markdown": len(adr),
        "contributing": (root / "CONTRIBUTING.md").exists(),
        "changelog": any((root / name).exists() for name in ("CHANGELOG.md", "CHANGELOG")),
        "license": any((root / name).exists() for name in ("LICENSE", "LICENSE.md", "COPYING")),
        "llms_txt": (root / "llms.txt").exists(),
    }


def detect_tests(root: Path, files: Iterable[Path]) -> dict[str, Any]:
    test_files = [p for p in files if TEST_FILE_RE.match(p.name)]
    configs = [rel(p, root) for p in files if p.name in TEST_CONFIG_NAMES]
    dirs = sorted({
        rel(p.parent, root) for p in files
        if p.parent.name in TEST_DIR_NAMES
    })
    return {
        "test_files": len(test_files),
        "dirs": dirs[:20],
        "configs": configs[:20],
        "examples": [rel(p, root) for p in test_files[:10]],
    }


def detect_ci(root: Path, files: Iterable[Path]) -> list[str]:
    found: list[str] = []
    for path in files:
        relative = rel(path, root)
        parts = path.relative_to(root).parts
        is_github_workflow = (
            path.suffix.lower() in {".yml", ".yaml"}
            and any(parts[i] == ".github" and parts[i + 1] == "workflows"
                    for i in range(len(parts) - 1))
        )
        if is_github_workflow or path.name in CI_NAMES:
            found.append(relative)
    return sorted(set(found))


def detect_deploy(root: Path, files: Iterable[Path]) -> list[str]:
    found: list[str] = []
    for path in files:
        relative = rel(path, root)
        if path.name in DEPLOY_NAMES or path.suffix == ".service":
            found.append(relative)
        elif "deploy" in path.parts and path.suffix.lower() in {".sh", ".ps1", ".yml", ".yaml"}:
            found.append(relative)
    return sorted(set(found))[:40]


def detect_database(root: Path, files: Iterable[Path]) -> list[str]:
    found: list[str] = []
    for path in files:
        relative = rel(path, root)
        if path.name in DB_FILE_NAMES:
            found.append(relative)
        elif any(part.lower() in DB_DIR_NAMES for part in path.relative_to(root).parts[:-1]):
            if path.suffix.lower() in {".sql", ".py", ".js", ".ts", ".rb", ".php"}:
                found.append(relative)
    return sorted(set(found))[:40]


def detect_env_files(root: Path, files: Iterable[Path]) -> list[str]:
    found = []
    for path in files:
        relative = rel(path, root)
        if path.name in ENV_NAMES or re.match(r"^\.env(\..+)?$", path.name):
            found.append(relative)
    return sorted(set(found))[:40]


def detect_hazards(root: Path, files: Iterable[Path]) -> list[str]:
    hazards: list[str] = []
    for path in files:
        relative = rel(path, root).lower()
        name = path.name.lower()
        if any(word in name for word in HAZARD_WORDS):
            hazards.append(rel(path, root))
        elif any(word in relative for word in ("auth/", "security/", "payments/", "billing/")):
            hazards.append(rel(path, root))
    return sorted(set(hazards))[:40]


def detect_noise(root: Path, files: Iterable[Path]) -> dict[str, Any]:
    root_files = [p for p in files if p.parent == root]
    ext_counts: Counter[str] = Counter(
        p.suffix.lower() or "<none>" for p in root_files
    )
    ignored_like = [p for p in root_files if p.suffix.lower() in {
        ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".yml", ".yaml",
        ".log", ".ogg", ".mp3", ".mp4", ".mov", ".pdf",
    }]
    return {
        "root_files": len(root_files),
        "root_extensions": [
            {"ext": ext, "files": count} for ext, count in ext_counts.most_common(12)
        ],
        "root_artifacts": len(ignored_like),
        "worktree_dirs": [
            name for name in ("nworktree", "worktrees", ".worktrees")
            if (root / name).is_dir()
        ],
        "test_results": any((root / name).exists() for name in ("test-results", "playwright-report")),
    }


# ---------------------------------------------------------------------------
# Command discovery
# ---------------------------------------------------------------------------


def parse_package_json(path: Path) -> dict[str, Any]:
    data = read_json(path)
    if not isinstance(data, dict):
        return {}
    scripts = data.get("scripts")
    return {
        "scripts": scripts if isinstance(scripts, dict) else {},
        "package_manager": data.get("packageManager"),
        "workspaces": data.get("workspaces"),
        "engines": data.get("engines"),
        "name": data.get("name"),
    }


def parse_pyproject_scripts(path: Path) -> dict[str, str]:
    text = read_text(path)
    scripts: dict[str, str] = {}
    try:
        import tomllib  # type: ignore
        data = tomllib.loads(text)
        project = data.get("project", {})
        if isinstance(project, dict):
            for key, value in (project.get("scripts") or {}).items():
                scripts[key] = str(value)
        poetry = data.get("tool", {}).get("poetry", {})
        if isinstance(poetry, dict):
            for key, value in (poetry.get("scripts") or {}).items():
                scripts[key] = str(value)
    except Exception:
        for match in re.finditer(r"^([A-Za-z0-9_.-]+)\s*=\s*[\"']([^\"']+)[\"']\s*$", text, re.MULTILINE):
            scripts[match.group(1)] = match.group(2)
    return scripts


def parse_make_targets(path: Path) -> list[str]:
    targets: list[str] = []
    for line in read_text(path).splitlines():
        match = re.match(r"^([A-Za-z0-9_.-]+):(?!=)", line)
        if not match:
            continue
        name = match.group(1)
        if name in {".PHONY", ".SUFFIXES", ".DEFAULT"} or name.startswith("."):
            continue
        targets.append(name)
    return sorted(set(targets))[:30]


def parse_just_recipes(path: Path) -> list[str]:
    recipes: list[str] = []
    for line in read_text(path).splitlines():
        match = re.match(r"^([A-Za-z0-9_-]+)(?:\s+[^:]*)?:", line)
        if match and not line.lstrip().startswith("#"):
            name = match.group(1)
            if name not in {"set", "alias", "export", "import", "mod"}:
                recipes.append(name)
    return sorted(set(recipes))[:30]


def parse_compose_services(path: Path) -> list[str]:
    services: list[str] = []
    in_services = False
    for line in read_text(path).splitlines():
        if re.match(r"^services:\s*$", line):
            in_services = True
            continue
        if in_services and line and not line.startswith(" "):
            break
        if in_services:
            match = re.match(r"^  ([A-Za-z0-9_.-]+):\s*$", line)
            if match:
                services.append(match.group(1))
    return services


def detect_package_manager(unit_dir: Path, unit_files: Iterable[Path]) -> str | None:
    names = {p.name for p in unit_files}
    package = unit_dir / "package.json"
    package_data = parse_package_json(package) if package.exists() else {}
    declared = package_data.get("package_manager")
    if declared:
        return str(declared)
    for lock, manager in LOCKFILES.items():
        if lock in names:
            return manager
    pyproject = unit_dir / "pyproject.toml"
    if pyproject.exists():
        text = read_text(pyproject)
        if "[tool.poetry]" in text:
            return "poetry"
        if "[tool.uv]" in text or "uv.lock" in names:
            return "uv"
        if "[tool.pdm]" in text:
            return "pdm"
    if "Pipfile" in names:
        return "pipenv"
    if "requirements.txt" in names:
        return "pip"
    if "go.mod" in names:
        return "go modules"
    if "Cargo.toml" in names:
        return "cargo"
    if "composer.json" in names:
        return "composer"
    if "Gemfile" in names:
        return "bundler"
    if any(name.endswith(".csproj") or name.endswith(".sln") for name in names):
        return "dotnet"
    if "pom.xml" in names:
        return "maven"
    if "build.gradle" in names or "build.gradle.kts" in names:
        return "gradle"
    return None


def discover_declared_commands(unit_dir: Path, unit_files: Iterable[Path]) -> list[dict[str, str]]:
    commands: list[dict[str, str]] = []

    package = unit_dir / "package.json"
    if package.exists():
        data = parse_package_json(package)
        for name, value in (data.get("scripts") or {}).items():
            commands.append({"cmd": f"npm run {name}", "source": "declared", "note": str(value)})

    pyproject = unit_dir / "pyproject.toml"
    if pyproject.exists():
        for name, value in parse_pyproject_scripts(pyproject).items():
            commands.append({"cmd": name, "source": "declared", "note": value})

    make = unit_dir / "Makefile"
    if make.exists():
        for target in parse_make_targets(make):
            commands.append({"cmd": f"make {target}", "source": "declared", "note": "Makefile target"})

    just = unit_dir / "justfile"
    if just.exists():
        for recipe in parse_just_recipes(just):
            commands.append({"cmd": f"just {recipe}", "source": "declared", "note": "just recipe"})

    for name in ("docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"):
        compose = unit_dir / name
        if compose.exists():
            for service in parse_compose_services(compose):
                commands.append({"cmd": f"docker compose up {service}", "source": "declared",
                                 "note": f"compose service in {name}"})
    return commands


def has_any(unit_files: Iterable[Path], names: set[str]) -> bool:
    return any(p.name in names for p in unit_files)


def suggest_commands(unit_dir: Path, unit_files: list[Path], stack_text: str) -> list[dict[str, str]]:
    names = {p.name for p in unit_files}
    suggested: list[dict[str, str]] = []

    def add(cmd: str, note: str) -> None:
        suggested.append({"cmd": cmd, "source": "suggested", "note": note})

    lower = stack_text.lower()
    if "python" in lower:
        if "conftest.py" in names or "pytest.ini" in names or any(
            p.name.startswith("test_") and p.suffix == ".py" for p in unit_files
        ):
            add("python -m pytest --collect-only -q", "test discovery")
            add("python -m pytest <test-file> -q", "focused test")
        if "manage.py" in names:
            add("python manage.py check", "Django system check")
        if ".ruff.toml" in names or "ruff.toml" in names:
            add("ruff check .", "lint")
        if "mypy.ini" in names or ".mypy.ini" in names:
            add("mypy .", "type check")
    if "node" in lower or "typescript" in lower or "javascript" in lower:
        if "tsconfig.json" in names:
            add("npx tsc --noEmit", "type check")
        if any(name.startswith("eslint.config") or name in {".eslintrc", ".eslintrc.js", ".eslintrc.cjs"} for name in names):
            add("npx eslint .", "lint")
        if "vitest.config.ts" in names or "vitest.config.js" in names:
            add("npx vitest run", "tests")
        if "jest.config.ts" in names or "jest.config.js" in names:
            add("npx jest --listTests", "test discovery")
        if "playwright.config.ts" in names or "playwright.config.js" in names:
            add("npx playwright test --list", "E2E discovery")
    if "go" in lower and "go.mod" in names:
        add("go vet ./...", "vet")
        add("go test ./...", "tests")
    if "rust" in lower and "Cargo.toml" in names:
        add("cargo fmt --check", "format check")
        add("cargo clippy -- -D warnings", "lint")
        add("cargo test --no-run", "compile tests")
    if ("c#" in lower or "dotnet" in lower or ".net" in lower) and any(
        p.suffix == ".csproj" or p.suffix == ".sln" for p in unit_files
    ):
        add("dotnet build", "build")
        add("dotnet test --list-tests", "test discovery")
    if "php" in lower and "composer.json" in names:
        add("composer test", "composer test script")
        add("vendor/bin/phpunit --list-tests", "test discovery")
    if "ruby" in lower and "Gemfile" in names:
        add("bundle exec rubocop", "lint")
        add("bundle exec rspec --dry-run", "test discovery")
    return suggested


def find_entrypoints(unit_dir: Path, unit_files: Iterable[Path]) -> list[str]:
    found: list[str] = []
    for path in unit_files:
        relative = path.relative_to(unit_dir)
        if path.name in ENTRY_NAMES:
            found.append(relative.as_posix())
            continue
        if len(relative.parts) <= 4:
            for pattern in ENTRY_GLOBS:
                if relative.match(pattern):
                    found.append(relative.as_posix())
                    break
    return sorted(set(found))[:20]


# ---------------------------------------------------------------------------
# Unit detection
# ---------------------------------------------------------------------------


def _workspace_patterns(root: Path, files: list[Path]) -> list[str]:
    patterns: list[str] = []
    package = root / "package.json"
    if package.exists():
        data = parse_package_json(package)
        workspaces = data.get("workspaces")
        if isinstance(workspaces, list):
            patterns.extend(str(item) for item in workspaces)
        elif isinstance(workspaces, dict):
            patterns.extend(str(item) for item in (workspaces.get("packages") or []))

    pnpm = root / "pnpm-workspace.yaml"
    if pnpm.exists():
        in_packages = False
        for line in read_text(pnpm).splitlines():
            if re.match(r"^packages:\s*$", line):
                in_packages = True
                continue
            if in_packages:
                match = re.match(r"^\s*-\s*[\"']?([^\"']+)[\"']?\s*$", line)
                if match:
                    patterns.append(match.group(1).strip())
                elif line.strip() and not line.startswith(" "):
                    in_packages = False

    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        text = read_text(pyproject)
        match = re.search(r"\[tool\.uv\.workspace\][\s\S]*?members\s*=\s*\[([^\]]+)\]", text)
        if match:
            patterns.extend(re.findall(r"[\"']([^\"']+)[\"']", match.group(1)))

    cargo = root / "Cargo.toml"
    if cargo.exists():
        text = read_text(cargo)
        match = re.search(r"\[workspace\][\s\S]*?members\s*=\s*\[([^\]]+)\]", text)
        if match:
            patterns.extend(re.findall(r"[\"']([^\"']+)[\"']", match.group(1)))

    go_work = root / "go.work"
    if go_work.exists():
        for match in re.finditer(r"^\s*(?:use\s+)?(\./[^\s]+)\s*$", read_text(go_work), re.MULTILINE):
            patterns.append(match.group(1))

    return [p for p in patterns if p and not p.startswith("!")]


def _expand_workspace_patterns(root: Path, patterns: Iterable[str]) -> list[Path]:
    dirs: list[Path] = []
    for pattern in patterns:
        clean = pattern.lstrip("./")
        if any(char in clean for char in "*?["):
            for match in root.glob(clean):
                if match.is_dir():
                    dirs.append(match.resolve())
        else:
            candidate = (root / clean).resolve()
            if candidate.is_dir():
                dirs.append(candidate)
    return [d for d in dirs if d == root or root in d.parents]


def build_units(root: Path, files: list[Path], depth: int) -> list[dict[str, Any]]:
    manifest_names = set(MANIFEST_STACK)
    manifest_dirs: set[Path] = set()
    for path in files:
        if path.name not in manifest_names:
            continue
        try:
            relative = path.relative_to(root)
        except ValueError:
            continue
        if len(relative.parts) - 1 > depth:
            continue
        if any(part in TOOLING_DIRS for part in relative.parts[:-1]):
            continue
        manifest_dirs.add(path.parent.resolve())

    workspace_patterns = _workspace_patterns(root, files)
    for directory in _expand_workspace_patterns(root, workspace_patterns):
        manifest_dirs.add(directory)

    if not manifest_dirs:
        if any(p.suffix.lower() in CODE_EXTS for p in files):
            manifest_dirs.add(root.resolve())
        else:
            return []

    # Drop directories that are not inside root.
    manifest_dirs = {d for d in manifest_dirs if d == root or root in d.parents}
    manifest_dirs = {
        d for d in manifest_dirs
        if not any(part in TOOLING_DIRS for part in d.relative_to(root).parts)
    }
    ordered = sorted(manifest_dirs, key=lambda d: (len(d.relative_to(root).parts), str(d)))

    units: list[dict[str, Any]] = []
    for unit_dir in ordered:
        unit_files = [
            p for p in files
            if p.parent == unit_dir or unit_dir in p.parents
        ]
        if not unit_files and unit_dir != root:
            continue

        direct_manifests = [p for p in unit_files if p.parent == unit_dir and p.name in manifest_names]
        direct_files = [p for p in unit_files if p.parent == unit_dir]
        stacks: Counter[str] = Counter()
        for manifest in direct_manifests:
            stack = MANIFEST_STACK.get(manifest.name)
            if stack:
                stacks[stack] += 1
        for path in unit_files:
            language = LANG_BY_EXT.get(path.suffix.lower())
            if language:
                stacks[language] += 1
        stack_list = [name for name, _ in stacks.most_common(4)]

        declared = discover_declared_commands(unit_dir, direct_manifests)
        suggested = suggest_commands(unit_dir, unit_files, " ".join(stack_list))
        tests = sum(1 for p in unit_files if TEST_FILE_RE.match(p.name))
        test_configs = sorted({p.name for p in unit_files if p.name in TEST_CONFIG_NAMES})

        units.append({
            "path": rel(unit_dir, root) or ".",
            "name": unit_dir.name if unit_dir != root else root.name,
            "stack": stack_list,
            "package_manager": detect_package_manager(unit_dir, direct_files),
            "declared_commands": declared,
            "suggested_commands": suggested,
            "entrypoints": find_entrypoints(unit_dir, unit_files),
            "test_files": tests,
            "test_configs": test_configs,
            "docs": {
                "readme": (unit_dir / "README.md").exists(),
                "docs_dir": any((unit_dir / name).is_dir() for name in DOC_DIR_NAMES),
            },
            "agent_file": (unit_dir / "AGENTS.md").exists()
            or (unit_dir / "CLAUDE.md").exists(),
            "file_count": len(unit_files),
            "workspace_root": unit_dir == root and bool(workspace_patterns),
        })
    return units


# ---------------------------------------------------------------------------
# State, warnings, next steps
# ---------------------------------------------------------------------------


def detect_state(root: Path, files: list[Path], units: list[dict[str, Any]],
                 docs: dict[str, Any], agent_files: list[dict[str, Any]]) -> dict[str, Any]:
    code_files = sum(1 for p in files if p.suffix.lower() in CODE_EXTS)
    manifest_count = sum(1 for p in files if p.name in MANIFEST_STACK)
    docs_rich = (
        (docs["docs_markdown"] >= 2)
        or (docs["readme_lines"] >= 50 and (docs["contributing"] or docs["adr_markdown"] > 0))
    )

    if agent_files:
        state, reason = "S3", "agent files present; audit and repair"
    elif code_files == 0 and manifest_count == 0:
        state, reason = "S0", "no code or manifests; bootstrap a walking skeleton"
    elif code_files > 0 and docs_rich:
        state, reason = "S2", "code and docs present; derive the agent router from docs"
    else:
        state, reason = "S1", "code present without durable docs; use code archaeology"

    return {
        "state": state,
        "reason": reason,
        "code_files": code_files,
        "manifest_files": manifest_count,
        "docs_only": code_files == 0 and any(
            p.suffix.lower() in {".md", ".mdx", ".txt"} for p in files
        ),
        "units": len(units),
    }


def build_warnings(root: Path, files: list[Path], docs: dict[str, Any],
                   agent_files: list[dict[str, Any]], tests: dict[str, Any],
                   ci: list[str], manifests: list[dict[str, str]],
                   units: list[dict[str, Any]], noise: dict[str, Any],
                   env_files: list[str]) -> list[str]:
    warnings: list[str] = []
    if not docs["readme"]:
        warnings.append("no README.md at the root")
    if not (root / ".gitignore").exists():
        warnings.append("no .gitignore")
    if tests["test_files"] == 0:
        warnings.append("no test files detected; the agent has no verification loop")
    if not ci:
        warnings.append("no CI configuration detected")
    if manifests and not any((root / lock).exists() for lock in LOCKFILES):
        if any(Path(item["path"]).parent == Path(".") for item in manifests):
            warnings.append("root manifest present but no lockfile detected")
    for agent in agent_files:
        if agent["lines"] > 260:
            warnings.append(f"{agent['path']}: {agent['lines']} lines exceeds the hard 260-line limit")
        elif agent["path"].endswith("AGENTS.md") and agent["lines"] > 180 and "/" not in agent["path"]:
            warnings.append(f"{agent['path']}: {agent['lines']} lines is above the root budget")
    if agent_files and not any(agent["kind"] == "AGENTS.md" for agent in agent_files):
        warnings.append("CLAUDE.md/GEMINI.md present but no AGENTS.md; consider one shared AGENTS.md")
    if docs["docs_markdown"] >= 2 and not agent_files:
        warnings.append("docs exist but no agent entry file; derive AGENTS.md from the docs")
    if noise["root_artifacts"] >= 10:
        warnings.append(f"{noise['root_artifacts']} non-code artifacts in the repo root; reduce agent noise")
    if noise["worktree_dirs"]:
        warnings.append("worktree directories present; they may contain stale AGENTS.md copies")
    if env_files:
        warnings.append(f"{len(env_files)} environment file(s) present; never read their contents")
    if any(unit["file_count"] > 5000 for unit in units):
        warnings.append("a unit has more than 5000 files; use scoped AGENTS.md and ignore generated dirs")
    return warnings


def build_next_steps(state: dict[str, Any], docs: dict[str, Any],
                     tests: dict[str, Any], ci: list[str],
                     agent_files: list[dict[str, Any]],
                     noise: dict[str, Any]) -> list[str]:
    steps: list[str] = []
    if state["state"] == "S0":
        steps.append("Decide the stack and create a walking skeleton with one failing test before writing architecture docs.")
    elif state["state"] == "S1":
        steps.append("Run undocumented-code archaeology; create AGENTS.md, docs/architecture.md and docs/testing.md.")
    elif state["state"] == "S2":
        steps.append("Create the root AGENTS.md router from the existing docs; verify every command against the code.")
    else:
        steps.append("Audit existing agent files with check_agent_docs.py; fix missing sections, duplicates and stale commands.")
    if tests["test_files"] == 0:
        steps.append("Add one focused test command first; verification is the highest-value agent context.")
    if not ci:
        steps.append("Wire tests, lint and the docs check into CI so documented commands are verified.")
    if noise["worktree_dirs"]:
        steps.append("Keep worktrees out of the agent context or refresh their AGENTS.md from the root.")
    if agent_files and not docs["docs_markdown"]:
        steps.append("Move detail out of AGENTS.md into docs/ before the router grows past its budget.")
    return steps


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def build_fact_sheet(root: Path, files: list[Path], depth: int) -> dict[str, Any]:
    languages = detect_languages(files)
    manifests = detect_manifests(root, files)
    agent_files = detect_agent_files(root, files)
    docs = detect_docs(root, files)
    tests = detect_tests(root, files)
    ci = detect_ci(root, files)
    deploy = detect_deploy(root, files)
    database = detect_database(root, files)
    env_files = detect_env_files(root, files)
    hazards = detect_hazards(root, files)
    noise = detect_noise(root, files)
    units = build_units(root, files, depth)
    state = detect_state(root, files, units, docs, agent_files)
    warnings = build_warnings(root, files, docs, agent_files, tests, ci, manifests, units, noise, env_files)
    next_steps = build_next_steps(state, docs, tests, ci, agent_files, noise)

    return {
        "schema": "agent-context-fact-sheet/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "root": str(root),
        "git": git_info(root),
        "state": state,
        "languages": languages,
        "manifests": manifests,
        "units": units,
        "docs": docs,
        "agent_files": agent_files,
        "tests": tests,
        "ci": ci,
        "deploy": deploy,
        "database": database,
        "env_files": env_files,
        "hazards": hazards,
        "noise": noise,
        "warnings": warnings,
        "next": next_steps,
    }


def _table(items: Iterable[str], limit: int = 12) -> str:
    values = list(items)
    if not values:
        return "  (none)"
    lines = [f"  - {item}" for item in values[:limit]]
    if len(values) > limit:
        lines.append(f"  - ... {len(values) - limit} more")
    return "\n".join(lines)


def render_text(fact: dict[str, Any]) -> str:
    state = fact["state"]
    lines: list[str] = []
    add = lines.append

    add("# Repo Fact Sheet")
    add("")
    add(f"root: {fact['root']}")
    add(f"state: {state['state']} - {state['reason']}")
    if state["docs_only"]:
        add("profile: docs-only (no application code)")
    add(f"units: {state['units']} | code files: {state['code_files']} | manifests: {state['manifest_files']}")

    git = fact["git"]
    if git.get("branch"):
        add(f"git: {git['branch']} @ {git['commit']}" + (" (dirty)" if git.get("dirty") else ""))
    if git.get("submodules"):
        add(f"submodules: {', '.join(git['submodules'])}")
    if git.get("worktrees", 1) > 1:
        add(f"git worktrees: {git['worktrees']} (stale agent files possible)")

    add("")
    add("## Languages")
    add(_table([f"{item['name']}: {item['files']}" for item in fact["languages"]], 10))

    add("")
    add("## Units")
    if not fact["units"]:
        add("  (none)")
    for unit in fact["units"]:
        add("")
        add(f"### {unit['path']}")
        add(f"  stack: {', '.join(unit['stack']) or 'unknown'}")
        add(f"  package manager: {unit['package_manager'] or 'unknown'}")
        add(f"  files: {unit['file_count']} | tests: {unit['test_files']} | agent file: {'yes' if unit['agent_file'] else 'no'}")
        if unit["entrypoints"]:
            add("  entry points:")
            add(_table(unit["entrypoints"], 8))
        if unit["declared_commands"]:
            add("  declared commands:")
            add(_table([f"{c['cmd']} - {c['note']}" for c in unit["declared_commands"]], 12))
        if unit["suggested_commands"]:
            add("  suggested commands (verify before documenting):")
            add(_table([f"{c['cmd']} - {c['note']}" for c in unit["suggested_commands"]], 10))

    add("")
    add("## Documentation")
    docs = fact["docs"]
    add(f"  README: {docs['readme'] or 'missing'} ({docs['readme_lines']} lines)")
    add(f"  docs markdown: {docs['docs_markdown']} | plans: {docs['plans_markdown']} | ADRs: {docs['adr_markdown']}")
    add(f"  CONTRIBUTING: {'yes' if docs['contributing'] else 'no'} | LICENSE: {'yes' if docs['license'] else 'no'}")

    add("")
    add("## Agent files")
    if fact["agent_files"]:
        add(_table([f"{a['path']} ({a['lines']} lines, {a['kind']})" for a in fact["agent_files"]]))
    else:
        add("  (none)")

    add("")
    add("## Verification")
    tests = fact["tests"]
    add(f"  test files: {tests['test_files']}")
    if tests["dirs"]:
        add(f"  test dirs: {', '.join(tests['dirs'][:8])}")
    if tests["configs"]:
        add(f"  test configs: {', '.join(tests['configs'][:8])}")
    add(f"  CI: {', '.join(fact['ci'][:8]) if fact['ci'] else 'none'}")
    if fact["deploy"]:
        add(f"  deploy: {', '.join(fact['deploy'][:8])}")

    if fact["database"]:
        add("")
        add("## Data / schema")
        add(_table(fact["database"], 8))
    if fact["hazards"]:
        add("")
        add("## Hazard candidates (review, do not assume)")
        add(_table(fact["hazards"], 8))
    if fact["env_files"]:
        add("")
        add("## Environment files (names only; never read contents)")
        add(_table(fact["env_files"], 8))

    add("")
    add("## Warnings")
    add(_table(fact["warnings"], 20))
    add("")
    add("## Suggested next")
    add(_table(fact["next"], 10))
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="repository root (default: .)")
    parser.add_argument("--depth", type=int, default=4, help="max manifest depth for units (default: 4)")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    parser.add_argument("--max-files", type=int, default=200_000, help="stop after N files")
    parser.add_argument("--skip", action="append", default=[], help="additional directory name to skip")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2
    extra_skip = {item.strip() for item in args.skip if item.strip()}
    files = walk_files(root, args.max_files, extra_skip)
    fact = build_fact_sheet(root, files, args.depth)
    if args.json:
        print(json.dumps(fact, indent=2, ensure_ascii=False))
    else:
        print(render_text(fact))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
