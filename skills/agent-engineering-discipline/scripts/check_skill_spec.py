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
SKILL.md as well as every platform pointer file defined by Core Rule 10
(CLAUDE.md, .github/copilot-instructions.md, GEMINI.md,
.cursor/rules/agents.mdc, .cursorrules).

Exit codes (aligned with deliverable-writing-audit/scripts/detect.py):
    0  All checks passed
    1  Structural defects found
    2  Execution error (e.g., non-existent path or unreadable file)
"""

from __future__ import annotations

import argparse
from collections import deque
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import unquote

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

# Frontmatter `description` heuristics (Core Rule 11): ensure explicit exclusion
# boundaries, quoted user trigger phrases, and absence of banned vagueness/mechanics.
RE_DESC_EXCLUSION = re.compile(
    r"(?:不適用|不要(?:載入|用|使用)|不得(?:載入|用|使用)|切勿(?:載入|用|使用)"
    r"|請勿(?:載入|用|使用)|不應(?:載入|用|使用)|毋須(?:載入|用|使用)|無須(?:載入|用|使用)"
    r"|不處理|不用於|不使用|排除(?:時機|情境|條件|範圍|於)"
    r"|\b(?:do\s+not|don't|never|must\s+not|should\s+not)\s+(?:load|use|apply|invoke|trigger)\b"
    r"|\b(?:not\s+(?:for|applicable|suitable|used\s+for|intended\s+for)|does\s+not\s+apply|skip\s+(?:when|for|if))\b)",
    re.IGNORECASE,
)
RE_DESC_TRIGGERS = re.compile(
    r"(?:「\s*\S[^」\n]*\S\s*」|『\s*\S[^』\n]*\S\s*』|“\s*\S[^”\n]*\S\s*”|‘\s*\S[^’\n]*\S\s*’"
    r"|(?<![A-Za-z0-9])'\s*\S[^'\n]*\S\s*'(?![A-Za-z0-9])"
    r"|(?<![A-Za-z0-9])\"\s*\S[^\"\n]*\S\s*\"(?![A-Za-z0-9]))"
)
RE_DESC_BANNED = re.compile(
    r"(?:(?<!不會)(?<!並非)(?<!不是)(?<!不屬)(?<!不要)(?<!不得)(?<![不非無])(?:自動觸發|自動載入|全面|強大)"
    r"|(?<!\bnot\s)(?<!\bnever\s)(?<!\bno\s)\b(?:comprehensive|powerful|robust|automatically\s+(?:triggered|loaded)|auto[- ](?:triggered|loaded))\b)",
    re.IGNORECASE,
)

# Platform pointer files (Core Rule 10). Each is a thin entrypoint that must only
# direct the agent to AGENTS.md, the single canonical source.
#
#   rel_parts   path of the pointer relative to the project root, as path parts
#   import_re   what counts as a valid reference to AGENTS.md. Claude Code loads
#               rules only through an `@AGENTS.md` import line, so a prose mention
#               would silently load nothing; other platforms accept any line that
#               names AGENTS.md.
#   frontmatter whether a leading YAML block is configuration, not rule prose
RE_IMPORT_LINE = re.compile(r"^@AGENTS\.md\s*$")
RE_MENTIONS_AGENTS = re.compile(r"AGENTS\.md")
RE_HEADING = re.compile(r"^#{1,6}\s+\S")


@dataclass(frozen=True)
class PointerSpec:
    label: str
    rel_parts: tuple[str, ...]
    import_re: re.Pattern
    frontmatter: bool = False


POINTER_SPECS = (
    PointerSpec("Claude Code", ("CLAUDE.md",), RE_IMPORT_LINE),
    PointerSpec("GitHub Copilot", (".github", "copilot-instructions.md"), RE_MENTIONS_AGENTS),
    PointerSpec("Gemini CLI / Antigravity", ("GEMINI.md",), RE_MENTIONS_AGENTS),
    PointerSpec("Cursor", (".cursor", "rules", "agents.mdc"), RE_MENTIONS_AGENTS, frontmatter=True),
    PointerSpec("Cursor / Windsurf (legacy)", (".cursorrules",), RE_MENTIONS_AGENTS),
)

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


def strip_outer_quotes(val: str) -> str:
    """Remove matching outer YAML quotes without stripping an interior trailing quote."""
    val = val.strip()
    if len(val) >= 2 and val[0] == val[-1] and val[0] in ("\"", "'"):
        return val[1:-1]
    return val


def parse_frontmatter(text: str) -> tuple[dict[str, str], int, str | None]:
    """Parse YAML frontmatter, including multiline block and folded scalars.

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
    fm_lines = lines[1:end]
    i = 0
    while i < len(fm_lines):
        raw = fm_lines[i]
        if not raw.strip() or raw.lstrip().startswith("#") or raw.startswith((" ", "\t", "-")):
            i += 1
            continue
        match = RE_TOP_LEVEL_KEY.match(raw)
        if not match:
            i += 1
            continue
        key = match.group(1)
        val = match.group(2).strip()
        if val in ("|", "|-", "|+", ">", ">-", ">+"):
            joiner = "\n" if val.startswith("|") else " "
            cont: list[str] = []
            i += 1
            while i < len(fm_lines):
                nxt = fm_lines[i]
                if not nxt.strip():
                    cont.append("")
                    i += 1
                elif nxt.startswith((" ", "\t")):
                    cont.append(nxt.strip())
                    i += 1
                else:
                    break
            fields[key] = strip_outer_quotes(joiner.join(p for p in cont if p))
        elif val == "":
            cont = []
            i += 1
            while i < len(fm_lines):
                nxt = fm_lines[i]
                if not nxt.strip():
                    cont.append("")
                    i += 1
                elif nxt.startswith((" ", "\t")) and not nxt.lstrip().startswith("- "):
                    cont.append(nxt.strip())
                    i += 1
                else:
                    break
            fields[key] = strip_outer_quotes(" ".join(p for p in cont if p))
        else:
            cont = [val]
            i += 1
            while i < len(fm_lines):
                nxt = fm_lines[i]
                if nxt.startswith((" ", "\t")) and not nxt.lstrip().startswith("- "):
                    cont.append(nxt.strip())
                    i += 1
                else:
                    break
            fields[key] = strip_outer_quotes(" ".join(cont))
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
    else:
        if len(description) > DESCRIPTION_MAX_LEN:
            report.add("P0", "description-length", skill_md, 1,
                       f"`description` length {len(description)} exceeds specification limit {DESCRIPTION_MAX_LEN}")
        check_description_quality(skill_md, description, report)

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
    check_no_orphan_files(skill_dir, report)


def check_description_quality(skill_md: Path, description: str, report: Report) -> None:
    """Enforce Core Rule 11 criteria on frontmatter `description`."""
    if not RE_DESC_EXCLUSION.search(description):
        report.add("P1", "description-missing-exclusion", skill_md, 1,
                   "`description` is missing an explicit exclusion boundary (e.g. 'Do not load when...')")
    if not RE_DESC_TRIGGERS.search(description):
        report.add("P1", "description-missing-triggers", skill_md, 1,
                   "`description` is missing quoted user trigger phrases")
    for match in RE_DESC_BANNED.finditer(description):
        report.add("P1", "description-banned-term", skill_md, 1,
                   f"`description` contains banned superlative or platform-mechanics term `{match.group(0)}`")


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


def clean_link_target(raw_target: str) -> str:
    """Extract and percent-decode the file path portion of a Markdown link target."""
    s = raw_target.strip()
    if s.startswith("<"):
        end = s.find(">")
        if end != -1:
            s = s[1:end].strip()
    else:
        title_match = re.match(r'^(\S+)(?:\s+(?:"[^"]*"|\'[^\']*\'|\([^)]*\)))?$', s)
        if title_match:
            s = title_match.group(1)
    return unquote(s.split("#", 1)[0].split("?", 1)[0].strip())


def strip_html_comments(text: str) -> str:
    """Remove HTML comments from Markdown source before prose/path extraction."""
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def iter_markdown_prose_lines(text: str):
    """Yield (1-indexed lineno, masked_line) skipping fenced blocks, HTML comments, and inline code."""
    in_fence = False
    in_comment = False
    for lineno, raw in enumerate(text.splitlines(), start=1):
        if RE_FENCE.match(raw):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        line = raw
        if in_comment:
            end_idx = line.find("-->")
            if end_idx == -1:
                continue
            line = line[end_idx + 3:]
            in_comment = False
        line = re.sub(r"<!--.*?-->", "", line)
        open_idx = line.find("<!--")
        if open_idx != -1:
            line = line[:open_idx]
            in_comment = True
        yield lineno, RE_INLINE_CODE.sub("``", line)


def collect_disk_relpaths(skill_dir: Path) -> set[str]:
    """Collect exact-case relative POSIX paths of all non-ignored entries under `skill_dir`."""
    relpaths: set[str] = set()
    for dirpath, dirs, files in os.walk(skill_dir, followlinks=False):
        dirs[:] = [d for d in dirs if d not in {".git", "__pycache__"}]
        base = Path(dirpath)
        for name in dirs + files:
            if name == "__pycache__" or name.endswith(".pyc"):
                continue
            p = base / name
            relpaths.add(p.relative_to(skill_dir).as_posix())
    return relpaths


def check_relative_links(skill_dir: Path, report: Report) -> None:
    """All internal relative links inside a Skill directory must resolve to exact-case existing paths."""
    skill_root = skill_dir.resolve()
    disk_relpaths = collect_disk_relpaths(skill_dir)
    link_pattern = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
    for md in sorted(skill_dir.rglob("*.md")):
        for lineno, masked in iter_markdown_prose_lines(read_text(md)):
            for target in link_pattern.findall(masked):
                cleaned = clean_link_target(target)
                if not cleaned or cleaned.startswith(("http://", "https://", "mailto:")):
                    continue
                if cleaned.startswith("/"):
                    report.add("P1", "absolute-link", md, lineno,
                               f"Link `{target}` starts with `/`, which breaks when installed into another project")
                    continue
                try:
                    resolved = (md.parent / cleaned).resolve()
                except (OSError, ValueError):
                    report.add("P1", "dead-link", md, lineno, f"Link `{target}` points to an invalid path")
                    continue
                if not resolved.exists():
                    report.add("P1", "dead-link", md, lineno, f"Link `{target}` points to a non-existent path")
                    continue
                if skill_root in resolved.parents:
                    rel_posix = (md.parent / cleaned).resolve().relative_to(skill_root).as_posix()
                    norm_posix = os.path.normpath((md.parent.relative_to(skill_dir) / cleaned).as_posix()).replace("\\", "/")
                    if rel_posix not in disk_relpaths or norm_posix not in disk_relpaths:
                        report.add("P1", "dead-link", md, lineno,
                                   f"Link `{target}` does not match exact on-disk casing")


def check_no_orphan_files(skill_dir: Path, report: Report) -> None:
    """Every file under references/, assets/, or scripts/ must be reachable from SKILL.md.

    Fenced CLI code blocks inside Markdown are intentionally scanned for explicit subpath
    mentions because Skills commonly document `scripts/*.py` invocations inside bash fences.
    """
    skill_root = skill_dir.resolve()
    all_subfiles: dict[str, Path] = {}
    for sub in ("references", "assets", "scripts"):
        base = skill_dir / sub
        if not base.is_dir() or base.is_symlink():
            continue
        for dirpath, dirs, files in os.walk(base, followlinks=False):
            dirs[:] = [d for d in dirs if d != "__pycache__" and not d.startswith(".")]
            base_path = Path(dirpath)
            for fname in files:
                if fname.startswith(".") or fname.endswith(".pyc"):
                    continue
                candidate = base_path / fname
                if candidate.is_symlink():
                    continue
                rel_posix = candidate.relative_to(skill_dir).as_posix()
                all_subfiles[rel_posix] = candidate

    if not all_subfiles:
        return

    link_pattern = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
    inline_code_pattern = re.compile(r"`([^`\n]+)`")
    subpath_pattern = re.compile(r"((?:references|assets|scripts)/[A-Za-z0-9_./-]+)")
    asset_quote_pattern = re.compile(
        r"""["']([^"'\n\s]+\.(?:md|py|sh|js|css|html|json|txt|yaml|yml|toml|svg|png|jpg|jpeg|gif|webp|ico|woff|woff2|ttf|otf|csv|tsv|sql|xml))["']""",
        re.IGNORECASE,
    )
    css_url_pattern = re.compile(r"url\(\s*['\"]?([^'\"\)\s#?,]+)['\"]?\s*\)", re.IGNORECASE)
    html_attr_pattern = re.compile(r"\b(?:src|href)=([^\s\"'>]+)", re.IGNORECASE)
    py_from_pattern = re.compile(r"^\s*from\s+(\.*)([A-Za-z0-9_.]*)\s+import\s+([^\n#]+)", re.M)
    py_imp_pattern = re.compile(r"^\s*import\s+([^\n#]+)", re.M)
    bfs_suffixes = {".md", ".py", ".sh", ".js", ".html", ".css", ".json"}

    visited: set[str] = set()
    referenced: set[str] = set()
    queue: deque[str] = deque(["SKILL.md"])

    while queue:
        cur_rel = queue.popleft()
        cur_path = skill_dir / cur_rel
        if cur_rel in visited or not cur_path.is_file():
            continue
        visited.add(cur_rel)
        text = read_text(cur_path)
        cands: list[Path] = []
        rel_cands: list[str] = []

        def add_cand(base: Path, rel_str: str) -> None:
            cands.append(base / rel_str)
            rel_cands.append((base.relative_to(skill_dir) / rel_str).as_posix())

        if cur_path.suffix == ".md":
            for _, masked in iter_markdown_prose_lines(text):
                for target in link_pattern.findall(masked):
                    cleaned = clean_link_target(target)
                    if not cleaned or cleaned.startswith(("http://", "https://", "mailto:", "/")):
                        continue
                    add_cand(cur_path.parent, cleaned)

            comment_free = strip_html_comments(text)
            for code in inline_code_pattern.findall(comment_free):
                for tok in code.split():
                    tok_clean = tok.strip(".,;:()[]{}\"'").split("#", 1)[0]
                    if not tok_clean:
                        continue
                    if "/" in tok_clean or tok_clean.endswith(tuple(bfs_suffixes)):
                        add_cand(skill_dir, tok_clean)
                        add_cand(cur_path.parent, tok_clean)

            for m in subpath_pattern.finditer(comment_free):
                rel = m.group(1).rstrip(".,;:")
                add_cand(skill_dir, rel)
                add_cand(cur_path.parent, rel)
        else:
            scan_text = strip_html_comments(text) if cur_path.suffix in {".html", ".svg", ".xml"} else text
            for m in subpath_pattern.finditer(scan_text):
                rel = m.group(1).rstrip(".,;:")
                add_cand(skill_dir, rel)
                add_cand(cur_path.parent, rel)
            for q in asset_quote_pattern.findall(scan_text):
                add_cand(cur_path.parent, q)
                add_cand(skill_dir, q)
            for raw_url in css_url_pattern.findall(scan_text) + html_attr_pattern.findall(scan_text):
                cleaned = clean_link_target(raw_url)
                if not cleaned or cleaned.startswith(("http://", "https://", "mailto:", "/", "data:")):
                    continue
                add_cand(cur_path.parent, cleaned)
                add_cand(skill_dir, cleaned)
            if cur_path.suffix == ".py":
                for dots, mod_base, names in py_from_pattern.findall(text):
                    up = max(0, len(dots) - 1)
                    rel_anchor = cur_path.parent
                    for _ in range(up):
                        if skill_dir in rel_anchor.parents:
                            rel_anchor = rel_anchor.parent
                    roots = [rel_anchor] if dots else [cur_path.parent, skill_dir / "scripts"]
                    bases = [mod_base.replace(".", "/")] if mod_base else []
                    for item in names.split(","):
                        ident = item.strip().split()[0] if item.strip() else ""
                        if ident and ident != "*" and not ident.startswith("("):
                            if mod_base:
                                bases.append(f"{mod_base.replace('.', '/')}/{ident}")
                            else:
                                bases.append(ident)
                    for r in roots:
                        if not r.is_dir():
                            continue
                        for b in bases:
                            add_cand(r, f"{b}.py")
                            add_cand(r, f"{b}/__init__.py")
                for names in py_imp_pattern.findall(text):
                    for item in names.split(","):
                        mod_name = item.strip().split()[0] if item.strip() else ""
                        if mod_name:
                            mod_rel = mod_name.replace(".", "/")
                            for r in (cur_path.parent, skill_dir / "scripts"):
                                if r.is_dir():
                                    add_cand(r, f"{mod_rel}.py")
                                    add_cand(r, f"{mod_rel}/__init__.py")

        norm_cands = {os.path.normpath(rc).replace("\\", "/") for rc in rel_cands}
        for cand in cands:
            try:
                p = cand.resolve()
            except (OSError, ValueError):
                continue
            if p.is_file() and skill_root in p.parents:
                rel_posix = p.relative_to(skill_root).as_posix()
                if rel_posix in all_subfiles and rel_posix in norm_cands:
                    referenced.add(rel_posix)
                    if Path(rel_posix).suffix in bfs_suffixes and rel_posix not in visited:
                        queue.append(rel_posix)

    for rel_path in sorted(all_subfiles.keys() - referenced):
        report.add("P1", "orphan-file", all_subfiles[rel_path], 1,
                   f"File `{rel_path}` is not referenced from SKILL.md or any reachable reference file")


# ---------------------------------------------------------------- Harness Checks

def pointer_root(path: Path, spec: PointerSpec) -> Path:
    """Project root implied by a pointer's location, e.g. the parent of `.github/`."""
    return path.parents[len(spec.rel_parts) - 1]


def body_lines(text: str, has_frontmatter: bool) -> list[tuple[int, str]]:
    """Non-blank (line_number, text) pairs, skipping a leading YAML configuration block."""
    lines = text.splitlines()
    start = 0
    if has_frontmatter and lines and RE_FRONTMATTER_FENCE.match(lines[0]):
        for idx in range(1, len(lines)):
            if RE_FRONTMATTER_FENCE.match(lines[idx]):
                start = idx + 1
                break
    return [(n, ln.strip()) for n, ln in enumerate(lines[start:], start=start + 1) if ln.strip()]


def check_pointer(path: Path, spec: PointerSpec, report: Report) -> None:
    """A platform entrypoint must only point at the sibling AGENTS.md (Core Rule 10).

    Valid forms: a symlink resolving to the project's AGENTS.md, or a short file
    whose every line is a heading or a reference to AGENTS.md. Anything else is a
    second copy of the rules that will drift from the canonical source.
    """
    report.entrypoints_scanned += 1
    name = "/".join(spec.rel_parts)
    agents = pointer_root(path, spec) / "AGENTS.md"
    agents_found = agents.exists()
    if not agents_found:
        report.add("P0", "agents-md-missing", path, 1,
                   f"{name} ({spec.label}) has no AGENTS.md at the project root; the pointer cannot resolve")

    if path.is_symlink():
        if agents_found and path.resolve() != agents.resolve():
            report.add("P0", "pointer-symlink-target", path, 1,
                       f"{name} ({spec.label}) is a symlink that does not resolve to AGENTS.md")
        return

    lines = body_lines(read_text(path), spec.frontmatter)
    if not lines:
        report.add("P1", "pointer-empty", path, 1,
                   f"{name} ({spec.label}) is empty; expected a reference to AGENTS.md")
        return

    if not any(spec.import_re.search(text) for _, text in lines):
        want = "an `@AGENTS.md` import line" if spec.import_re is RE_IMPORT_LINE else "a reference to AGENTS.md"
        report.add("P0", "pointer-no-reference", path, 1,
                   f"{name} ({spec.label}) is missing {want}; the canonical rules are never loaded")

    for lineno, text in lines:
        if RE_HEADING.match(text) or spec.import_re.search(text):
            continue
        report.add("P1", "pointer-extra", path, lineno,
                   f"{name} ({spec.label}) contains prose beyond the pointer: {text[:40]}")


# ---------------------------------------------------------------- Traversal & Output

def match_pointer(path: Path) -> PointerSpec | None:
    """The pointer spec whose relative location matches the end of `path`, if any."""
    for spec in POINTER_SPECS:
        if path.parts[-len(spec.rel_parts):] == spec.rel_parts:
            return spec
    return None


def collect_targets(paths: list[Path]) -> tuple[list[Path], list[tuple[Path, PointerSpec]]]:
    """Collect all Skill directories and platform pointer files, deduplicated and sorted."""
    skill_dirs: set[Path] = set()
    entrypoints: dict[Path, PointerSpec] = {}
    for path in paths:
        if path.is_file() or path.is_symlink():
            if path.name == "SKILL.md":
                skill_dirs.add(path.parent)
            elif (spec := match_pointer(path)) is not None:
                entrypoints[path] = spec
            continue
        if (path / "SKILL.md").exists():
            skill_dirs.add(path)
        for found in path.rglob("SKILL.md"):
            if not any(p in {".git", "node_modules", ".venv", "venv", "__pycache__"} for p in found.parts):
                skill_dirs.add(found.parent)
        for spec in POINTER_SPECS:
            for found in walk_named(path, spec.rel_parts[-1]):
                if match_pointer(found) is spec:
                    entrypoints[found] = spec
    return sorted(skill_dirs), sorted(entrypoints.items())


def walk_named(root: Path, name: str):
    """Yield every file or symlink called `name` under `root`, including dangling symlinks.

    `Path.rglob` skips dangling symlinks, which are exactly the pointer defects
    worth reporting, so the walk is done with `os.walk`. Prunes version control
    and dependency trees so unrelated large directories are not traversed.
    """
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in {".git", "node_modules", ".venv", "venv", "__pycache__"}]
        if name in files:
            yield Path(dirpath) / name


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
    for entrypoint, spec in entrypoints:
        check_pointer(entrypoint, spec, report)

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
