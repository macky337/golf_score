"""オフラインスコア入力PWAをStreamlitコンポーネントとして配信する。"""

from pathlib import Path

import streamlit.components.v1 as components


_PWA_PATH = Path(__file__).resolve().parent.parent / "static" / "offline-score"
_offline_score_component = components.declare_component(
    "offline_score",
    path=str(_PWA_PATH),
)


def render_offline_score_pwa():
    """端末内で動くPWA入力画面を表示する。"""
    _offline_score_component(default=None, height=760)
