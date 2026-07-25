import json
from io import BytesIO

import pytest
from PIL import Image

from modules.scorecard_ocr import ScorecardOcrError, _prepare_scorecard_image, _response_text, extract_scores


def test_response_text_reads_output_message():
    assert _response_text({"output": [{"type": "message", "content": [{"type": "output_text", "text": '{"players": []}'}]}]}) == '{"players": []}'


def test_response_text_rejects_empty_response():
    with pytest.raises(ScorecardOcrError):
        _response_text({"output": []})


def test_extract_scores_rejects_unknown_segment_before_calling_api(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    with pytest.raises(ScorecardOcrError, match="区分"):
        extract_scores(b"image", "image/jpeg", [{"member_id": 1, "name": "山田"}], "other")


def test_prepare_scorecard_image_rotates_portrait_image_to_landscape():
    raw = BytesIO()
    Image.new("RGB", (20, 40), "white").save(raw, format="PNG")

    result, mime_type = _prepare_scorecard_image(raw.getvalue(), "image/png")

    with Image.open(BytesIO(result)) as image:
        assert image.size == (40, 20)
    assert mime_type == "image/jpeg"
