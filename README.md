# Downloads Organizer for macOS

This utility keeps `~/Downloads` organized without deleting files. It creates a structured folder tree, classifies files using MIME type, extension, filename signals, and macOS metadata where useful, moves duplicates to `Duplicate Files`, and installs a LaunchAgent so new files are organized automatically.

## Files

- `organize_downloads.py` - organizer implementation
- `install.sh` - installs the utility, organizes existing files, configures screenshots, and starts the LaunchAgent
- `uninstall.sh` - removes the LaunchAgent and restores screenshots to Desktop
- `com.user.downloads-organizer.plist` - LaunchAgent template

## Install

```bash
chmod +x install.sh uninstall.sh organize_downloads.py
./install.sh
```

The installer:

1. Creates the folder structure under `~/Downloads`.
2. Organizes existing loose files.
3. Moves existing Desktop screenshots into `~/Downloads/Images/Screenshots`.
4. Sets future macOS screenshots to `~/Downloads/Images/Screenshots`.
5. Installs and starts `~/Library/LaunchAgents/com.user.downloads-organizer.plist`.

## Dry Run

```bash
python3 organize_downloads.py --dry-run --verbose
```

## Uninstall

```bash
./uninstall.sh
```

The uninstaller removes the LaunchAgent and restores screenshots to `~/Desktop`. It leaves organized files untouched.

## Logs

The main log is written to:

```text
~/Downloads/organization_log.txt
```

LaunchAgent stdout and stderr are written to:

```text
~/Library/Logs/downloads-organizer/downloads_organizer.out.log
~/Library/Logs/downloads-organizer/downloads_organizer.err.log
```

## Safety

- No files are deleted.
- Existing files are never overwritten.
- Name collisions become `filename (1)`, `filename (2)`, and so on.
- Duplicate content is detected with SHA256 and moved to `Duplicate Files`.
- Partial browser downloads such as `.crdownload`, `.download`, and `.part` are skipped.
- The script is idempotent and safe to run repeatedly.
