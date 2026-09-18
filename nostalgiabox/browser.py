"""The TV Guide: a generic, one-level-at-a-time file browser.

Unlike ``channel.py`` (which recursively flattens a whole show folder into a
shuffle bag), the Guide lists exactly what's in the current folder and lets
you descend into sub-folders interactively - Home (the configured channels),
then whatever's inside, however deep, with no season/episode-specific logic
at all. Selecting a file hands its path back to the caller to play; there is
no "episode" concept here, just directories and playable files.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class DirEntry:
    """One row in the guide: either a sub-folder or a playable file."""

    name: str
    path: Path
    is_dir: bool


def list_dir(path: Path, extensions: Sequence[str]) -> List[DirEntry]:
    """List the immediate contents of ``path``: sub-folders, then playable files.

    Both groups are sorted case-insensitively by name, mirroring the
    conventions already used for channel auto-discovery (``config.py``'s
    ``_discover_channels``) and episode scanning (``channel.py``'s
    ``scan_episodes``): skip dotfiles, filter files to ``extensions``.
    """
    if not path.is_dir():
        return []
    exts = {e.lower() for e in extensions}
    dirs: List[Path] = []
    files: List[Path] = []
    for p in path.iterdir():
        if p.name.startswith("."):
            continue
        if p.is_dir():
            dirs.append(p)
        elif p.is_file() and p.suffix.lower() in exts:
            files.append(p)
    dirs.sort(key=lambda p: p.name.lower())
    files.sort(key=lambda p: p.name.lower())
    return [DirEntry(p.name, p, True) for p in dirs] + [
        DirEntry(p.name, p, False) for p in files
    ]


@dataclass
class _Frame:
    """One level of the browse stack: what's listed, and what's highlighted."""

    label: str
    entries: List[DirEntry] = field(default_factory=list)
    selected: int = 0


class GuideState:
    """Tracks where in the folder tree the viewer currently is browsing.

    ``home_entries`` is fixed at construction (one entry per browsable
    channel folder) - Home never needs rescanning, so ``reset_to_home`` is
    just a cheap stack reset, not a re-list.
    """

    def __init__(self, home_entries: Sequence[DirEntry], extensions: Sequence[str]) -> None:
        self._home_entries: List[DirEntry] = list(home_entries)
        self._extensions = tuple(extensions)
        self._stack: List[_Frame] = [_Frame("TV Guide", list(self._home_entries))]

    def reset_to_home(self) -> None:
        self._stack = [_Frame("TV Guide", list(self._home_entries))]

    def move(self, delta: int) -> None:
        """Move the selection up/down within the current folder (wraps)."""
        frame = self._stack[-1]
        if not frame.entries:
            return
        frame.selected = (frame.selected + delta) % len(frame.entries)

    def enter(self) -> Optional[Path]:
        """Select the highlighted entry.

        Descending into a folder pushes a new frame and returns ``None``;
        selecting a file returns its path for the caller to play.
        """
        frame = self._stack[-1]
        if not frame.entries:
            return None
        entry = frame.entries[frame.selected]
        if entry.is_dir:
            self._stack.append(_Frame(entry.name, list_dir(entry.path, self._extensions)))
            return None
        return entry.path

    def back(self) -> bool:
        """Go up one folder level. Returns False if already at Home."""
        if len(self._stack) <= 1:
            return False
        self._stack.pop()
        return True

    def current_view(self) -> Tuple[str, List[DirEntry], int]:
        """``(breadcrumb, entries, selected_index)`` for the current folder."""
        frame = self._stack[-1]
        breadcrumb = " > ".join(f.label for f in self._stack)
        return breadcrumb, frame.entries, frame.selected


__all__ = ["DirEntry", "list_dir", "GuideState"]
