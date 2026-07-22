"""生成済みPDFを端末の共有シートへ渡すUI。"""

import base64
import json

import streamlit.components.v1 as components


def build_pdf_share_html(pdf_data, filename):
    """PDFをWeb Share APIへ渡すボタンHTMLを生成する。"""
    encoded_pdf = base64.b64encode(pdf_data).decode("ascii")
    filename_json = json.dumps(filename, ensure_ascii=False).replace("<", "\\u003c")
    return f"""
    <style>
      body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }}
      #share-pdf {{
        width: 100%; min-height: 48px; border: 0; border-radius: 8px;
        padding: 0.55rem 0.8rem; color: white; background: #06c755;
        font-size: 1rem; font-weight: 700; cursor: pointer;
      }}
      #share-pdf:disabled {{ opacity: 0.55; cursor: default; }}
      #share-status {{ margin: 0.35rem 0 0; color: #68707c; font-size: 0.82rem; }}
    </style>
    <button id="share-pdf" type="button">📤 LINEなどへPDFを共有</button>
    <p id="share-status">タップ後、共有先からLINEを選択してください。</p>
    <script>
      const button = document.querySelector("#share-pdf");
      const status = document.querySelector("#share-status");
      const binary = atob("{encoded_pdf}");
      const bytes = Uint8Array.from(binary, character => character.charCodeAt(0));
      const file = new File([bytes], {filename_json}, {{ type: "application/pdf" }});

      function shareNavigator() {{
        try {{
          if (window.parent && window.parent.navigator && window.parent.navigator.share) {{
            return window.parent.navigator;
          }}
        }} catch (error) {{}}
        return navigator;
      }}

      button.addEventListener("click", async () => {{
        const target = shareNavigator();
        if (!target.share || (target.canShare && !target.canShare({{ files: [file] }}))) {{
          status.textContent = "このブラウザではPDF共有を利用できません。上のダウンロードボタンをご利用ください。";
          return;
        }}
        button.disabled = true;
        try {{
          await target.share({{ files: [file] }});
          status.textContent = "共有先へPDFを渡しました。";
        }} catch (error) {{
          if (error && error.name !== "AbortError") {{
            status.textContent = "共有できませんでした。PDFをダウンロードしてLINEへ添付してください。";
          }}
        }} finally {{
          button.disabled = false;
        }}
      }});
    </script>
    """


def render_pdf_share_button(pdf_data, filename):
    """生成済みPDF用の共有ボタンを表示する。"""
    if not isinstance(pdf_data, bytes) or not pdf_data:
        raise ValueError("共有するPDFデータがありません")
    if not filename:
        raise ValueError("PDFファイル名がありません")
    components.html(build_pdf_share_html(pdf_data, filename), height=86)
