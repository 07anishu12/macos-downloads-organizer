#!/usr/bin/env bash
set -euo pipefail

PLIST_LABEL="com.user.downloads-organizer"
PLIST_PATH="${HOME}/Library/LaunchAgents/${PLIST_LABEL}.plist"

launchctl bootout "gui/$(id -u)" "${PLIST_PATH}" >/dev/null 2>&1 || true
rm -f "${PLIST_PATH}"

defaults write com.apple.screencapture location "${HOME}/Desktop"
killall SystemUIServer >/dev/null 2>&1 || true

echo "Uninstalled Downloads Organizer LaunchAgent."
echo "Screenshot location restored to: $(defaults read com.apple.screencapture location)"
echo "Organized files were left untouched."
