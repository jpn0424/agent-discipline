# Core Rule 09: Deliverable Hygiene & Architecture Decisions

## Why This Rule Exists (Why)
Shipping code or documentation packages that contain local absolute paths like `/Users/<user>/...` or internal developer jargon leaks host topology and signals draft-quality work.
Meanwhile, leaving architectural decisions unrecorded causes future contributors or agents to unknowingly re-introduce designs that were already evaluated and rejected.
Because both failures happen when the author is focused on implementation details rather than final presentation, pre-delivery verification requires an independent scan rather than relying on author memory alone.

---

## How to Execute (How)

### 1. Deliverable Hygiene
> [!IMPORTANT]
> **Hard constraint:** Zero discretion.

**Artifacts and deliverables are not synonyms.** Artifacts encompass everything produced during work—including work items, ADRs, and internal harness notes—whereas deliverables are the specific subset handed over to and accepted by an external recipient or published repository. This section governs deliverables.

- **Eliminate Local Absolute Paths and Secrets**: Deliverables must never contain local absolute paths such as `/Users/<user>/...`, `/home/<user>/...`, or `C:\Users\<user>\...`, nor any real credentials or internal hostnames; replace them with relative paths or semantic placeholders (`<SERVICE_BASE_URL>`, `<API_KEY>`).
- **Language and Terminology Standard**: Write in clear, direct standard English (`en-US`); preserve canonical technical identifiers and protocol names verbatim (such as `Git`, `OpenAPI`, `JSON-RPC`, `Payload`, `Schema`).
- **No Pseudo-Legal or Archaic Adverbs**: Write in plain modern technical prose; do not use archaic or legalese particles (`heretofore`, `thereof`, `wherein`, `therein`, `vis-à-vis`, `aforementioned`, `henceforth`) where direct determiners or prepositions (`its`, `in which`, `about`, `this`) suffice. Mixing registers forces the reader to parse stylistic ornament instead of operational rules.
- **Parentheses Reserved for Acronym Definitions and Symbols**: If a point requires explanation, write it as a full sentence in the body; if a term is ambiguous, replace it with an exact term. Stuffing causal explanations or backstory into parentheses fractures the main clause—see `B2 Parenthetical Gloss` in `deliverable-writing-audit`.

> [!NOTE]
> The hard constraint tag in this section applies strictly to the first bullet (credentials and local paths). **Language and register rules are criteria**—violating them does not cause irreversible damage or harm third parties. They sit in the same section for topical grouping, not equal deontic force; when a target project defines its own language conventions, the project's conventions take precedence.

### 2. Nygard ADR Records (`decisions.md`)

The criterion is **"if someone overturns this decision later, will they need to know why we chose this boundary and why the alternatives failed?"** If yes, record it in the project's decision log using the Nygard ADR format; if no, recording it in the work item is sufficient. When initializing a decision log for the first time, copy [assets/decision-template.md](../../assets/decision-template.md) to `docs/decisions/decisions.md` (or the project's established path). Each ADR entry contains three sections—`Context`, `Decision`, and `Consequences`—and the `Decision` section must record **both the chosen option and the rejected options with their rejection reasons**.

Treat recorded ADRs as append-only: to overturn a prior decision, append a new ADR entry and mark the old entry `Superseded by AD-xxxx` rather than editing historical rationale in place. Before modifying architecture, governance rules, or directory layout in a project that maintains a `decisions.md`, read the existing entries first so you do not re-propose a previously rejected design.

### 3. Pre-Delivery Writing Audit Gate

The criterion is **"will other files, agents, or humans cite this text as a reference?"** Harness files, Skill specifications, work items, ADRs, deliverables, commit messages, and PR descriptions all qualify—confirm their delivery profile before writing, and scan them after writing before reporting completion.

- **Before writing**: Identify which delivery profile applies (`harness`, `agent-facing`, `deliverable`, `ticket`, `changelog`, or `pr-commit`), as tolerance levels vary by profile.
- **After writing, before reporting**: Run `deliverable-writing-audit` in `detect` mode across every modified file. If the project includes `detect.py`, execute it and include the result in your verification output.
- **A hit is not automatically an error**: Check each hit against the `Exceptions` field in `pattern-catalog.md`, and note in your report why any kept hit is a valid exception.
- **Exit code `0` from the script is not a full pass**: `detect.py` only catches surface mechanical shapes. Semantic symptoms—such as `B4 Heading Echo`, `C2 Unstructured Prose for Enumerable Facts`, or `C4 Scattered Duplicate Rules` (when paraphrased)—require reading the text paragraph by paragraph against `pattern-catalog.md`. Treating a green script exit code as proof of semantic quality confuses the instrument's reach with reality; see [Core Rule 08](08-honesty-and-evidence.md).

**Why audit before delivery rather than after user correction**: Most writing defects happen not because the author is unaware of the rules, but because attention is consumed by code logic during drafting. Once a flawed specification is delivered, downstream files cite it, multiplying the cost of a single fix.

**Division of labor**: This rule defines **when** the writing audit must run. Symptom definitions, severity tiers, the profile tolerance matrix, and editor preservation constraints are defined exclusively in `deliverable-writing-audit`.

---

## Gotchas

From real failures, not derived rules.

### A File Loaded by an Agent Is Not Your Personal Scratchpad

**When it happens**: While drafting a file intended for an agent to load at runtime, you include the intermediate trade-offs you weighed, exceptions you hit during debugging, or historical notes on how the rule evolved.

**Why it goes unnoticed**: Because you just walked through that reasoning, the backstory feels like the central thread rather than noise. Only when a fresh agent loads the file without conversational context does it become clear that the directive is buried under historical commentary—and an executing agent treats every sentence in its prompt as an active instruction.

**Criterion**: Every sentence in an agent-loaded file must answer **"what should the reader do right now?"** Delete any sentence that cannot answer that question, and move historical rationale into a work item or `decisions.md`.

### Parenthetical Glosses Are Where Unplaced Context Leaks Out

**When it happens**: After writing a rule sentence, you worry the reader might not understand the rationale or edge case, so you tack on a parenthetical remark `(because previously...)` or `(note that...)`.

**Why it goes unnoticed**: Each parenthetical remark looks helpful in isolation. The damage accumulates through density: the main clauses fracture into two parallel tracks, forcing the reader to constantly filter primary rules from side commentary.

**Criterion**: Reserve parentheses strictly for acronym introductions and symbolic notation. If a point matters enough to state, make it a standalone sentence or a dedicated table column; otherwise delete it.

### Pre-Delivery Auditing Covers Commit Messages and PR Descriptions

**When it happens**: You carefully audit the repository's Markdown files, then hastily generate the commit message or PR description at the very end of the task.

**Why it goes unnoticed**: Commit messages and PR descriptions often sit outside the author's mental category of "documentation," and are written when attention has already shifted to wrapping up. Most accidental leaks of internal hostnames and AI attribution signatures happen right here.

**Criterion**: Apply the exact same pre-delivery audit gate (`pr-commit` profile) to commit messages and PR descriptions—scanning for credentials, internal identifiers, and AI attribution signatures before submitting.
