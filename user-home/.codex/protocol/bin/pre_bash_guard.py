#!/usr/bin/env python3
"""PreToolUse(Bash) hook – enforce safety rules before bash execution.

Guards against:
  - Killing foreign processes (cross-checks owned_processes registry)
  - Destructive file operations on critical paths without prior authorization
  - GPU commands without a prior probe step
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


RUNTIME_STATE = Path.home() / '.codex' / 'runtime_state'
OWNED_PATH = RUNTIME_STATE / 'process_guard' / 'owned.json'
GPU_PROBED_FLAG = RUNTIME_STATE / 'gpu_probed'

# ── Patterns ──────────────────────────────────────────────────────────────────

# Commands that kill processes
KILL_RE = re.compile(
    r'\b(kill|pkill|killall|skill)\b',
    re.IGNORECASE,
)

# Extracting numeric PIDs from kill commands  (e.g.  kill 12345, kill -9 12345)
KILL_PID_RE = re.compile(
    r'\bkill\s+(?:-\d+\s+)?(\d+)',
    re.IGNORECASE,
)

# Broad destructive file patterns
DESTRUCTIVE_RE = re.compile(
    r'\brm\s+.*-[^\s]*r[^\s]*f|'          # rm -rf / rm -fr
    r'\brm\s+-rf\b|'
    r'\bmkfs\b|'
    r'\bdd\s+.*of=/',
    re.IGNORECASE,
)

# Critical paths that should never be bulk-deleted
CRITICAL_PATHS = (
    'specs/', 'ops/', 'AGENTS.md', 'CLAUDE.md',
    '.codex/', '.claude/', '.agents/',
    '/etc/', '/usr/', '/home/',
)

# GPU launch patterns (training / inference / CUDA)
GPU_LAUNCH_RE = re.compile(
    r'\btorchrun\b|'
    r'\bpython.*train|'
    r'\baccelerate\s+launch\b|'
    r'\bdeepspeed\b|'
    r'\bnvidia-smi\b|'
    r'\bCUDA_VISIBLE_DEVICES\b',
    re.IGNORECASE,
)

# ── Helpers ───────────────────────────────────────────────────────────────────

def read_json(path: Path, default=None):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return default


def owned_pids() -> set[int]:
    payload = read_json(OWNED_PATH, {'items': []})
    return {
        int(item['pid'])
        for item in payload.get('items', [])
        if str(item.get('pid', '')).isdigit()
    }


def check_kill_safety(command: str) -> str | None:
    """Return a rejection reason if the command kills a foreign process."""
    if not KILL_RE.search(command):
        return None

    pids_in_cmd = {int(m) for m in KILL_PID_RE.findall(command)}
    if not pids_in_cmd:
        # Generic kill/pkill without extractable PID – warn but allow
        return None

    owned = owned_pids()
    foreign = pids_in_cmd - owned
    if foreign:
        return (
            f'Blocked: kill targets foreign PIDs {sorted(foreign)}. '
            f'Only owned PIDs may be killed. '
            f'Currently owned: {sorted(owned) if owned else "none"}.'
        )
    return None


def check_destructive(command: str) -> str | None:
    """Return a rejection reason for destructive operations on critical paths."""
    if not DESTRUCTIVE_RE.search(command):
        return None
    for crit in CRITICAL_PATHS:
        if crit in command:
            return (
                f'Blocked: destructive operation targets critical path "{crit}". '
                f'This requires explicit Layer-1 authorization.'
            )
    return None


def check_gpu_probe(command: str) -> str | None:
    """Warn (not block) if a GPU launch happens without a prior probe."""
    if not GPU_LAUNCH_RE.search(command):
        return None
    # nvidia-smi itself IS a probe – don't block it
    if command.strip().startswith('nvidia-smi'):
        return None
    if not GPU_PROBED_FLAG.exists():
        return (
            'Warning: GPU launch detected but no GPU probe has been recorded '
            'in this session. Run gpu_probe.py or nvidia-smi first.'
        )
    return None


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    try:
        hook_input = json.load(sys.stdin)
    except Exception:
        hook_input = {}

    command = ''
    tool_input = hook_input.get('tool_input', hook_input)
    if isinstance(tool_input, dict):
        command = tool_input.get('command', '')
    elif isinstance(tool_input, str):
        command = tool_input

    if not command:
        # Nothing to guard
        print(json.dumps({'status': 'approve'}))
        return 0

    # Run checks in priority order
    reason = check_kill_safety(command)
    if reason:
        print(json.dumps({'status': 'reject', 'reason': reason}))
        return 1

    reason = check_destructive(command)
    if reason:
        print(json.dumps({'status': 'reject', 'reason': reason}))
        return 1

    # GPU probe is a soft warning, not a hard block
    warning = check_gpu_probe(command)

    result: dict = {'status': 'approve'}
    if warning:
        result['warning'] = warning

    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
