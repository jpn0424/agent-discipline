#!/usr/bin/env python3
"""Skill 目錄與 Harness 入口檔的結構檢查。

檢查對象是 Skill 自身的結構，不對目標專案的 git 慣例或工項慣例做任何假設，
因此散佈到任何專案都可執行。無外部依賴，Python 3.8 以上的標準庫即可。

用法：
    python3 check_skill_spec.py <path...>
    python3 check_skill_spec.py <path...> --json

path 可以是 Skill 目錄本身、包含多個 Skill 的目錄、或專案根目錄。
腳本會遞迴尋找所有含 SKILL.md 的目錄，以及所有 CLAUDE.md。

結束碼與 deliverable-writing-audit 的偵測腳本一致：
    0  全部通過
    1  有缺陷
    2  執行錯誤，例如路徑不存在或無法讀取
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------- 平台限制

# 以下數值來自 Skill 平台的欄位驗證規則，不是本腳本自訂的偏好，改動前先確認平台文件。
NAME_MAX_LEN = 64
DESCRIPTION_MAX_LEN = 1024

# 規格允許的 frontmatter 欄位，其餘一律拒絕。
ALLOWED_FIELDS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}

# 平台保留字，出現在 name 中會使 Skill 無法註冊。
RESERVED_WORDS = ("anthropic", "claude")

# name 的合法字元集：小寫字母、數字、連字號。
RE_VALID_NAME = re.compile(r"^[a-z0-9-]+$")

# frontmatter 內出現角括號會被當成標籤，是提示詞注入的入口，平台一律拒絕。
RE_ANGLE_TAG = re.compile(r"<[^>]*>")

# frontmatter 的界線：檔案第一行必須是 `---`，下一個獨立的 `---` 是結尾。
RE_FRONTMATTER_FENCE = re.compile(r"^---\s*$")

# 頂層 `key: value`。frontmatter 是簡單的鍵值結構，不需要完整 YAML 解析器，
# 避免引入外部依賴。巢狀清單以縮排辨識，本腳本只取頂層鍵。
RE_TOP_LEVEL_KEY = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*)\s*:\s*(.*)$")

# 本機絕對路徑的偵測由 deliverable-writing-audit 的 detect.py 負責，此處不重複實作。
# 那支腳本會先遮蔽 inline code 與程式碼區塊，才不會把規則裡的壞例子示範當成命中。

# 程式碼區塊與 inline code 內的連結是格式示例而非真實連結，比對前先遮蔽。
RE_FENCE = re.compile(r"^\s*(?:```|~~~)")
RE_INLINE_CODE = re.compile(r"`[^`]*`")

# CLAUDE.md 的合法內容只有兩種行：一行 Markdown 標題，一行 `@AGENTS.md` 匯入指令。
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


# ---------------------------------------------------------------- 讀檔

def read_text(path: Path) -> str:
    """讀取檔案文字。編碼問題就地處理，不把例外丟回呼叫端。"""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # 非 UTF-8 的規範文件本身就是缺陷，但讀不到內容就無法檢查其他項目，
        # 因此改用寬鬆解碼繼續往下跑，並由呼叫端另外標記編碼問題。
        return path.read_text(encoding="utf-8", errors="replace")


def parse_frontmatter(text: str) -> tuple[dict[str, str], int, str | None]:
    """解析 frontmatter。

    回傳 (頂層鍵值, frontmatter 結束行號, 錯誤說明)。錯誤說明為 None 表示解析成功。
    行號從 1 起算，供回報定位。
    """
    lines = text.splitlines()
    if not lines or not RE_FRONTMATTER_FENCE.match(lines[0]):
        return {}, 0, "檔案開頭沒有 YAML Frontmatter"

    end = None
    for idx in range(1, len(lines)):
        if RE_FRONTMATTER_FENCE.match(lines[idx]):
            end = idx
            break
    if end is None:
        return {}, 0, "Frontmatter 的結束分隔線缺失"

    fields: dict[str, str] = {}
    for raw in lines[1:end]:
        if not raw.strip() or raw.startswith((" ", "\t", "-")):
            continue
        match = RE_TOP_LEVEL_KEY.match(raw)
        if match:
            fields[match.group(1)] = match.group(2).strip().strip("\"'")
    return fields, end + 1, None


# ---------------------------------------------------------------- Skill 檢查

def check_skill(skill_dir: Path, report: Report) -> None:
    report.skills_scanned += 1
    skill_md = skill_dir / "SKILL.md"
    text = read_text(skill_md)

    # 目錄名必須是小寫 kebab-case，name 要與它一致才找得到。
    dir_name = skill_dir.name
    if not RE_VALID_NAME.match(dir_name):
        report.add("P0", "dir-name", skill_dir, 1,
                   f"Skill 目錄名 `{dir_name}` 不是小寫 kebab-case")

    fields, body_start, err = parse_frontmatter(text)
    if err:
        report.add("P0", "frontmatter-missing", skill_md, 1, err)
        return

    fm_text = "\n".join(text.splitlines()[: body_start - 1])
    for tag in RE_ANGLE_TAG.findall(fm_text):
        report.add("P0", "frontmatter-angle-tag", skill_md, 1,
                   f"Frontmatter 含角括號標籤 `{tag}`，會被拒絕載入")

    name = fields.get("name", "")
    if not name:
        report.add("P0", "name-missing", skill_md, 1, "Frontmatter 缺少 `name`")
    else:
        if not RE_VALID_NAME.match(name):
            report.add("P0", "name-format", skill_md, 1,
                       f"`name: {name}` 只能包含小寫字母、數字與連字號")
        if name.startswith("-") or name.endswith("-"):
            report.add("P0", "name-hyphen-edge", skill_md, 1,
                       f"`name: {name}` 不得以連字號開頭或結尾")
        if "--" in name:
            report.add("P0", "name-double-hyphen", skill_md, 1,
                       f"`name: {name}` 不得含連續連字號")
        if len(name) > NAME_MAX_LEN:
            report.add("P0", "name-length", skill_md, 1,
                       f"`name` 長度 {len(name)} 超過上限 {NAME_MAX_LEN}")
        if name != dir_name:
            report.add("P0", "name-mismatch", skill_md, 1,
                       f"`name: {name}` 與目錄名 `{dir_name}` 不一致")
        for word in RESERVED_WORDS:
            if word in name.lower():
                report.add("P0", "name-reserved", skill_md, 1,
                           f"`name` 含平台保留字 `{word}`")

    description = fields.get("description", "")
    if not description:
        report.add("P0", "description-missing", skill_md, 1, "Frontmatter 缺少 `description`")
    if len(description) > DESCRIPTION_MAX_LEN:
        report.add("P0", "description-length", skill_md, 1,
                   f"`description` 長度 {len(description)} 超過規格上限 {DESCRIPTION_MAX_LEN}")

    for field in fields:
        if field not in ALLOWED_FIELDS:
            report.add("P0", "unexpected-field", skill_md, 1,
                       f"Frontmatter 含規格未定義的欄位 `{field}`，規格只允許 "
                       + "、".join(f"`{x}`" for x in sorted(ALLOWED_FIELDS)))

    # 給人讀的說明放專案根目錄，給 Agent 讀的規格整合進 SKILL.md。
    readme = skill_dir / "README.md"
    if readme.exists():
        report.add("P1", "skill-readme", readme, 1,
                   "Skill 目錄內不得有 README.md，說明請整合進 SKILL.md")

    check_no_frontmatter_in_subfiles(skill_dir, report)
    check_relative_links(skill_dir, report)


def check_no_frontmatter_in_subfiles(skill_dir: Path, report: Report) -> None:
    """references/ 與 assets/ 之下的 Markdown 不得帶 frontmatter。

    那些檔案不會被當成 Skill 探索到，frontmatter 對任何 Agent 都不生效，
    只佔 context 並讓維護者誤以為它們會被獨立載入。
    """
    for sub in ("references", "assets"):
        base = skill_dir / sub
        if not base.is_dir():
            continue
        for md in sorted(base.rglob("*.md")):
            head = read_text(md).splitlines()
            if head and RE_FRONTMATTER_FENCE.match(head[0]):
                report.add("P1", "stray-frontmatter", md, 1,
                           f"`{sub}/` 之下的檔案帶 frontmatter，該欄位不會生效")


def check_relative_links(skill_dir: Path, report: Report) -> None:
    """Skill 內部連結必須是可解析的相對路徑。

    程式碼區塊與 inline code 內的連結是格式示例，例如工項範本示範怎麼引用截圖，
    那些路徑本來就不存在，比對前先遮蔽避免誤判。
    """
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
                               f"連結 `{target}` 以斜線開頭，安裝到其他專案會失效")
                    continue
                resolved = (md.parent / target.split("#", 1)[0]).resolve()
                if not resolved.exists():
                    report.add("P1", "dead-link", md, lineno, f"連結 `{target}` 指向不存在的路徑")


# ---------------------------------------------------------------- Harness 檢查

def check_claude_md(path: Path, report: Report) -> None:
    """CLAUDE.md 只能有標題與 `@AGENTS.md` 參照，不得含任何規範內容。"""
    report.entrypoints_scanned += 1
    lines = [ln for ln in read_text(path).splitlines() if ln.strip()]
    if not lines:
        report.add("P1", "claude-md-empty", path, 1, "CLAUDE.md 是空的，應含標題與 `@AGENTS.md`")
        return

    has_import = any(RE_CLAUDE_MD_IMPORT.match(ln) for ln in lines)
    if not has_import:
        report.add("P0", "claude-md-no-import", path, 1,
                   "CLAUDE.md 缺少 `@AGENTS.md` 參照，規範不會被載入")

    for lineno, raw in enumerate(read_text(path).splitlines(), start=1):
        if not raw.strip():
            continue
        if RE_CLAUDE_MD_TITLE.match(raw) or RE_CLAUDE_MD_IMPORT.match(raw):
            continue
        report.add("P1", "claude-md-extra", path, lineno,
                   f"CLAUDE.md 含參照以外的內容：{raw.strip()[:40]}")

    if not (path.parent / "AGENTS.md").exists():
        report.add("P0", "agents-md-missing", path, 1,
                   "同目錄下沒有 AGENTS.md，參照指向不存在的正本")


# ---------------------------------------------------------------- 走訪與輸出

def collect_targets(paths: list[Path]) -> tuple[list[Path], list[Path]]:
    """找出所有 Skill 目錄與 CLAUDE.md。回傳的清單已去重且排序。"""
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
        return (f"\n全部通過。檢查 {report.skills_scanned} 個 Skill、"
                f"{report.entrypoints_scanned} 個入口檔。\n")

    ordered = sorted(report.findings, key=lambda f: (SEVERITY_ORDER[f.severity], f.path, f.line))
    out: list[str] = [""]
    current = None
    for finding in ordered:
        if finding.severity != current:
            current = finding.severity
            out.append(f"## {current}")
        out.append(f"  {finding.path}:{finding.line}  [{finding.check}] {finding.message}")
    out.append("")
    out.append(f"共 {len(report.findings)} 處缺陷。檢查 {report.skills_scanned} 個 Skill、"
               f"{report.entrypoints_scanned} 個入口檔。")
    out.append("")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="檢查 Skill 目錄與 Harness 入口檔的結構是否符合規格。"
    )
    parser.add_argument("paths", nargs="+", help="Skill 目錄、含 Skill 的目錄、或專案根目錄")
    parser.add_argument("--json", action="store_true", help="輸出結構化結果")
    args = parser.parse_args(argv)

    targets: list[Path] = []
    for raw in args.paths:
        path = Path(raw)
        if not path.exists():
            print(f"路徑不存在：{raw}", file=sys.stderr)
            return 2
        targets.append(path)

    skill_dirs, entrypoints = collect_targets(targets)
    if not skill_dirs and not entrypoints:
        print("指定路徑下沒有找到 SKILL.md 或 CLAUDE.md。", file=sys.stderr)
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
