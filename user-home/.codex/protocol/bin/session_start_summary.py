#!/usr/bin/env python3
"""SessionStart hook – produce a run-state summary for the Orchestrator.

When a Codex session starts or resumes, this hook scans durable state files
and emits a compact JSON summary so the Orchestrator knows where things
left off without relying on chat memory.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


RUNTIME_STATE = Path.home() / '.codex' / 'runtime_state'
CHECKPOINT_PATH = RUNTIME_STATE / 'checkpoint.json'
OWNED_PATH = RUNTIME_STATE / 'process_guard' / 'owned.json'


def read_json(path: Path, default=None):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return default


def read_text(path: Path) -> str:
    if not path.exists():
        return ''
    try:
        return path.read_text(encoding='utf-8').strip()
    except Exception:
        return ''


def find_repo_root() -> Path | None:
    """Walk upward from CWD to find a directory containing AGENTS.md or specs/."""
    cwd = Path.cwd()
    for d in [cwd, *cwd.parents]:
        if (d / 'AGENTS.md').exists() or (d / 'specs').is_dir():
            return d
    return cwd


def latest_run_dir(repo: Path) -> Path | None:
    """Return the most recently modified run directory under artifacts/runs/."""
    runs_dir = repo / 'artifacts' / 'runs'
    if not runs_dir.is_dir():
        return None
    run_dirs = sorted(
        [d for d in runs_dir.iterdir() if d.is_dir()],
        key=lambda d: d.stat().st_mtime,
        reverse=True,
    )
    return run_dirs[0] if run_dirs else None


def summarize_specs(repo: Path) -> dict:
    summary = {}
    for name in ('current_run.md', 'mission.md', 'learned_constraints.md'):
        p = repo / 'specs' / name
        text = read_text(p)
        if text:
            # First 500 chars as preview
            summary[name] = text[:500] + ('…' if len(text) > 500 else '')
        else:
            summary[name] = None
    return summary


def summarize_latest_run(repo: Path) -> dict | None:
    run_dir = latest_run_dir(repo)
    if not run_dir:
        return None
    info: dict = {'run_id': run_dir.name}
    reports = run_dir / 'reports'
    if reports.is_dir():
        info['reports'] = [f.name for f in sorted(reports.iterdir()) if f.is_file()]
    receipts = run_dir / 'receipts'
    if receipts.is_dir():
        info['receipts'] = [f.name for f in sorted(receipts.iterdir()) if f.is_file()]
    return info


def main() -> int:
    # Read hook input from stdin (Codex passes event context)
    try:
        hook_input = json.load(sys.stdin)
    except Exception:
        hook_input = {}

    repo = find_repo_root()
    checkpoint = read_json(CHECKPOINT_PATH)
    owned = read_json(OWNED_PATH, {'items': []})

    summary = {
        'hook': 'session_start_summary',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'repo_root': str(repo) if repo else None,
        'specs': summarize_specs(repo) if repo else {},
        'latest_run': summarize_latest_run(repo) if repo else None,
        'checkpoint': checkpoint,
        'owned_processes': len(owned.get('items', [])),
        'session_event': hook_input.get('type', 'unknown'),
    }

    # Determine resumption status
    if checkpoint:
        summary['resumption'] = {
            'last_stage': checkpoint.get('stage', 'unknown'),
            'last_phase': checkpoint.get('phase', 'unknown'),
            'stopped_at': checkpoint.get('stopped_at', 'unknown'),
            'pending_issues_count': len(checkpoint.get('pending_issues', [])),
        }
    else:
        summary['resumption'] = None

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
