# Contributing to agent-discipline

Thank you for helping maintain and improve `agent-discipline`.

This repository ships the engineering discipline and deliverable writing audit suite for AI coding agents. Every rule in `agent-engineering-discipline` constrains agent action boundaries, prevents irreversible operations, and protects deliverable integrity; every symptom in `deliverable-writing-audit` identifies a writing pattern that degrades a specification into a working draft. Please read the guidelines below before opening an Issue or Pull Request.

---

## Core Design Philosophy

When proposing a new rule, symptom, or revision, adhere to four foundational principles:

1. **Anchored in Real Failure Evidence (No Speculation)**:
   - Every rule and writing symptom must originate from recurring failures or user corrections observed in real engineering sessions—such as accidental file deletion, unverified completion claims, unauthorized edits, or speculative schema fields.
   - Generic `"best practices"` or hypothetical guardrails without empirical failure evidence are not accepted.

2. **Binary Normative Modality (Deontic Modality)**:
   - **`[Hard Constraint]` (`MUST` / `MUST NOT`)**: Reserved strictly for irreversible actions (deletion, git commits/pushes), security, external system mutations, and epistemic honesty baselines. Executed literally with zero discretion.
   - **`Criterion` (`SHOULD` / `MAY`)**: Rules that depend on context must state `"The criterion is '...'"` and include a concrete contrast table of valid contexts vs. failure modes.

3. **Progressive Disclosure Architecture**:
   - Top-level `SKILL.md` entrypoints retain only routing tables and core invariant summaries.
   - Detailed rules and catalogs belong in modular files under `references/` so they load on demand without flooding the Agent's Context Window.

4. **Single Source of Truth (SSOT)**:
   - Never define the same rule in multiple files. Keep the normative text in one canonical file and reference it via relative Markdown links elsewhere.

---

## Proposal and Contribution Workflow

### 1. How Issues and Pull Requests Are Handled

This repository is mirrored and published from an upstream development monorepo, where each release corresponds to a version tag. Because the upstream monorepo is the Canonical Source (SSOT):

- **Issues**: Open Issues directly for bug reports, false-positive reports, or rule proposals.
- **Pull Requests**: Treated as proposals rather than merged directly here. When accepted, maintainers apply the change in the upstream monorepo, ship it in the next tagged release, and reply on the PR with the release version.

Changes merged directly into this mirror repository would be overwritten on the next upstream sync, so direct merges are not used.

### 2. Proposing or Revising an Engineering Rule

When proposing a new core rule or revising an existing rule in `agent-engineering-discipline`, include in your Issue or PR:
- **Failure scenario**: Under what circumstances does the Agent make this mistake?
- **Why it goes unnoticed at the time**: Why does the defective behavior look plausible in the moment?
- **Criterion and remediation**: What executable step or check prevents the failure?
- **Hard constraint or criterion**: Which modal strength governs the rule, and why?

### 3. Proposing or Revising a Writing Symptom

When proposing or revising a symptom in `deliverable-writing-audit`, provide all six fields defined in `pattern-catalog.md`: **Symptom**, **Why**, **Fix**, **Exceptions**, **Evidence**, and **Detection**.

- **Evidence describes the failure pattern**: State what went wrong in the text and what misjudgement or information loss it caused the reader. Never include verbatim user quotes, personal names, project names, or internal tool names.
- **Synchronize the detection mapping**: When adding a symptom, update `references/category-map.md` in the same change to record whether it is detected mechanically by `detect.py` or evaluated by semantic judgement.

### 4. Local Verification

Before submitting, run both built-in verification scripts from the suite root (or `i18n/en` root):

```bash
python3 skills/agent-engineering-discipline/scripts/check_skill_spec.py .
python3 skills/deliverable-writing-audit/scripts/detect.py .
```

Verify that both pass:
- **Structural check (`check_skill_spec.py`)**: Valid YAML Frontmatter, `description` stating both trigger conditions and negative boundaries, and zero broken relative Markdown links.
- **Writing audit (`detect.py`)**: Zero hits reported. If a hit matches a documented exception in `pattern-catalog.md`, state the exemption rationale in your PR description.

Additionally, ensure all scripts rely exclusively on the Python 3 standard library with zero external `pip` dependencies.

---

## License

By submitting a contribution to this project, you agree that your contribution will be licensed under the [MIT License](../../LICENSE).
