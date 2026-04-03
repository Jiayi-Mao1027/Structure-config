# Global Codex Runtime Rules for This Agent System

These are reusable runtime rules.
They do not override repository semantics.

## Priority
1. repository `AGENTS.md`
2. repository `specs/*`
3. repository `ops/contracts/*`
4. repository run artifacts
5. this global helper layer

## Runtime duties
- On first meaningful repo entry, run `ensure-project-state`.
- Use Codex subagents only for Codex-owned roles.
- Use Claude-side skills and bridge helpers only for Claude-owned roles.
- Do not treat hooks or helper scripts as the source of task semantics.
- Keep project-level `.codex` thin unless a repo-specific override is truly necessary.
