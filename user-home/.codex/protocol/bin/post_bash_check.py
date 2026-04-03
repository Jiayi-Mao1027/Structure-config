#!/usr/bin/env python3
"""PostToolUse(Bash) hook – register processes and record outcomes.

After every bash command:
  - Detect background processes that may have been spawned
  - Auto-register new owned PIDs
  - Mark gpu_probed flag when a GPU probe was run
  - Log non-zero exit codes to the runtime event log
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


RUNTIME_STATE = Path.home() / '.codex' / 'runtime_state'
OWNED_PATH = RUNTIME_STATE / 'process_guard' / 'owned.json'
BASELINE_PATH = RUNTIME_STATE / 'process_guard' / 'baseline.json'
GPU_PROBED_FLAG = RUNTIME_STATE / 'gpu_probed'
EVENT_LOG = RUNTIME_STATE / 'event_log.jsonl'


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path, default=None):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return default


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def append_event(event: dict) -> None:
    EVENT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with EVENT_LOG.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')


# ── Background PID detection ─────────────────────────────────────────────────

# Patterns that commonly produce background PIDs in output
# e.g. "[1] 12345", "PID: 12345", "Started process 12345"
BG_PID_RE = re.compile(
    r'\[\d+\]\s+(\d{3,})|'            # [1] 12345
    r'\bPID[:\s]+(\d{3,})|'            # PID: 12345  /  PID 12345
    r'\bstarted\s+.*?(\d{4,})',        # Started ... 12345
    re.IGNORECASE,
)

# Commands that are known to launch background work
BG_LAUNCH_RE = re.compile(
    r'\bnohup\b|'
    r'&\s*$|'                           # trailing &
    r'\btorchrun\b|'
    r'\baccelerate\s+launch\b|'
    r'\bdeepspeed\b',
    re.IGNORECASE,
)

# GPU probe patterns
GPU_PROBE_RE = re.compile(
    r'\bgpu_probe\.py\b|'
    r'\bnvidia-smi\b',
    re.IGNORECASE,
)


def extract_bg_pids(output: str) -> list[int]:
    """Extract candidate background PIDs from command output."""
    pids = []
    for m in BG_PID_RE.finditer(output):
        for g in m.groups():
            if g and g.isdigit():
                pid = int(g)
                # Reasonable PID range
                if 2 <= pid <= 4194304:
                    pids.append(pid)
    return pids


def register_pids(pids: list[int], label: str) -> int:
    """Register discovered PIDs into the owned-process registry."""
    payload = read_json(OWNED_PATH, {'items': []})
    existing = {
        int(item['pid'])
        for item in payload.get('items', [])
        if str(item.get('pid', '')).isdigit()
    }
    added = 0
    for pid in pids:
        if pid not in existing:
            payload['items'].append({
                'pid': pid,
                'label': label,
                'registered_at': now_iso(),
                'ppid': os.getppid(),
                'source': 'post_bash_hook_auto',
            })
            added += 1
    if added:
        write_json(OWNED_PATH, payload)
    return added


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    try:
        hook_input = json.load(sys.stdin)
    except Exception:
        hook_input = {}

    tool_input = hook_input.get('tool_input', {})
    tool_output = hook_input.get('tool_output', hook_input.get('output', ''))
    if isinstance(tool_input, dict):
        command = tool_input.get('command', '')
    else:
        command = str(tool_input)

    if isinstance(tool_output, dict):
        stdout_text = tool_output.get('stdout', '') or tool_output.get('output', '')
        exit_code = tool_output.get('exit_code', tool_output.get('exitCode', 0))
    else:
        stdout_text = str(tool_output)
        exit_code = hook_input.get('exit_code', 0)

    result: dict = {'hook': 'post_bash_check', 'actions': []}

    # 1. Mark GPU probed flag
    if command and GPU_PROBE_RE.search(command):
        GPU_PROBED_FLAG.parent.mkdir(parents=True, exist_ok=True)
        GPU_PROBED_FLAG.write_text(now_iso(), encoding='utf-8')
        result['actions'].append('gpu_probed_flag_set')

    # 2. Detect and register background PIDs
    if command and BG_LAUNCH_RE.search(command):
        pids = extract_bg_pids(stdout_text)
        if pids:
            added = register_pids(pids, label=f'auto:{command[:60]}')
            result['actions'].append(f'registered_{added}_pids')
            result['registered_pids'] = pids

    # 3. Log non-zero exit codes
    try:
        exit_code_int = int(exit_code)
    except (TypeError, ValueError):
        exit_code_int = 0

    if exit_code_int != 0:
        event = {
            'type': 'bash_nonzero_exit',
            'timestamp': now_iso(),
            'command_preview': command[:200] if command else '',
            'exit_code': exit_code_int,
        }
        append_event(event)
        result['actions'].append(f'logged_exit_code_{exit_code_int}')

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
