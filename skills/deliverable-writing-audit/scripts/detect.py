#!/usr/bin/env python3
"""Deliverable writing symptom detector.

Depends only on the Python 3 standard library. Detects symptoms marked as
mechanically detectable in references/pattern-catalog.md; symptoms requiring
semantic comprehension are out of scope for this script (see
references/category-map.md).

Usage:
    python3 detect.py <path...> [--profile NAME] [--json] [--terms FILE]

Exit codes: 0 clean, 1 hits found, 2 execution error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------- Symptom Definitions

# (type, catalog_id, severity, label)
META = {
    "secret-leak": ("A1", "P0", "Secret and credential leakage"),
    "ai-signature": ("A2", "P0", "AI attribution signature"),
    "unverified-status": ("A4", "P0", "Residual unverified status"),
    "abs-path": ("A5", "P0", "Local absolute path"),
    "change-narration": ("B1", "P1", "Change narration and before/after comparison"),
    "paren-gloss": ("B2", "P1", "Parenthetical gloss"),
    "note-to-self": ("B3", "P1", "Residual note-to-self"),
    "unevidenced-limit": ("C1", "P1", "Capability limitation claim (verify evidence)"),
    "retired-term": ("C3", "P1", "Revived retired terminology"),
    "duplicated-rule": ("C4", "P1", "Scattered duplicate rules"),
    "dev-jargon-leak": ("C7", "P1", "Developer jargon leaked into deliverables"),
    "vague-filler": ("D1", "P2", "Vague quantifiers and filler words density"),
    "emoji-density": ("D2", "P2", "Emoji density"),
    "label-period": ("D3", "P2", "Period inside bold list label"),
}

SEVERITY_ORDER = {"P0": 0, "P1": 1, "P2": 2}

# Profile tolerance matrix. Unlisted entries default to strict.
PROFILES = {
    "harness": {
        "dev-jargon-leak": "skip",
        "emoji-density": "relaxed",
        "duplicated-rule": "extra",
        "unverified-status": "extra",
    },
    "agent-facing": {
        "dev-jargon-leak": "extra",
        "retired-term": "extra",
        "unverified-status": "extra",
        "duplicated-rule": "extra",
        "emoji-density": "relaxed",
    },
    "deliverable": {
        "secret-leak": "extra",
        "abs-path": "extra",
        "dev-jargon-leak": "extra",
        "note-to-self": "extra",
        "unverified-status": "extra",
        "retired-term": "extra",
    },
    "ticket": {
        "change-narration": "relaxed",
        "note-to-self": "relaxed",
        "abs-path": "relaxed",
        "dev-jargon-leak": "skip",
        "retired-term": "relaxed",
        "duplicated-rule": "skip",
        "emoji-density": "skip",
        "unverified-status": "extra",
    },
    "changelog": {
        "change-narration": "skip",
        "paren-gloss": "relaxed",
        "retired-term": "skip",
        "duplicated-rule": "skip",
        "emoji-density": "skip",
        "unverified-status": "relaxed",
        "abs-path": "relaxed",
        "unevidenced-limit": "relaxed",
    },
    "pr-commit": {
        "secret-leak": "extra",
        "change-narration": "relaxed",
        "duplicated-rule": "skip",
        "unverified-status": "skip",
        "retired-term": "relaxed",
        "unevidenced-limit": "skip",
    },
}

RE_SECRET_ASSIGN = re.compile(
    r"(?:^|[^A-Za-z])[A-Z0-9_]{0,24}(?:PASSWORD|PASSWD|SECRET|TOKEN|API_?KEY|ACCESS_?KEY|CLIENT_SECRET|PRIVATE_KEY)"
    r"\s*[=:]\s*(?!\s*$)(?!<)(?!\{)(?!\$)[^\s\"']{4,}",
    re.IGNORECASE,
)
# {0,40} is the maximum character distance between the shell verb and `.env`,
# wide enough for flags and relative paths (`grep -i SECRET ../config/.env`)
# while narrow enough not to pair an unrelated command with a later `.env` mention.
RE_SECRET_DUMP = re.compile(r"\b(?:cat|grep|echo|print|head|tail|less|more)\b[^\n]{0,40}\.env\b")
# Allowlist matches the end of the hostname rather than any substring; otherwise
# allowlisting shields.io would also allowlist shields.io.attacker.net.
RE_INTERNAL_HOST = re.compile(
    r"https?://(?![^\s/]*"
    r"(?:localhost|127\.0\.0\.1|example\.[a-z]{2,}|github\.com|skills\.sh|shields\.io)"
    r"(?![a-z0-9.-]))"
    r"[^\s/]*\.[a-z]{2,}(?:\.[a-z]{2,})+"
)
RE_AI_SIGNATURE = re.compile(
    r"(?:"
    r"provide[d]?\s+by\s+\[?(?:claude|gemini|chatgpt|copilot|codex|cursor|antigravity|openai|anthropic)"
    r"|generated\s+(?:with|by)\s+\[?(?:claude|gemini|chatgpt|copilot|codex|cursor|antigravity|openai|anthropic)"
    r"|co-authored-by:\s*(?:(?:github\s+)?copilot|claude|codex|cursor|gemini|antigravity)"
    r"|🤖"
    r")",
    re.IGNORECASE,
)
# Attributive `unverified <noun>` (e.g. "unverified work", "unverified claim") is
# normal rule prose; A4 targets standalone/predicate status markers ("untested",
# "to be confirmed", "is/remains unverified", "| unverified |", "TBD").
RE_UNVERIFIED = re.compile(
    r"未實測|未測試|待確認|待驗證|尚未驗證|推定支援|狀態未知"
    r"|\buntested\b|\bto be confirmed\b|\bto be verified\b|\byet to be (?:tested|verified)\b"
    r"|\bnot yet (?:tested|verified)\b|\bassumed supported\b|\bstatus unknown\b"
    r"|(?:status|state|\bis|\bremains|\bleft)\s*[:=]?\s*\bunverified\b"
    r"|\|\s*unverified\s*\|"
    r"|\bTBD\b|\bTODO\b(?=.*(?:test|verif|測|驗))",
    re.IGNORECASE,
)
RE_ABS_PATH = re.compile(r"(?:/Users/[A-Za-z0-9._-]+|/home/[A-Za-z0-9._-]+|[A-Za-z]:\\\\?Users\\\\?[A-Za-z0-9._-]+)")
# Attributive uses such as "retired terminology" or "已退役術語" are category labels
# rather than change narration, excluded via lookahead.
RE_CHANGE_NARRATION = re.compile(
    r"原本[^\n]{0,12}(?:改為|改成)"
    r"|原本(?:是|走|用)[^\n]{0,30}(?:現在|後來|改)"
    r"|之前(?:是|走|用|採用|的做法)"
    r"|以前(?:是|走|用)"
    r"|本次(?:調整|修改|變更|重構)"
    r"|這次(?:改|調整)了"
    r"|後來(?:發現|改)"
    r"|舊(?:版|做法|方式)(?:是|走|用)"
    r"|已(?:改為|改成|棄用|退役|移除|廢除)(?!術語|名詞|清單|項目|標記|字詞)"
    r"|不再(?:使用|支援|走)"
    r"|第[一二三四五六七八九十\d]+輪(?:修正|調整)"
    r"|從前"
    r"|\boriginally\b[^\n]{0,35}\b(?:changed to|replaced with|updated to)\b"
    r"|\bpreviously\s+(?:was|used|relied on|adopted|walked|ran)\b"
    r"|\bformerly\s+(?:was|used|relied on|adopted)\b"
    r"|\bin this\s+(?:update|change|modification|refactor|revision)\b"
    r"|\bwe\s+later\s+(?:found|discovered|changed)\b"
    r"|\bthe\s+old\s+(?:version|approach|method)\s+(?:was|used)\b"
    r"|\bhas\s+been\s+(?:changed to|deprecated|retired|removed|abolished)\b"
    r"|\bno\s+longer\s+(?:used|supported|active)\b"
    r"|\bafter\s+round\s+(?:one|two|three|four|five|\d+)\s+of\s+(?:fixes|changes|revisions|updates)\b",
    re.IGNORECASE,
)
RE_NOTE_TO_SELF = re.compile(
    r"\bTODO\b|\bFIXME\b|\bXXX\b|\bHACK\b|\bfill in later\b|\bfor now just\b|\bI guess\b|\bfix later\b"
    r"|待補|先這樣|我猜|暫時先|等等再說|\?\?\?"
)
RE_LIMIT_CLAIM = re.compile(
    r"做不到|只能由|無法(?:取得|讀取|建立|完成|支援)|不支援|辦不到"
    r"|\bcannot\s+(?:fetch|retrieve|read|create|complete|support|be\s+fetched|be\s+retrieved|be\s+read|be\s+created|be\s+supported)\b"
    r"|\bdoes\s+not\s+support\b|\bis\s+not\s+supported\b|\bonly\s+supported\s+(?:by|via)\b"
    r"|\bimpossible\s+to\s+(?:fetch|read|create|support)\b",
    re.IGNORECASE,
)
RE_EVIDENCE = re.compile(
    r"錯誤原文|原文如下|實測|已驗證|截圖|TASK-\d|AD-\d|HD-\d|證據|errors?[:：]"
    r"|\bverbatim\s+error\b|\berror\s+output\b|\bverified\b|\btested\b|\bscreenshot\b|\bevidence\b|\bHTTP\s+[45]\d\d\b",
    re.IGNORECASE,
)
RE_DEV_JARGON = re.compile(r"\.claude/|\.agents?/|\.cursor/|\.windsurf/|\.github/copilot-instructions|CLAUDE\.md|GEMINI\.md|Harness|本機|本地開發|subagent|validator|AD-\d{3,}|HD-\d{3,}|TASK-\d{6,}")
# Matches only bold list labels ending in a period. Unbolded list openings are
# frequently complete imperative sentences ("- Run the test suite. If it fails..."),
# which cannot be separated from noun labels in regex without a POS parser.
RE_LABEL_PERIOD = re.compile(r"^\s*[-*+]\s+\*\*([^*。：:\n]{1,30})[。.]\*\*\s*\S")
RE_HEADING = re.compile(r"^\s{0,3}#{1,6}\s")
RE_TABLE_ROW = re.compile(r"^\s*\|")
RE_EMOJI = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F2FF\U0001F900-\U0001F9FF]"
)
# Structural status glyphs in tables and lists are excluded from emoji density.
STATUS_GLYPHS = set("✅⚠️❌✔️❎⛔️🔴🟠🟡".replace("️", "")) | {"✅", "⚠", "❌", "✔", "🔴", "🟠", "🟡"}

VAGUE_WORDS_ZH = ["相關", "之類", "等等", "適當", "盡量", "某種", "某些", "一些", "大概", "基本上", "原則上"]
RE_VAGUE_EN = re.compile(
    r"\betc\.|\band so on\b|\bappropriately\b|\bas much as possible\b|\bsome kind of\b|\broughly\b|\bbasically\b|\bin principle\b",
    re.IGNORECASE,
)

# Density thresholds in hits per 1,000 characters. Tier 3 symptoms count words
# that are normal in isolation and problematic only at high density. Thresholds
# are calibrated above the maximum observed across the clean suite corpus so
# normal specifications do not trigger false positives.
EMOJI_PER_KCHAR = 1.0
VAGUE_PER_KCHAR = 4.0

# Parentheses preceded by `]` are Markdown link targets `[label](url)` and are
# excluded via negative lookbehind `(?<!\])`.
RE_PAREN = re.compile(r"(?<!\])[（(]([^（()）]{2,100})[)）]")
PAREN_GLOSS_HINT_ZH = re.compile(r"因為|所以|其實|亦即|也就是|原本|之前|曾經|已棄用|為了|避免|例如|注意|不是|舊的|導致|以免|意思是")
PAREN_GLOSS_HINT_EN = re.compile(
    r"\b(?:because|since|therefore|i\.e\.|that is|namely|originally|previously|formerly|deprecated|in order to|to avoid|for example|e\.g\.|note that|meaning that|used to|which we)\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------- Preprocessing

RE_FENCE = re.compile(r"^\s*(?:```|~~~)")


def mask_quoted(text: str, mask_code: bool = True) -> str:
    """Mask quoted spans and inline code to implement the self-reference exemption.

    `mask_code=False` preserves inline code spans because leaked credentials,
    AI signatures, and local absolute paths frequently appear inside backticks.
    """
    if mask_code:
        text = re.sub(r"`[^`\n]*`", lambda m: " " * len(m.group(0)), text)
    for opener, closer in (("「", "」"), ("『", "』"), ('"', '"'), ("“", "”")):
        text = re.sub(
            re.escape(opener) + r"[^" + re.escape(closer) + r"\n]{0,400}" + re.escape(closer),
            lambda m: " " * len(m.group(0)),
            text,
        )
    return text


def read_lines(path: Path) -> list[tuple[int, str, str, str]]:
    """Return (lineno, raw, fully_masked, quote_only_masked), stripping fenced code blocks."""
    out: list[tuple[int, str, str, str]] = []
    in_fence = False
    for i, raw in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if RE_FENCE.match(raw):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        out.append((i, raw, mask_quoted(raw), mask_quoted(raw, mask_code=False)))
    return out


def guess_profile(path: Path) -> str:
    """Infer delivery profile from file path.

    Deliberately does not force `skills/` to `agent-facing`: file paths alone
    cannot tell whether a Skill targets business agents or developers. For
    engineering governance Skills, `Harness`, platform config directories, and local paths are
    the subject matter rather than noise. Pass `--profile agent-facing`
    explicitly when auditing business-agent Skills.
    """
    p = "/" + str(path).replace("\\", "/").lstrip("./")
    name = path.name
    if name in {"CHANGELOG.md", "decisions.md"} or "release-notes" in p:
        return "changelog"
    if "/tasks/" in p or name.startswith("TASK-"):
        return "ticket"
    return "harness"


# ---------------------------------------------------------------- Detection

class Hit:
    __slots__ = ("type", "line", "text", "note", "borderline")

    def __init__(self, type_: str, line: int, text: str, note: str = "", borderline: bool = False):
        self.type = type_
        self.line = line
        self.text = text.strip()[:160]
        self.note = note
        self.borderline = borderline


def scan_file(path: Path, terms: list[str]) -> list[Hit]:
    lines = read_lines(path)
    hits: list[Hit] = []
    body_chars = sum(len(raw) for _, raw, _, _ in lines) or 1

    for lineno, raw, masked, masked_keep_code in lines:
        for rx, type_, note, target in (
            (RE_SECRET_ASSIGN, "secret-leak", "Suspected hardcoded credential value", masked_keep_code),
            (RE_SECRET_DUMP, "secret-leak", "Dumping .env contents to output", masked),
            (RE_AI_SIGNATURE, "ai-signature", "", masked),
            (RE_UNVERIFIED, "unverified-status", "", masked),
            (RE_NOTE_TO_SELF, "note-to-self", "", masked),
        ):
            for m in rx.finditer(target):
                hits.append(Hit(type_, lineno, raw[m.start():m.end()], note))

        # A5 matches against masked_keep_code because paths inside backticks are
        # still leaks. Angle-bracket placeholders (`/Users/<user>/...`) do not
        # match RE_ABS_PATH's character class and are naturally exempt.
        for m in RE_ABS_PATH.finditer(masked_keep_code):
            quoted = not masked[m.start():m.end()].strip()
            note = "Inside quote or code span; verify whether format example or live path" if quoted else ""
            hits.append(Hit("abs-path", lineno, raw[m.start():m.end()], note))

        for m in RE_INTERNAL_HOST.finditer(masked_keep_code):
            hits.append(Hit("secret-leak", lineno, m.group(0), "Internal hostname; replace with placeholder", borderline=True))

        for m in RE_CHANGE_NARRATION.finditer(masked):
            hits.append(Hit("change-narration", lineno, raw[m.start():m.end()]))

        for m in RE_PAREN.finditer(masked):
            inner = m.group(1)
            if re.search(r"[一-鿿]", inner):
                borderline = not PAREN_GLOSS_HINT_ZH.search(inner)
                if borderline and len(inner) <= 8:
                    continue
                hits.append(Hit("paren-gloss", lineno, raw[m.start():m.end()], borderline=borderline))
            else:
                if PAREN_GLOSS_HINT_EN.search(inner):
                    hits.append(Hit("paren-gloss", lineno, raw[m.start():m.end()], borderline=False))
                elif len(inner.split()) >= 12:
                    hits.append(Hit("paren-gloss", lineno, raw[m.start():m.end()], borderline=True))

        if (
            RE_LIMIT_CLAIM.search(masked)
            and not re.search(r"\b(?:if|when|whenever|unless)\b[^\n]{0,35}\bcannot\b", masked, re.IGNORECASE)
            and not RE_EVIDENCE.search(raw)
        ):
            hits.append(Hit("unevidenced-limit", lineno, raw, "No evidence marker on same line; verify manually"))

        for t in terms:
            if t and t in masked:
                hits.append(Hit("retired-term", lineno, t, "Retired term"))

        if not RE_TABLE_ROW.match(raw):
            for m in RE_DEV_JARGON.finditer(masked):
                hits.append(Hit("dev-jargon-leak", lineno, raw[m.start():m.end()]))

        m = RE_LABEL_PERIOD.match(raw)
        if m:
            hits.append(Hit("label-period", lineno, m.group(0), "Replace period at end of bold label with colon"))

    # Density checks: evaluated once per file
    emoji_hits = [
        (lineno, ch)
        for lineno, raw, _, _ in lines
        if not RE_TABLE_ROW.match(raw)
        for ch in RE_EMOJI.findall(raw)
        if ch not in STATUS_GLYPHS
    ]
    if emoji_hits:
        per_kchar = len(emoji_hits) * 1000 / body_chars
        if per_kchar >= EMOJI_PER_KCHAR:
            hits.append(
                Hit("emoji-density", emoji_hits[0][0],
                    "".join(c for _, c in emoji_hits[:12]),
                    f"{per_kchar:.1f} per 1k chars ({len(emoji_hits)} total)")
            )

    vague_total = sum(
        sum(masked.count(w) for w in VAGUE_WORDS_ZH) + len(RE_VAGUE_EN.findall(masked))
        for _, _, masked, _ in lines
    )
    if vague_total:
        per_kchar = vague_total * 1000 / body_chars
        if per_kchar >= VAGUE_PER_KCHAR:
            first = next(
                (
                    lineno
                    for lineno, _, masked, _ in lines
                    if any(w in masked for w in VAGUE_WORDS_ZH) or RE_VAGUE_EN.search(masked)
                ),
                1,
            )
            hits.append(Hit("vague-filler", first, f"{vague_total} occurrences",
                            f"{per_kchar:.1f} per 1k chars (threshold {VAGUE_PER_KCHAR})"))

    return hits


def scan_duplicates(files: list[Path], min_len: int = 40) -> dict[Path, list[Hit]]:
    """Detect exact duplicate substantive lines across files as an SSOT violation signal.

    min_len is the minimum character length after stripping whitespace and leading
    list/heading markers. Lines shorter than 40 normalized characters are structural
    markers (`---`, fences, table dividers, `> [!NOTE]`, frontmatter keys) rather
    than duplicated normative rules.
    """
    index: dict[str, list[tuple[Path, int, str]]] = defaultdict(list)
    for path in files:
        for lineno, raw, _, _ in read_lines(path):
            norm = re.sub(r"\s+", "", raw)
            norm = re.sub(r"^[-*+>#\d.]+", "", norm)
            if len(norm) < min_len or RE_TABLE_ROW.match(raw):
                continue
            index[norm].append((path, lineno, raw))

    out: dict[Path, list[Hit]] = defaultdict(list)
    for occurrences in index.values():
        distinct = {p for p, _, _ in occurrences}
        if len(distinct) < 2:
            continue
        where = ", ".join(sorted(f"{p.name}:{ln}" for p, ln, _ in occurrences))
        for path, lineno, raw in occurrences:
            out[path].append(Hit("duplicated-rule", lineno, raw, f"Also appears at {where}"))
    return out


# ---------------------------------------------------------------- Output

def apply_strictness(hits: list[Hit], profile: str) -> list[Hit]:
    rules = PROFILES.get(profile, {})
    by_type: dict[str, list[Hit]] = defaultdict(list)
    for h in hits:
        by_type[h.type].append(h)

    kept: list[Hit] = []
    for type_, group in by_type.items():
        level = rules.get(type_, "strict")
        if level == "skip":
            continue
        if level == "relaxed":
            group = [h for h in group if not h.borderline]
            if len(group) < 2:
                continue
        elif level == "strict":
            group = [h for h in group if not h.borderline]
        kept.extend(group)
    return kept


def collect_files(paths: list[str]) -> list[Path]:
    out: list[Path] = []
    ignored = {".git", "node_modules", ".venv", "venv", "__pycache__"}
    for p in paths:
        path = Path(p)
        if path.is_dir():
            out.extend(sorted(q for q in path.rglob("*.md") if not any(x in q.parts for x in ignored)))
        elif path.is_file():
            out.append(path)
        else:
            raise FileNotFoundError(p)
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Deliverable writing symptom detector")
    ap.add_argument("paths", nargs="+", help="Files or directories (directories are scanned recursively for *.md)")
    ap.add_argument("--profile", choices=sorted(PROFILES), help="Delivery profile; inferred per file when omitted")
    ap.add_argument("--terms", help="File listing retired project terms, one per line (`#` for comments)")
    ap.add_argument("--json", action="store_true", help="Emit structured JSON output")
    args = ap.parse_args(argv)

    try:
        files = collect_files(args.paths)
    except FileNotFoundError as exc:
        print(f"Path not found: {exc}", file=sys.stderr)
        return 2
    if not files:
        print("No auditable files found", file=sys.stderr)
        return 2

    terms: list[str] = []
    if args.terms:
        try:
            terms = [
                ln.strip()
                for ln in Path(args.terms).read_text(encoding="utf-8").splitlines()
                if ln.strip() and not ln.startswith("#")
            ]
        except OSError as exc:
            print(f"Failed to read terms file: {exc}", file=sys.stderr)
            return 2

    dup = scan_duplicates(files) if len(files) > 1 else {}

    report: list[dict] = []
    for path in files:
        profile = args.profile or guess_profile(path)
        hits = scan_file(path, terms) + dup.get(path, [])
        hits = apply_strictness(hits, profile)
        hits.sort(key=lambda h: (SEVERITY_ORDER[META[h.type][1]], h.line))
        report.append({
            "file": str(path),
            "profile": profile,
            "hits": [
                {
                    "type": h.type,
                    "catalog": META[h.type][0],
                    "severity": META[h.type][1],
                    "label": META[h.type][2],
                    "line": h.line,
                    "text": h.text,
                    "note": h.note,
                    "borderline": h.borderline,
                }
                for h in hits
            ],
        })

    total = sum(len(r["hits"]) for r in report)

    if args.json:
        print(json.dumps({"total": total, "files": report}, ensure_ascii=False, indent=2))
        return 1 if total else 0

    for entry in report:
        if not entry["hits"]:
            continue
        print(f"\n{entry['file']}  [profile: {entry['profile']}]")
        for h in entry["hits"]:
            note = f"  — {h['note']}" if h["note"] else ""
            mark = " [borderline]" if h["borderline"] else ""
            print(f"  {h['severity']}{mark} {h['catalog']} {h['label']}  :{h['line']}  {h['text']}{note}")

    borderline_total = sum(1 for r in report for h in r["hits"] if h["borderline"])

    print(f"\nTotal {total} hit(s) across {len(files)} file(s).")
    if total:
        print("A hit is not necessarily an error: check the 'Exceptions' field in references/pattern-catalog.md before adjudicating.")
    if borderline_total:
        print(f"{borderline_total} hit(s) tagged [borderline]: surface pattern matches with common legitimate uses; "
              "surfaced only under Extra-strict profiles and require human/agent judgement.")
    return 1 if total else 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        sys.exit(2)
