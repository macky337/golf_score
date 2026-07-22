"""オフラインスコア入力UIをStreamlitに埋め込む。"""

import base64
import hashlib
import json
from pathlib import Path

import streamlit.components.v1 as components


_PWA_PATH = Path(__file__).resolve().parent.parent / "static" / "offline-score"


def offline_instance_id(round_data, players):
    """ID再利用時にも別ラウンドを区別できる端末保存用識別子を返す。"""
    identity = {
        "round_id": round_data.get("round_id"),
        "created_at": round_data.get("created_at"),
        "date_played": round_data.get("date_played"),
        "course_name": round_data.get("course_name"),
        "member_ids": sorted(player.get("member_id") for player in players),
    }
    serialized = json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:24]


def _initial_package_script(package):
    """HTMLを壊さずに開始データを埋め込むスクリプトを返す。"""
    if package is None:
        return ""
    encoded = base64.b64encode(
        json.dumps(package, ensure_ascii=False).encode("utf-8")
    ).decode("ascii")
    return (
        "<script>window.__GOLF_SCORE_INITIAL_PACKAGE__ = "
        f"JSON.parse(new TextDecoder().decode(Uint8Array.from(atob('{encoded}'), "
        "character => character.charCodeAt(0))));</script>"
    )


def render_offline_score_pwa(package=None):
    """端末内で動くスコア入力UIを表示する。

    Railwayのプロキシ環境でカスタムコンポーネントの静的ファイルが取得できない場合があるため、
    ファイルを埋め込んで配信する。
    """
    index_html = (_PWA_PATH / "index.html").read_text(encoding="utf-8")
    styles = (_PWA_PATH / "styles.css").read_text(encoding="utf-8")
    script = (_PWA_PATH / "app.js").read_text(encoding="utf-8")

    body = index_html.split("<body>", 1)[1].split("</body>", 1)[0]
    body = body.replace('<script src="./app.js"></script>', "")
    initial_package = _initial_package_script(package)
    embedded_html = (
        f"<style>{styles}</style>{body}{initial_package}<script>{script}</script>"
    )
    components.html(embedded_html, height=800, scrolling=True)
