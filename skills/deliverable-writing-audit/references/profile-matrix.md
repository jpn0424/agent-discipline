# Profile Tolerance Matrix

Read this table after determining the `profile` and before adjudicating any hits. Skipping this table treats every document at full `harness` strictness, causing heavy false positives on `ticket` and `changelog` files—recording change history in those two profiles is the proper form, not a writing symptom.

Profile resolution rules are defined in the `"Automatic Profile Precedence"` section of [SKILL.md](../SKILL.md). Symptom definitions reside in [pattern-catalog.md](pattern-catalog.md).

## Matrix

Symptoms not listed below apply at `Strict` tolerance across all profiles.

| Symptom | harness | agent-facing | deliverable | ticket | changelog | pr-commit |
| --- | --- | --- | --- | --- | --- | --- |
| Secret and credential leakage | Strict | Strict | **Extra-strict** | Strict | Strict | **Extra-strict** |
| Local absolute path | Strict (exempt when pointing to external SoT; use placeholders for format examples) | Strict | **Extra-strict** | Relaxed | Relaxed | Strict |
| Operational metadata (work item IDs, decision IDs, sync status) | Relaxed (developer-facing) | **Extra-strict** (must not leak) | **Extra-strict** | Skip (is the work item itself) | Skip | Relaxed (may cite work item IDs) |
| Change narration / before-after comparison | Strict | Strict | Strict | Relaxed (recording history is its job) | Skip (inherently a change log) | Relaxed (explains what changed) |
| Parenthetical gloss | Strict | Strict | Strict | Strict | Relaxed | Strict |
| Residual note-to-self | Strict | Strict | **Extra-strict** | Relaxed (todos are field content) | Strict | Strict |
| Residual unverified status | **Extra-strict** | **Extra-strict** | **Extra-strict** | **Extra-strict** | Relaxed | Skip |
| Unevidenced capability limitation claim | Strict | **Extra-strict** | **Extra-strict** | Strict | Relaxed | Skip |
| Revived retired terminology | Strict | **Extra-strict** | **Extra-strict** | Relaxed (may explain why retired) | Skip | Relaxed |
| Developer jargon (platform config directories such as `.claude/` or `.agents/`, `Harness`, local path aliases) | Skip | Strict | **Extra-strict** | Skip | Relaxed | Strict |
| Emoji density | Relaxed | Relaxed | Strict | Skip | Skip | Strict |
| Excessive domain implementation detail | Skip | Skip | Skip | Skip | Relaxed | **Extra-strict** (PRs must stay accessible) |
| Scattered duplicate rules | **Extra-strict** | **Extra-strict** | Strict | Skip | Skip | Skip |
| Tautological and non-operational definitions | **Extra-strict** | **Extra-strict** | **Extra-strict** | Relaxed | Relaxed | Skip |
| Deontic modality confusion | **Extra-strict** | **Extra-strict** | **Extra-strict** | Relaxed | Skip | Relaxed |

## Semantics of the Four Tolerance Levels

- **Extra-strict**: Flags even `[borderline]` cases.
- **Strict**: Evaluates according to the symptom's baseline tier and exception clauses; this is the default tolerance level.
- **Relaxed**: Flags only pronounced clusters (two or more non-borderline hits in a file); a single isolated occurrence is exempted.
- **Skip**: Does not audit this symptom under this profile because the form is legitimate here. Hits are omitted from the report.

Exempted hits under `Strict` or `Relaxed` must still be noted in your report with the reason for exemption so the user knows you inspected them rather than missed them.
