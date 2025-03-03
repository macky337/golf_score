import streamlit as st

def apply_fixed_first_column_style():
    """固定列スタイルをアプリケーション全体に適用するヘルパー関数"""
    st.markdown("""
        <style>
        /* データフレームテーブルのプレイヤー列を固定表示 */
        [data-testid="stDataFrame"] table {
            position: relative !important;
        }
        
        [data-testid="stDataFrame"] table th:first-child,
        [data-testid="stDataFrame"] table td:first-child {
            position: sticky !important;
            left: 0 !important;
            background-color: white !important;
            z-index: 1 !important;
            box-shadow: 2px 0px 3px rgba(0,0,0,0.1) !important;
        }
        
        /* テーブルヘッダーとプレイヤー列の交差部分 */
        [data-testid="stDataFrame"] table th:first-child {
            z-index: 2 !important;
            background-color: #f0f2f6 !important;
        }
        
        /* スクロール時にヘッダーの背景が透明になるのを防ぐ */
        [data-testid="stDataFrame"] table thead th {
            background-color: #f0f2f6 !important;
        }
        
        /* スクロールバーを常に表示 */
        [data-testid="stDataFrame"] {
            overflow-x: auto !important;
            max-width: 100% !important;
        }
        
        /* マルチインデックスヘッダー対応 */
        [data-testid="stDataFrame"] table tr:nth-child(1) th:first-child,
        [data-testid="stDataFrame"] table tr:nth-child(2) th:first-child {
            position: sticky !important;
            left: 0 !important;
            z-index: 2 !important;
            background-color: #f0f2f6 !important;
        }
        </style>
    """, unsafe_allow_html=True)
