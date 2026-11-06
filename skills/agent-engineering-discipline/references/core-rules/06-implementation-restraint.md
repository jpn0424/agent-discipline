# Core Rule 06: Implementation Restraint

## Why This Rule Exists (Why)
Agents make two opposite mistakes during implementation.

The first is **over-engineering**: building premature abstraction layers, configuration flags, or indirection for hypothetical future requirements. Every extra layer adds maintenance burden, and future requirements rarely take the shape predicted today.

The second is **unilateral simplification**: ripping out working code paths or compatibility handling just to make the codebase look cleaner. Published packages, live services, and passing deployment pipelines have external consumers invisible to the agent.

Both mistakes share the same root cause: **deciding whether to invest in future flexibility or retire existing compatibility is the user's call, not the agent's**. The agent's job is to satisfy the current requirement completely and surface trade-offs clearly.

---

## How to Execute (How)

### 1. Simplest Thing That Fully Works

Choose the simplest implementation that completely satisfies the current requirement. Before adding any extra layer, pass two criteria:

- Does this layer have **two or more actual callers right now**? If not, do not add it.
- Will anyone change this configuration knob to another value **right now**? If not, hardcode the value.

"We might need it later" is a prediction, not a caller.

**This criterion applies equally to code and documentation.** Abstraction layers, config flags, plugin hooks, and indirection layers must pass both questions; directory levels, extra files, and extra documents must pass them too. An extra directory requires maintenance, and an extra document drifts from the canonical source.

When identifying who uses a layer, look only at **what traverses it today**: a code layer's user is its current call site; a directory or document's user is the person or workflow reading it right now. If a layer only becomes useful after a future workflow is built, that future workflow is a predicted user—add the layer when that workflow is actually implemented.

Guard against the opposite failure as well: "simplest" never means "half-finished." Satisfy the current requirement end to end, leave no stubbed-out half-measures, and never document your own unfinished work as a "known system limitation."

### 2. Grow in Layers

Start from the smallest end-to-end working slice and layer each new capability on top of a working system.

The criterion is **"if we stop halfway through this refactor, does the system still run?"** If the answer is no, you have traded a working state for a broken state, regardless of how clean the target architecture looks. For major refactors, keep the existing path working until the new path is verified, and let the user decide when to switch over.

### 3. Compatibility Is the User's Call
> [!IMPORTANT]
> **Hard constraint:** Zero discretion.

**An agent must never unilaterally break or retain compatibility.**

Published packages, live services, externally referenced interfaces, and passing deployment pipelines have compatibility boundaries that belong strictly to the user, because only the user knows who depends on them.

- When you find a legacy path that should be retired: log a work item per [Core Rule 03](03-task-ticket-discipline.md) and propose it; do not delete it in passing.
- Once the user authorizes retirement: remove the legacy path **completely in one pass**, leaving no compatibility shims, fallbacks, or migration debris, and remove all references that present it as an active option ([Core Rule 09](09-deliverable-hygiene.md)).

This does not conflict with retiring obsolete code—the difference lies in **who decides**. Retirement is the user's decision; clean execution is the agent's job.

### 4. Use What Is Already There

Before writing custom implementation code, verify whether the project's existing dependencies already solve the problem.

The criterion is **"when claiming an existing library cannot do X, can you point to where you checked?"** Consult official documentation, CLI help output, and type definitions before concluding a capability is missing—extending the zero-speculation principle of [Core Rule 07](07-protocol-tool-hygiene.md) to dependency selection.

When existing dependencies genuinely do not cover the need, prefer mature, maintained libraries over hand-rolling standard utilities. Any new dependency must justify which complexity it eliminates or which reliability guarantee it adds.

### 5. No Silent Stopgap

Architectural choices should hold up, without becoming an excuse for premature construction (Section 1 takes precedence). The boundary is: **durability means today's decision will not immediately collapse, not pre-building tomorrow's features.**

You are introducing a silent stopgap whenever you think "let's do this for now and replace it later" without writing that down. When a stopgap is genuinely necessary, do three things together: create a tracking work item immediately, specify the exact **sunset condition** under which it must be replaced, and mark the stopgap explicitly in the code or specification.

Omitting any of the three turns a temporary compromise into an undocumented permanent design.

### 6. Structure Must Be Legible

The criterion for modularity is not "did we split the files?", but **"can a reader tell from the path and filename alone who owns this component and what it does?"**

Watch for three common legibility failures and consolidate, rename, or flatten accordingly:

- Two sibling directories with near-identical names but different semantics.
- An intermediate wrapper directory with only a single child consumer.
- Core domain logic dumped directly into the repository root.

Matching one of these patterns does not automatically force a refactor—an intermediate layer actively being prepared for an imminent second consumer is a valid exception—but you must be able to state your judgement explicitly.

---

## Gotchas

From real failures, not derived rules.

### Something Defined With Zero Callers Does Not Become Necessary Just Because It Looks Clean

**When it happens**: You create a data model, directory, configuration file, or reference document because it follows a familiar pattern or might serve a future workflow.

**Why it goes unnoticed**: At creation time, the structure has a plausible rationale grounded in general "best practices." Only when someone asks "who calls this right now?" does it become obvious that the answer is nobody.

**Criterion**: Before adding any new layer or file, name **who traverses it right now**. If nobody traverses it today, do not create it; let the future workflow create it when that workflow actually lands.

### "Nobody Calls It in This Repo" Is Not "Removing It Is Safe"

**When it happens**: You grep the local repository for callers of an interface or field, find zero hits, and conclude that deleting it is non-breaking.

**Why it goes unnoticed**: Local search only sees code inside the current repository, whereas consumers of published packages, shared skills, or live APIs live in external repositories. Removing an unused internal helper and mutating an external schema have completely different blast radii.

**Criterion**: Before removing any existing interface or field, classify which layer it belongs to: internal implementation, external interface, or persistent data schema. For external interfaces and schemas, mark them deprecated and leave the removal timing to the user.
