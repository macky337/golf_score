"""オフラインスコア入力UIをStreamlitに埋め込む。"""

from pathlib import Path

import streamlit.components.v1 as components


_PWA_PATH = Path(__file__).resolve().parent.parent / "static" / "offline-score"
def render_offline_score_pwa():
    """端末内で動くスコア入力UIを表示する。

    Railwayのプロキシ環境でカスタムコンポーネントの静的ファイルが取得できない場合があるため、
    ファイルを埋め込んで配信する。
    """
    index_html = (_PWA_PATH / "index.html").read_text(encoding="utf-8")
    styles = (_PWA_PATH / "styles.css").read_text(encoding="utf-8")
    script = (_PWA_PATH / "app.js").read_text(encoding="utf-8")

    body = index_html.split("<body>", 1)[1].split("</body>", 1)[0]
    body = body.replace('<script src="./app.js"></script>', "")
    embedded_html = f"<style>{styles}</style>{body}<script>{script}</script>"
    components.html(embedded_html, height=800, scrolling=True)
