# <Project Name> — <One-sentence summary of what this repository is>
> [REQUIRED] Copy to root as AGENTS.md. Pair with the pointer files of the platforms your team actually uses (see Core Rule 10 for the entrypoint list); each only points to AGENTS.md.

## Project Positioning & Deliverables
> [REQUIRED] Define deliverables, consumers, and edit boundaries.

| Target | Content | Modification Boundary |
| --- | --- | --- |
| `<primary-deliverable-path>` | <What this deliverable is and who consumes it> | <Whether it can be edited directly and who is affected> |
| `<secondary-deliverable-path>` | | |
| `AGENTS.md` | Canonical governance specification for this repository | Developer-facing; not shipped inside external deliverables |

## File Structure
> [REQUIRED] Map core directories and file ownership.

| Path | Content |
| --- | --- |
| `<path>` | <Content> |
| `docs/tasks/` | Work items and index, named `TASK-YYYYMMDD-HHMMSS-<rr>-<slug>.md` (backward-compatible with `TASK-YYYYMMDD-NN`) |
| `AGENTS.md` / Platform Pointer Files | Canonical governance source and platform pointers |

## Skills Classification & Positioning
> [CONDITIONAL] Required if the project defines custom Skills.

| Skill | Type | Responsibility |
| --- | --- | --- |
| `<skill-name>` | Governance / Auditor / Execution | <What it owns and what falls outside its boundary> |

> [!NOTE]
> If any rule is intentionally repeated between this file and a Skill, state here that the duplication is deliberate and link to the canonical source in the Skill. Because `AGENTS.md` is always loaded while Skills load conditionally, that loading gap justifies repeating critical safety rails; duplication without that loading gap is a defect.

---

## Core Development Rules (Constraints)
> [REQUIRED] Separate `[Hard Constraint]` rules from situational criteria.

Rules prefixed with `[Hard Constraint]` carry zero discretion and must be executed literally—reserved strictly for actions whose violation is irreversible or affects third parties. Unprefixed rules state the judgement criterion and failure mode so the agent can adapt to context. Writing every rule at maximum strength prevents the agent from distinguishing irreversible boundaries from situational heuristics.

### 1. Execution & Authorization

#### Always
> [REQUIRED] Positive authorization and tracking habits.

- **Confirm scope before acting**: The user's instruction verb defines the authorized scope. When asked to "review," "evaluate," or "report," read and analyze without modifying files; when asked to "give the command," output the command without executing it; when in doubt, stop and ask rather than picking the higher-risk path.
- **Create a work item before modifying files**: Before modifying any code, configuration, or specification, create a work item in `docs/tasks/`—one task per work item. When discovering a new issue, either fix it immediately or log a work item right away.
- **Report modified files**: Every final response at the end of a turn must list the exact paths of all created, modified, or deleted files.

#### Never
> [REQUIRED] Prohibited unauthorized or destructive actions.

- **[Hard Constraint] No unauthorized remote or history writes**: `git commit`, `git push`, opening a PR, and any remote write operation require explicit user instruction in the current turn. Prior-turn approval never carries over.
- **[Hard Constraint] No irreversible deletion**: Never run `rm -rf` when cleaning up files. Use `/usr/bin/trash` on macOS, or the platform's recoverable deletion mechanism elsewhere.
- **No out-of-scope drift**: Modify only the files within the user's specified scope. Log adjacent defects as new work items or mention them in one sentence rather than fixing them in passing.

### 2. Verification & Honesty

#### Always
> [REQUIRED] Evidence and verification requirements.

- **[Hard Constraint] Claim carries evidence**: Whenever writing "fixed," "completed," or "verified," co-locate the proof in the same place—verbatim tool output, read-back state, screenshot path, or the work item's verification results section. Downgrade any claim that lacks evidence.
- **Fix acceptance criteria before acting**: Write decidable acceptance criteria into the work item before touching files. Never weaken criteria after the fact to match a partial result; if criteria must change, document what changed and why.
- **Execute to verify**: Run the actual tests or verification commands before claiming completion; reading code never substitutes for execution.
- **Verify with the real toolchain**: Walk the exact toolchain and path the user will traverse. An internal API succeeding in isolation does not prove the user workflow works.
- **Preserve verbatim errors**: When reporting a failure, paste the exact error message without summarizing or paraphrasing, and state which layer failed. Mask only sensitive credentials with placeholders.

#### Never
> [REQUIRED] Prohibited unverified claims and guesswork.

- **[Hard Constraint] No residual unverified status**: Capability tables allow only "Verified" or "Known Unsupported"—never leave "Untested," "Unknown," "Assumed Supported," or `TBD`. If blocked, state what prerequisite is missing.
- **No unevidenced limitation claims**: Test all relevant operations before writing "cannot," "only supports," or "unsupported." Never frame a capability that already succeeded as a limitation.
- **No speculative filling**: When a tool or lookup returns no data, report "not found" and stop. Never guess query variations blindly, pull from unrelated sources, or invent plausible field values.

### 3. Implementation & Data

#### Always
> [REQUIRED] Minimal implementation and source lookup rules.

- **Zero-speculation schema lookup**: Query the authoritative source to verify exact key names, types, and required constraints before assembling any payload. Memory, similar APIs, and snippet examples are not authoritative sources.
- **Simplest thing that fully works**: Choose the minimal implementation that satisfies the current requirement end to end. The criterion is "does this abstraction have two or more callers right now?"—if not, do not add it.
- **Use existing dependencies first**: Verify whether the project's installed dependencies already solve the problem by checking official docs and type definitions before writing custom helpers.

#### Never
> [REQUIRED] Prohibited premature abstraction and silent stopgaps.

- **No premature construction**: Never add abstraction layers, config flags, plugin hooks, or wrapper directories just because "we might need them later."
- **[Hard Constraint] No unilateral compatibility breaks**: Compatibility boundaries for published packages, live services, and external interfaces belong strictly to the user. Log a work item to propose retiring a legacy path rather than deleting it in passing.
- **No silent stopgaps**: Whenever a temporary stopgap is necessary, create a tracking work item immediately, specify its exact sunset condition, and mark it in the code or docs.

### 4. Documentation & Delivery

#### Always
> [REQUIRED] Language, SSOT, and current-state rules.

- **Language standard**: <Specify the project's language convention, e.g., Write all documentation and comments in clear standard English, preserving technical identifiers verbatim>.
- **Single source of truth**: Define each rule in exactly one canonical file and link to it from elsewhere. Any intentional duplication across an always-loaded boundary must declare its rationale and link to the canonical source.
- **State current facts only**: Normative files describe only what the rule is right now. Keep chronological evolution, retired alternatives, and change narratives in work items, `decisions.md`, or commit messages.

#### Never
> [REQUIRED] Prohibited leaks, signatures, and glosses.

- **[Hard Constraint] No credential or local path leakage**: Deliverables must never contain real credentials, internal hostnames, real business IDs, or local absolute paths (such as `/Users/<user>/...`); replace them with semantic placeholders or relative paths.
- **No AI attribution signatures**: Deliverables, commit messages, and PR descriptions must never contain AI generation footers or robot emojis.
- **No change narration or parenthetical glosses**: Normative prose must not contain chronological drift, before/after comparisons, or parenthetical backstory—promote needed context into standalone sentences or table columns.
