# Symptom ↔ Detection Script Mapping

This table is the drift-prevention contract between [pattern-catalog.md](pattern-catalog.md) and `../scripts/detect.py`. When adding a symptom to the catalog, assign it to one of the sections below; when adding a script `type`, map it back to its catalog ID here.

The catalog contains 28 symptoms; the script defines 14 `type` values. The difference **is not a coverage gap**—those remaining symptoms require semantic comprehension to evaluate.

## A. Direct Mapping (Symptom → Script `type`)

| Script `type` | Catalog ID | Symptom | Detection Mechanism |
| --- | --- | --- | --- |
| `secret-leak` | A1 | Secret and credential leakage | Credential assignment patterns, `.env` dump commands, non-allowlisted external hostnames |
| `ai-signature` | A2 | AI attribution signature | Fixed string and phrase matching |
| `unverified-status` | A4 | Residual unverified status | Status token matching |
| `abs-path` | A5 | Local absolute path | Path prefix matching including inside code spans; angle-bracket placeholders do not match the character class and are naturally exempt |
| `change-narration` | B1 | Change narration and before/after comparison | Chronological and before/after phrase matching |
| `paren-gloss` | B2 | Parenthetical gloss | Parentheses containing explanatory or causal gloss markers |
| `note-to-self` | B3 | Residual note-to-self | Draft marker matching |
| `retired-term` | C3 | Revived retired terminology | Exact matching against `--terms` list |
| `duplicated-rule` | C4 | Scattered duplicate rules | Exact duplicate substantive lines across files |
| `dev-jargon-leak` | C7 | Developer jargon leaked into deliverables | Jargon token and internal ID pattern matching |
| `vague-filler` | D1 | Vague quantifiers and filler words | Density per 1,000 characters, threshold `4.0` |
| `emoji-density` | D2 | Emoji density | Density per 1,000 characters, threshold `1.0`, excluding table status glyphs |
| `label-period` | D3 | Period inside bold list label | List bullet + **bold** short label + period. Unbolded forms belong to semantic judgement; see Group D below |

## B. Partial Mapping (Script Flags Location; Judgement Remains with Agent)

| Script `type` | Catalog ID | Reason for Limitation |
| --- | --- | --- |
| `unevidenced-limit` | C1 | The script locates limitation phrases (`"cannot"`, `"unsupported"`, `"only via"`) and checks whether the same line contains an evidence marker. Whether the evidence is **sufficient**, whether all relevant operations were tested, and whether an already-succeeded operation was misdescribed as a limitation require reading the surrounding context. All script hits require human/agent verification. |

## C. Judgement Only (No Script `type`)

These symptoms require semantic comprehension and are executed by the Agent against the catalog. They are listed here so future maintainers do not mistake their absence from `detect.py` for an implementation gap.

| Catalog ID | Symptom | Why Semantic Judgement Is Required |
| --- | --- | --- |
| A3 | Unverified success claim | Verifying whether `"Fixed"` or `"Completed"` has backing evidence requires locating the corresponding verbatim error, read-back result, or screenshot across the entire document, which may legitimately reside in another section. |
| B4 | Heading echo | Requires judging whether the opening line merely paraphrases the heading. Surface word-overlap thresholds miss low-overlap paraphrases while falsely flagging legitimate high-overlap section summaries. |
| B5 | Self-Describing metadiscourse | Distinguishing self-describing metadiscourse from a scope boundary declaration requires judging whether removing the sentence causes the reader to misjudge the document's scope. Both share identical syntax; the difference is whether the sentence points to content in another file. |
| B6 | Heading-scope mismatch | Requires counting how many distinct topics a section contains, and topic boundaries are semantic rather than syntactic. Paragraph count, length, and heading wording cannot determine this. |
| C2 | Unstructured prose for enumerable facts | Requires judging whether a passage is **enumerating items**. Long paragraphs are not inherently defective; paragraphs explaining rationale belong in prose. |
| C5 | Summarized away verbatim error | Judging that verbatim error output is missing where it belongs requires recognizing that the passage is reporting a failure in the first place. |
| C6 | Speculative filling | A fabricated field name that looks plausible is lexically indistinguishable from a verified field name; the difference lies in whether the schema was queried. |
| C8 | Project-specific facts leaked into shared rules | Distinguishing a public standard from a project-internal identifier requires knowing whether that name exists in external specifications. Lexically they look identical. |
| C9 | Navigation carrying target content | Requires judging whether a table cell states **routing scope** or **content summary**. Both have similar length and sentence structure; the difference is whether the cell duplicates the target file's substance. |
| C10 | Cross-file inconsistency | A script can detect two identical lines, not two mutually contradictory claims. Detecting contradiction requires understanding what each sentence asserts and whether both can hold simultaneously. |
| C11 | Multiple terms for one concept | Requires knowing that two lexically unrelated words refer to the same entity within the domain. |
| C12 | Tautological and non-operational definitions | Judging whether a definition is circular or lacks repeatable verification steps requires analyzing its genus-differentia structure and operational testability. |
| C13 | Deontic modality confusion | Judging whether a rule is an irreversible `[Hard Constraint]` or a context-dependent `Criterion` requires evaluating system risk and consequence reversibility. |
| D4 | Excessive domain implementation detail | `"Excessive"` is relative to the target reader. The exact same technical passage is appropriate in an architecture spec and excessive in a PR description. |

## D. Attempted Mechanization Later Withdrawn

Recorded here to prevent repeating rejected experiments:

- **A3 Unverified success claim** was considered for regex detection via `"Fixed / Completed without an evidence marker in the same paragraph"`. Withdrawn because evidence legitimately resides in dedicated sections (`## Verification Results` in a work item, or a separate test output block); any rule strict enough to catch true positives produced mass false positives on normal multi-section documents.
- **B4 Heading echo** was considered via character/token overlap between a heading and its first sentence. Withdrawn because paraphrases can have near-zero lexical overlap while legitimate topic introductions often repeat key nouns from the heading, making both false negatives and false positives inseparable by threshold.
- **D3 Unbolded list-label periods** were initially included alongside bold labels. Withdrawn because unbolded opening spans in list items are frequently complete imperative sentences (`"- Run the test suite. If it fails..."`), and distinguishing a noun phrase label from an imperative clause in English or Chinese without a part-of-speech parser is unreliable in regex. The script therefore restricts detection to the high-precision **bold** form (`- **Label.**`), leaving unbolded forms to semantic judgement.

## Two Counts Are Independent

Do not attempt to force these two numbers to match during maintenance:

- **28 symptoms** in the catalog: the complete checklist for human and agent semantic auditing, including judgement-only items.
- **14 `type` values** in the script: the mechanically detectable subset.
