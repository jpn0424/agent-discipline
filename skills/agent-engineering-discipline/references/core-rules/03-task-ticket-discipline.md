# Core Rule 03: Work Item Discipline

## Why This Rule Exists (Why)
During a work session, agents frequently spot edge-case bugs or refactoring candidates and offer an oral promise: "we can clean that up later." Once the session ends, that oral promise vanishes completely.

A work item does more than prevent forgetting. Anyone inspecting the repository afterward must be able to see what constituted completion at the time—without pre-written acceptance criteria, completion degenerates into the executor's subjective claim; without screenshots for visual state changes, prose claims cannot be independently audited. Every work item therefore records its status, execution method, and acceptance criteria, plus screenshots whenever visual or external UI state is involved.

---

## How to Execute (How)

### 1. Work Item Before Touch

A **Work Item** is the minimal tracking unit carrying the inputs, outputs, constraints, and verification evidence of a single task. The criterion for creating a work item before acting is **"will this change ever need to be traced after the fact?"** Modifying code, Skills, or deployment configuration always qualifies: copy [assets/task-template.md](../../assets/task-template.md) to `docs/tasks/TASK-YYYYMMDD-HHMMSS-<rr>-<slug>.md`, one task per work item.

Generate the prefix using "date + second-level timestamp + 2-digit hex random suffix" such as `TASK-20261030-024000-a1` so parallel agents and isolated Git worktrees maintain strict chronological ordering with zero ID collisions. Run the standard-library generator before creating the file rather than guessing a timestamp:

```bash
python3 -c "import time,secrets; print(time.strftime('TASK-%Y%m%d-%H%M%S-') + secrets.token_hex(1))"
```

Historical work items using the `TASK-YYYYMMDD-NN` format remain untouched; do not rename them retroactively. Answering questions, reading code, or producing ephemeral analysis that modifies no files does not require post-hoc traceability, so creating a work item would only add noise. For a single-character typo fix, ask whether anyone will later ask why that line changed—if yes, create a work item.

### 2. No Oral Postponement

A known defect has only two valid destinations: fixed right now, or assigned a work item ID right now. A third destination does not exist.

The test is straightforward: if your response contains phrases like "later," "in a future pass," or "leave it like this for now," the issue is slipping into that nonexistent third destination. Replace the phrase with a concrete work item reference, such as "Logged under `TASK-20260723-143000-a1`, status `[Pending]`." If you cannot point to a work item ID, the issue has not been tracked.

### 3. Screenshots for UI and External System Operations

The criterion is **"can another person inspect the evidence of this verification?"** Whenever verification involves a UI or produces visible state in an external system, prose descriptions cannot be audited; save screenshots under `docs/tasks/screenshots/` and link them via a relative path in the work item: `![Verification Screenshot](screenshots/TASK-20260723-143000-a1__login.png)`.

Add `docs/tasks/screenshots/` to `.gitignore`—screenshots frequently capture customer names, internal hostnames, or session tokens. There is zero room for discretion here; see [Core Rule 09](09-deliverable-hygiene.md).

For pure code or documentation tasks where the evidence is command output rather than a screen state, write `Not applicable` in the screenshot field. Writing `Not applicable` proves you evaluated the requirement; leaving the field blank looks like an oversight.

### 4. State, Relations, Method, and Acceptance on the Work Item

The criterion is **"if another agent or engineer picks up this work item, can they proceed without asking you where it stands?"** Four fields carry that responsibility.

**Current status has exactly four valid values**: `[Pending]`, `[In Progress]`, `[Completed]`, and `[Cancelled]`. Status expresses where the work item sits in the workflow lifecycle—not what ruling it is waiting on, which condition is blocking it, or how much evidence has been gathered. Those details belong in the work item body.

Whenever you are tempted to invent a fifth status value, the phrase in mind describes a circumstance rather than a lifecycle state—for example, "Awaiting Evaluation" could mean nobody has picked it up yet or someone is actively evaluating it right now, obscuring the very question the status field exists to answer.

**Related work items express directional dependencies and lineage**: When a work item has a blocker, supersedes an older approach, or builds on prior findings, declare `Related Work Items` in the header using three named directional forms, or write `None` when independent:
- `Blocked by TASK-...`: Execution cannot start until the referenced work item reaches `[Completed]`.
- `Supersedes TASK-...`: This work item replaces and retires an older work item.
- `References TASK-...`: Shares domain context or builds on findings from the referenced work item without a blocking dependency.

**Execution method is declared on the work item**: Test-First, Brainstorm and Plan, Research, another named method, or `Not applicable`. See the `Methods` section of [SKILL.md](../../SKILL.md) for how to select an execution method. Single-line fixes and pure prose edits write `Not applicable` without further justification.

**Acceptance criteria are fixed when the work item is created**: Write each condition on its own line in a form that can be checked without subjective re-interpretation. Acceptance criteria and verification steps are distinct: acceptance criteria define what must hold true, while verification steps define the commands or checks used to gather that proof. For how to make criteria decidable, see [Core Rule 04](04-delegation-contract.md); this section requires that they exist and are written before touching files.

**Never weaken acceptance criteria after the fact to fit a partial result.** If execution falls short of a criterion, adjust the implementation or renegotiate scope with the user—never silently edit the criterion so you can mark `[Completed]`. If a criterion genuinely must change, record what changed and why inside the work item.
