#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-$(command -v python3)}"
INSTALL_DIR="${HOME}/.local/share/downloads-organizer"
DOWNLOADS_DIR="${HOME}/Downloads"
LAUNCH_AGENTS_DIR="${HOME}/Library/LaunchAgents"
LAUNCH_LOG_DIR="${HOME}/Library/Logs/downloads-organizer"
PLIST_LABEL="com.user.downloads-organizer"
PLIST_PATH="${LAUNCH_AGENTS_DIR}/${PLIST_LABEL}.plist"

if [[ -z "${PYTHON_BIN}" ]]; then
  echo "python3 was not found. Install Python 3.12+ and rerun this script." >&2
  exit 1
fi

mkdir -p "${INSTALL_DIR}" "${LAUNCH_AGENTS_DIR}" "${LAUNCH_LOG_DIR}" "${DOWNLOADS_DIR}"
cp "${SCRIPT_DIR}/organize_downloads.py" "${INSTALL_DIR}/organize_downloads.py"
chmod 755 "${INSTALL_DIR}/organize_downloads.py"

cat > "${PLIST_PATH}" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${PLIST_LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>${PYTHON_BIN}</string>
    <string>${INSTALL_DIR}/organize_downloads.py</string>
    <string>--downloads-dir</string>
    <string>${DOWNLOADS_DIR}</string>
    <string>--verbose</string>
    <string>--notify</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>StartInterval</key>
  <integer>30</integer>
  <key>WatchPaths</key>
  <array>
    <string>${DOWNLOADS_DIR}</string>
  </array>
  <key>ProcessType</key>
  <string>Background</string>
  <key>StandardOutPath</key>
  <string>${LAUNCH_LOG_DIR}/downloads_organizer.out.log</string>
  <key>StandardErrorPath</key>
  <string>${LAUNCH_LOG_DIR}/downloads_organizer.err.log</string>
</dict>
</plist>
PLIST

launchctl bootout "gui/$(id -u)" "${PLIST_PATH}" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$(id -u)" "${PLIST_PATH}"
launchctl enable "gui/$(id -u)/${PLIST_LABEL}"
launchctl kickstart -k "gui/$(id -u)/${PLIST_LABEL}" || true

echo "Downloads Organizer is running in the background."
echo "It starts automatically whenever you log in and re-checks Downloads every 30 seconds."
echo "LaunchAgent: ${PLIST_PATH}"
echo "Logs: ${LAUNCH_LOG_DIR}"
