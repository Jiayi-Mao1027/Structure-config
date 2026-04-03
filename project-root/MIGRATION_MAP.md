# Migration Map

## Principle
Do not replace the repository's protocol layer with a thin helper-only layer.
Retain repo-semantic assets in the repo; move reusable runtime helpers to user-home.

## Keep in the repo
- `AGENTS.md`
- `CLAUDE.md`
- `specs/*`
- `ops/contracts/*`
- `ops/templates/*`
- `artifacts/runs/*`

## Move to user-home
- reusable Codex global config
- reusable hooks
- reusable protocol helper scripts
- reusable Claude bridge config template
- reusable Claude-owned skills
- reusable Codex-owned subagents

## Important non-goal
Project-level `.codex` should not become the true execution brain.


## Claude worker placement correction
- remove any `~/.claude/agents/*` role registry
- keep only `~/.claude/CLAUDE.md` as a thin shared runtime note
- move all Claude leaf-worker contracts and entry wrappers into `~/.agents/skills/cc-*`
