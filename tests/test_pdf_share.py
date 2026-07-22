import base64
import re

import pytest

from modules.pdf_share import build_pdf_share_html, render_pdf_share_button


def test_pdf_share_html_embeds_pdf_and_escapes_filename():
    pdf_data = b"%PDF-1.4\nexample"
    markup = build_pdf_share_html(pdf_data, '結果 "確定"</script>.pdf')
    encoded = re.search(r'atob\("([A-Za-z0-9+/=]+)"\)', markup).group(1)

    assert base64.b64decode(encoded) == pdf_data
    assert 'new File([bytes], "結果 \\"確定\\"\\u003c/script>.pdf"' in markup
    assert "</script>.pdf" not in markup
    assert "LINEなどへPDFを共有" in markup
    assert "navigator.share" in markup


@pytest.mark.parametrize("pdf_data, filename", [(b"", "result.pdf"), (b"pdf", "")])
def test_pdf_share_button_rejects_missing_data(pdf_data, filename):
    with pytest.raises(ValueError):
        render_pdf_share_button(pdf_data, filename)
