#!/usr/bin/env python3
"""交付文件書寫徵狀偵測器。

只依賴 Python 3 標準庫。偵測 references/pattern-catalog.md 中標為「可機械偵測」
的徵狀；需要讀懂語意的徵狀不在此腳本範圍，見 references/category-map.md。

用法：
    python3 detect.py <path...> [--profile NAME] [--json] [--terms FILE]

結束碼：0 乾淨、1 有命中、2 執行錯誤。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------- 徵狀定義

# (type, 目錄編號, 嚴重度, 標籤)
META = {
    "secret-leak": ("A1", "P0", "機敏值外洩"),
    "ai-signature": ("A2", "P0", "AI 署名"),
    "unverified-status": ("A4", "P0", "「未實測」殘留"),
    "abs-path": ("A5", "P0", "本機絕對路徑"),
    "change-narration": ("B1", "P1", "流水帳與比較新舊"),
    "paren-gloss": ("B2", "P1", "括號補述"),
    "note-to-self": ("B3", "P1", "個人註記殘留"),
    "unevidenced-limit": ("C1", "P1", "限制宣稱（需人工核對證據）"),
    "retired-term": ("C3", "P1", "已退役術語復活"),
    "duplicated-rule": ("C4", "P1", "規則重複散落"),
    "dev-jargon-leak": ("C7", "P1", "開發者術語滲入交付物"),
    "vague-filler": ("D1", "P2", "模糊量詞與填充詞密度"),
    "emoji-density": ("D2", "P2", "emoji 密度"),
    "label-period": ("D3", "P2", "條列標籤用句號"),
}

SEVERITY_ORDER = {"P0": 0, "P1": 1, "P2": 2}

# 情境寬容矩陣。未列出者一律 strict。
PROFILES = {
    "harness": {
        "abs-path": "relaxed",
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
# {0,40} 是指令動詞與 `.env` 之間允許的距離，足以容納旗標與相對路徑
# （`grep -i SECRET ../config/.env`），又短到不會把同一行裡不相干的指令與 `.env` 誤配成一組。
RE_SECRET_DUMP = re.compile(r"\b(?:cat|grep|echo|print|head|tail|less|more)\b[^\n]{0,40}\.env\b")
# 白名單比對主機名的結尾，不比對子字串。否則白名單項目會連帶放行把它當前綴的
# 主機，例如放行 shields.io 會一併放行 shields.io.attacker.net。
RE_INTERNAL_HOST = re.compile(
    r"https?://(?![^\s/]*"
    r"(?:localhost|127\.0\.0\.1|example\.[a-z]{2,}|github\.com|skills\.sh|shields\.io)"
    r"(?![a-z0-9.-]))"
    r"[^\s/]*\.[a-z]{2,}(?:\.[a-z]{2,})+"
)
RE_AI_SIGNATURE = re.compile(
    r"(?:provide[d]?\s+by\s+claude|generated\s+with\s+\[?claude|co-authored-by:\s*claude|🤖)",
    re.IGNORECASE,
)
RE_UNVERIFIED = re.compile(r"未實測|未測試|待確認|待驗證|尚未驗證|推定支援|狀態未知|\bTBD\b|\bTODO\b(?=.*(?:測|驗))")
RE_ABS_PATH = re.compile(r"(?:/Users/[A-Za-z0-9._-]+|/home/[A-Za-z0-9._-]+|[A-Za-z]:\\\\?Users\\\\?[A-Za-z0-9._-]+)")
# 「已退役術語」這類定語用法是分類標籤而非變更敘述，以 lookahead 排除。
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
)
RE_NOTE_TO_SELF = re.compile(r"\bTODO\b|\bFIXME\b|\bXXX\b|待補|先這樣|我猜|暫時先|等等再說|\?\?\?")
RE_LIMIT_CLAIM = re.compile(r"做不到|只能由|無法(?:取得|讀取|建立|完成|支援)|不支援|辦不到")
RE_EVIDENCE = re.compile(r"錯誤原文|原文如下|實測|已驗證|截圖|TASK-\d|AD-\d|HD-\d|證據|errors?[:：]")
RE_DEV_JARGON = re.compile(r"\.claude/|\.agents/|Harness|本機|本地開發|subagent|validator|AD-\d{3,}|HD-\d{3,}|TASK-\d{6,}")
# 只抓粗體標籤形式。未加粗的開頭片段常是完整句子（「重新執行測試。若…」），
# 而中文動詞偵測不可靠，無法用正則分出標籤與句子，因此收斂到誤判最低的強形式。
RE_LABEL_PERIOD = re.compile(r"^\s*[-*+]\s+\*\*([^*。：:\n]{1,20})。\*\*\s*\S")
RE_HEADING = re.compile(r"^\s{0,3}#{1,6}\s")
RE_TABLE_ROW = re.compile(r"^\s*\|")
RE_EMOJI = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F2FF\U0001F900-\U0001F9FF]"
)
# 表格狀態標記與清單標記屬結構化資訊，不計入 emoji 密度。
STATUS_GLYPHS = set("✅⚠️❌✔️❎⛔️🔴🟠🟡".replace("️", "")) | {"✅", "⚠", "❌", "✔", "🔴", "🟠", "🟡"}

VAGUE_WORDS = ["相關", "之類", "等等", "適當", "盡量", "某種", "某些", "一些", "大概", "基本上", "原則上"]

# 密度門檻，單位為每千字元命中數。這兩條是 Tier 3 徵狀：被計數的字詞本身都是正常用字，
# 只有密度明顯偏高才代表文件在用模糊詞或裝飾替代具體敘述。門檻因此刻意設在遠高於
# 乾淨語料的位置，寧可漏標也不要讓正常文件被標。
#
# 校準基準是本 repo 現行的 24 個 Markdown 檔，以本腳本自身的計數方式實測：
#   模糊詞：中位數 0.00／最高 2.65（`task-template.md`）
#   emoji（已扣除 STATUS_GLYPHS）：中位數 0.00／最高 0.10
# 兩個門檻都取在最高值之上，因此現行語料全數不觸發。改動門檻前先在目標語料重測，
# 不要憑感覺調整——這兩個數字的意義是「相對於乾淨語料的倍數」，不是絕對品質線。
EMOJI_PER_KCHAR = 1.0   # 現行語料最高值的約 10 倍
VAGUE_PER_KCHAR = 4.0   # 現行語料最高值的約 1.5 倍

# 括號內出現這些字代表是補敘述而非術語對照。
# {2,80}：下限 2 排除空括號與單字元符號；上限 80 之外的括號內容已是完整段落，
# 屬「該寫成正文」而不是「括號補述」，改由 C2 該結構化卻寫成流水句判讀。
RE_PAREN = re.compile(r"[（(]([^（()）]{2,80})[)）]")
PAREN_GLOSS_HINT = re.compile(r"因為|所以|其實|亦即|也就是|原本|之前|曾經|已棄用|為了|避免|例如|注意|不是|舊的|導致|以免|意思是")


# ---------------------------------------------------------------- 前處理

RE_FENCE = re.compile(r"^\s*(?:```|~~~)")


def mask_quoted(text: str, mask_code: bool = True) -> str:
    """遮蔽引用內容，實作自我引用豁免。

    `mask_code=False` 保留 inline code 內容：機敏值與 AI 署名常寫在反引號內，
    那不是引用示例而是真的洩漏。
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
    """回傳 (行號, 原始行, 全遮蔽行, 僅遮蔽引用行)，並剔除 fenced code block。"""
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
    """依路徑推斷交付情境。

    刻意不把 `skills/` 一律判成 `agent-facing`：路徑看不出這個 Skill 的讀者是
    業務 agent 還是開發者。談開發工作流的 Skill，`Harness`、`.claude/`、`本機`
    正是它的主題而非雜訊。需要 `agent-facing` 的加嚴時以 `--profile` 明指。
    """
    p = "/" + str(path).replace("\\", "/").lstrip("./")
    name = path.name
    if name in {"CHANGELOG.md", "decisions.md"} or "release-notes" in p:
        return "changelog"
    if "/tasks/" in p or name.startswith("TASK-"):
        return "ticket"
    return "harness"


# ---------------------------------------------------------------- 偵測

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
            (RE_SECRET_ASSIGN, "secret-leak", "疑似寫死的憑證值", masked_keep_code),
            (RE_SECRET_DUMP, "secret-leak", "把 .env 內容導出到輸出", masked),
            (RE_AI_SIGNATURE, "ai-signature", "", masked),
            (RE_UNVERIFIED, "unverified-status", "", masked),
            (RE_NOTE_TO_SELF, "note-to-self", "", masked),
        ):
            for m in rx.finditer(target):
                hits.append(Hit(type_, lineno, raw[m.start():m.end()], note))

        # A5 在 masked_keep_code 上比對：路徑包成 code span 一樣是洩漏，
        # 遮蔽後整段漏判。已佔位符化的示例（`/Users/<使用者>/...`）不符合 RE_ABS_PATH
        # 的字元集，天然豁免，因此不需要為格式示例另開放行條件。
        # 命中不標 borderline：borderline 只在 extra 情境浮出，而本徵狀要在
        # 預設情境就攔下，人工判讀由 note 承擔。
        for m in RE_ABS_PATH.finditer(masked_keep_code):
            quoted = not masked[m.start():m.end()].strip()
            note = "位於引用或 code span 內，判讀是格式示例還是真實路徑" if quoted else ""
            hits.append(Hit("abs-path", lineno, raw[m.start():m.end()], note))

        for m in RE_INTERNAL_HOST.finditer(masked_keep_code):
            hits.append(Hit("secret-leak", lineno, m.group(0), "內部主機名，改用佔位符", borderline=True))

        for m in RE_CHANGE_NARRATION.finditer(masked):
            hits.append(Hit("change-narration", lineno, raw[m.start():m.end()]))

        for m in RE_PAREN.finditer(masked):
            inner = m.group(1)
            if not re.search(r"[一-鿿]", inner):
                continue  # 純英文／符號視為術語對照
            borderline = not PAREN_GLOSS_HINT.search(inner)
            if borderline and len(inner) <= 8:
                continue
            hits.append(Hit("paren-gloss", lineno, raw[m.start():m.end()], borderline=borderline))

        if RE_LIMIT_CLAIM.search(masked) and not RE_EVIDENCE.search(raw):
            hits.append(Hit("unevidenced-limit", lineno, raw, "同一行找不到證據標記，需人工核對"))

        for t in terms:
            if t and t in masked:
                hits.append(Hit("retired-term", lineno, t, "已退役術語"))

        if not RE_TABLE_ROW.match(raw):
            for m in RE_DEV_JARGON.finditer(masked):
                hits.append(Hit("dev-jargon-leak", lineno, raw[m.start():m.end()]))

        m = RE_LABEL_PERIOD.match(raw)
        if m:
            hits.append(Hit("label-period", lineno, m.group(0), "標籤結尾的句號應改冒號"))

    # 密度類：整檔一次判定
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
                    f"每千字 {per_kchar:.1f} 個，共 {len(emoji_hits)} 個")
            )

    vague_total = sum(masked.count(w) for _, _, masked, _ in lines for w in VAGUE_WORDS)
    if vague_total:
        per_kchar = vague_total * 1000 / body_chars
        if per_kchar >= VAGUE_PER_KCHAR:
            first = next(
                (lineno for lineno, _, masked, _ in lines if any(w in masked for w in VAGUE_WORDS)), 1
            )
            hits.append(Hit("vague-filler", first, f"共 {vague_total} 處",
                            f"每千字 {per_kchar:.1f} 處，超過 {VAGUE_PER_KCHAR} 門檻"))

    return hits


def scan_duplicates(files: list[Path], min_len: int = 40) -> dict[Path, list[Hit]]:
    """跨檔比對完全重複的實質內容行。

    min_len 是參與比對的最短行長，單位為字元。低於此長度的重複幾乎都是結構標記而非規則
    重複：本 repo 現行語料的 14 處跨檔重複行全部短於 40 字元，且全為 `---`、程式碼圍籬、
    表格分隔列、`> [!NOTE]`、frontmatter 的 `allowed-tools` 項目這類必然相同的版式。
    設在 40 讓這些結構標記全數落在門檻之下，同時語意完整的中文規則句普遍超過 40 字元。
    """
    """找出跨檔完全重複的實質內容行，作為 SSOT 違反的線索。"""
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
            out[path].append(Hit("duplicated-rule", lineno, raw, f"同內容也出現於 {where}"))
    return out


# ---------------------------------------------------------------- 輸出

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
    for p in paths:
        path = Path(p)
        if path.is_dir():
            out.extend(sorted(q for q in path.rglob("*.md") if ".git" not in q.parts))
        elif path.is_file():
            out.append(path)
        else:
            raise FileNotFoundError(p)
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="交付文件書寫徵狀偵測器")
    ap.add_argument("paths", nargs="+", help="檔案或目錄（目錄則遞迴掃 *.md）")
    ap.add_argument("--profile", choices=sorted(PROFILES), help="交付情境，省略則逐檔自動判定")
    ap.add_argument("--terms", help="專案已退役術語清單，一行一個，`#` 開頭為註解")
    ap.add_argument("--json", action="store_true", help="輸出結構化結果")
    args = ap.parse_args(argv)

    try:
        files = collect_files(args.paths)
    except FileNotFoundError as exc:
        print(f"找不到路徑：{exc}", file=sys.stderr)
        return 2
    if not files:
        print("沒有可稽核的檔案", file=sys.stderr)
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
            print(f"讀取術語清單失敗：{exc}", file=sys.stderr)
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
            mark = " [邊界]" if h["borderline"] else ""
            print(f"  {h['severity']}{mark} {h['catalog']} {h['label']}  :{h['line']}  {h['text']}{note}")

    borderline_total = sum(1 for r in report for h in r["hits"] if h["borderline"])

    print(f"\n共 {total} 處命中，掃描 {len(files)} 個檔案。")
    if total:
        print("命中不等於錯誤：請逐條對照 references/pattern-catalog.md 的「例外」小節後判讀。")
    if borderline_total:
        print(f"其中 {borderline_total} 處標為 [邊界]：形式命中但正當用途常見，"
              "只在加嚴情境浮出，嚴重度不代表確定是缺陷，一律人工判讀。")
    return 1 if total else 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        sys.exit(2)
