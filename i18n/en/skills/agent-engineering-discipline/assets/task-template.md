# [Status] TASK-YYYYMMDD-HHMMSS-<rr>-<slug>: Concise Work Item Title

- **Created Date**: YYYY-MM-DD
- **Current Status**: `[Pending]` / `[In Progress]` / `[Completed]` / `[Cancelled]`
- **Related Work Items**: `None` (or `Blocked by TASK-...` / `Supersedes TASK-...` / `References TASK-...`)

---

## Description
> [REQUIRED] State background, problem, and goal.

Summarize the problem to solve and the expected outcome.

## Inputs
> [REQUIRED] List source paths, specs, and known facts.

Facts and preconditions known before acting: source files, parameters, and prior state. When delegating to another agent, specify enough detail that the executor can start without asking follow-up questions.

- Source files: `path/to/...`
- Prior state:

## Execution Method
> [CONDITIONAL] Name method, or write Not applicable.

- **Method**: Test-First / Brainstorm and Plan / Research / Other (state basis) / Not applicable
- **Acceptance basis**: The chosen method determines how acceptance criteria are verified. Test-First requires tests transitioning from red to green; Research requires structural completeness and verified primary sources; Not applicable relies on static specification checks.

## Scope of Changes
> [REQUIRED] List every file path to be touched.

- [ ] Code: `src/...`
- [ ] Skills / Configuration:

## Constraints
> [REQUIRED] Define file boundaries and red lines.

- **File boundary**: Exact paths permitted to change and paths off-limits.
- **Prohibited actions**: Adjacent issues excluded from this pass; log a new work item if discovered rather than fixing in passing.
- **Behavior when blocked**: Stop and report where blocked and what prerequisite is missing; do not improvise workarounds.

## Acceptance Criteria
> [REQUIRED] List decidable completion checks.

Written before acting, one criterion per line, phrased so an evaluator can verify completion without redoing the work. Never weaken criteria after the fact to fit partial results; if a criterion must change, record what changed and why.

- [ ] Criterion 1
- [ ] Criterion 2

## Verification and Testing
> [REQUIRED] Provide executable verification steps.

Exact commands or structural checks used to gather the proof required by the acceptance criteria above.

```bash
python3 -m pytest tests/ -q
```

## Verification Results
> [REQUIRED] Record outputs and exit codes after work.

When the deliverable is prose, record a pointer to the canonical file path and section rather than copying the prose body into the work item—copying prose into a work item creates cross-file duplication without adding runtime protection.

- **Test Result**: `[Passed / Failed]`
- **Verification Screenshot**: `docs/tasks/screenshots/TASK-YYYYMMDD-HHMMSS-<rr>-<slug>__01.png` (attach when UI or visible external state is involved; write `Not applicable` for pure code or documentation tasks)
