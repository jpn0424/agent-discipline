# Core Rule 10: Harness Document Layout

## Contents

- 1. Canonical Source vs. Pointers: `AGENTS.md` is the single canonical source; other entrypoints contain only a pointer
- 2. Canonical Structure of `AGENTS.md`: Four ordered sections, rule formatting, binary deontic strength, fixed modal verbs, and list exhaustiveness markers
- 3. Division Between `docs/` and `references/`: The criterion is who authors the file, not its topic
- 4. Declared Duplication: Valid only across an always-loaded vs. conditionally-loaded boundary
- Gotchas: Confusing two documentation directories when topics overlap, and treating human entrypoints as a miscellaneous catch-all

## Why This Rule Exists (Why)
`AGENTS.md` is the cross-platform convention read by multiple coding agents, whereas `CLAUDE.md` is read only by Claude Code. Putting governance rules directly inside `CLAUDE.md` leaves other agents unguided; maintaining full copies in both files guarantees they will drift out of sync.

The same split occurs between documentation folders. Without a clear boundary between `docs/` and `references/`, project-authored records and read-only external reference specs get mixed together, leaving agents unable to tell which files they are supposed to maintain and which files are immutable external contracts.

---

## How to Execute (How)

### 1. One Source, Many Pointers

| File | Supported Platform | Role | Permitted Content |
| --- | --- | --- | --- |
| `AGENTS.md` | Universal Standard / All Platforms | **Canonical Source (SSOT)** | All workspace governance rules and architectural mappings |
| `CLAUDE.md` | Claude Code | Platform Pointer | One H1 title line + `@AGENTS.md`, with zero rule prose |
| `.github/copilot-instructions.md` | GitHub Copilot | Platform Pointer | Pointer line referencing `AGENTS.md` (e.g. `See AGENTS.md for workspace rules.`) |
| `.cursor/rules/agents.mdc` / `.cursorrules` | Cursor / Windsurf | Platform Pointer | Rule configured to always apply and pointing to `AGENTS.md` |
| `GEMINI.md` | Gemini CLI / Antigravity | Platform Pointer | Native `AGENTS.md` support; if a dedicated file is needed, point to `AGENTS.md` |
| Other agent entrypoints | Respective Platforms | Platform Pointer | Same principle, using each platform's native include syntax pointing to `AGENTS.md` |

Taking Claude Code as an example, the complete content of `CLAUDE.md` must be these two lines and nothing else:

```markdown
# Claude Code — <Project Name>

@AGENTS.md
```

`@AGENTS.md` is Claude Code's native import directive, which expands `AGENTS.md` into context at load time. Any additional prose placed in `CLAUDE.md` creates a redundant second source of truth. If a project is primarily driven by another agent (such as GitHub Copilot or Cursor), create the platform-specific pointer file pointing to `AGENTS.md`; creating unused entrypoint files is not required.

> [!NOTE]
> Naming specific agent files here is **intentional** and does not violate [Core Rule 11](11-skill-and-agent-spec.md). Because this section defines the exact entrypoint filenames and import syntax across agent platforms, replacing them with generic placeholders would make the rule unexecutable.

### 2. Canonical Structure of `AGENTS.md`

Arrange `AGENTS.md` in four sequential sections so the agent learns its boundaries before reading specific rules:

1. **Project Positioning & Deliverables**: What this repository is, what it produces, who consumes each output, and the modification boundary for each target. Present as a table.
2. **File Structure**: Directory paths mapped to their contents and ownership. Present as a table.
3. **Skills Classification & Positioning**: Which Skills exist in the workspace, their type (`Governance` / `Auditor` / `Execution`), their responsibilities, and why they do not replace one another. Present as a table.
4. **Core Development Rules (Constraints)**: Grouped by domain, with each domain split into `#### Always` and `#### Never`.

Start every rule bullet with a **bold summary label** followed by a colon and the rule body so agents can locate rules by scanning labels:

```markdown
#### Never

- **[Hard Constraint] No Unauthorized Commit**: `git commit`, `git push`, and opening PRs require explicit user instruction in the current turn.
```

**Separate rules into two deontic strengths.** Rules whose violation is irreversible or affects third parties are written in the imperative mood and prefixed with `[Hard Constraint]`; all other rules are written as **criteria**, stating the judgement basis and the observable failure mode so the agent can exercise situational judgement.

When every rule is written at maximum strength, the agent cannot tell which boundaries are genuinely irreversible and ends up applying context-dependent heuristics rigidly in situations where they cause errors. For the distinction between strengths and the complete list of hard constraints, see the `Abstract` and `Hard Constraints` sections of `SKILL.md`.

**Use fixed modal verbs within each strength.** Prohibitions always use `must never` or `must not`; obligations always use `must`. Rotating among synonyms (`shall not`, `may not`, `is forbidden to`, `should avoid`) tricks readers into guessing whether different verbs imply different priority tiers.

**Mark lists as exhaustive or illustrative.** Introduce exhaustive enumerations with `only` or an explicit count (`the four values below`); introduce open examples with `for example` or `such as`. Unmarked lists in technical specifications are frequently misread as closed enumerations, causing agents to treat unlisted cases as exempt.

Highlight critical preconditions using `> [!IMPORTANT]` or `> [!NOTE]` callouts rather than burying them in parenthetical asides.

### 3. Own Output vs. External Reference (`docs/` vs. `references/`)

**There is only one criterion: is this file authored and maintained by this project, or is it an external artifact that this project only reads as a reference?**

- **`docs/`**: Files authored and continuously updated by this project—including work items, ADRs, architecture specs, and investigation reports.
- **`references/`**: Pre-existing external artifacts not authored by this project and never modified by this project, kept locally so agents can verify facts against them.

#### Directory Mapping

| Content Type | Target Directory |
| --- | --- |
| Work items and verification screenshots | `docs/tasks/`, `docs/tasks/screenshots/` |
| Architecture Decision Records (ADRs) | Project-convention ADR path, such as `docs/decisions/`, `.agent/decisions.md`, or `.claude/decisions.md` |
| Requirements, specifications, research reports, comparative analyses, integration reports | `docs/` |
| Backlogs, test scenario scripts, session transcripts | `docs/` |
| Snapshots of external repository code or configuration | `references/` |
| Upstream deployment scripts, `Dockerfile` samples, pipeline definitions | `references/` |
| Project layout and structure templates | `references/` |
| Target project mapping guides and delivery target schemas | `references/` |
| Business application scenarios and acceptance preconditions for target deliverables | `references/` |
| External platform contracts and static field lookup tables | `references/` |

#### Never

- **Never modify files under root `references/`**: They belong to upstream sources and are read-only in this workspace. If an upstream contract changes, update it in the source repository or log a work item under `docs/tasks/` documenting the discrepancy.
- **Never place runtime agent skills inside `docs/`**: Runtime skills belong in platform-convention skill directories (such as `.agent/skills/`, `.claude/skills/`, or `skills/`). `docs/` holds human and developer records, not runtime instructions.

> [!IMPORTANT]
> **The directory name `references/` carries different semantics at two levels—never conflate them.** Root-level `<repo>/references/` holds read-only external snapshots as defined above; skill-level `skills/<name>/references/` holds the progressively disclosed rule files that belong to that Skill's own canonical source, governed by [Core Rule 11](11-skill-and-agent-spec.md). Both can coexist in the same repository.

**Why the criterion is "who authors it" rather than "is it business or engineering"**: Topical boundaries blur in practice—business application scenarios for target deliverables are both domain context and engineering preconditions, while a delivery mapping guide covers both architecture and workflow. Authorship has zero ambiguity: if this project writes and evolves it, put it in `docs/`; if this project only reads it to check external facts, put it in `references/`. The cost of misclassifying is that an agent either modifies an external source of truth it has no authority to touch, or treats a read-only reference as an active project backlog to maintain.

### 4. Declare Accepted Duplication

**Intentional duplication is valid under only one condition: one location is always loaded into context, and the other is conditionally loaded.** Because `AGENTS.md` is loaded in every session while a Skill is loaded only when triggered, repeating the most critical hard constraints in `AGENTS.md` is justified—otherwise a session that fails to trigger the Skill would operate without safety rails.

Whenever you introduce such intentional duplication, add an explicit note in the always-loaded file stating that the overlap is deliberate and pointing to the canonical source in the Skill; otherwise a subsequent writing audit will flag and delete it as a `C4 Scattered Duplicate Rules` defect.

**When that precondition does not hold, a declaration never makes duplication valid.** If both files are conditionally loaded—such as two files under `skills/<name>/references/`—repeating a rule across them adds zero safety while doubling maintenance and context cost. Delete the duplicate copy and replace it with a relative link.

Undeclared duplication is a defect; declared duplication whose precondition does not hold is a defect in the rationale itself.

---

## Gotchas

From real failures, not derived rules.

### Two Documentation Directories Are Most Easily Flipped When Their Topics Overlap

**When it happens**: You have a document that discusses both the project's domain logic and an external platform's engineering constraints, making both `docs/` and `references/` look plausible.

**Why it goes unnoticed**: In the moment, you classify the file by its subject matter, whereas the directory boundary is defined by **authorship and mutation lifecycle**—files this project owns and edits vs. read-only external artifacts. Classifying by subject matter causes cross-cutting files to land in the wrong directory.

**Criterion**: Before placing a file, ask who maintains it and what triggers an edit. If it evolves with this project's own tasks, place it in `docs/`; if it is an external baseline kept for read-only lookup, place it in `references/`.

### A Human Entrypoint Is Not a Catch-All Drawer

**When it happens**: You have a useful note or operational detail with no obvious home, and dropping it into `README.md` feels harmless because `README.md` is already meant for humans.

**Why it goes unnoticed**: Each added paragraph is factually accurate and relevant to the project. Over several iterations, however, the entrypoint balloons into an unstructured compendium, burying the installation and quick-start steps a new reader actually needs.

**Criterion**: Keep the human entrypoint focused strictly on what a first-time reader needs to understand, install, and start using the project. The criterion is **"if we remove this section from `README.md`, can a new user still install and use the project?"** If yes, move that content to its dedicated reference or documentation file.
