#!/usr/bin/env python3
"""Structural validator for Skill directories and Harness entrypoints.

Validates the self-contained structure of Skills without making assumptions
about a target project's git workflow or work item conventions, so it runs
cleanly in any repository using only the Python 3.8+ standard library.

Usage:
    python3 check_skill_spec.py <path...>
    python3 check_skill_spec.py <path...> --json

<path> may be a single Skill directory, a container of multiple Skills, or a
project root. The script recursively discovers all directories containing
SKILL.md as well as all CLAUDE.md files.

Exit codes (aligned with deliverable-writing-audit/scripts/detect.py):
    0  All checks passed
    1  Structural defects found
    2  Execution error (e.g., non-existent path or unreadable file)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------- Platform Constraints

# Enforced by the Skill specification and agent runtime loaders.
NAME_MAX_LEN = 64
DESCRIPTION_MAX_LEN = 1024

# Allowed top-level YAML frontmatter keys per the Agent Skills specification.
ALLOWED_FIELDS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}

# Reserved platform words that cannot appear in a Skill name.
RESERVED_WORDS = ("anthropic", "claude")

# Valid character set for `name`: lowercase alphanumeric and hyphens.
RE_VALID_NAME = re.compile(r"^[a-z0-9-]+$")

# Angle brackets inside frontmatter are rejected as potential prompt-injection tags.
RE_ANGLE_TAG = re.compile(r"<[^>]*>")

# Frontmatter delimiter: line 1 must be `---`, closed by a matching `---` line.
RE_FRONTMATTER_FENCE = re.compile(r"^---\s*$")

# Top-level `key: value` parser (avoids external PyYAML dependency).
RE_TOP_LEVEL_KEY = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*)\s*:\s*(.*)$")

# Fenced code blocks and inline code spans hold illustrative link examples and
# are masked before checking relative link resolution.
RE_FENCE = re.compile(r"^\s*(?:```|~~~)")
RE_INLINE_CODE = re.compile(r"`[^`]*`")

# CLAUDE.md may contain only an H1 heading and an `@AGENTS.md` import directive.
RE_CLAUDE_MD_TITLE = re.compile(r"^#\s+\S")
RE_CLAUDE_MD_IMPORT = re.compile(r"^@AGENTS\.md\s*$")

SEVERITY_ORDER = {"P0": 0, "P1": 1, "P2": 2}


@dataclass
class Finding:
    severity: str
    check: str
    path: str
    line: int
    message: str


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)
    skills_scanned: int = 0
    entrypoints_scanned: int = 0

    def add(self, severity: str, check: str, path: Path, line: int, message: str) -> None:
        self.findings.append(Finding(severity, check, path.as_posix(), line, message))


# ---------------------------------------------------------------- File Reading

def read_text(path: Path) -> str:
    """Read UTF-8 file text, falling back to replacement characters on decode errors."""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def parse_frontmatter(text: str) -> tuple[dict[str, str], int, str | None]:
    """Parse YAML frontmatter.

    Returns (top_level_fields, body_start_line_1_indexed, error_message).
    """
    lines = text.splitlines()
    if not lines or not RE_FRONTMATTER_FENCE.match(lines[0]):
        return {}, 0, "File does not start with YAML frontmatter (`---`)"

    end = None
    for idx in range(1, len(lines)):
        if RE_FRONTMATTER_FENCE.match(lines[idx]):
            end = idx
            break
    if end is None:
        return {}, 0, "Missing closing YAML frontmatter fence (`---`)"

    fields: dict[str, str] = {}
    for raw in lines[1:end]:
        if not raw.strip() or raw.startswith((" ", "\t", "-")):
            continue
        match = RE_TOP_LEVEL_KEY.match(raw)
        if match:
            fields[match.group(1)] = match.group(2).strip().strip("\"'")
    return fields, end + 1, None


# ---------------------------------------------------------------- Skill Checks

def check_skill(skill_dir: Path, report: Report) -> None:
    report.skills_scanned += 1
    skill_md = skill_dir / "SKILL.md"
    text = read_text(skill_md)

    dir_name = skill_dir.name
    if not RE_VALID_NAME.match(dir_name):
        report.add("P0", "dir-name", skill_dir, 1,
                   f"Skill directory name `{dir_name}` must be lowercase kebab-case")

    fields, body_start, err = parse_frontmatter(text)
    if err:
        report.add("P0", "frontmatter-missing", skill_md, 1, err)
        return

    fm_text = "\n".join(text.splitlines()[: body_start - 1])
    for tag in RE_ANGLE_TAG.findall(fm_text):
        report.add("P0", "frontmatter-angle-tag", skill_md, 1,
                   f"Frontmatter contains angle-bracket tag `{tag}`, which platform loaders reject")

    name = fields.get("name", "")
    if not name:
        report.add("P0", "name-missing", skill_md, 1, "Frontmatter is missing required field `name`")
    else:
        if not RE_VALID_NAME.match(name):
            report.add("P0", "name-format", skill_md, 1,
                       f"`name: {name}` may contain only lowercase letters, digits, and hyphens")
        if name.startswith("-") or name.endswith("-"):
            report.add("P0", "name-hyphen-edge", skill_md, 1,
                       f"`name: {name}` must not start or end with a hyphen")
        if "--" in name:
            report.add("P0", "name-double-hyphen", skill_md, 1,
                       f"`name: {name}` must not contain consecutive hyphens (`--`)")
        if len(name) > NAME_MAX_LEN:
            report.add("P0", "name-length", skill_md, 1,
                       f"`name` length {len(name)} exceeds maximum {NAME_MAX_LEN}")
        if name != dir_name:
            report.add("P0", "name-mismatch", skill_md, 1,
                       f"`name: {name}` does not match parent directory name `{dir_name}`")
        for word in RESERVED_WORDS:
            if word in name.lower():
                report.add("P0", "name-reserved", skill_md, 1,
                           f"`name` contains reserved platform word `{word}`")

    description = fields.get("description", "")
    if not description:
        report.add("P0", "description-missing", skill_md, 1, "Frontmatter is missing required field `description`")
    if len(description) > DESCRIPTION_MAX_LEN:
        report.add("P0", "description-length", skill_md, 1,
                   f"`description` length {len(description)} exceeds specification limit {DESCRIPTION_MAX_LEN}")

    for field_name in fields:
        if field_name not in ALLOWED_FIELDS:
            report.add("P0", "unexpected-field", skill_md, 1,
                       f"Frontmatter contains unsupported field `{field_name}`; allowed fields are "
                       + ", ".join(f"`{x}`" for x in sorted(ALLOWED_FIELDS)))

    readme = skill_dir / "README.md"
    if readme.exists():
        report.add("P1", "skill-readme", readme, 1,
                   "Skill directory must not contain README.md; place human docs at the suite/repo root")

    check_no_symlinks_in_skill(skill_dir, report)
    check_no_frontmatter_in_subfiles(skill_dir, report)
    check_relative_links(skill_dir, report)


def check_no_symlinks_in_skill(skill_dir: Path, report: Report) -> None:
    """Skill source directories must not contain internal symbolic links.

    Internal symlinks break cross-project portability and packaging, and running
    `ln -s` without `-n` against an existing directory symlink creates recursive
    self-referencing loops inside the Skill directory.
    """
    for dirpath, dirnames, filenames in os.walk(skill_dir, followlinks=False):
        base = Path(dirpath)
        for name in sorted(dirnames + filenames):
            candidate = base / name
            if candidate.is_symlink():
                target = os.readlink(candidate)
                report.add("P0", "skill-internal-symlink", candidate, 1,
                           f"Skill directory must not contain symbolic links (points to `{target}`); "
                           "remove it and use `ln -snf` when mounting external entrypoints")


def check_no_frontmatter_in_subfiles(skill_dir: Path, report: Report) -> None:
    """Markdown files under references/ and assets/ must not contain YAML frontmatter."""
    for sub in ("references", "assets"):
        base = skill_dir / sub
        if not base.is_dir():
            continue
        for md in sorted(base.rglob("*.md")):
            head = read_text(md).splitlines()
            if head and RE_FRONTMATTER_FENCE.match(head[0]):
                report.add("P1", "stray-frontmatter", md, 1,
                           f"File under `{sub}/` contains YAML frontmatter, which has no effect outside SKILL.md")


def check_relative_links(skill_dir: Path, report: Report) -> None:
    """All internal relative links inside a Skill directory must resolve to existing files."""
    link_pattern = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
    for md in sorted(skill_dir.rglob("*.md")):
        in_fence = False
        for lineno, raw in enumerate(read_text(md).splitlines(), start=1):
            if RE_FENCE.match(raw):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            masked = RE_INLINE_CODE.sub("``", raw)
            for target in link_pattern.findall(masked):
                if target.startswith(("http://", "https://", "#", "mailto:")):
                    continue
                if target.startswith("/"):
                    report.add("P1", "absolute-link", md, lineno,
                               f"Link `{target}` starts with `/`, which breaks when installed into another project")
                    continue
                resolved = (md.parent / target.split("#", 1)[0]).resolve()
                if not resolved.exists():
                    report.add("P1", "dead-link", md, lineno, f"Link `{target}` points to a non-existent path")


# ---------------------------------------------------------------- Harness Checks

def check_claude_md(path: Path, report: Report) -> None:
    """CLAUDE.md must contain only an H1 title and `@AGENTS.md` pointer."""
    report.entrypoints_scanned += 1
    lines = [ln for ln in read_text(path).splitlines() if ln.strip()]
    if not lines:
        report.add("P1", "claude-md-empty", path, 1, "CLAUDE.md is empty; expected title and `@AGENTS.md`")
        return

    has_import = any(RE_CLAUDE_MD_IMPORT.match(ln) for ln in lines)
    if not has_import:
        report.add("P0", "claude-md-no-import", path, 1,
                   "CLAUDE.md is missing `@AGENTS.md` import directive")

    for lineno, raw in enumerate(read_text(path).splitlines(), start=1):
        if not raw.strip():
            continue
        if RE_CLAUDE_MD_TITLE.match(raw) or RE_CLAUDE_MD_IMPORT.match(raw):
            continue
        report.add("P1", "claude-md-extra", path, lineno,
                   f"CLAUDE.md contains prose beyond the pointer: {raw.strip()[:40]}")

    if not (path.parent / "AGENTS.md").exists():
        report.add("P0", "agents-md-missing", path, 1,
                   "Sibling AGENTS.md is missing; pointer cannot resolve")


# ---------------------------------------------------------------- Traversal & Output

def collect_targets(paths: list[Path]) -> tuple[list[Path], list[Path]]:
    """Collect all Skill directories and CLAUDE.md files, deduplicated and sorted."""
    skill_dirs: set[Path] = set()
    entrypoints: set[Path] = set()
    for path in paths:
        if path.is_file():
            if path.name == "SKILL.md":
                skill_dirs.add(path.parent)
            elif path.name == "CLAUDE.md":
                entrypoints.add(path)
            continue
        if (path / "SKILL.md").exists():
            skill_dirs.add(path)
        for found in path.rglob("SKILL.md"):
            skill_dirs.add(found.parent)
        for found in path.rglob("CLAUDE.md"):
            entrypoints.add(found)
    return sorted(skill_dirs), sorted(entrypoints)


def render(report: Report) -> str:
    if not report.findings:
        return (f"\nAll checks passed. Scanned {report.skills_scanned} Skill(s), "
                f"{report.entrypoints_scanned} entrypoint(s).\n")

    ordered = sorted(report.findings, key=lambda f: (SEVERITY_ORDER[f.severity], f.path, f.line))
    out: list[str] = [""]
    current = None
    for finding in ordered:
        if finding.severity != current:
            current = finding.severity
            out.append(f"## {current}")
        out.append(f"  {finding.path}:{finding.line}  [{finding.check}] {finding.message}")
    out.append("")
    out.append(f"Found {len(report.findings)} defect(s). Scanned {report.skills_scanned} Skill(s), "
               f"{report.entrypoints_scanned} entrypoint(s).")
    out.append("")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Validate Skill directory and Harness entrypoint structure."
    )
    parser.add_argument("paths", nargs="+", help="Skill directory, container directory, or project root")
    parser.add_argument("--json", action="store_true", help="Output structured JSON report")
    args = parser.parse_args(argv)

    targets: list[Path] = []
    for raw in args.paths:
        path = Path(raw)
        if not path.exists():
            print(f"Path does not exist: {raw}", file=sys.stderr)
            return 2
        targets.append(path)

    skill_dirs, entrypoints = collect_targets(targets)
    if not skill_dirs and not entrypoints:
        print("No SKILL.md or Harness entrypoints found under specified paths.", file=sys.stderr)
        return 2

    report = Report()
    for skill_dir in skill_dirs:
        check_skill(skill_dir, report)
    for entrypoint in entrypoints:
        check_claude_md(entrypoint, report)

    if args.json:
        print(json.dumps(
            {
                "findings": [f.__dict__ for f in report.findings],
                "skills_scanned": report.skills_scanned,
                "entrypoints_scanned": report.entrypoints_scanned,
            },
            ensure_ascii=False,
            indent=2,
        ))
    else:
        print(render(report))

    return 1 if report.findings else 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        sys.exit(2)
