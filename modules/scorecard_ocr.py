"""Scorecard OCR helpers.

The reader deliberately returns suggestions rather than writing score data.  OCR is
not reliable enough for handwritten scorecards to save values without a review.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import unicodedata
from pathlib import Path
from typing import Any, Iterable


class ScorecardOcrError(RuntimeError):
    """Raised when the local OCR engine cannot read an image."""


def is_available() -> bool:
    return shutil.which("tesseract") is not None


def extract_text(image_bytes: bytes, suffix: str = ".jpg") -> str:
    """Read a scorecard image with the locally installed Tesseract binary."""
    if not image_bytes:
        raise ScorecardOcrError("画像ファイルが空です。")
    if not is_available():
        raise ScorecardOcrError(
            "画像読み取りエンジン（Tesseract）がこの環境にインストールされていません。"
        )

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as image_file:
        image_file.write(image_bytes)
        image_path = Path(image_file.name)
    try:
        result = subprocess.run(
            ["tesseract", str(image_path), "stdout", "-l", "jpn+eng", "--psm", "6"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise ScorecardOcrError("画像の読み取りがタイムアウトしました。") from exc
    finally:
        image_path.unlink(missing_ok=True)

    if result.returncode != 0:
        detail = result.stderr.strip() or "不明なエラー"
        raise ScorecardOcrError(f"画像を読み取れませんでした: {detail}")
    return result.stdout.strip()


def _normalise(value: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", value)).casefold()


def _numbers_after_name(line: str, name: str) -> list[int]:
    """Extract signed integers following a matched member name in an OCR line."""
    # NFKC converts full-width digits and signs before this expression is applied.
    return [
        int(value)
        for value in re.findall(r"(?<!\d)[+-]?\d{1,3}(?!\d)", unicodedata.normalize("NFKC", line))
    ]


def suggest_scores(ocr_text: str, members: Iterable[dict[str, Any]]) -> dict[int, dict[str, int]]:
    """Return ``member_id -> score/putt/game_point`` suggestions.

    A row is accepted only when it contains a known member name and at least two
    numeric values.  This keeps headings, hole numbers, and totals out of the
    automatic suggestions.
    """
    suggestions: dict[int, dict[str, int]] = {}
    lines = [line for line in ocr_text.splitlines() if line.strip()]
    for member in members:
        member_id = member.get("member_id")
        name = member.get("name")
        if member_id is None or not name:
            continue
        needle = _normalise(str(name))
        for line in lines:
            if needle not in _normalise(line):
                continue
            values = _numbers_after_name(line, str(name))
            if len(values) < 2:
                continue
            suggestion = {"score": values[0], "putt": values[1]}
            if len(values) >= 3:
                suggestion["game_pt"] = values[2]
            suggestions[int(member_id)] = suggestion
            break
    return suggestions
