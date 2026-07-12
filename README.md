# macOS Downloads Organizer

> A safe, idempotent utility that continuously organizes `~/Downloads` without deleting or overwriting files.

The organizer classifies files using MIME type, extension, filename signals, and selected macOS metadata. It creates a predictable folder structure, detects duplicate content with SHA-256, and installs a LaunchAgent so new files can be handled automatically.

## Features

- Dry-run mode before moving anything.
- MIME, extension, filename, and metadata-aware classification.
- SHA-256 duplicate detection; duplicates are moved to `Duplicate Files` rather than deleted.
- Collision-safe renaming (`filename (1)`, `filename (2)`, …).
- Partial-download protection for `.crdownload`, `.download`, and `.part` files.
- LaunchAgent setup for continuous operation.
- Clean uninstall that removes the agent without deleting organized files.

## Files

```text
organize_downloads.py                    # organizer implementation
install.sh                               # installation and LaunchAgent setup
uninstall.sh                             # remove agent and restore screenshot location
com.user.downloads-organizer.plist       # LaunchAgent template
```

## Install

```bash
chmod +x install.sh uninstall.sh organize_downloads.py
./install.sh
```

The installer creates the folder layout beneath `~/Downloads`, organizes loose files, places screenshots in `~/Downloads/Images/Screenshots`, and installs `com.user.downloads-organizer.plist` in `~/Library/LaunchAgents`.

## Start safely

Run a dry run first:

```bash
python3 organize_downloads.py --dry-run --verbose
```

Review the planned actions before invoking the installer on files you care about.

## Uninstall

```bash
./uninstall.sh
```

The uninstaller removes the LaunchAgent and restores the default screenshot location. It leaves previously organized files untouched.

## Logs

- Main activity log: `~/Downloads/organization_log.txt`
- LaunchAgent stdout: `~/Library/Logs/downloads-organizer/downloads_organizer.out.log`
- LaunchAgent stderr: `~/Library/Logs/downloads-organizer/downloads_organizer.err.log`

## Status

Active utility project. Planned work includes automated tests with temporary directories and a short visual installation walkthrough.
