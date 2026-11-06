# Test-First

The red-green-refactor cycle follows the standard definition of Test-Driven Development (TDD) and is not restated here. Apply it when writing or modifying code logic, configuration, or service wiring; this file records only the two deltas where agents repeatedly fail in practice.

## The Target of the Change Determines the Test Level

"Test" does not mean "unit test." Picking the wrong test level makes test-first appear unexecutable for infrastructure or wiring tasks, causing the agent to skip testing altogether.

| Target of Change | Test Level | Subject of Assertion |
| --- | --- | --- |
| Code logic, data transformations, algorithms | Unit test, isolating external dependencies | Input maps to the expected output |
| External interfaces, service wiring, container/proxy config, deployment manifests | Acceptance test, sending requests to the live running target | Observable external behavior and exposed surface |

Both levels can work together: define the target behavior with a failing acceptance test first, drive internal logic with unit tests, and watch the acceptance test turn green once wiring is complete.

**When a change has no unit-testable surface, drive it with an acceptance test alone.** Container definitions, reverse-proxy rules, and deployment scripts assert behavior on the running service, not the return value of a function. Never write trivial mock-heavy unit tests just to check a box—doing so renders a green test suite meaningless.

## The Red Test Must Fail for the Right Reason

An acceptance test against a service that has not started will always fail, but "Connection Refused" and "Response Payload Mismatch" are two completely different red states. The former only proves the service is down; only the latter proves the assertion is actually inspecting behavior.

After the target service is up and wired, verify that the test fails at least once due to an **assertion mismatch** before making it pass, confirming that the test is not a tautology that passes unconditionally.

## Related Rules

When a test fails, paste the verbatim error output into the conversation before fixing it; see [Core Rule 08](../core-rules/08-honesty-and-evidence.md). For recoverable cleanup of temporary test files and retention of external test records, see [Core Rule 05](../core-rules/05-execution-safety.md). For decidability of acceptance criteria, see [Core Rule 04](../core-rules/04-delegation-contract.md).
