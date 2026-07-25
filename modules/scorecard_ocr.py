"""Vision-based scorecard reader.

Golf Network scorecards are dense, sideways tables.  Local OCR cannot reliably
associate the vertical player names with the OUT/IN totals, so this module uses
the configured OpenAI vision API and returns reviewable suggestions only.
"""
from __future__ import annotations

import base64
import json
import os
from typing import Any, Iterable

import requests


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


def extract_scores(
    image_bytes: bytes,
    mime_type: str,
    members: Iterable[dict[str, Any]],
    segment: str,
) -> dict[int, dict[str, int]]:
    """Read OUT or IN totals from a Golf Network scorecard image.

    ``segment`` must be ``front`` (holes 1-9) or ``back`` (holes 10-18).
    The table can be sideways; the model is explicitly instructed to orient it
    before reading.  Game points are intentionally not inferred from this card.
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
                    },
                    "required": ["name", "score", "putt"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["players"],
        "additionalProperties": False,
    }
    prompt = f"""この画像は Golf Network のゴルフスコア表です。画像が横向きなら、まず正しい向きに回転して読み取ってください。
対象は {target} の合計欄です。各プレイヤーについて、合計スコアと合計パット数を抽出してください。
照合対象の参加者は次の名前だけです: {names}。
画像にいない参加者や、数値を確信できない参加者は返さないでください。各ホールの数字やGROSS/NETではなく、対象9ホールの集計欄を使ってください。ゲームポイントは抽出しません。"""
    encoded = base64.b64encode(image_bytes).decode("ascii")
    request_body = {
        "model": os.environ.get("OPENAI_VISION_MODEL", "gpt-5.4-mini"),
        "store": False,
        "input": [{
            "role": "user",
            "content": [
                {"type": "input_text", "text": prompt},
                {"type": "input_image", "image_url": f"data:{mime_type};base64,{encoded}", "detail": "high"},
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

    member_by_name = {str(member["name"]).replace(" ", ""): int(member["member_id"]) for member in known_members}
    suggestions: dict[int, dict[str, int]] = {}
    for player in result.get("players", []):
        member_id = member_by_name.get(str(player.get("name", "")).replace(" ", ""))
        score, putt = player.get("score"), player.get("putt")
        if member_id is None or not isinstance(score, int) or not isinstance(putt, int):
            continue
        if 0 <= score <= 100 and 0 <= putt <= 40:
            suggestions[member_id] = {"score": score, "putt": putt}
    return suggestions
