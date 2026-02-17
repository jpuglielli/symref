from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types import FrameType

_PACKAGE_DIR = Path(__file__).parent.resolve()


def _capture_source() -> tuple[str, int]:
    """Walk the call stack to find the first frame outside the symref package."""
    frame: FrameType | None = sys._getframe(1)  # noqa: SLF001
    while frame is not None:
        filename = frame.f_code.co_filename
        try:
            frame_path = Path(filename).resolve()
        except (OSError, ValueError):
            frame = frame.f_back
            continue
        if not frame_path.is_relative_to(_PACKAGE_DIR):
            return (filename, frame.f_lineno)
        frame = frame.f_back
    return ("<unknown>", 0)
