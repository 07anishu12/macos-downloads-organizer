# macOS Downloads Organizer

<<<<<<< HEAD
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
=======
This utility keeps `~/Downloads` organized without deleting files. It uses a simple folder layout, classifies files using MIME type, extension, filename signals, and macOS metadata where useful, moves duplicates to `Duplicate Files`, and installs a LaunchAgent so new files are organized automatically.

## Folder Layout

- `Media/Screenshots` - screenshots and screen captures
- `Media/Images` - regular images
- `Media/Videos` - short videos
- `Media/Movies` - videos longer than 20 minutes when macOS duration metadata is available
- `Media/Audio` - music, songs, and audio files
- `Documents/PDFs` - PDF files
- `Documents/Word` - Word and OpenDocument text files
- `Documents/Excel` - Excel spreadsheets
- `Documents/CSV` - CSV files
- `Documents/PowerPoint` - PowerPoint and Keynote files
- `Documents/Text` - text, RTF, and Markdown files
- `Code/*` - code files grouped by language
- `Resume` - resumes, CVs, and curriculum vitae files
- `Finance` - invoices, receipts, salary, payslip, bank, and tax files
- `DMG` - disk images
- `Archives` - zip, rar, 7z, tar, gz, and related archive files
- `Applications` and `Installers` - app bundles, packages, and ISO files
- `Duplicate Files` - files with duplicate SHA256 content
- `Misc` - anything that does not fit the categories above
>>>>>>> b726704 (Simplify organizer layout and add background notifications)

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

<<<<<<< HEAD
## Start safely
=======
1. Creates the folder structure under `~/Downloads`.
2. Organizes existing loose files.
3. Migrates files from old organizer folders such as `Images`, `PDFs`, `Work`, `AI`, `Fonts`, and `Resume` into the simpler layout.
4. Moves existing Desktop screenshots into `~/Downloads/Media/Screenshots`.
5. Sets future macOS screenshots to `~/Downloads/Media/Screenshots`.
6. Installs and starts `~/Library/LaunchAgents/com.user.downloads-organizer.plist`.
7. Enables move notifications for future automatic organization.

## Notifications

The background organizer runs continuously through LaunchAgent. It starts automatically when you log in, watches `~/Downloads` for changes, and re-checks every 30 seconds after login or wake. When it moves a new file, it shows a macOS notification saying which folder the file was moved to.

For click-to-open-folder notifications, install `terminal-notifier`:

```bash
brew install terminal-notifier
```

Without `terminal-notifier`, the organizer falls back to the built-in macOS notification command. You will still see a notification, but clicking it may not open the destination folder.
>>>>>>> b726704 (Simplify organizer layout and add background notifications)

Run a dry run first:

```bash
python3 organize_downloads.py --dry-run --verbose
```

<<<<<<< HEAD
Review the planned actions before invoking the installer on files you care about.
=======
To preview cleanup of the older, more detailed folder layout:

```bash
python3 organize_downloads.py --dry-run --verbose --migrate-legacy
```

## One-Time Cleanup

Run this when you want to organize Downloads once without installing the background LaunchAgent:

```bash
./organize_now.sh
```

## Start Background Organizer

Run this when you want the organizer to keep running automatically in the background without doing a full reinstall:

```bash
./start_background.sh
```

This installs the LaunchAgent, starts it immediately, and makes it start again whenever you log in.
>>>>>>> b726704 (Simplify organizer layout and add background notifications)

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
