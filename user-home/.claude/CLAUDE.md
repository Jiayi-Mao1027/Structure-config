# Global Claude Runtime Notes for This Agent System

This directory is **not** the role registry for Claude leaf workers.
In this system, Claude acts as an external worker invoked through Codex-owned skills under `~/.agents/skills/cc-*`.

That means:
- role-specific contracts belong in the corresponding `cc-*` skill
- repository `ops/contracts/*.md` remains the project source of truth
- this file only defines Claude-side shared runtime behavior

## Priority
1. repository `AGENTS.md`
2. repository `CLAUDE.md`
3. repository `ops/contracts/*`
4. current run artifacts and packets
5. the active `cc-*` skill contract and runtime wrapper
6. this global helper layer

## Shared runtime notes
- Do not invent a separate Claude-side role tree under `~/.claude`.
- Treat the active `cc-*` skill as the worker entrypoint.
- Read the bound packet and repo docs before acting.
- Keep evidence paths in every meaningful judgment.
- Never kill a process or shell you did not launch yourself.
- For Opus work, respect bootstrap checks, GPU probing, process ownership, and execution manifest discipline.
