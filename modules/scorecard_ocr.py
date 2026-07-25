"""Vision-based scorecard reader.

Golf Network scorecards are dense, sideways tables.  Local OCR cannot reliably
associate the vertical player names with the OUT/IN totals, so this module uses
the configured OpenAI vision API and returns reviewable suggestions only.
"""
from __future__ import annotations

import base64
from io import BytesIO
import json
import os
import unicodedata
from typing import Any, Iterable

import requests
from PIL import Image, ImageOps


class ScorecardOcrError(RuntimeError):
    """Raised when a scorecard cannot be read."""


def is_available() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY"))


def _response_text(payload: dict[str, Any]) -> str:
    for item in payload.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "output_text":
                return content.get("text", "")
    raise ScorecardOcrError("画像読み取りの応答に結果が含まれていません。")


def _prepare_scorecard_image(image_bytes: bytes, mime_type: str) -> tuple[bytes, str]:
    """Rotate portrait Golf Network scorecard screenshots to landscape."""
    try:
        with Image.open(BytesIO(image_bytes)) as source:
            image = ImageOps.exif_transpose(source)
            if image.height > image.width:
                image = image.rotate(90, expand=True)
            if image.mode not in {"RGB", "L"}:
                image = image.convert("RGB")
            output = BytesIO()
            image.save(output, format="JPEG", quality=95)
            return output.getvalue(), "image/jpeg"
    except (OSError, ValueError) as exc:
        raise ScorecardOcrError("画像ファイルを開けませんでした。") from exc


def _normalise_name(value: str) -> str:
    return "".join(unicodedata.normalize("NFKC", value).split()).casefold()


def extract_scores(
    image_bytes: bytes,
    mime_type: str,
    members: Iterable[dict[str, Any]],
    segment: str,
) -> dict[int, dict[str, int]]:
    """Read OUT or IN totals from a Golf Network scorecard image.

    ``segment`` must be ``front`` (holes 1-9) or ``back`` (holes 10-18).
    The table is normalised to landscape before being sent to the model.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ScorecardOcrError("OPENAI_API_KEY が設定されていません。")
    if not image_bytes:
        raise ScorecardOcrError("画像ファイルが空です。")
    if segment not in {"front", "back"}:
        raise ScorecardOcrError("この画像形式からエキストラスコアは読み取れません。")

    known_members = [member for member in members if member.get("member_id") is not None and member.get("name")]
    if not known_members:
        raise ScorecardOcrError("照合する参加者名がありません。")
    target = "OUT（1〜9番）" if segment == "front" else "IN（10〜18番）"
    names = "、".join(str(member["name"]) for member in known_members)
    schema = {
        "type": "object",
        "properties": {
            "players": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "score": {"type": "integer"},
                        "putt": {"type": "integer"},
                        "game_pt": {"type": "integer"},
                    },
                    "required": ["name", "score", "putt", "game_pt"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["players"],
        "additionalProperties": False,
    }
    prompt = f"""この画像は Golf Network のゴルフスコア表です。すでに横向きに補正されています。
対象は {target} の合計欄です。各プレイヤーについて、合計スコア・合計パット数・ゲームポイント合計を抽出してください。
照合対象の参加者は次の名前だけです: {names}。
プレイヤー名は表の左側に縦書きであり、各名前に対応する横一行の色付きセルを読みます。別の行の値を対応づけないでください。
色付きセルは左が打数、右がパット数です。対象9ホールを合計し、9番または18番の直後の集計値と照合してください。右端のGROSS/NETは使いません。
ゲームポイントは各プレイヤー行の直下にある細い数値行の、対象9ホール最後の合計値です。確信できない参加者は返さないでください。"""
    prepared_image, prepared_mime_type = _prepare_scorecard_image(image_bytes, mime_type)
    encoded = base64.b64encode(prepared_image).decode("ascii")
    request_body = {
        "model": os.environ.get("OPENAI_VISION_MODEL", "gpt-5.4-mini"),
        "store": False,
        "input": [{
            "role": "user",
            "content": [
                {"type": "input_text", "text": prompt},
                {"type": "input_image", "image_url": f"data:{prepared_mime_type};base64,{encoded}", "detail": "high"},
            ],
        }],
        "text": {"format": {"type": "json_schema", "name": "scorecard_totals", "strict": True, "schema": schema}},
    }
    try:
        response = requests.post(
            "https://api.openai.com/v1/responses",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=request_body,
            timeout=60,
        )
    except requests.RequestException as exc:
        raise ScorecardOcrError("画像読み取りAPIに接続できませんでした。") from exc
    if not response.ok:
        try:
            message = response.json().get("error", {}).get("message", response.text)
        except ValueError:
            message = response.text
        raise ScorecardOcrError(f"画像読み取りに失敗しました: {message}")
    try:
        result = json.loads(_response_text(response.json()))
    except (ValueError, json.JSONDecodeError) as exc:
        raise ScorecardOcrError("画像読み取り結果を解釈できませんでした。") from exc

    member_by_name = {_normalise_name(str(member["name"])): int(member["member_id"]) for member in known_members}
    suggestions: dict[int, dict[str, int]] = {}
    for player in result.get("players", []):
        member_id = member_by_name.get(_normalise_name(str(player.get("name", ""))))
        score, putt, game_pt = player.get("score"), player.get("putt"), player.get("game_pt")
        if member_id is None or not all(isinstance(value, int) for value in (score, putt, game_pt)):
            continue
        if 0 <= score <= 100 and 0 <= putt <= 40 and -300 <= game_pt <= 300:
            suggestions[member_id] = {"score": score, "putt": putt, "game_pt": game_pt}
    return suggestions
