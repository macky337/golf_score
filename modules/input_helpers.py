"""
スマホ/PC対応の入力ヘルパー関数
"""
import streamlit as st


def is_mobile():
    """
    モバイルデバイスかどうかを判定
    Streamlit の session_state にデバイス情報がある場合はそれを使用
    なければ画面幅で判定（簡易版）
    """
    # セッション状態にキャッシュ
    if 'is_mobile_device' not in st.session_state:
        # Streamlit は User-Agent に直接アクセスできないため、
        # カスタムコンポーネントなしでは画面幅による判定を使用
        # ユーザーが手動で切り替えられるトグルを提供
        st.session_state.is_mobile_device = False
    
    return st.session_state.is_mobile_device


def toggle_input_mode():
    """
    入力モードを切り替えるトグルボタンを表示
    ページの上部に配置して、ユーザーが手動で切り替え可能にする
    """
    col1, col2 = st.columns([0.7, 0.3])
    with col2:
        current_mode = "📱 スマホモード" if st.session_state.get('is_mobile_device', False) else "💻 PCモード"
        if st.button(f"🔄 {current_mode}", key="toggle_mode_btn"):
            st.session_state.is_mobile_device = not st.session_state.get('is_mobile_device', False)
            st.rerun()


def smart_number_input(label, key, min_value=0, max_value=100, default_value=0, step_buttons=None):
    """
    スマホ/PC対応の数値入力ウィジェット
    
    Parameters:
    -----------
    label : str
        ラベル
    key : str
        session_state のキー
    min_value : int
        最小値
    max_value : int
        最大値
    default_value : int
        デフォルト値
    step_buttons : list of int, optional
        スマホモード時のステップボタン（例: [-5, -1, 1, 5]）
        指定しない場合は自動設定
    
    Returns:
    --------
    int : 入力された値
    """
    # session_state の初期化
    if key not in st.session_state:
        st.session_state[key] = default_value
    
    # デフォルトのステップボタン
    if step_buttons is None:
        if max_value <= 50:
            step_buttons = [-5, -1, 1, 5]
        else:
            step_buttons = [-10, -1, 1, 10]
    
    if is_mobile():
        # スマホモード: st.number_input のみ（フォーム内でボタンは使用不可）
        # ステップを小さくして上下矢印で調整しやすくする
        st.session_state[key] = st.number_input(
            label,
            min_value=min_value,
            max_value=max_value,
            value=st.session_state[key],
            step=1,  # 1ずつ増減
            key=f"{key}_mobile",
            help="📱 スマホモード: 上下矢印で1ずつ調整できます"
        )
        return st.session_state[key]
    
    else:
        # PCモード: 通常の number_input
        st.session_state[key] = st.number_input(
            label,
            min_value=min_value,
            max_value=max_value,
            value=st.session_state[key],
            key=f"{key}_pc"
        )
        return st.session_state[key]
