#!/usr/bin/env bash
set -euo pipefail
~/.codex/protocol/bin/ensure_project_state.sh "${1:-$(pwd)}"
python ~/.codex/protocol/bin/owned_processes.py snapshot
