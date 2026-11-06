# Core Rule 04: Delegation Contract

## Why This Rule Exists (Why)
When a work item written only as a personal reminder is handed to another agent, the executing agent fills every unstated gap with confident guesswork. The resulting output looks complete on the surface while diverging from the intended design, hiding defects until late integration.

Writing a work item as an explicit contract turns "is this ready to delegate?" into an observable fact before execution starts, rather than a gamble discovered after the subagent finishes.

---

## How to Execute (How)

### 1. Three Contract Sections (Inputs, Outputs, Constraints)

A delegable work item must specify three sections; complete any missing section before handing it off:

| Contract Section | Required Content | Risk When Omitted |
| --- | --- | --- |
| **Inputs** | Preconditions: source file paths, parameters, prior state, and known facts | Executor invents or searches arbitrary sources, causing silent drift |
| **Outputs** | Target deliverables and **decidable acceptance criteria** (see Section 2) | Executor defines its own lowered bar for completion |
| **Constraints** | Explicit file boundaries and prohibited actions (see Section 3) | Executor performs unauthorized edits or scope creep |

**Criterion**: Hand the work item to an agent with zero access to the current conversation transcript—can it execute the task from start to finish by reading the work item alone? If not, the contract still has unstated gaps.

Do not assign "delegation difficulty tiers." Difficulty ratings are pre-execution guesses that cannot be calibrated and incentivize under-rating tasks just to dispatch them. Contract completeness is directly observable before execution.

### 2. Acceptance Criteria Must Be Decidable, Not Merely Executable

Output specifications must allow **an evaluator to determine whether the work item is complete without redoing the work**.

Automated unit tests are one special case of decidability for code tasks, not the definition of decidability itself. Match the verification form to the nature of the artifact:

| Artifact Nature | Acceptance Criteria | Typical Counterexample |
| --- | --- | --- |
| Code and configuration | Runs cleanly, automated tests pass, validator script exits with code `0` | "Should work now" |
| Research and investigation | Required structural sections present, primary sources and citations verified | "Researched the topic" |
| Exploration and inventory | Directly answers the stated questions, output feeds cleanly into downstream work items | "Got a rough idea" |

**Acceptance verifies conformance to specification, not the ultimate truth of a research conclusion.** Verifying whether a research conclusion is substantively right requires redoing the research, which is governed by domain credibility criteria rather than work item acceptance.

If you cannot state how completion will be judged, the output itself is not yet defined. Refine the output definition rather than weakening the acceptance bar.

### 3. Write Constraints for the Executor

Inputs and outputs are written naturally; constraints are what authors skip. Yet subagent failures rarely stem from lack of capability—they stem from doing things nobody asked for. Every `Constraints` section must specify three items:

- **File boundary**: Exact paths the executor may modify and paths it must not touch. Parallel work items are safe only when their file boundaries are disjoint.
- **Prohibited actions**: Adjacent issues excluded from this pass. If discovered, log a new work item per [Core Rule 03](03-task-ticket-discipline.md) instead of fixing them in passing.
- **Behavior when blocked**: Stop immediately and report what is blocking and which condition is missing; never improvise a workaround or force through an unverified path.

### 4. Executors Do Not Self-Certify

Evaluate completion strictly against the acceptance criteria written in the work item, never by trusting the executor's own summary claim. This extends the two-tier governance of [Core Rule 11](11-skill-and-agent-spec.md) to work item acceptance.

When output fails the contract, determine whether the executor lacked capability or the contract left a gap. Re-run with a stronger model for the former; tighten the contract for the latter—**the distinction lies in whether the contract was ambiguous, not how bad the output looks**.

### 5. Contracts Can Evolve

A contract is not frozen at creation time. Unstated assumptions often surface only during the first execution pass; when they do, update the work item and record what changed.

Creating a work item requires **converging enough to take the next step reliably**, not predicting every detail upfront. Over-specifying at the point of maximum uncertainty wastes effort, whereas delegating an unconverged stub dumps design responsibility onto the agent with the least context.
