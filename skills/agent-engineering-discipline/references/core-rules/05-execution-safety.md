# Core Rule 05: Execution Safety & Resource Hygiene

## Why This Rule Exists (Why)
Unconfirmed automatic commits pollute Git history, while running `rm -rf` on temporary test files permanently destroys data with zero recovery path if a path variable expands unexpectedly.
Records created in external systems carry an additional cost: those systems are shared beyond the current test session and rarely have a recycle bin—once wiped, neither the agent nor the user can restore them.
Helper scripts and test runners carry a parallel risk: a script that wipes an unvalidated target path, strips path prefixes with character-set operations, or spawns subprocesses without bytecode isolation can overwrite source trees, leak repo-wide git status into subdirectory checks, or leave untracked cache files inside deliverables.

---

## How to Execute (How)

### 1. Git Commit Discipline (No Unauthorized Commit)
> [!IMPORTANT]
> **Hard constraint:** Zero discretion.

- **No Commit Without Explicit Instruction**: Execute `git commit` only when the user explicitly instructs you to commit in the current turn, such as saying "please commit these changes." Without that explicit instruction, leave changes staged or in the working tree.
- **Pre-Commit Hygiene Check**: Before running `git commit`, inspect `git status` and `git diff` to verify that no temporary scratch files, secrets, or `.DS_Store` files are staged.

### 2. Recoverable File Deletion (`trash` CLI)
> [!IMPORTANT]
> **Hard constraint:** Zero discretion.

- **Never Use `rm -rf`**: Never run `rm -rf` when cleaning up test artifacts or temporary files; the operation is irreversible.
- **Move to Trash**: On macOS, always run `/usr/bin/trash <path>` so deleted files can be restored from Trash. On platforms without a system trash CLI, move files to an isolated temporary staging directory or ask the user for instructions—never execute permanent unrecoverable deletion.

### 3. Test Data and External System Record Boundaries
> [!IMPORTANT]
> **Hard constraint:** Zero discretion.

- **Default to Retain**: Retain all data and external system records created during testing for user inspection unless the user explicitly instructs you to clean them up.
- **Reversible State Transitions Only**: When instructed to clean up external records, query their current state first and use only **reversible state transitions** provided by that system (such as voiding, cancelling, or deactivating)—never mutate the database directly to erase rows.
- **Self-Created Scope Only**: Clean up only the specific records created during the current test pass; never touch pre-existing records or data created by others.

### 4. Script Path Guards, Bytecode Isolation, and Subdirectory Scope

When authoring or running build, view-generation, or validation scripts, the criterion is **"if this script receives an unexpected path or runs inside a deliverable directory, can it overwrite source files or leave untracked artifacts behind?"** Guard against four recurring failure modes:

- **Path Overlap Guard**: Any script that cleans, rebuilds, or overwrites a target directory must resolve both source and target paths first, reject targets that equal the source directory, contain the source directory, reside inside the source directory, point to an existing regular file, or point to a non-empty directory lacking a self-created marker file, and use the recoverable deletion method in Section 2 when removing files.
- **Subprocess Bytecode Isolation**: Test suites invoking Python scripts inside a Skill or deliverable directory via a subprocess must pass `-B` or set `PYTHONDONTWRITEBYTECODE=1`, and set `sys.dont_write_bytecode = True` before in-process module imports, so interpreter bytecode caches do not pollute deliverable trees.
- **Path Prefix and File URI Parsing**: Strip leading `./` prefixes with a regex such as `re.sub(r"^(?:\./)+", "", path)` rather than character-set `strip("./")`, because `strip("./")` removes leading dots from hidden directories such as `.config/`; decode `file://` URIs only once while handling Windows drive-letter authority forms such as `file://C:/...`.
- **Git Subdirectory Status Filtering**: When running `git status --porcelain -z` inside a repository subdirectory, filter paths by `git rev-parse --show-prefix` so repo-wide changes do not leak into local assertions.
