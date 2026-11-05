# Core Rule 07: Protocol & Tool Hygiene

## Why This Rule Exists (Why)
In Stdio MCP mode, `stdout` is reserved exclusively for the JSON-RPC transport stream. If server code calls a bare `print()`, diagnostic text is injected directly into the JSON stream, causing the MCP client to crash with a JSON parse error.
Meanwhile, guessing API field names from memory—such as passing `memo` or `details` without checking the schema—triggers runtime payload validation errors or silent data loss.

---

## How to Execute (How)

### 1. Stdout Protection (Stdio / Stderr Isolation)
> [!IMPORTANT]
> **Hard constraint:** Zero discretion.

- **`stdout` Reserved for JSON-RPC**: Server-side code **must never call bare `print(...)`** to standard output.
- **Route Diagnostics to `stderr`**: Write all debug logs and diagnostic messages explicitly to `sys.stderr`:
  ```python
  import sys
  print("[DEBUG] Processing payload...", file=sys.stderr)
  ```

### 2. Zero-Speculation Schema Lookup (No Schema Guessing)
The criterion is **"for every key name you write, can you point to the authoritative source where you verified it?"** If not, do not write the key yet.

- **Query Before Constructing**: Before assembling any API or tool payload, query the **authoritative source** to confirm exact key names, types, and required constraints. A guessed field name and a real field name look identical in code; the only difference is whether you verified it.
- **What Qualifies as an Authoritative Source**: Live schema definitions returned or published by the target system itself—schema introspection endpoints, OpenAPI / JSON Schema specs, the tool's own registered schema declaration, or the system's canonical field contract documentation.
- **What Does Not Qualify**: Field names recalled from memory, similar APIs from other projects, illustrative snippet examples, or schemas inspected in a previous session but not re-verified against the current version.
- **Stop When Unreachable**: If the authoritative source cannot be reached or does not expose the field, stop and report that the schema could not be verified—never substitute a plausible-looking key name.
