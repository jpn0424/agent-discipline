# Pattern Catalog

## Contents

Contains 28 writing symptoms across four groups. Every entry specifies six fields: **Symptom**, **Why**, **Fix**, **Exceptions**, **Evidence**, and **Detection**.

| Group | Tier & Severity | Entries |
| --- | --- | --- |
| A. Security and Credibility | Tier 1A, P0 | A1 Secret and Credential Leakage / A2 AI Attribution Signature / A3 Unverified Success Claim / A4 Residual Unverified Status / A5 Local Absolute Path |
| B. Formal Noise | Tier 1B, P1 | B1 Change Narration and Before/After Comparison / B2 Parenthetical Gloss / B3 Residual Note-to-Self / B4 Heading Echo / B5 Self-Describing Metadiscourse / B6 Heading-Scope Mismatch |
| C. Semantic Comprehension | Tier 2, P1 | C1 Unevidenced Capability Limitation Claim / C2 Unstructured Prose for Enumerable Facts / C3 Revived Retired Terminology / C4 Scattered Duplicate Rules / C5 Summarized Away Verbatim Error / C6 Speculative Filling / C7 Developer Jargon Leaked into Deliverables / C8 Project-Specific Facts Leaked into Shared Rules / C9 Navigation Carrying Target Content / C10 Cross-File Inconsistency / C11 Multiple Terms for One Concept / C12 Tautological and Non-Operational Definitions / C13 Deontic Modality Confusion |
| D. Density and Formatting | Tier 3, P2 | D1 Vague Quantifiers and Filler Words / D2 Emoji Density / D3 Period Inside Bold List Label / D4 Excessive Domain Implementation Detail (`pr-commit` profile only) |

Two additional sections follow Group D: `"When to Rewrite the Entire Document Instead of Patching"` defines the three-condition criterion for full document reconstruction; `"Self-Reference Exemption"` exempts quoted negative examples within this Skill from triggering self-audit flags.

---

Every symptom in this catalog originated from real corrections. The **Evidence** field records the evidence category and the underlying failure pattern—what went wrong in the text at the time and what misjudgement or information loss it caused the reader:

- **Post-hoc correction**: The defect was written into a document and explicitly corrected by the user afterward. This is the strongest form of evidence.
- **Pre-emptive guardrail**: The user repeatedly wrote an explicit prohibition into task prompts before delegating work. Repeated pre-emptive defense proves the failure recurs without a standing guardrail.
- **External research**: Published empirical findings. Entries cite the source and measured subject while explicitly stating the **Gap** between the external study and this context—external studies rarely measure document prose directly, so applying them without noting the gap would be extrapolation.

The **Detection** field specifies whether the symptom is matched mechanically by `scripts/detect.py` or requires semantic judgement by the Agent. Full mapping details reside in [category-map.md](category-map.md). Theoretical alignments across the five foundational pillars (Gricean maxims, Controlled Natural Language, operational definitions, deontic logic, and Information Mapping) reside in [methodology-grounding.md](methodology-grounding.md).

> [!NOTE]
> **The Evidence field records the structural failure pattern, never verbatim user quotes.** A single correction is one surface instance of an underlying failure mode; the rule exists to prevent the failure mode itself. Personal names, accounts, project names, repo names, decision IDs, work item IDs, and specific internal tool names are strictly omitted.

---

## A. Security and Credibility (Tier 1A — Flag on Sight, P0)

A hit in this band is a delivery defect that compromises security or invalidates trust in the document.

### A1. Secret and Credential Leakage

**Symptom**: Deliverable text contains real credentials, passwords, tokens, internal hostnames, internal account names, real order numbers, tax IDs, vendor codes, or GUIDs. Also includes dumping `.env` contents via `cat`, `grep`, `echo`, or `print` into tool output or transcripts.

**Why**: Deliverables are pushed to remote repositories or handed to third parties. Once a secret enters git history, revoking the commit does not guarantee removal.

**Fix**: Replace every real value with a semantic placeholder (`C0000001`, `PO000000001`, `<SERVICE_BASE_URL>`, `<PASSWORD>`). When verifying that an environment variable exists, check only for key presence without printing its value.

**Exceptions**: None. This symptom has zero exceptions.

**Evidence**: Pre-emptive guardrail recurring across multiple projects, plus one post-hoc correction. The failure has two entry points. First, real business identifiers and internal hostnames were pasted as format examples in deliverables and commit messages. Second, a delegated agent ran a text search across an environment file to verify configuration, dumping live credentials into the conversation transcript.

**Detection**: Mechanical (pattern shape) + Semantic judgement (whether the value is live). Because internal hostname detection matches domain structure rather than consulting an external DNS directory, the script tags hostname hits as `[borderline]`: they are filtered out under `Strict` and `Relaxed` profiles and surface only under `Extra-strict`, where a human or agent verifies whether the domain is public.

### A2. AI Attribution Signature

**Symptom**: Deliverables, commit messages, or PR descriptions contain platform attribution signatures such as `"provide by Claude"`, `"Generated with Claude"`, `"Generated with Gemini"`, `"Co-Authored-By: GitHub Copilot"`, or `"🤖 Generated with"`.

**Why**: Engineering deliverables and internal repository records must not advertise the authoring tool.

**Fix**: Delete the entire attribution line or block; do not paraphrase it.

**Exceptions**: Citing an external repository, project, or author when documenting the provenance of a tool or methodology is a citation, not an attribution signature.

**Evidence**: Post-hoc correction, twice. Tools automatically appended attribution footers to deliverables and pull requests that the human author had neither written nor reviewed, causing the transmitted artifact to diverge from the reviewed text.

**Detection**: Mechanical.

### A3. Unverified Success Claim

**Symptom**: A document or report claims `"Fixed"`, `"Completed"`, `"Verified"`, or `"Working"`, but provides no corresponding evidence in the same document—no verbatim error output, no read-back payload, no screenshot, and no completed verification section in the work item. Also includes treating tool responses containing ⚠️ or ❌ as successes.

**Why**: This is the highest-cost symptom in the catalog. When a user proceeds on the basis of a false `"Fixed"` claim, the underlying defect surfaces later in a harder-to-diagnose state, and every subsequent completion claim loses credibility.

**Fix**: Downgrade the claim to the actual verified state, and either attach the verification evidence or state explicitly which precondition is missing to run verification. The claim and its evidence must be inspectable together.

**Exceptions**: None.

**Evidence**: Post-hoc correction that became a permanent architecture decision, reinforced by recurring pre-emptive guardrails. The failure occurred when verification took a shortcut: calling an internal helper succeeded, so the task was reported as fixed while the actual user-facing execution path still failed three consecutive independent verifications. Two related entry points are misreading warning/error glyphs in tool responses as success, and reporting overall completion when sub-items remain unfinished.

**Contrast**: Writing `"Fixed, all tests pass"` without any test output in the document is a hit. Writing `"Fixed; pytest -q reports 12 passed, output attached in the block below"` is not a hit because the evidence accompanies the claim.

**Detection**: Semantic judgement.

### A4. Residual Unverified Status

**Symptom**: Capability tables or status fields retain markers such as `"untested"`, `"unverified"`, `"to be confirmed"`, `"status unknown"`, `"assumed supported"`, `"not sure"`, `"TBD"`, or `"?"`.

**Why**: A capability claim has only two valid states in a deliverable specification: verified working or verified unsupported. Leaving an unknown marker shifts the verification burden onto the reader, and subsequent maintainers cannot tell whether the capability was never tested or could not be tested.

**Fix**: Run the verification immediately. If verification is genuinely blocked, document the exact blocker and missing precondition rather than leaving an ambiguous status token.

**Exceptions**: The `"Verification Results"` section of an active work item may remain `"Pending"` or `"In Progress"` while the work item is still open—that tracks workflow state rather than asserting system capability.

**Evidence**: Strongly worded post-hoc correction that became a standing project constraint. The status column drifted out of sync with established facts: elsewhere in the same document multiple successful runs were already recorded, yet the capability matrix still read `"untested"`, leaving the reader with two contradictory claims when live verification was immediately available.

**Detection**: Mechanical.

### A5. Local Absolute Path

**Symptom**: Distributed or delivered files contain `/Users/<user>/...`, `C:\Users\<user>\...`, or `/home/<user>/...` with a concrete username.

**Why**: Another machine or user environment will not share the author's local directory tree. Once a Skill is installed into another repository, hardcoded local paths break and leak the author's filesystem layout.

**Fix**: Convert to a repository-relative path or describe the location structurally (`"under docs/tasks/ at the repository root"`), unless an official platform specification mandates a fixed path.

**Exceptions**: `Relaxed` under `harness` and `ticket` profiles—developer-facing governance files pointing to an external local repository as a Single Source of Truth are legitimate. Zero exceptions under `agent-facing` and `deliverable`.

**Evidence**: Post-hoc correction, twice. Specifications referenced files using the author's machine-specific path prefix, which broke immediately when read by another developer or agent on a different host.

**Detection**: Mechanical.

---

## B. Formal Noise (Tier 1B — Flag on Sight, P1)

Fixing these makes the document cleaner to read, but **a hit does not mean the content is factually wrong** and does not constitute evidence that the document is untrustworthy. In `detect` mode, list Tier 1B separately from Tier 1A.

### B1. Change Narration and Before/After Comparison

**Symptom**: Normative specification prose narrates how the rule evolved rather than stating what holds now. Typical phrases: `"Originally X, changed to Y"`, `"Previously used X, now uses Y"`, `"In this update..."`, `"Has been deprecated..."`, `"We later found..."`, `"After round two of fixes..."`, `"Because it previously..."`.

**Why**: The reader receives an archaeological log instead of a specification. They must parse obsolete history before discovering what to do today, and every revision bloats the file with historical sediment instead of keeping it current.

**Fix**: State only what holds today. Change history belongs in work items, `decisions.md`, or commit messages. If an obsolete approach must be mentioned to prevent regression, write it as a direct present-tense prohibition (`"Never use X"`), not a historical narrative.

**Exceptions**: `Relaxed` under `ticket` and `pr-commit`; `Skip` under `changelog`—recording what changed is the core purpose of work items, PRs, and changelogs.

**Evidence**: Post-hoc correction—the single highest-frequency symptom in this catalog. Every time a specification was updated, the author left the story of the update and the previous behavior inside the normative body, turning the specification into a cumulative diff log after a few iterations.

**Detection**: Mechanical (phrase matching) + Semantic judgement (whether a prohibition is necessary).

### B2. Parenthetical Gloss

**Symptom**: Using parentheses `(...)` to tuck in causal explanations, historical backstory, side notes, or self-justification. For example: `"All configuration is injected via environment variables (previously hardcoded in config files, which we removed because deployments kept overwriting them)."`.

**Why**: Parenthetical glosses usually capture the author's stream of consciousness rather than structured information for the reader. Splitting a sentence into a main clause and a parenthetical aside forces the reader to parse two tracks at once. If a point matters, state it in a main clause; if it is a recurring attribute, give it a dedicated table column.

**Fix**: Handle parenthetical content in one of three ways: delete it, promote it to a standalone sentence, or extract it into a dedicated table column.

**Exceptions**: Standard acronym introductions on first use (`"Controlled Natural Language (CNL)"`), bilingual term alignments, unit symbols, and verbatim quoted text. Those are notation, not narrative asides.

**Evidence**: Post-hoc correction, recurring across multiple sessions. Two failure modes appeared: stuffing historical rationale for retired approaches inside parentheses in the middle of a rule, and hiding structured attributes inside parenthetical notes within table cells where they could not be scanned across rows.

**Detection**: Mechanical (parentheses containing explanatory or causal gloss markers) + Semantic judgement (distinguishing acronym/term notation).

### B3. Residual Note-to-Self

**Symptom**: Leaving draft markers such as `TODO`, `FIXME`, `XXX`, `HACK`, `"fill in later"`, `"for now just"`, `"I guess"`, `"fix later"`, or `"???"` inside a deliverable document.

**Why**: These are scratchpad markers from the drafting process. Leaving them in a deliverable makes it impossible for the reader or agent to tell whether the item is still unfinished or was finished without cleaning up the note.

**Fix**: Resolve the item immediately, or open a tracked work item under work item discipline and state the known limitation explicitly in the specification. Never leave informal deferred notes in deliverables.

**Exceptions**: `Relaxed` under `ticket`—recording pending tasks is the purpose of a work item's checklist.

**Evidence**: Post-hoc correction and pre-emptive guardrail. Authors treated agent-facing instruction files as personal scratchpads, leaving open questions and reminders inline where executing agents could not distinguish authoritative directives from author notes-to-self.

**Detection**: Mechanical.

### B4. Heading Echo

**Symptom**: The first sentence beneath a heading merely paraphrases the heading before the real content begins. For example, following `## Performance` with `"Performance is a critical aspect of the system."`

**Why**: The heading already established the topic. An echo consumes the highest-attention position in the section while conveying zero information.

**Fix**: Delete the echo line and open directly with the substantive point.

**Exceptions**: None, though severity is P2.

**Evidence**: Post-hoc correction. The opening paragraph of a specification spent its first lines restating the title and explaining how the file was generated rather than stating what the specification governs, depriving the reader of an immediate scope signal.

**Contrast**: Following `## Performance` with `"Performance is important."` is a hit; following it with `"Queries degrade above 200 rows; thresholds and measurement commands follow."` is not a hit because it states the concrete problem governed by the section.

**Detection**: Semantic judgement.

### B5. Self-Describing Metadiscourse

**Symptom**: Sentences whose grammatical subject is the document or section itself rather than the domain rule or action. Typical phrasing: `"This section only does two things"`, `"The following paragraphs will explain"`, `"This section does not repeat"`, `"The three groups below exhaustively list every item"`, and introductory roadmaps that narrate the section layout.

**Why**: The document's structure is already visible through its headings, lists, and tables. Describing that structure in prose consumes space for zero informational gain, and encourages further metadiscourse every time a section is added.

**Fix**: Delete the metadiscourse. Use the opening line to state the section's decision criterion or begin directly with the rules.

**Exceptions**: **Scope boundary declarations are exempt.** A statement such as `"Shared workflow skeleton resides in the main entrypoint; this file specifies only the delta unique to this method"` tells the reader where out-of-scope content lives. Without it, a reader would mistake the current file for the complete workflow or duplicate content across both files. The criterion is `"If this sentence is deleted, will the reader misjudge the boundary of this document?"` If yes, it is a boundary declaration—keep it; if no, it is self-describing metadiscourse—delete it.

**Evidence**: Post-hoc correction. Section openings restated structural counts already obvious from the subheadings without stating the section's purpose.

**Contrast**: `"This section does two things: gives the location and adds exceptions"` is a hit—deleting it causes zero scope confusion. `"Shared workflow skeleton resides in the main entrypoint; this file specifies only the delta"` is not a hit—deleting it misleads the reader into thinking this file is self-contained.

**Detection**: Semantic judgement.

### B6. Heading-Scope Mismatch

**Symptom**: Two forms. First, **a single heading houses multiple distinct topics** without subheadings to separate them, leaving the reader unable to predict what follows. Second, **the heading label does not match the extension of its body text**, promising either a narrower or a broader scope than what is actually written.

**Why**: Headings are the landmarks readers and agents use to decide whether to read a section and how to link back to a specific rule later. When multiple topics hide under one heading, none of them can be referenced individually, forcing other documents to restate the rule inline and spawning duplicates (`C4`).

**Fix**: Count the distinct topics inside the section. If there is more than one, split them under dedicated headings; if the heading title fails to name the topic, rename the heading. **The criterion is the number of topics, not the number of paragraphs**—an abstract is one paragraph, whereas a rationale section spanning three paragraphs about the same mechanism is still a single topic.

**Exceptions**: `Skip` under `changelog`.

**Evidence**: Post-hoc correction. A section titled `"Abstract"` contained four paragraphs covering four distinct topics: what the Skill governs, which invariants it protects, why governance does not dictate execution methods, and how the two modal rule strengths differ. The heading promised a high-level summary while the body buried three standalone normative rules that needed independent citation.

**Contrast**: Placing scope overview, system invariants, and modal strength definitions all under `## Abstract` is a hit because modal strength definitions are not part of an abstract. Placing precedence clues, six-profile differences, and fallback behavior under `## Profile Determination and Tolerance` is not a hit because all three paragraphs address facets of the same decision.

**Detection**: Semantic judgement.

---

## C. Semantic Comprehension (Tier 2 — Flag in Clusters, P1)

A single isolated subtlety may be benign; two or more in the same paragraph or section indicate that the passage must be rewritten.

### C1. Unevidenced Capability Limitation Claim

**Symptom**: Writing `"cannot"`, `"unsupported"`, `"only possible via"`, or `"unable to"` without pointing to evidence—no exhaustive test of relevant operations, no verbatim error output, and no work item ID. The most severe form is **misdescribing an already-succeeded operation as a limitation**.

**Why**: An unevidenced limitation claim gets cited downstream as an established architectural constraint, distorting design decisions across other documents—when in reality the author simply did not test the right operation.

**Fix**: Before writing `"cannot"`, test every relevant operation against the live system or schema. If the limitation is real, attach the verbatim error and identify the exact layer that rejected it (schema unreadable / candidate lookup missing / blocked by required field). Capabilities that already succeeded must be documented positively as working; gaps in downstream steps must be described separately without negating the capability that succeeded.

**Exceptions**: `Relaxed` under `changelog`; `Skip` under `pr-commit`.

**Evidence**: Strongly worded post-hoc correction that became a permanent project constraint. Two failure modes occurred: first, an operation succeeded and satisfied the immediate requirement, yet the author documented the feature as unsupported because a subsequent optional step had a gap; second, the author declared a capability impossible without checking existing tools in the workspace.

**Contrast**: Writing `"This API does not support batch writes"` without stating what was tested is a hit. Writing `"The batch endpoint returns HTTP 405; single-record writes succeed; verbatim error attached below"` is not a hit because it cites evidence and preserves what works.

**Detection**: Semantic judgement. The script flags lines containing limitation phrases without inline evidence markers for human review, but cannot judge whether the evidence is sufficient.

### C2. Unstructured Prose for Enumerable Facts

**Symptom**: Capabilities, limitations, multi-stage workflows, or field specifications—items that are inherently enumerable—are compressed into a continuous prose paragraph. For example: `"After creation the API does not return the field section, field-by-field read-back fails for these two types, and only summary queries return partial fields"`, forcing the reader to mentally untangle what works at each stage.

**Why**: Readers consult capability documentation to compare what works and what does not across stages or types. A prose paragraph forces every reader to reconstruct the state matrix in their head, introducing interpretation errors.

**Fix**: Decompose by stage or entity type. Identify the distinct phases or categories first, then tabulate what is supported and unsupported at each stage using ✅ / ⚠️ / ❌ status glyphs in aligned table columns.

**Exceptions**: Paragraphs explaining **why** a design choice was made belong in prose. The criterion is `"Is this passage enumerating parallel items or states?"`

**Evidence**: Post-hoc correction that required two revisions before the user supplied the target table layout directly. A multi-stage operation had different support levels at each stage, but was written as a single dense paragraph with caveats mixed inline.

**Contrast**: Packing read/write support differences across three field types into one running sentence is a hit. Presenting a three-column table (`Field Type`, `Readable`, `Writable`) is not a hit.

**Detection**: Semantic judgement.

### C3. Revived Retired Terminology

**Symptom**: A document uses terminology that the project has explicitly retired, or implies that a retired mechanism remains an optional fallback.

**Why**: Retiring a mechanism means that option no longer exists, not that it is merely discouraged. Leaving retired terms in active specifications invites the next agent or maintainer to revive the dead path as a fallback.

**Fix**: Rewrite the sentence to state only the current canonical mechanism. Evaluate whether even negative mentions (`"We no longer use X"`) are necessary—if not required to prevent an active regression trap, remove the mention entirely.

**Exceptions**: `Relaxed` under `ticket` and `pr-commit`; `Skip` under `changelog`—historical records may explain why a term or mechanism was retired.

**Evidence**: Post-hoc correction across multiple cleanup rounds. Even after a mechanism was officially retired, residual mentions across reference files made it read like a valid secondary option, requiring repeated sweeps to eradicate.

**Detection**: Mechanical via `--terms <file>` supplying the project's retired terminology list.

### C4. Scattered Duplicate Rules

**Symptom**: The substance of a single rule appears in two or more files instead of being defined in one canonical source and linked from elsewhere. **Both verbatim copies and paraphrased restatements count**—rewording a duplicate does not make it a distinct rule; it only makes divergence harder to spot.

**Why**: Two copies of a rule inevitably drift out of sync, causing different agents to follow conflicting instructions depending on which file they loaded. In repository audits, this is the single most common structural defect.

**Fix**: Determine which architectural layer owns the rule, keep the canonical text in that single file, and replace every other occurrence with a markdown link.

**Exceptions**: `Skip` under `ticket`, `changelog`, and `pr-commit`.

**Evidence**: Post-hoc correction. The same constraint was copied across multiple files without designating a single canonical source. Remediating it required inventorying every occurrence and deciding its proper layer before deleting duplicates, lest the surviving copy remain in the wrong file.

**Detection**: Mechanical (exact cross-file duplicate lines via `scan_duplicates`) + Semantic judgement (paraphrased duplicates and canonical layer ownership).

### C5. Summarized Away Verbatim Error

**Symptom**: A report or work item states `"The tool returned an error"` or `"The server rejected the request"` without quoting the verbatim error message.

**Why**: Verbatim error output is the primary observational evidence for debugging. Summarizing an error strips away status codes, field names, and stack context, taking diagnostic judgement away from the user.

**Fix**: Paste the verbatim error message and identify the exact layer where the failure occurred.

**Exceptions**: When the raw error contains live secrets, mask only the secret substrings with semantic placeholders (`<PASSWORD>`, `<TOKEN>`) and preserve the rest verbatim.

**Evidence**: Recurring pre-emptive guardrail. Delegated agents repeatedly paraphrased tool failures and read-back payloads into one-line summaries, forcing the user to mandate verbatim error and field-level read-back pasting in every delegation prompt.

**Contrast**: Writing `"The tool failed, so we switched to an alternative"` is a hit. Writing `"The tool returned ConnectionRefusedError: [Errno 61] Connection refused on port 8080, so we switched to..."` is not a hit.

**Detection**: Semantic judgement.

### C6. Speculative Filling

**Symptom**: A document states field names, button labels, UI control names, status codes, order numbers, or parameter shapes that were never verified against the authoritative source—including plausible-looking keys invented by the author.

**Why**: Speculative identifiers get treated as real contracts by downstream code and fail at runtime. Readers cannot tell from the prose which identifiers were verified against the schema and which were guessed.

**Fix**: Query the authoritative schema source first. If the schema cannot be retrieved, stop and report `"Unable to verify schema"` rather than guessing a plausible identifier.

**Exceptions**: Placeholder values explicitly marked as illustrative format examples that cannot be mistaken for live schema contracts.

**Evidence**: High-frequency pre-emptive guardrail across projects. When an agent could not immediately read a schema, it guessed plausible-looking field names, option codes, or test IDs and proceeded—producing syntactically valid artifacts that failed on execution. This directly maps to Core Rule 07 in `agent-engineering-discipline`.

**Contrast**: Writing an unverified field name from memory as if it were part of the API schema is a hit. Writing `"Field name unverified; blocked pending schema access"` is not a hit because the unknown is explicitly surfaced.

**Detection**: Semantic judgement.

### C7. Developer Jargon Leaked into Deliverables

**Symptom**: Deliverables intended for end users or business-domain agents contain internal harness maintenance metadata—decision IDs (`AD-00xx`, `HD-00xx`), work item IDs (`TASK-...`), sync statuses, `.claude/`, `.agents/`, `Harness`, local machine aliases, or internal validator names.

**Why**: End users and domain-execution agents lack the repository governance context. To a business agent, internal governance IDs are noise that dilutes domain instructions and guardrails.

**Fix**: Replace internal jargon with formal domain descriptions or delete it outright. Keep governance metadata inside `decisions.md` and `docs/tasks/`.

**Exceptions**: `Skip` under `harness` and `ticket`—developer-facing governance specifications and work items legitimately cite decision and work item IDs.

**Evidence**: Pre-emptive guardrail that became a standing project constraint. Authors mixed domain execution instructions for business agents with internal maintenance notes about how the Skill itself was refactored, cluttering the executing agent's context window.

**Detection**: Mechanical (jargon token matching) + Semantic judgement (whether a citation is legitimate in context).

### C8. Project-Specific Facts Leaked into Shared Rules

**Symptom**: A general specification intended for reuse across multiple repositories contains identifiers that exist only inside one specific project—internal tool names, API endpoints, custom status enums, database column names, business domain nouns, specific agent platform CLI names, project names, repo names, decision IDs, or work item IDs.

**Why**: General rules are typically distilled from a concrete debugging session in a specific project. When the source project's tool name or status enum slips into the distilled rule, the rule looks concrete and authoritative in its home repo but becomes unexecutable the moment the Skill is installed into another project that lacks that tool. Over-specific leakage is harder to spot than vague prose because it masquerades as fact-based writing.

**Fix**: Replace the project-specific identifier with its structural role and state the decision criterion. Change `"Call get_order_schema first"` to `"Query the authoritative schema source first"`, then define what qualifies as an authoritative source. Change `"Only use the Cancel status"` to `"Only use a reversible state transition provided by the target system"`.

**Exceptions**: Public standards and universal specifications may be named directly because they are invariant across projects (`OpenAPI`, `JSON Schema`, `JSON-RPC`, `git`, `Nygard ADR`, `YAML Frontmatter`). Illustrative identifiers inside `assets/` templates are format examples and are exempt.

**Criterion**: The criterion is `"Does this identifier exist in every repository that installs this specification?"` If the answer is no, replace it with its structural role.

**Evidence**: Post-hoc correction. When general engineering rules were extracted from a project session, hardcoded status values, specific CLI tool names, and personal account names rode along into the shared rule files. The normative counterpart is Core Rule 11 in `agent-engineering-discipline`.

**Contrast**: Hardcoding a project-internal status enum in a cross-project rule is a hit. Writing `"the pending-review state defined by the target workflow"` is not a hit.

**Detection**: Semantic judgement.

### C9. Navigation Carrying Target Content

**Symptom**: Cells in an index, directory, or routing table contain a summary of the target file's contents rather than its name, path, and routing scope. The most common form is concatenating all subheadings of the target file into a single table cell.

**Why**: The job of navigation is to help the reader locate the right file, not to replace reading it. Once a content summary is embedded in a routing table, it becomes a second copy of the rule that drifts out of sync when the target file changes, while turning a vertical list of headings into a dense horizontal wall of text.

**Fix**: Give each routing row only the name, link, and a one-line scope boundary stating **when to load the file**, not what rules the file contains inside.

**Exceptions**: `Skip` under `changelog`. A table of contents at the top of a single file that lists only section headings and anchor links is exempt because it contains no duplicate prose.

**Evidence**: Strongly worded post-hoc correction. After a refactoring pass, a routing table concatenated every subheading of each target file into its summary column while repeating cross-mappings already stated in another section—multiplying duplication in the exact refactoring meant to eliminate it.

**Contrast**: Writing `"Fact verification, goal priority over current state, asking when ambiguous, batching questions"` in a routing cell is a hit because it copies the target file's four subheadings. Writing `"Boundary between autonomous judgement and asking the user"` is not a hit because it states the routing scope needed to decide whether to open the file.

**Detection**: Semantic judgement.

### C10. Cross-File Inconsistency

**Symptom**: Two places in the repository make mutually contradictory claims about the same subject. Three forms: direct contradiction (two passages assert opposite rules), indirect contradiction (two passages each look valid in isolation but cannot both hold simultaneously), and contradiction with established domain facts.

**Why**: When two canonical files disagree, neither humans nor agents can tell which one governs. Unlike `C4` (where the same sentence appears twice), `C10` means two sentences actively conflict—`C4` risks future drift, whereas `C10` causes immediate execution errors today.

**Fix**: Determine which file is the Canonical Source (SSOT), update it to the verified rule, and replace the conflicting passage in the other file with a pointer. If both claims are valid under different conditions, make the partitioning condition explicit in the canonical rule rather than leaving the reader to guess.

**Exceptions**: `Relaxed` under `ticket` and `changelog`, which legitimately record before-and-after states across time.

**Evidence**: External research. RFCScope categorized 273 verified technical errata across IETF RFC specifications and found that inconsistency accounted for 202 errata while under-specification accounted for 37—**inconsistency is the dominant defect class in normative specifications**, far outweighing lack of detail. **Gap**: RFCScope measured network protocol RFCs rather than Agent Harness and Skill specifications; we adopt only the structural conclusion that cross-file inconsistency warrants a dedicated catalog entry.

**Detection**: Semantic judgement. The script detects identical duplicate lines (`C4`) but cannot detect semantic contradiction between two differently worded sentences.

### C11. Multiple Terms for One Concept

**Symptom**: Referring to the same entity or concept by two or more different names without declaring them synonymous, or introducing a domain-specific term on first use without defining it.

**Why**: When terminology drifts across paragraphs, the reader must mentally construct an alias table—and their table may not match the author's. Uncontrolled synonyms also break cross-referencing across rules because an agent cannot tell whether Term A in Rule 3 is the same entity as Term B in Rule 9.

**Fix**: Lock a single canonical term per concept (`One Concept, One Term`) and replace every variant across the suite. When an older alias must be mentioned once so existing users can locate it, declare the equivalence at first mention and use only the canonical term thereafter.

**Exceptions**: Verbatim quotes from external sources retain their original wording.

**Evidence**: External research plus two repository corrections. RFCScope identified `"undefined terminology"` as a distinct errata subclass; within this repository, work items were previously called `"tickets"`, `"issues"`, and `"task cards"` interchangeably, and `"artifact"` and `"deliverable"` were used as synonyms despite having a strict superset-subset relationship in software engineering.

**Detection**: Semantic judgement.

### C12. Tautological and Non-Operational Definitions

**Symptom**: Defining a concept by repeating the term itself or a near-synonym (`"Work item management means properly managing work items"`), or relying on abstract adjectives (`"high-quality code"`, `"clear structure"`, `"logically self-consistent"`) without stating the proximate genus, specific differentia, and observable verification steps.

**Why**: A tautology creates the illusion of a specification while providing zero decision power, reducing acceptance review to subjective opinion. Without an operational definition, `"compliant"` and `"non-compliant"` are indistinguishable in practice.

**Fix**: Rewrite the definition using **Genus (parent category) + Differentia (distinguishing invariant)** paired with a repeatable **Operational Definition** that specifies what command or inspection to run, on what input, and what observable output or state transition confirms compliance.

**Exceptions**: Industry-standard terms already governed by an unambiguous external specification.

**Evidence**: Theoretical grounding reinforced by post-hoc corrections. Grounded in Aristotelian genus-differentia definition and Bridgman's operationalism. In practice, when asked to define a criterion, drafts repeatedly returned circular paraphrases or abstract slogans that could not adjudicate any concrete edge case.

**Contrast**: Defining acceptance criteria as `"Clear acceptance criteria are criteria that make requirements clear to everyone"` is a hit. Defining them as `"Acceptance criteria are a line-by-line checklist locked before implementation that an evaluator can verify as passed or failed without redoing the task"` is not a hit.

**Detection**: Semantic judgement.

### C13. Deontic Modality Confusion

**Symptom**: Phrasing an irreversible, security-critical, or third-party-impacting `[Hard Constraint]` with weak hedges (`"try to"`, `"we recommend"`, `"where appropriate"`, `"in principle"`), or phrasing a context-dependent `Criterion` with absolute imperatives (`"must always"`, `"strictly prohibited"`). Also includes rotating between different modal keywords for the same obligation strength.

**Why**: Weakening a hard constraint invites catastrophic irreversible actions (such as unrecoverable file deletion or secret leakage); over-hardening a context-dependent criterion forces agents to execute rules blindly in contexts where an exception applies, causing secondary failures. Modal confusion destroys the normative precision of the entire specification.

**Fix**: Align strictly with RFC 2119 deontic logic and Core Rule 10: every `[Hard Constraint]` uses direct imperatives (`"Must..."`, `"Never..."`); every `Criterion` uses the fixed pattern `"The criterion is '...'"`, stating the decision boundary paired with a failure-mode contrast table.

**Exceptions**: Conversational scripts and user-facing dialogue examples.

**Evidence**: Normative drafting theory plus repository corrections. Three failure modes occurred in practice: writing every rule at identical modal strength so readers could not tell which violations were irreversible; phrasing a hard safety boundary as a polite suggestion; and rotating modal verbs so readers tried to guess a nonexistent hierarchy of obligation.

**Contrast**: Writing `"We recommend avoiding rm -rf"` is a hit because an irreversible safety boundary is downgraded to a suggestion. Writing `"[Hard Constraint] Never run rm -rf"` is not a hit.

**Detection**: Semantic judgement.

---

## D. Density and Formatting (Tier 3 — Flag by Density, P2)

These involve normal words or symbols used in excess. Flag only when density across the file exceeds the calibrated threshold, and flag the passage as a whole rather than nitpicking isolated occurrences.

### D1. Vague Quantifiers and Filler Words

**Symptom**: High-density accumulation of hedges and vague fillers such as `"etc."`, `"and so on"`, `"appropriate"`, `"properly"`, `"as much as possible"`, `"some kind of"`, `"certain"`, `"roughly"`, `"basically"`, or `"in principle"`.

**Why**: The value of a specification lies in its executability. `"Handle appropriately"` cannot be executed; the reader is forced to invent their own threshold.

**Fix**: Replace vague fillers with concrete conditions, numeric thresholds, or an explicit `Criterion`. Where no deterministic threshold exists, state explicitly **who makes the call**.

**Exceptions**: Verbatim user quotes and conversational dialogue templates preserve their original phrasing.

**Evidence**: Post-hoc correction. Drafts traded away concrete boundaries for vague generalizations, leaving readers without actionable rules.

**External basis**: A prohibition on filler words yielded the largest reasoning improvement across six models, seven reasoning tasks, and 15,600 trials, outperforming deeper theoretical linguistic constraints in inverse order to theoretical complexity (`arXiv:2604.02699`, 2026). **Gap**: That study measured model reasoning accuracy when forbidden from generating filler tokens, whereas this symptom measures filler word density inside static specification files. Because those two targets are distinct, **severity remains P2**, and the external study is noted only as background context rather than grounds for promotion.

**Detection**: Mechanical (density calculation per 1,000 characters).

### D2. Emoji Density

**Symptom**: Excessive decorative emojis across prose paragraphs or section headings.

**Why**: Visual hierarchy in a technical specification belongs to its structural headings, lists, and tables. Once decorative emojis proliferate, they lose all emphasis value and add visual noise.

**Fix**: Strip decorative emojis down to zero or near-zero in prose.

**Exceptions**: Structural status glyphs inside tables (✅ / ⚠️ / ❌) are exempt—they encode discrete state values in capability matrices and are explicitly required by the suite's formatting conventions.

**Evidence**: Post-hoc correction where decorative emojis crowded out structural hierarchy and the user requested reducing them.

**Detection**: Mechanical (density per 1,000 characters excluding table status glyphs).

### D3. Period Inside Bold List Label

**Symptom**: A bulleted list item opens with a short bold label ending in a period, followed by a sentence fragment or explanation—for example: `- **Verification method.** Check each field by reading it back.`

**Why**: A period signals the syntactic end of a complete sentence, whereas a short noun label is introducing the clause that follows. A colon (`:`) or em dash (`—`) properly binds the label to its definition.

**Fix**: Replace the period inside the bold label with a colon (`- **Verification method:** Check each field...`).

**Exceptions**: When the bold span is itself a complete grammatical sentence, a period is valid. The mechanical detector targets only **bold** short labels (`^\s*[-*+]\s+\*\*([^*。：:\n]{1,30})[。.]\*\*\s*\S`) because unbolded list openings are frequently complete imperative sentences (`"- Run the test suite. If it fails..."`) that cannot be separated from noun labels by regex without a part-of-speech parser. Unbolded forms remain under semantic judgement.

**Evidence**: Adapted from the `"List-label periods"` pattern in the upstream `avoid-ai-writing` methodology. Because it is the only Tier 3 symptom not derived from a direct user correction in this repository, it is conservatively assigned to P2.

**Detection**: Mechanical.

### D4. Excessive Domain Implementation Detail (`pr-commit` profile only)

**Symptom**: A commit message or pull request description focuses primarily on low-level code mechanics or internal domain plumbing, paired with an overly long title.

**Why**: The primary reader of a PR description is a teammate reviewing the change; they need to grasp **what changed and why** at a glance before diving into implementation mechanics in the diff.

**Fix**: Use concise, accessible bullet points stating what changed and what problem it solves. Keep the commit/PR title short and high-level; leave internal class and cursor mechanics out of the title.

**Exceptions**: None under `pr-commit`. `Skip` under `harness`, `agent-facing`, `deliverable`, and `ticket`.

**Evidence**: Post-hoc correction, three times. Commit messages and PR descriptions were written as line-by-line code walkthroughs, forcing reviewers to reverse-engineer the high-level purpose of the change from low-level implementation details.

**Contrast**: Titling a PR `"Fix duplicate charge in OrderService during batch flush caused by unrewound cursor"` is a hit. Titling it `"Fix duplicate charge during batch checkout"` and keeping cursor details in the body is not a hit.

**Detection**: Semantic judgement.

---

## When to Rewrite the Entire Document Instead of Patching

When a document simultaneously meets all three conditions below, line-by-line patching will not salvage it because the document's skeleton itself is a draft:

1. Five or more Tier 1 hits across the file.
2. Hits spanning three or more distinct symptom groups (`A`–`D`).
3. Zero structured tables or lists across its capability and limitation descriptions.

When all three hold, recommend a full rewrite: state the document's single-sentence purpose first, rebuild the section headings around that purpose, and explicitly tell the user in your report why you recommend a full rewrite over incremental patching.

## Self-Reference Exemption

This catalog and `SKILL.md` must quote defective examples when defining symptoms. Examples enclosed in quotation marks (`"..."`, `“...”`, `「...」`, `『...』`) and fenced/inline code spans are exempt from self-audit flags; audit only the normative prose of this Skill itself.
