# Codex-Native Agent Subsystem Bootstrap Pack (v5)

A controlled, role-separated execution architecture for [OpenAI Codex CLI](https://github.com/openai/codex). The system uses Codex as the persistent orchestrator (Layer 2) while delegating leaf-worker roles to Claude through explicit bridge skills.

## Architecture Overview

```
Layer 1 (User)
  │
  ▼
Layer 2 (Codex Orchestrator)          ← single control plane
  │
  ├── Codex-owned roles (native)
  │     ├── Preflight Auditor
  │     ├── Postrun Auditor
  │     └── Codex Anomaly Analyst
  │
  └── Claude-owned roles (via cc-* skills)
        ├── cc-refresher
        ├── cc-curator
        ├── cc-opus-coder
        └── cc-claude-anomaly-analyst
```

### Core Principles

- **Codex-centered control**: Codex Orchestrator is the only front-facing controller. Claude is an external worker domain, not a control plane.
- **Role separation**: Fixed downstream roles with typed responsibilities and explicit ownership boundaries.
- **File-backed state**: Important run state is reconstructible from artifacts, not chat memory.
- **Typed issue taxonomy**: Every unresolved item is classified as `user_decision`, `orchestrator_default`, `execution_layer_fix`, `nonblocking_risk`, or `hard_stop`.
- **Mediated change-set expansion**: Reading scope may expand freely; authoritative execution scope may not expand silently.

### Canonical Run Cycle

```
compile → ensure-project-state → refresher → curator
→ preflight(initial_readiness) → opus(implement) → opus(debug)
→ preflight(run_gate) → opus(execute) → postrun → upward_report
```

Stages may loop, reroute, pause, or stop depending on what is discovered. The Orchestrator decides all stage transitions.

## Directory Structure

```
codex_native_bootstrap_pack_v5/
├── project-root/                    # Merge into your repository root
│   ├── .codex/config.toml           # Thin project-level Codex config
│   ├── AGENTS.md                    # Project-coupled runtime rules
│   ├── CLAUDE.md                    # Project-level Claude notes (placeholder)
│   ├── MIGRATION_MAP.md             # Placement guidance
│   ├── ops/
│   │   ├── contracts/               # Role contracts (project source of truth)
│   │   │   ├── anomaly-analyst.md
│   │   │   ├── curator.md
│   │   │   ├── layer2-orchestrator.md
│   │   │   ├── opus-coder.md
│   │   │   ├── postrun-auditor.md
│   │   │   ├── preflight-auditor.md
│   │   │   └── refresher.md
│   │   └── templates/               # Execution plan, manifest, task-spec templates
│   └── specs/                       # Run-state documents (placeholders)
│       ├── mission.md
│       ├── current_run.md
│       └── learned_constraints.md
│
└── user-home/                       # Merge into user's home directory (~)
    ├── .agents/skills/              # Claude leaf-worker skill definitions
    │   ├── cc-claude-anomaly-analyst/
    │   ├── cc-curator/
    │   ├── cc-opus-coder/
    │   ├── cc-refresher/
    │   └── ensure-project-state/
    ├── .claude/
    │   ├── CLAUDE.md                # Thin shared Claude runtime notes
    │   └── settings.json
    └── .codex/
        ├── AGENTS.md                # User-level control-plane constitution
        ├── config.toml              # Orchestrator model/behavior config
        ├── bridge_api.toml          # Claude bridge API config (fill in your keys)
        ├── hooks.json               # Lifecycle hooks (session/bash/stop)
        ├── rules/default.rules      # Shared runtime rules
        ├── agents/                  # Codex-native subagent definitions
        │   ├── codex_anomaly_analyst.toml
        │   ├── postrun_auditor.toml
        │   └── preflight_auditor.toml
        └── protocol/
            ├── bin/                 # Shared helper scripts
            │   ├── claude_skill_runner.py   # Claude bridge runner (SDK-based)
            │   ├── ensure_project_state.sh  # Bootstrap repo state
            │   ├── gpu_probe.py             # GPU discovery & selection
            │   ├── owned_processes.py       # Process ownership guard
            │   ├── validate_json.py         # JSON validation helper
            │   ├── session_start_summary.py # SessionStart hook
            │   ├── pre_bash_guard.py        # PreToolUse(Bash) safety guard
            │   ├── post_bash_check.py       # PostToolUse(Bash) auto-register
            │   └── stop_checkpoint.py       # Stop checkpoint persistence
            ├── runtime/
            │   └── gpu_policy.toml          # GPU selection policy
            ├── schemas/
            │   ├── preflight_issue.schema.json
            │   └── receipt.schema.json
            └── templates/                   # Protocol document templates
                ├── execution-plan.md
                ├── handoff.md
                ├── role-report.md
                ├── task-spec.md
                └── upward-report.md
```

## Setup

### 1. Merge project-root into your repository

```bash
cp -r project-root/* /path/to/your/repo/
```

Fill in `specs/mission.md`, `specs/current_run.md`, and `CLAUDE.md` with your project's actual content.

### 2. Merge user-home into your home directory

```bash
cp -r user-home/.codex ~/
cp -r user-home/.claude ~/
cp -r user-home/.agents ~/
```

### 3. Configure API credentials

Edit `~/.codex/bridge_api.toml` and fill in your actual `api_key` and `api_base_url`:

```toml
[claude_bridge]
api_base_url = "https://your-api-provider.com"
api_key = "sk-your-real-key-here"
```

All API settings are read exclusively from this toml file. They are not forwarded to environment variables.

### 4. Requirements

- **Linux** (Windows is not supported)
- **Python 3.11+** (for `tomllib` support in the bridge runner)
- **claude-code-sdk** Python package (for `claude_skill_runner.py`)
- **nvidia-smi** (only needed when GPU probing is used)

## Lifecycle Hooks

The system includes four lifecycle hooks (`~/.codex/hooks.json`) that form a runtime enforcement loop:

| Hook | Event | Script | Purpose |
|------|-------|--------|---------|
| **SessionStart** | `startup\|resume` | `session_start_summary.py` | Read durable state (specs, checkpoint, latest run) and emit a JSON summary so the Orchestrator knows where to resume |
| **PreToolUse** | `Bash` | `pre_bash_guard.py` | Block kills of foreign PIDs (cross-checks `owned_processes`), block destructive ops on critical paths, warn on GPU launches without prior probe |
| **PostToolUse** | `Bash` | `post_bash_check.py` | Auto-detect and register background PIDs, set `gpu_probed` flag, log non-zero exit codes to event log |
| **Stop** | any | `stop_checkpoint.py` | Persist stage/phase/owned-process state to `checkpoint.json` so the next session can pick up cleanly |

Runtime state produced by hooks is stored under `~/.codex/runtime_state/` (excluded from git).

## Role Summary

| Role | Owner | Purpose |
|------|-------|---------|
| **Orchestrator** | Codex (Layer 2) | Single control plane; interrogates, plans, gates, synthesizes |
| **Refresher** | Claude (skill) | Initialize/refresh run-state spec documents |
| **Curator** | Claude (skill) | Workspace hygiene decisions (retain/archive/delete/promote) |
| **Opus Coder** | Claude (skill) | Primary execution: implement → debug → execute |
| **Preflight Auditor** | Codex (subagent) | Stage-aware readiness audit (`initial_readiness` / `run_gate`) |
| **Postrun Auditor** | Codex (subagent) | Execution-outcome evaluation against frozen objectives |
| **Codex Anomaly Analyst** | Codex (subagent) | Independent read-only anomaly route |
| **Claude Anomaly Analyst** | Claude (skill) | Independent read-only anomaly route (second perspective) |

## Source-of-Truth Priority

1. `~/.codex/AGENTS.md` — user-level control architecture
2. User-level Codex config and protocol helpers
3. User-level skill definitions (`~/.agents/skills/`)
4. Repo-level `AGENTS.md` — project-coupled semantics
5. Repo-level `CLAUDE.md`
6. `specs/` — run-state documents
7. `ops/contracts/` — role contracts
8. `ops/templates/` — protocol templates
9. `artifacts/runs/<run_id>/` — run artifacts

## Version History

### v5
- Lifecycle hooks implemented: `SessionStart`, `PreToolUse(Bash)`, `PostToolUse(Bash)`, `Stop` with four enforcement scripts.
- API settings read exclusively from `bridge_api.toml`; no env-var forwarding.
- JSON schemas enforce enum constraints for `issue_type` and `stage_effect`.
- `receipt.schema.json` aligned with runner code validation (`role`, `phase`, `scope_completed`, `issues`).
- All shell scripts unified to `python3`.
- `validate_json.py` now handles missing files and invalid JSON gracefully.
- Fixed Opus Coder `worker.md` markdown formatting (was incorrectly wrapped in fenced code block).
- Fixed phantom reference to non-existent `gpu_policy.md`.
- Fixed duplicate section numbering in `~/.codex/AGENTS.md`.

### v4
- Role contracts embedded directly into Codex subagent prompts and Claude skill workers. Repository `ops/contracts/*.md` remains project source of truth, but workers no longer rely on thin pointers.

### v3
- Rebuilt from repository original protocol assets instead of thin ad-hoc layer.
- `ensure-project-state` implemented as actual helper script.
- `cc-opus-coder` gained GPU probing and owned-process tracking helpers.
- Claude leaf workers moved from `~/.claude/agents/` to `~/.agents/skills/cc-*`.
- `~/.claude/CLAUDE.md` kept as thin shared runtime layer only.
