# Core Rule 11: Skill Frontmatter & Multi-Agent Governance

## Why This Rule Exists (Why)
Omitting YAML frontmatter prevents spec-compliant agents from discovering and dynamically loading a Skill.
Meanwhile, when a developer agent writes implementation code and then writes its own mocked verification, it easily falls into confirmation bias.
Because a Skill is itself a deliverable, it is vulnerable to three additional structural failures beyond frontmatter: copying detailed rules into `SKILL.md` creates two copies that inevitably drift apart; extracting a rule from a live session while leaving that project's internal tool names in the prose produces instructions that fail in every other repository; and drafting rules before establishing baseline failure evaluations produces speculative prose that cannot be falsified.

---

## How to Execute (How)

### 1. Skill YAML Frontmatter Standard
Only two fields are required; omitting either prevents the Skill from being discovered or loaded:

```yaml
---
name: skill-name
description: Plain statement of what the Skill does and when to load it
---
```

All other spec fields (`license`, `compatibility`, `metadata`, `allowed-tools`) are optional—do not add them without a concrete operational need, as every extra field is another surface that can go stale.
- **Preserve Frontmatter During Refactoring**: Never strip YAML frontmatter when editing or refactoring `SKILL.md`.

**Frontmatter applies exclusively to `SKILL.md`.** Files under `references/` and `assets/` **must never** contain YAML frontmatter: they are not standalone discoverable Skills, so frontmatter in those files has zero effect on any agent while wasting context tokens and misleading maintainers. The criterion is **"will an agent platform discover this file as a standalone Skill?"**—if no, it must not have frontmatter.

#### Criteria for Authoring `description`

The sole purpose of `description` is to support one decision: **should the agent load this Skill for the current prompt?** Because `description` stays resident in the system prompt across every turn and gets truncated when many Skills are installed, every word that fails to sharpen that loading decision dilutes trigger accuracy.

Apply a strict operational test to every clause in `description`: **if deleting that clause would not change the decision of whether to load the Skill, delete it.**

Four components are mandatory:

| Required Component | Normative Form | Defect Form to Avoid |
| --- | --- | --- |
| Core capability | Concrete actions performed and artifacts produced | Vague category labels such as "A skill suite for..." |
| Applicable scenarios | Specific task contexts where the Skill applies | Broad domain nouns that match almost every conversation |
| User trigger phrases | Realistic user intents and keywords | Omitting triggers—this is the primary driver of recall |
| Exclusion boundary | Explicit adjacent scenarios where the Skill must not load | Omitting exclusions—purely positive triggers over-fire |

Place the exclusion boundary in the middle of `description` and reserve the final sentence for an explicit positive load directive, stating clearly when the Skill must be loaded even if the user never mentions the Skill by name. Putting a negative exclusion at the very end causes models to anchor on "do not use."

Four patterns must never appear in `description`:

- **Metaphors and personification**: They describe a mental image rather than a trigger condition.
- **Internal platform mechanics**: Phrases like "automatically triggered" describe the host runtime, not when to select the Skill.
- **Unmeasurable superlatives**: Words like "comprehensive," "powerful," or "robust" carry zero selection signal.
- **Tautologies**: Statements true of any Skill, such as "guides agent behavior."

These criteria are codified as rules rather than left to intuition because the defect recurs repeatedly: even after one round of cleanup, newly created Skills still open with metaphors. Checking a new `description` against this table item by item is a mandatory step whenever authoring a Skill.

Every structural requirement in this section is deterministically verifiable, **so it is enforced by script rather than by human vigilance**. Run `scripts/check_skill_spec.py` after editing any Skill; see the `Structure Check` section of `SKILL.md` for usage. This marks the exact boundary of when a rule should be a prose hard constraint: if a check can be mechanized in a script, put it in a script and reserve prose rules for what scripts cannot judge.

### 2. Entry File Points, Not Restates

`SKILL.md` is a routing entrypoint, not a container for full rule bodies. Apply three criteria:

- **The conceptual layer provides the mental model, not the rule text**: Show the agent which action it is in and what failure mode is at stake, while leaving the normative rule text inside its dedicated file under `references/`. Paraphrasing a rule in `SKILL.md` alongside a link creates a duplicate source of truth that will drift.
- **Index tables state only the name, path, and a one-line scope**: Help the reader decide **when to open the file**, not summarize everything inside it.
- **Section openings state the purpose of the section, never describe its layout**: The reader can already see the headings and tables; narrating "this section contains two tables" adds zero information.

Do not force a single rigid heading template across all Skills. A governance Skill follows the chronological sequence of work actions, whereas an auditing Skill follows the narrowing sequence of diagnostic checks.

Corresponding prose symptoms are defined in the catalog of `deliverable-writing-audit`; this section defines only the structural criteria for the entrypoint file.

### 3. No Project-Specific Facts in Shared Rules

A published Skill will be installed into repositories its author has never seen. Leaving a source project's internal tool names, endpoint paths, status strings, or domain nouns inside a shared rule hands the installer an instruction that cannot execute in their environment.

**Criterion**: Every proper noun in a shared rule must answer **"does this exact name exist in every project that installs this Skill?"** If the answer is no, replace it:

| Project-Specific Artifact (Prohibited) | General Normative Abstraction (Required Replacement) |
| --- | --- |
| Internal tool name, API name, or endpoint path | The **functional role** that tool plays, plus the criterion for what qualifies as an authoritative source |
| Hardcoded status code or field name | The **semantic category** of that state, such as "a reversible cancellation state" |
| Domain-specific business noun | General engineering term, such as "external system record" instead of an internal voucher type |
| Specific agent platform or CLI name | "A spec-compliant agent" or "the platform's delegation mechanism" |
| Internal project name, repo slug, ADR ID, or work item ID | Delete, or state the underlying problem pattern without internal identifiers |

**Exception for public standards**: Public specifications and universal tools do not vary by project and may be named directly—such as `OpenAPI`, `JSON Schema`, `JSON-RPC`, `git`, `Nygard ADR`, and `YAML Frontmatter`. The criterion is **"is this name a public standard or one project's internal naming?"**

**Exception for templates**: Files under `assets/` exist to illustrate concrete formatting; placeholder IDs and sample fields inside `assets/` are format demonstrations, not shared rules.

**Why this must be an explicit rule rather than left to intuition**: The source of such leakage is always the same—a rule is distilled from a real working session where the source project's tool names were right in the active context and got written into the rule in passing. In the moment, those concrete names read naturally and persuasively; only when installed into another project does the instruction fail. Checking every proper noun against this table is mandatory whenever abstracting a rule.

### 4. Evaluate First

The criterion is **"does this Skill solve a failure observed in real runs, or a hypothetical problem imagined by the author?"**

Follow a fixed sequence: run representative tasks **without** the Skill loaded and record the exact points where the agent fails or lacks context; turn those failures into at least three evaluation scenarios and measure the unassisted baseline; write the minimal Skill content needed to address those failures; then re-run the evaluations against the baseline and iterate.

Reversing this order—writing a comprehensive rulebook first and looking for test cases afterward—produces untestable bloat with no baseline to prove whether the Skill helped or hurt.

Never let the session that authored the Skill self-certify its evaluation; run behavioral validation in a clean session with zero authoring context, matching the separation principle in [Core Rule 04](04-delegation-contract.md).

### 5. Two-Tier Subagent Governance (Developer vs. Validator)
- **Developer Agent (Primary Executor)**: Writes code, updates specifications, and prepares work items.
- **Validator Subagent (Independent Verifier)**: When verifying MCP tools or end-to-end natural-language workflows, delegate verification to an independent subagent with a clean context window to exercise the real user interface without author bias.
