import json

import pytest

from modules.scorecard_ocr import ScorecardOcrError, _response_text, extract_scores


def test_response_text_reads_output_message():
    assert _response_text({"output": [{"type": "message", "content": [{"type": "output_text", "text": '{"players": []}'}]}]}) == '{"players": []}'


def test_response_text_rejects_empty_response():
    with pytest.raises(ScorecardOcrError):
        _response_text({"output": []})


def test_extract_scores_rejects_extra_before_calling_api(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    with pytest.raises(ScorecardOcrError, match="エキストラ"):
        extract_scores(b"image", "image/jpeg", [{"member_id": 1, "name": "山田"}], "extra")
