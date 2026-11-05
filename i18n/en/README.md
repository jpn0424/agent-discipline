# agent-discipline

[繁體中文](../../README.md) | [English](README.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](../../LICENSE) [![skills.sh](https://img.shields.io/badge/ecosystem-skills.sh-purple.svg)](https://skills.sh/) [![Python: 3.x](https://img.shields.io/badge/python-3.x-green.svg)](skills/agent-engineering-discipline/scripts/check_skill_spec.py)

Engineering discipline and deliverable writing audit suite for AI coding agents. One directory per Skill, where the directory name matches the Skill's frontmatter `name`, installable directly via the [`skills`](https://skills.sh/) CLI below.

## Included Skills

| Skill | Type | Summary |
| :--- | :--- | :--- |
| [`agent-engineering-discipline`](skills/agent-engineering-discipline/) | Normative | Governance layer for engineering discipline: creating work items with locked scope and acceptance criteria before modifying files, authorization boundaries, honest reporting with verifiable evidence, zero-speculation schema queries, minimal implementation and compatibility boundaries, two-tier governance, and Nygard ADR decision records. Execution methods inside a work item—such as test-first or two-phase planning—are chosen based on task characteristics. |
| [`deliverable-writing-audit`](skills/deliverable-writing-audit/) | Auditing | Symptom-based auditing and rewriting for existing text: 28 named writing symptoms, tolerance levels across six delivery profiles, and three operating modes (`detect` flag-only, `rewrite` return revised text, `edit` modify in place), defaulting to `detect`. Ships with a zero-dependency detection script. |

The former governs agent behavior before and after touching files; the latter audits the prose produced. Because the former's deliverable hygiene rule requires auditing modified files with the latter, install both together for complete coverage.

## Installation

Run the following command at the **root of your target repository**:

```bash
npx skills add jpn0424/agent-discipline/i18n/en --agent claude-code --copy -y
```

The `/i18n/en` subpath points `npx skills` directly at the English suite mirror while keeping the canonical Skill names (`agent-engineering-discipline` and `deliverable-writing-audit`). Purpose of the three flags: `--agent claude-code` restricts installation to Claude Code without creating `.junie/` or `.cursor/` directories; `--copy` writes real files into `.claude/skills/` instead of symlinking to `.agents/`, preventing broken links if `.agents/` is not committed; `-y` skips interactive prompts.

For the Traditional Chinese (default root) edition, omit `/i18n/en`:

```bash
npx skills add jpn0424/agent-discipline --agent claude-code --copy -y
```

## First-Time Usage After Installation

1. **Let Claude Code discover the Skills**: If `.claude/skills/` did not exist in the project before installation, restart Claude Code once so it watches the new directory; if the directory already existed, discovery is immediate.
2. **Confirm loading**: Type `/` in the prompt; both Skill names should appear in the command menu.
3. **Triggering**, either way:
   - **Automatic**: When your request matches the scenarios in a Skill's `description`, Claude loads and applies the specification automatically.
   - **Manual**: Invoke `/agent-engineering-discipline` or `/deliverable-writing-audit` directly.

Once loaded, `SKILL.md` stays active for the session, while deep files under `references/` and `assets/` are loaded on demand so they do not flood the context window upfront.

## How to Verify It Works

**`agent-engineering-discipline`** does not execute a standalone action; it governs how the Agent behaves across subsequent engineering tasks. After loading it, assign a development task and verify that the Agent:

- Creates a work item locking scope and acceptance criteria before modifying files.
- Performs only analysis and reporting—without editing files—when your verb is `"review"` or `"audit"`.
- Points to concrete evidence in the same place whenever claiming `"completed"` or `"fixed"`.

All three must hold for governance to be active. If any of the three is missing, the specification did not enter the session context.

**`deliverable-writing-audit`** activates when you ask the Agent to inspect existing text. Ask it to review a document and verify that it:

- Flags hits without altering files unless you explicitly ask for modifications.
- Cites line numbers and verbatim quotes for every hit.
- Separates security and credibility defects (Tier 1A) from readability and formal noise (Tier 1B).

You can also run the mechanical detection script directly without an Agent:

```bash
python3 skills/deliverable-writing-audit/scripts/detect.py <file-or-directory>
```

## Core Rules

The eleven core rules of `agent-engineering-discipline`:

| ID | Core Rule | Prevented Failure Mode (Anti-Pattern) |
| :--- | :--- | :--- |
| CR-01 | Judgement Responsibility | Pushing investigation back onto the user; asking the user to repeat facts already in the workspace |
| CR-02 | Authorization & Scope Boundary | Editing files when asked to `"review"`; modifying file B as a side effect when asked to change file A |
| CR-03 | Work Item Discipline | Promising `"we'll fix that later"` orally and losing track once the session ends |
| CR-04 | Delegation Contract | Writing work items only the author understands, forcing delegated executors to guess |
| CR-05 | Execution Safety | Unauthorized `git commit` / `git push` and unrecoverable deletion via `rm -rf` |
| CR-06 | Implementation Restraint & Compatibility | Building speculative abstractions; silently ripping out working compatibility shims |
| CR-07 | Protocol & Schema Hygiene | Polluting `stdout` protocol channels with diagnostics; guessing unverified API field names |
| CR-08 | Honesty & Evidence | Claiming unverified work is `"complete"`; declaring working capabilities `"unsupported"` |
| CR-09 | Deliverable Hygiene & ADR | Leaking local absolute paths or secrets into deliverables; leaving major architectural decisions unrecorded |
| CR-10 | Harness Document Layout | Scattering duplicate rules across files until different agents read contradictory versions |
| CR-11 | Skill Spec & Two-Tier Governance | Breaking Skill discovery via malformed frontmatter; allowing executors to self-certify completion |

### Key Design Principles

**CR-06: Compatibility boundaries are decided by the user, never at the Agent's discretion.**

- **No speculative abstraction**: Choose the simplest implementation that satisfies current requirements. The criterion for adding an abstraction layer, configuration toggle, or plugin hook is `"Do two or more concrete callers exist right now?"` If not, do not add it.
- **Breaking compatibility is a user decision**: Published packages, live services, and externally referenced interfaces have downstream consumers invisible to the Agent, so the Agent must never unilaterally break or preserve compatibility. When a legacy path should be retired, open a work item and propose it; once the user approves retirement, remove the entire path cleanly in a single pass without leaving dead shims behind.

This rule deliberately rejects the blanket slogan `"always delete compatibility layers"`. The distinction lies in who makes the call: deciding to retire a path belongs to the user; executing the cleanup belongs to the Agent.

**CR-04: Contract completeness replaces difficulty tiers.**

- **No delegation difficulty tiers**: Difficulty ratings are pre-execution guesses that cannot be calibrated, and the delegator has a built-in incentive to underrate difficulty just to hand the task off.
- **Three contract sections are the delegation threshold**: A delegable work item must specify Inputs, Outputs with Acceptance Criteria, and Constraints. The criterion is whether an executor with zero access to the current conversation can start work by reading the work item alone; if not, the contract still has gaps.

## User-Customizable vs. Invariant Sections

The suite's governance architecture draws a strict line between **non-negotiable safety invariants** and **project-customizable sections**:

### Non-Negotiable Governance Core (Invariants)
- **Four Invariants**: Record before acting, obtain authorization before crossing boundaries, attach evidence to every completion claim, and preserve a recovery path for every destructive operation.
- **Hard Constraints**: Explicit per-turn authorization before writing to remotes, zero `rm -rf`, reversible state transitions only on external records, zero secrets or local absolute paths in deliverables, and co-located evidence for every completion claim. Agents execute these literally with zero discretion.

### User-Customizable Sections
- **Project Governance Entrypoint (`AGENTS.md`)**:
  - The single canonical entrypoint for project-local rules. Copy `assets/agents-template.md` to your repository root as `AGENTS.md` and customize project overview, directory layout, modification boundaries, and project-specific `Always` / `Never` rules.
  - **Extending project-specific hard constraints**: Add repository-specific red lines—such as read-only core directories, forbidden environment variables, or deployment commands requiring confirmation—under `#### Never` in `AGENTS.md`.
- **Execution Methods (`references/methods/`)**:
  - Governance does not lock you into a single development methodology. Declare `test-first`, `brainstorm-and-plan`, standard industry methods (such as TDD or BDD), or `"Not applicable"` per work item.
- **Work Item and ADR Templates (`assets/`)**:
  - `task-template.md` and `decision-template.md` provide baseline schemas that teams may adapt to match their existing issue trackers and workflows.

## Directory Structure

```
agent-discipline/
├── README.md                                   # Suite documentation (Traditional Chinese, default)
├── LICENSE                                     # MIT License
├── CONTRIBUTING.md                             # Contribution and governance guide
├── skills/                                     # Default Traditional Chinese Skills
│   ├── agent-engineering-discipline/
│   └── deliverable-writing-audit/
└── i18n/
    └── en/                                     # Complete English Suite Mirror
        ├── README.md                           # English suite documentation (this file)
        ├── CONTRIBUTING.md                     # English contribution guide
        └── skills/
            ├── agent-engineering-discipline/
            │   ├── SKILL.md                    # Main entrypoint: rule routing, action table, CLI usage
            │   ├── references/
            │   │   ├── core-rules/             # 11 core engineering rules
            │   │   └── methods/                # 2 calibrated execution method deltas
            │   ├── assets/                     # Governance templates: agents-template.md, task-template.md, decision-template.md
            │   └── scripts/check_skill_spec.py # Zero-dependency structural & link checker
            └── deliverable-writing-audit/
                ├── SKILL.md                    # Main entrypoint: 6 audit steps, modes, severity, output format
                ├── references/
                │   ├── pattern-catalog.md      # 28 writing symptoms: symptom, why, fix, exceptions, evidence, detection
                │   ├── profile-matrix.md       # Tolerance levels across 6 delivery profiles
                │   ├── category-map.md         # Mechanical script types vs. semantic judgement mapping
                │   └── methodology-grounding.md# Post-hoc mapping to 5 theoretical pillars
                └── scripts/detect.py           # Zero-dependency writing symptom detector
```

## Contributing and License

- Issues are welcome. Pull requests are treated as proposals and published from the upstream monorepo in the next tagged release; see [CONTRIBUTING.md](CONTRIBUTING.md).
- Released under the [MIT License](../../LICENSE).
