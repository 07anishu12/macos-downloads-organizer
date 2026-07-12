#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-$(command -v python3)}"

if [[ -z "${PYTHON_BIN}" ]]; then
  echo "python3 was not found. Install Python 3.12+ and rerun this script." >&2
  exit 1
fi

"${PYTHON_BIN}" "${SCRIPT_DIR}/organize_downloads.py" \
  --downloads-dir "${HOME}/Downloads" \
  --migrate-legacy \
  --verbose
