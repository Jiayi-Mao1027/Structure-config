# Codex-Native Agent Subsystem Bootstrap Pack (v3)

This revision is rebuilt from the repository's original protocol assets rather than replacing them with a thinner ad-hoc layer.

What changed from the earlier pack:
- `project-root/AGENTS.md` and `project-root/CLAUDE.md` are now direct modifications of the repo originals.
- `project-root/ops/contracts/*.md` are included as adapted versions of the original contracts.
- Claude-side skills are rewritten to mirror those contracts instead of inventing new lightweight prompts.
- `ensure-project-state` now has an actual helper script.
- `cc-opus-coder` now has actual helper scripts for GPU probing and owned-process tracking.
- project-level `.codex` is intentionally thin.

Intended usage:
1. Merge `project-root/*` into the repository root.
2. Merge `user-home/.codex`, `user-home/.agents`, and `user-home/.claude` into the user's home directory.
3. Fill in `~/.codex/bridge_api.toml` from the provided example.
4. Keep project semantics in the repo; keep reusable runtime helpers in user-home.


## v4 correction
Role contracts are now embedded directly into Codex subagent prompts, Claude leaf-worker notes, and Claude carrier skills. Repository `ops/contracts/*.md` remains the project source of truth, but leaf workers no longer rely on a thin pointer such as "go read the contract".


## Corrected Claude leaf-worker placement
Claude leaf workers are not defined under `~/.claude/agents/`. All Claude leaf-worker contracts now live in `~/.agents/skills/cc-*`, and `~/.claude/CLAUDE.md` is kept as a thin shared runtime layer only.
