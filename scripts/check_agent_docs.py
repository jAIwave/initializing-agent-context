#!/usr/bin/env python3
"""Generic checker for agent-facing repository docs.

Checks:
  - relative links and Markdown anchors,
  - links that escape the repository,
  - required sections in AGENTS.md (configurable aliases for EN/DE),
  - size budgets for root and unit AGENTS.md,
  - ownership dates and review freshness,
  - volatile numbers ("123 tests", "Stand 2026"),
  - parent/child AGENTS.md index coverage,
  - optional duplicate-fact detection across AGENTS.md files.

Configuration: .agent-docs.json in the repository root (all keys optional).

Usage:
    python check_agent_docs.py --root .
    python check_agent_docs.py --root . --strict
    python check_agent_docs.py --root . --json
    python check_agent_docs.py --root . --duplicates
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote


def configure_stdio() -> None:
    """Keep non-ASCII repository content from crashing output."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError):
            pass


configure_stdio()

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULT_CONFIG: dict[str, Any] = {
    "required_sections": ["commands", "read_next", "ownership"],
    "root_extra_sections": ["invariants"],
    "max_lines": {
        "root_warn": 180,
        "root_hard": 260,
        "unit_warn": 220,
        "unit_hard": 260,
    },
    "soft_root_target": 120,
    "review_max_age_days": 365,
    "check_duplicates": False,
    "allow_missing_root": False,
    "section_aliases": {},
    "include": [
        "AGENTS.md", "README.md",
        "docs/*.md", "docs/**/*.md", "doc/*.md", "doc/**/*.md",
    ],
    "exclude_dirs": [
        "node_modules", "venv", ".venv", "dist", "build", "out", "target",
        ".git", ".next", ".nuxt", "coverage", "test-results",
        "playwright-report", "nworktree", "worktrees", ".worktrees",
        "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ],
    "exclude": [],
}

SECTION_ALIASES: dict[str, list[str]] = {
    "commands": ["commands", "befehle", "setup & commands", "commands & verification"],
    "read_next": ["read next", "weiterlesen", "next reads", "references", "read next / references"],
    "ownership": ["ownership", "owner", "verantwortlich", "ownership & review", "maintainer"],
    "invariants": ["hard invariants", "harte invarianten", "invariants", "boundaries",
                   "hard rules", "harte regeln", "ask first", "never"],
}

HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
NUMBER_PREFIX_RE = re.compile(r"^\d+(?:\.\d+)*[.)]?\s+")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+[\"'][^\"']*[\"'])?\)")
LINE_SUFFIX_RE = re.compile(r":\d+(?:-\d+)?$")
MOJIBAKE_RE = re.compile(
    r"(\u00c3\u00a4|\u00c3\u00b6|\u00c3\u00bc|\u00c3\u0178|\u00c3\u201e"
    r"|\u00c3\u2013|\u00c3\u0153|\u00e2\u20ac\u201c|\u00e2\u20ac\u201d"
    r"|\u00e2\u20ac\u017e|\u00e2\u20ac\u0153|\u00e2\u20ac\u2026|\u00c2 )"
)
GITHUB_PUNCT_RE = re.compile(
    r"[\\'!\"#$%&()*+,./:;<=>?@\[\]^`{|}~"
    r"\u2000-\u206F\u2E00-\u2E7F]"
)
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
LAST_REVIEWED_RE = re.compile(
    r"(?:last reviewed|zuletzt gepr\u00fcft|reviewed)\s*:?\s*(\d{4}-\d{2}-\d{2})", re.IGNORECASE
)
REVIEW_BY_RE = re.compile(
    r"(?:review by|n\u00e4chste pr\u00fcfung|review due|next review)\s*:?\s*(\d{4}-\d{2}-\d{2})",
    re.IGNORECASE,
)
OWNER_RE = re.compile(r"^\s*(?:owner|verantwortlich)\s*:\s*(.+?)\s*$", re.IGNORECASE | re.MULTILINE)
BOILERPLATE_RE = re.compile(
    r"^(?:owner|last reviewed|review by|n\u00e4chste pr\u00fcfung|parent|scope)\b",
    re.IGNORECASE,
)

VOLATILE_PATTERNS = [
    (re.compile(r"\b\d{2,5}\s+(?:tests?|passed|failed|files?|lines?)\b", re.IGNORECASE),
     "test/file/line count"),
    (re.compile(r"\bstand\s+20\d\d\b", re.IGNORECASE), "date snapshot"),
    (re.compile(r"\bcollected\b", re.IGNORECASE), "pytest collected count"),
    (re.compile(r"\btests?/[^\s`]+\s*\(\d+\)", re.IGNORECASE), "test path with count"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def has_mojibake(text: str) -> bool:
    for line in text.splitlines():
        if MOJIBAKE_RE.search(line) and "mojibake" not in line.lower():
            return True
    return False


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return ""


def merged_config(root: Path, override: str | None) -> dict[str, Any]:
    config = json.loads(json.dumps(DEFAULT_CONFIG))  # deep copy
    candidates = []
    if override:
        candidates.append(Path(override))
    candidates.append(root / ".agent-docs.json")
    for candidate in candidates:
        if candidate.exists():
            try:
                loaded = json.loads(read_text(candidate))
            except json.JSONDecodeError as exc:
                print(f"warning: cannot parse {candidate}: {exc}", file=sys.stderr)
                continue
            if isinstance(loaded, dict):
                for key, value in loaded.items():
                    if key == "max_lines" and isinstance(value, dict):
                        config["max_lines"].update(value)
                    else:
                        config[key] = value
    return config


def strip_code(text: str) -> str:
    """Replace fenced and inline code with blanks, preserving line count."""
    out: list[str] = []
    in_fence = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            out.append("")
            continue
        if in_fence:
            out.append("")
        else:
            out.append(re.sub(r"`[^`]*`", "", line))
    return "\n".join(out)


def github_slug(text: str) -> str:
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"<[!/a-z].*?>", "", text.strip().lower(), flags=re.IGNORECASE)
    text = GITHUB_PUNCT_RE.sub("", text)
    return re.sub(r"\s", "-", text)


def heading_key(text: str) -> str:
    text = NUMBER_PREFIX_RE.sub("", text.strip().lower())
    text = text.replace("`", "").strip()
    text = re.sub(r"\s+", " ", text)
    return text.rstrip(":").strip()


def anchors(path: Path) -> set[str]:
    result: set[str] = set()
    for line in read_text(path).splitlines():
        match = HEADING_RE.match(line)
        if match:
            result.add(github_slug(match.group(2)))
    return result


def headings(text: str) -> list[str]:
    result = []
    for line in text.splitlines():
        match = HEADING_RE.match(line)
        if match:
            result.append(heading_key(match.group(2)))
    return result


def has_section(text: str, canonical: str, aliases: dict[str, list[str]] | None = None) -> bool:
    alias_map = aliases or SECTION_ALIASES
    for heading in headings(text):
        for alias in alias_map.get(canonical, [canonical]):
            if heading == alias or heading.startswith(alias + " ") or heading.endswith(" " + alias):
                return True
    return False


def section_alias_map(config: dict[str, Any]) -> dict[str, list[str]]:
    aliases = {key: list(values) for key, values in SECTION_ALIASES.items()}
    extra = config.get("section_aliases") or {}
    if isinstance(extra, dict):
        for key, values in extra.items():
            if isinstance(values, list):
                aliases.setdefault(str(key), []).extend(str(value) for value in values)
    return aliases


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def resolve_link(source: Path, target: str, root: Path) -> Path | None:
    if target.startswith(("http://", "https://", "mailto:", "tel:", "#", "/")):
        return None
    target = target.strip("<>")
    base = target.split("#", 1)[0]
    if not base:
        return None
    base = unquote(base)
    base = LINE_SUFFIX_RE.sub("", base)
    try:
        resolved = (source.parent / base).resolve()
    except OSError:
        return None
    return resolved if is_relative_to(resolved, root) else resolved


def parse_date(value: str) -> date | None:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def collect_files(root: Path, config: dict[str, Any]) -> list[Path]:
    exclude = set(config.get("exclude_dirs", []))
    exclude_globs = list(config.get("exclude", []))
    include = list(config.get("include", []))
    files: list[Path] = []
    for dirpath, dirnames, filenames in os_walk(root, exclude):
        for name in filenames:
            path = Path(dirpath) / name
            relative = rel(path, root)
            if any(fnmatch.fnmatch(relative, pattern) for pattern in exclude_globs):
                continue
            if path.name in {"AGENTS.md", "CLAUDE.md"}:
                files.append(path)
                continue
            if any(fnmatch.fnmatch(relative, pattern) for pattern in include):
                files.append(path)
    return sorted(set(files))


def os_walk(root: Path, exclude: set[str]):
    import os
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            d for d in dirnames
            if d not in exclude and not (d.startswith(".") and d not in {
                ".github", ".gitlab", ".kilo", ".claude", ".cursor", ".agents",
            })
        )
        yield dirpath, dirnames, filenames


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def check_links(path: Path, text: str, root: Path, errors: list[str]) -> None:
    stripped = strip_code(text)
    relative = rel(path, root)
    for match in LINK_RE.finditer(stripped):
        target = match.group(1)
        resolved = resolve_link(path, target, root)
        if resolved is None:
            continue
        if not is_relative_to(resolved, root):
            errors.append(f"{relative}: link escapes the repository: {target}")
            continue
        if not resolved.exists():
            errors.append(f"{relative}: missing link target: {target} -> {rel(resolved, root)}")
            continue
        if "#" in target and resolved.suffix.lower() == ".md":
            fragment = unquote(target.split("#", 1)[1])
            if fragment and fragment not in anchors(resolved):
                errors.append(f"{relative}: missing anchor: {target}")


def check_agent_file(path: Path, text: str, root: Path, config: dict[str, Any],
                     warnings: list[str], errors: list[str]) -> None:
    relative = rel(path, root)
    is_root = path == root / "AGENTS.md"
    lines = len(text.splitlines())
    max_lines = config["max_lines"]
    warn_limit = int(max_lines["root_warn"] if is_root else max_lines["unit_warn"])
    hard_limit = int(max_lines["root_hard"] if is_root else max_lines["unit_hard"])

    if lines > hard_limit:
        errors.append(f"{relative}: {lines} lines exceeds the hard limit of {hard_limit}")
    elif lines > warn_limit:
        warnings.append(f"{relative}: {lines} lines is above the warning limit of {warn_limit}")
    if is_root and lines > int(config.get("soft_root_target", 120)):
        warnings.append(
            f"{relative}: {lines} lines is above the soft root target of "
            f"{config.get('soft_root_target', 120)}"
        )

    required = list(config.get("required_sections", []))
    if is_root:
        required.extend(config.get("root_extra_sections", []))
    aliases = section_alias_map(config)
    for section in required:
        if not has_section(text, section, aliases):
            warnings.append(f"{relative}: recommended section missing: {section}")

    owner = OWNER_RE.search(text)
    if not owner:
        warnings.append(f"{relative}: no Owner line found")

    last = LAST_REVIEWED_RE.search(text)
    review_by = REVIEW_BY_RE.search(text)
    last_date = parse_date(last.group(1)) if last else None
    review_date = parse_date(review_by.group(1)) if review_by else None

    today = date.today()
    override_today = config.get("today")
    if override_today:
        parsed = parse_date(str(override_today))
        if parsed:
            today = parsed

    if last_date is None and review_date is None:
        warnings.append(f"{relative}: no review date (Last reviewed / Review by)")
    if review_date and review_date < today:
        warnings.append(f"{relative}: review overdue since {review_date.isoformat()}")
    if last_date:
        age = (today - last_date).days
        max_age = int(config.get("review_max_age_days", 365))
        if age > max_age:
            warnings.append(f"{relative}: last reviewed {age} days ago (max {max_age})")

    for pattern, label in VOLATILE_PATTERNS:
        matches = list(pattern.finditer(strip_code(text)))
        if matches:
            snippet = matches[0].group(0).strip()
            warnings.append(f"{relative}: volatile {label}: {snippet!r}")


def check_index(root: Path, agents: list[Path], warnings: list[str]) -> None:
    if len(agents) <= 1:
        return
    by_dir = {path.parent: path for path in agents}
    for child in agents:
        if child == root / "AGENTS.md":
            continue
        parent = None
        for directory in child.parents:
            if directory in by_dir and directory != child.parent:
                parent = by_dir[directory]
                break
        if parent is None:
            continue
        parent_text = read_text(parent)
        if not parent_text:
            continue
        stripped = strip_code(parent_text)
        child_rel = rel(child, parent.parent).replace("\\", "/")
        child_name = child.parent.name
        candidates = {
            child_rel,
            f"./{child_rel}",
            f"{child_name}/AGENTS.md",
            f"[{child_name}]({child_rel})",
        }
        linked = any(candidate in stripped for candidate in candidates)

        if not linked:
            for match in LINK_RE.finditer(stripped):
                resolved = resolve_link(parent, match.group(1), root)
                if resolved == child:
                    linked = True
                    break
        if not linked:
            warnings.append(
                f"{rel(parent, root)}: does not link child {rel(child, root)} "
                "(index coverage)"
            )


def normalize_fact(line: str) -> str | None:
    line = line.strip()
    if not line or line.startswith(("#", "|", "```", ">", "<!--")):
        return None
    if BOILERPLATE_RE.match(line):
        return None
    line = re.sub(r"^[-*+]\s+", "", line)
    line = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line)
    line = line.replace("`", "")
    line = re.sub(r"\s+", " ", line).strip().lower()
    if len(line) < 45:
        return None
    return line


def check_duplicates(agents: list[Path], root: Path, warnings: list[str]) -> None:
    facts: dict[str, set[str]] = {}
    for path in agents:
        for line in strip_code(read_text(path)).splitlines():
            normalized = normalize_fact(line)
            if normalized:
                facts.setdefault(normalized, set()).add(rel(path, root))
    reported = 0
    for fact, files in facts.items():
        if len(files) < 2:
            continue
        warnings.append(
            "possible duplicate fact in " + ", ".join(sorted(files)) + f": {fact[:90]!r}"
        )
        reported += 1
        if reported >= 20:
            warnings.append("... duplicate report truncated at 20 items")
            break


def run(root: Path, config: dict[str, Any], want_duplicates: bool, check_indexes: bool) -> dict[str, Any]:
    files = collect_files(root, config)
    errors: list[str] = []
    warnings: list[str] = []

    agents = [p for p in files if p.name == "AGENTS.md"]
    if not agents and not config.get("allow_missing_root", False):
        warnings.append("no AGENTS.md at the repository root")

    for path in files:
        if not path.exists():
            continue
        text = read_text(path)
        if has_mojibake(text):
            warnings.append(f"{rel(path, root)}: possible UTF-8 mojibake")
        check_links(path, text, root, errors)
        if path.name == "AGENTS.md":
            check_agent_file(path, text, root, config, warnings, errors)

    if check_indexes:
        check_index(root, agents, warnings)
    if want_duplicates or config.get("check_duplicates", False):
        check_duplicates(agents, root, warnings)

    return {
        "root": str(root),
        "files_checked": len(files),
        "agents": [rel(p, root) for p in agents],
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "errors": len(errors),
            "warnings": len(warnings),
            "status": "fail" if errors else ("warn" if warnings else "pass"),
        },
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="repository root (default: .)")
    parser.add_argument("--config", help="path to .agent-docs.json")
    parser.add_argument("--strict", action="store_true", help="treat warnings as errors")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument("--quiet", action="store_true", help="only errors in text output")
    parser.add_argument("--duplicates", action="store_true", help="report duplicate facts across AGENTS.md files")
    parser.add_argument("--no-index", action="store_true", help="skip parent/child index coverage")
    parser.add_argument("--today", help="override today's date (YYYY-MM-DD), for tests")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2

    config = merged_config(root, args.config)
    if args.today:
        config["today"] = args.today
    if args.duplicates:
        config["check_duplicates"] = True

    result = run(root, config, args.duplicates, not args.no_index)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("Agent docs check")
        print(f"root: {result['root']}")
        print(f"files: {result['files_checked']} | AGENTS.md: {len(result['agents'])}")
        if result["errors"]:
            print("")
            print("Errors:")
            for item in result["errors"]:
                print(f"  - {item}")
        if result["warnings"] and not args.quiet:
            print("")
            print("Warnings:")
            for item in result["warnings"]:
                print(f"  - {item}")
        print("")
        print(
            f"{result['summary']['errors']} errors, "
            f"{result['summary']['warnings']} warnings"
        )

    if result["errors"] or (args.strict and result["warnings"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
