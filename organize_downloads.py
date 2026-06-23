#!/usr/bin/env python3
"""Professional-grade macOS Downloads organizer.

This utility organizes files under ~/Downloads without deleting anything.
It is intentionally conservative: files already inside managed destination
folders are left alone unless they are duplicate candidates in an unmanaged
scan. Duplicate files are moved to "Duplicate Files" instead of being removed.
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import mimetypes
import os
import plistlib
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


APP_NAME = "downloads-organizer"
PLIST_LABEL = "com.user.downloads-organizer"
LOG_FILENAME = "organization_log.txt"


FOLDER_STRUCTURE: tuple[str, ...] = (
    "Images",
    "Images/Screenshots",
    "Images/Photos",
    "Images/Wallpapers",
    "Images/Logos",
    "Videos",
    "Audio",
    "PDFs",
    "Documents",
    "Documents/Word",
    "Documents/Excel",
    "Documents/PowerPoint",
    "Documents/Text",
    "HTML",
    "Code",
    "Code/Python",
    "Code/JavaScript",
    "Code/HTML",
    "Code/CSS",
    "Code/JSON",
    "Code/SQL",
    "Code/XML",
    "Archives",
    "Applications",
    "Installers",
    "DMG",
    "Fonts",
    "Torrents",
    "AI",
    "Design",
    "Work",
    "Personal",
    "Resume",
    "Finance",
    "Research",
    "Misc",
    "Duplicate Files",
)

MANAGED_ROOTS = {part.split("/")[0] for part in FOLDER_STRUCTURE}


KEYWORDS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("resume", "cv", "curriculum vitae"), "Resume"),
    (("invoice", "receipt", "reciept", "salary", "payslip", "bank", "tax"), "Finance"),
    (("research", "paper", "dataset", "model", "experiment"), "Research"),
    (("proposal", "presentation", "ppt", "pitch", "job", "application", "interview", "offer"), "Work"),
    (("chatgpt", "openai", "claude", "gemini", "llm", "ai-", "_ai", "stable diffusion", "midjourney"), "AI"),
    (("figma", "sketch", "adobe", "photoshop", "illustrator", "xd", "design", "mockup", "wireframe"), "Design"),
    (("personal", "family", "medical", "health", "passport", "aadhaar", "pan card"), "Personal"),
)

SCREENSHOT_PATTERNS = (
    "screenshot",
    "screen shot",
    "chatgpt image",
    "whatsapp image",
)

WALLPAPER_PATTERNS = ("wallpaper", "background", "desktop")
LOGO_PATTERNS = ("logo", "brandmark", "icon")

CODE_EXTENSIONS = {
    ".py": "Code/Python",
    ".ipynb": "Code/Python",
    ".js": "Code/JavaScript",
    ".mjs": "Code/JavaScript",
    ".cjs": "Code/JavaScript",
    ".ts": "Code/JavaScript",
    ".jsx": "Code/JavaScript",
    ".tsx": "Code/JavaScript",
    ".html": "Code/HTML",
    ".htm": "Code/HTML",
    ".css": "Code/CSS",
    ".scss": "Code/CSS",
    ".sass": "Code/CSS",
    ".json": "Code/JSON",
    ".jsonl": "Code/JSON",
    ".sql": "Code/SQL",
    ".xml": "Code/XML",
    ".yaml": "Code/JSON",
    ".yml": "Code/JSON",
    ".toml": "Code/JSON",
}

DOCUMENT_EXTENSIONS = {
    ".pdf": "PDFs",
    ".doc": "Documents/Word",
    ".docx": "Documents/Word",
    ".odt": "Documents/Word",
    ".xls": "Documents/Excel",
    ".xlsx": "Documents/Excel",
    ".csv": "Documents/Excel",
    ".ppt": "Documents/PowerPoint",
    ".pptx": "Documents/PowerPoint",
    ".key": "Documents/PowerPoint",
    ".txt": "Documents/Text",
    ".rtf": "Documents/Text",
    ".md": "Documents/Text",
}

ARCHIVE_EXTENSIONS = {
    ".zip",
    ".rar",
    ".7z",
    ".tar",
    ".gz",
    ".bz2",
    ".xz",
    ".tgz",
    ".tbz",
}

APPLICATION_EXTENSIONS = {".app": "Applications", ".pkg": "Installers", ".mpkg": "Installers", ".iso": "Applications", ".dmg": "DMG"}
FONT_EXTENSIONS = {".ttf", ".otf", ".woff", ".woff2", ".eot"}
TORRENT_EXTENSIONS = {".torrent"}


@dataclass(frozen=True)
class FileDecision:
    source: Path
    destination_dir: Path
    reason: str
    duplicate_of: Path | None = None


class DownloadsOrganizer:
    def __init__(self, downloads_dir: Path, dry_run: bool = False, verbose: bool = False) -> None:
        self.downloads_dir = downloads_dir.expanduser().resolve()
        self.dry_run = dry_run
        self.verbose = verbose
        self.log_file = self.downloads_dir / LOG_FILENAME
        self.logger = self._build_logger()

    def _build_logger(self) -> logging.Logger:
        logger = logging.getLogger(APP_NAME)
        logger.setLevel(logging.DEBUG if self.verbose else logging.INFO)
        logger.handlers.clear()

        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        console.setLevel(logging.DEBUG if self.verbose else logging.INFO)
        logger.addHandler(console)

        if not self.dry_run:
            self.downloads_dir.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(self.log_file, encoding="utf-8")
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.DEBUG)
            logger.addHandler(file_handler)

        return logger

    def create_folder_structure(self) -> None:
        for relative in FOLDER_STRUCTURE:
            path = self.downloads_dir / relative
            if self.dry_run:
                self.logger.info("DRY RUN create folder: %s", path)
            else:
                path.mkdir(parents=True, exist_ok=True)

    def organize(self) -> None:
        self.logger.info("Starting Downloads organization for %s", self.downloads_dir)
        self.create_folder_structure()
        files = list(self.iter_candidate_files())
        self.logger.info("Found %d candidate file(s)", len(files))

        seen_hashes = self.existing_hash_index(files)
        for file_path in files:
            try:
                if not file_path.exists() or not (file_path.is_file() or self.is_application_bundle(file_path)):
                    continue
                decision = self.decide(file_path, seen_hashes)
                self.move_file(decision)
            except Exception as exc:  # noqa: BLE001 - log and continue by design
                self.logger.exception("ERROR processing %s: %s", file_path, exc)

        self.logger.info("Finished Downloads organization")

    def iter_candidate_files(self) -> Iterable[Path]:
        if not self.downloads_dir.exists():
            return []

        candidates: list[Path] = []
        for root, dirs, files in os.walk(self.downloads_dir):
            root_path = Path(root)

            pruned_dirs: list[str] = []
            for dirname in dirs:
                dir_path = root_path / dirname
                if dir_path.name.startswith("."):
                    self.logger.debug("SKIPPED hidden directory: %s", dir_path)
                    continue
                if self.is_inside_managed_root(dir_path):
                    self.logger.debug("SKIPPED managed directory: %s", dir_path)
                    continue
                if dir_path.suffix.lower() == ".app":
                    candidates.append(dir_path)
                    continue
                pruned_dirs.append(dirname)
            dirs[:] = pruned_dirs

            for filename in files:
                path = root_path / filename
                if path.name == LOG_FILENAME:
                    continue
                if path.name.startswith("."):
                    self.logger.debug("SKIPPED hidden file: %s", path)
                    continue
                if self.is_partial_download(path):
                    self.logger.info("SKIPPED partial download: %s", path)
                    continue
                if self.is_inside_managed_root(path):
                    self.logger.debug("SKIPPED managed folder file: %s", path)
                    continue
                candidates.append(path)
        return candidates

    def is_inside_managed_root(self, path: Path) -> bool:
        try:
            relative = path.relative_to(self.downloads_dir)
        except ValueError:
            return False
        return bool(relative.parts) and relative.parts[0] in MANAGED_ROOTS

    @staticmethod
    def is_partial_download(path: Path) -> bool:
        partial_suffixes = (".download", ".crdownload", ".part", ".tmp")
        return path.suffix.lower() in partial_suffixes or path.name.endswith(".download")

    @staticmethod
    def is_application_bundle(path: Path) -> bool:
        return path.is_dir() and path.suffix.lower() == ".app"

    def existing_hash_index(self, candidates: list[Path]) -> dict[str, Path]:
        candidate_set = {p.resolve() for p in candidates if p.exists()}
        hashes: dict[str, Path] = {}
        for path in self.downloads_dir.rglob("*"):
            if not path.is_file() or path.name == LOG_FILENAME or self.is_partial_download(path):
                continue
            try:
                resolved = path.resolve()
                if resolved in candidate_set:
                    continue
                digest = self.sha256(path)
                hashes.setdefault(digest, path)
            except Exception as exc:  # noqa: BLE001
                self.logger.debug("Could not hash existing file %s: %s", path, exc)
        return hashes

    def decide(self, path: Path, seen_hashes: dict[str, Path]) -> FileDecision:
        if path.is_dir():
            destination = self.classify(path)
            return FileDecision(path, self.downloads_dir / destination, f"classified as {destination}")

        digest = self.sha256(path)
        duplicate_of = seen_hashes.get(digest)
        if duplicate_of and duplicate_of.resolve() != path.resolve():
            return FileDecision(path, self.downloads_dir / "Duplicate Files", f"SHA256 duplicate of {duplicate_of}", duplicate_of)
        seen_hashes.setdefault(digest, path)

        destination = self.classify(path)
        return FileDecision(path, self.downloads_dir / destination, f"classified as {destination}")

    def classify(self, path: Path) -> str:
        name = self.normalized_name(path)
        suffix = path.suffix.lower()
        mime = self.mime_type(path)
        metadata = self.metadata_kind(path)
        if self.looks_like_image(mime, suffix, metadata):
            if any(pattern in name for pattern in SCREENSHOT_PATTERNS):
                return "Images/Screenshots"
            if any(pattern in name for pattern in WALLPAPER_PATTERNS):
                return "Images/Wallpapers"
            if any(pattern in name for pattern in LOGO_PATTERNS):
                return "Images/Logos"

        if suffix in APPLICATION_EXTENSIONS:
            return APPLICATION_EXTENSIONS[suffix]
        if suffix in ARCHIVE_EXTENSIONS or "archive" in (mime or ""):
            return "Archives"
        if suffix in FONT_EXTENSIONS or (mime or "").startswith("font/"):
            return "Fonts"
        if suffix in TORRENT_EXTENSIONS or mime == "application/x-bittorrent":
            return "Torrents"

        keyword_destination = self.keyword_destination(name)
        if keyword_destination:
            return keyword_destination

        if self.looks_like_image(mime, suffix, metadata):
            return "Images/Photos"

        if self.looks_like_video(mime, suffix):
            return "Videos"
        if self.looks_like_audio(mime, suffix):
            return "Audio"
        if suffix in DOCUMENT_EXTENSIONS:
            return DOCUMENT_EXTENSIONS[suffix]
        if suffix in CODE_EXTENSIONS:
            return CODE_EXTENSIONS[suffix]
        if mime == "text/html":
            return "HTML"
        if mime == "application/pdf":
            return "PDFs"

        return "Misc"

    @staticmethod
    def normalized_name(path: Path) -> str:
        return re.sub(r"[_\-.]+", " ", path.stem.lower())

    @staticmethod
    def keyword_destination(text: str) -> str | None:
        for keywords, destination in KEYWORDS:
            if any(keyword in text for keyword in keywords):
                return destination
        return None

    @staticmethod
    def looks_like_image(mime: str | None, suffix: str, metadata: str | None) -> bool:
        image_exts = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic", ".heif", ".tiff", ".tif", ".bmp", ".svg"}
        return (mime or "").startswith("image/") or suffix in image_exts or "image" in (metadata or "").lower()

    @staticmethod
    def looks_like_video(mime: str | None, suffix: str) -> bool:
        video_exts = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm", ".wmv"}
        return (mime or "").startswith("video/") or suffix in video_exts

    @staticmethod
    def looks_like_audio(mime: str | None, suffix: str) -> bool:
        audio_exts = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".aiff"}
        return (mime or "").startswith("audio/") or suffix in audio_exts

    @staticmethod
    def sha256(path: Path) -> str:
        hasher = hashlib.sha256()
        with path.open("rb") as file_obj:
            for chunk in iter(lambda: file_obj.read(1024 * 1024), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    @staticmethod
    def mime_type(path: Path) -> str | None:
        try:
            result = subprocess.run(
                ["file", "-b", "--mime-type", str(path)],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                mime = result.stdout.strip()
                if mime:
                    return mime
        except Exception:
            pass
        guessed, _ = mimetypes.guess_type(path.name)
        return guessed

    @staticmethod
    def metadata_kind(path: Path) -> str | None:
        try:
            result = subprocess.run(
                ["mdls", "-name", "kMDItemKind", "-raw", str(path)],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
            value = result.stdout.strip()
            if result.returncode == 0 and value and value != "(null)":
                return value
        except Exception:
            return None
        return None

    def move_file(self, decision: FileDecision) -> None:
        source = decision.source
        target_dir = decision.destination_dir
        target_path = self.unique_destination(target_dir / source.name)

        if source.resolve() == target_path.resolve():
            self.logger.info("SKIPPED already in destination: %s", source)
            return

        if self.dry_run:
            duplicate_note = f" duplicate_of={decision.duplicate_of}" if decision.duplicate_of else ""
            self.logger.info("DRY RUN move: %s -> %s (%s%s)", source, target_path, decision.reason, duplicate_note)
            return

        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(target_path))
        if decision.duplicate_of:
            self.logger.info("DUPLICATE moved: %s -> %s duplicate_of=%s", source, target_path, decision.duplicate_of)
        else:
            self.logger.info("MOVED: %s -> %s (%s)", source, target_path, decision.reason)

    @staticmethod
    def unique_destination(path: Path) -> Path:
        if not path.exists():
            return path
        stem = path.stem
        suffix = path.suffix
        parent = path.parent
        counter = 1
        while True:
            candidate = parent / f"{stem} ({counter}){suffix}"
            if not candidate.exists():
                return candidate
            counter += 1

    def configure_screenshots(self) -> None:
        screenshot_dir = self.downloads_dir / "Images" / "Screenshots"
        if self.dry_run:
            self.logger.info("DRY RUN configure screenshots to %s", screenshot_dir)
            return

        screenshot_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(["defaults", "write", "com.apple.screencapture", "location", str(screenshot_dir)], check=True)
        subprocess.run(["killall", "SystemUIServer"], check=False)
        verification = subprocess.run(
            ["defaults", "read", "com.apple.screencapture", "location"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.logger.info("Screenshot destination verified as: %s", verification.stdout.strip())

    def move_desktop_screenshots(self) -> None:
        desktop = Path.home() / "Desktop"
        destination = self.downloads_dir / "Images" / "Screenshots"
        if not desktop.exists():
            self.logger.info("SKIPPED Desktop screenshot move: Desktop does not exist")
            return

        screenshot_re = re.compile(r"^(screen shot|screenshot|chatgpt image|whatsapp image)", re.IGNORECASE)
        for path in desktop.iterdir():
            if not path.is_file() or not screenshot_re.search(path.name):
                continue
            mime = self.mime_type(path)
            if not self.looks_like_image(mime, path.suffix.lower(), self.metadata_kind(path)):
                self.logger.info("SKIPPED Desktop non-image screenshot-like file: %s", path)
                continue
            target = self.unique_destination(destination / path.name)
            if self.dry_run:
                self.logger.info("DRY RUN move Desktop screenshot: %s -> %s", path, target)
            else:
                destination.mkdir(parents=True, exist_ok=True)
                shutil.move(str(path), str(target))
                self.logger.info("MOVED Desktop screenshot: %s -> %s", path, target)


def write_launch_agent_template(path: Path, python_path: Path, script_path: Path, downloads_dir: Path) -> None:
    launch_log_dir = Path.home() / "Library" / "Logs" / APP_NAME
    plist = {
        "Label": PLIST_LABEL,
        "ProgramArguments": [
            str(python_path),
            str(script_path),
            "--downloads-dir",
            str(downloads_dir),
            "--verbose",
        ],
        "RunAtLoad": True,
        "StartInterval": 30,
        "WatchPaths": [str(downloads_dir)],
        "StandardOutPath": str(launch_log_dir / "downloads_organizer.out.log"),
        "StandardErrorPath": str(launch_log_dir / "downloads_organizer.err.log"),
    }
    with path.open("wb") as file_obj:
        plistlib.dump(plist, file_obj, sort_keys=False)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Organize ~/Downloads safely and automatically.")
    parser.add_argument("--downloads-dir", type=Path, default=Path.home() / "Downloads")
    parser.add_argument("--dry-run", action="store_true", help="Show intended actions without moving files.")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging.")
    parser.add_argument("--configure-screenshots", action="store_true", help="Set macOS screenshot destination.")
    parser.add_argument("--move-desktop-screenshots", action="store_true", help="Move existing Desktop screenshots.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    organizer = DownloadsOrganizer(args.downloads_dir, dry_run=args.dry_run, verbose=args.verbose)

    try:
        organizer.organize()
        if args.configure_screenshots:
            organizer.configure_screenshots()
        if args.move_desktop_screenshots:
            organizer.move_desktop_screenshots()
    except Exception as exc:  # noqa: BLE001
        organizer.logger.exception("Fatal organizer error: %s", exc)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
