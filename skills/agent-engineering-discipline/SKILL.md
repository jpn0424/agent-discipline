---
name: agent-engineering-discipline
description: "Governs how an engineering task is conducted: create a work item before modifying files to lock scope and acceptance criteria, attach verifiable evidence to every completion claim, require explicit per-turn authorization for remote writes, use recoverable deletion instead of rm -rf, and neither build premature abstractions nor unilaterally remove compatibility layers. Governance defines how a work item is opened and closed; execution methods inside the task, such as test-first, are chosen by task nature and declared in the work item. Do not load when only answering conceptual questions, explaining existing code, or querying data without modifying files. Otherwise, load whenever the conversation will touch files—when the user says 'update this', 'implement this feature', 'add a field', 'open a ticket', 'run tests', 'can we commit', or 'refactor this', or asks to plan architecture, construct API payloads, organize project docs, or prepare a PR, even without mentioning rules or discipline."
---

# Agent Engineering Discipline

## Abstract

This Skill governs how a software engineering task is conducted—how a work item is created, how scope is bounded, how completion is verified, and which actions require explicit authorization—protecting four invariants: a record exists before acting, authorization exists before crossing boundaries, evidence accompanies every claim, and irreversible operations have a recovery path. Because these four invariants hold regardless of task type or technology stack, they are codified as governance rules rather than optional suggestions; whether work inside a task proceeds via test-first, spec-first, or another execution method is determined by the nature of the task and declared in the work item.

## Core Rules

Eleven core rules form the single source of truth for cross-project engineering governance:

| Rule | Governance Scope |
| --- | --- |
| [Core Rule 01](references/core-rules/01-judgement-responsibility.md) | Judgement Responsibility: Boundary between autonomous verification and asking the user |
| [Core Rule 02](references/core-rules/02-authorization-boundary.md) | Authorization Boundary: Per-turn remote write gates, instruction verbs, and scope locking |
| [Core Rule 03](references/core-rules/03-task-ticket-discipline.md) | Work Item Discipline: Creation, status transitions, acceptance criteria, and screenshot records |
| [Core Rule 04](references/core-rules/04-delegation-contract.md) | Delegation Contract: Input, acceptance, and constraint completeness when handing off tasks |
| [Core Rule 05](references/core-rules/05-execution-safety.md) | Execution Safety: Boundaries on irreversible operations and external resource cleanup |
| [Core Rule 06](references/core-rules/06-implementation-restraint.md) | Implementation Restraint: Minimal sufficient implementation and compatibility maintenance |
| [Core Rule 07](references/core-rules/07-protocol-tool-hygiene.md) | Protocol and Schema Hygiene: `stdout` stream isolation and zero-speculation schema lookup |
| [Core Rule 08](references/core-rules/08-honesty-and-evidence.md) | Honesty and Evidence: Co-located evidence, capability status, and instrument calibration |
| [Core Rule 09](references/core-rules/09-deliverable-hygiene.md) | Deliverable Hygiene and ADR: Deliverable sanitization, decision records, and writing audit gate |
| [Core Rule 10](references/core-rules/10-harness-doc-layout.md) | Harness Document Layout: Canonical `AGENTS.md` source of truth and tool entrypoint division |
| [Core Rule 11](references/core-rules/11-skill-and-agent-spec.md) | Skill Specification and Two-Tier Governance: Skill authoring rules and verifier delegation |

Rules in this specification carry two levels of enforcement strength:

- **Hard Constraints**: Executed literally with zero room for discretion; any violation is a defect.
- **Criteria**: Carry situational discretion, stating the decision basis and canonical failure modes. The agent determines the appropriate action for the context and explains the rationale in its report.

Criteria are not optional suggestions—applying the literal wording blind to context is just as much a failure as ignoring the rule. Whenever the context cannot be determined with certainty, default to the hard constraint boundary and state the question explicitly in your response.

## Hard Constraints

The following ten baselines are executed literally with zero room for discretion:

1. **Remote writes require current-turn authorization**: `git commit`, `git push`, opening a PR, replying to a PR, and pushing a tag require explicit user instruction in the current turn. Prior permission in an earlier turn does not carry over. Once authorized, commit messages and PR descriptions must never contain sensitive data or AI co-author signatures.
2. **Verify `git status` before committing**: Confirm that no temporary files, credentials, or `.DS_Store` artifacts are staged by mistake.
3. **Cleanup is never implicitly authorized by any instruction verb**: Instructions to "update", "fix", or "implement" never authorize deleting existing data; cleanup requires separate, explicit instruction.
4. **Never use `rm -rf`**: On macOS, move files to Trash via `/usr/bin/trash <path>`; on other platforms, use the platform's recoverable deletion mechanism or move files to a temporary quarantine directory.
5. **External system records only undergo reversible state transitions**: Retain all test data and external records by default for inspection; when explicitly instructed to clean up, verify record state first, use only the target system's void, cancel, or deactivate transitions rather than hard deletion, and touch only records created during the current session.
6. **Deliverables must never expose sensitive values or local absolute paths**: Replace real credentials, internal hostnames, real ticket IDs, and local paths such as `/Users/<user>/...` with semantic placeholders or repository-relative paths.
7. **`stdout` is reserved exclusively for protocol traffic in Stdio mode**: Server code must never call bare `print()`; route all diagnostic output to `sys.stderr`.
8. **Co-locate every claim with its evidence**: Whenever reporting "fixed", "completed", "verified", or "working", attach the verbatim tool output, read-back result, screenshot path, or verification output in the same place. Never claim completion before obtaining evidence.
9. **Capability status allows only two valid states**: Record only `Verified` or `Known Unsupported`; never leave ambiguous states such as `Untested` or `TBD`. If verification is blocked, state the exact blocking condition.
10. **Never unilaterally break or retain compatibility**: Retiring published packages, live services, external interfaces, or passing deployment pipelines is the user's decision; when an obsolete path should be retired, open a work item to propose it rather than removing it in passing.

## Governance Model: Six Actions

Governance regulates **where failures occur**. Every task progresses through six sequential actions, each with explicit entry preconditions and exit postconditions, while the rules act as guardrails preventing failure spillover.

When advancing a task, identify which action you are currently performing to focus on its corresponding failure modes and governing rules:

| Action | Failure Mode | Applicable Rules |
| --- | --- | --- |
| Judge | Filling verifiable gaps with guesswork; modifying architecture or rules without first reading the project's `decisions.md` to check rejected alternatives; or pushing already-settled decisions back onto the user | [Core Rule 01](references/core-rules/01-judgement-responsibility.md), [Core Rule 08](references/core-rules/08-honesty-and-evidence.md), [Core Rule 09](references/core-rules/09-deliverable-hygiene.md) |
| Authorize | Editing files when the verb is "review"; answering beyond the scope of what was asked | [Core Rule 02](references/core-rules/02-authorization-boundary.md) |
| Define | Modifying files before creating a work item; waiting until after seeing results to define acceptance criteria | [Core Rule 03](references/core-rules/03-task-ticket-discipline.md), [Core Rule 04](references/core-rules/04-delegation-contract.md) |
| Execute | Building premature abstractions; unilaterally removing active compatibility layers; speculating schema definitions from memory | [Core Rule 06](references/core-rules/06-implementation-restraint.md), [Core Rule 07](references/core-rules/07-protocol-tool-hygiene.md) |
| Collect Evidence | Trusting an uncalibrated verification script; verifying via a shortcut that bypasses the user's actual toolchain | [Core Rule 02](references/core-rules/02-authorization-boundary.md), [Core Rule 08](references/core-rules/08-honesty-and-evidence.md), [Core Rule 09](references/core-rules/09-deliverable-hygiene.md) |
| Report | Making claims without co-located evidence; summarizing away failures | [Core Rule 08](references/core-rules/08-honesty-and-evidence.md) |

[Core Rule 02](references/core-rules/02-authorization-boundary.md) and [Core Rule 08](references/core-rules/08-honesty-and-evidence.md) guard against the two highest-frequency failures: acting beyond authorized scope and making unsubstantiated claims.

## Methods

Declare the execution method in the work item based on the nature of the task; write `N/A` for straightforward fixes or minor documentation edits. Consult [references/methods/](references/methods/) when specific method guardrails apply:

- **Test-First**: See [test-first.md](references/methods/test-first.md). Select the test level (unit test vs. acceptance test) based on the change target, and verify that the red test fails on a behavioral assertion rather than a broken connection or import error.
- **Brainstorm and Plan**: See [brainstorm-and-plan.md](references/methods/brainstorm-and-plan.md). For architectural changes or complex refactors, analyze the problem and output a plan before touching code, then pause for user approval.
- **Research**: Use when the deliverable is an analytical report without code implementation. No separate method file is needed; see [04-delegation-contract.md](references/core-rules/04-delegation-contract.md) for acceptance criteria—verify structural completeness, source attribution, and supporting evidence rather than test suite status.
- **External Standard Methodologies**: Reference established methods such as BDD or SDD directly by name in the work item without restating their public definitions.

## Assets

Located under [assets/](assets/), providing canonical structures for task deliverables:

- **Creating a Work Item**: Copy [task-template.md](assets/task-template.md) to `docs/tasks/TASK-YYYYMMDD-HHMMSS-<rr>-<slug>.md` to bound scope, constraints, and verifiable acceptance criteria before modifying files. Generate the ID via `python3 -c "import time,secrets; print(time.strftime('TASK-%Y%m%d-%H%M%S-') + secrets.token_hex(1))"`.
- **Architecture Decision Records**: Copy [decision-template.md](assets/decision-template.md) to `docs/decisions/decisions.md` (or the project's designated ADR file such as `.agent/decisions.md` or `.claude/decisions.md`) to record decisions affecting architecture, compatibility, or external contracts.
- **Project Harness Source of Truth**: Copy [agents-template.md](assets/agents-template.md) to the project root as `AGENTS.md`, following the layout in [Core Rule 10](references/core-rules/10-harness-doc-layout.md) to fill in project positioning and custom rules.

## Structure Check

Run after modifying any Skill or Harness entrypoint file and before reporting completion:

```bash
python3 scripts/check_skill_spec.py <project-path>
# Option: --json outputs structured JSON results
```

Requires only the Python 3 standard library with no external dependencies. Exit code `0` indicates all checks passed, `1` indicates structural defects, and `2` indicates an execution error. Validates deterministic structural invariants: YAML frontmatter completeness, `name` formatting, absence of angle-bracket tags, absence of `README.md` or symbolic links inside a Skill directory, absence of frontmatter in subdirectory files, relative link resolution, and platform pointer integrity (such as `CLAUDE.md` with `@AGENTS.md` only).
