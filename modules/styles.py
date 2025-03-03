import streamlit as st

def apply_fixed_first_column_style():
    """固定列スタイルをアプリケーション全体に適用するヘルパー関数"""
    st.markdown("""
        <style>
        /* プレイヤー列を強制的に固定表示するためのより強力なCSS */
        [data-testid="stDataFrame"] div[data-testid="stTable"] table,
        [data-testid="stDataFrame"] > div > div > div > div > div table {
            position: relative !important;
            border-collapse: collapse !important;
            table-layout: auto !important;
        }
        
        [data-testid="stDataFrame"] div[data-testid="stTable"] table th:first-of-type,
        [data-testid="stDataFrame"] div[data-testid="stTable"] table td:first-of-type,
        [data-testid="stDataFrame"] > div > div > div > div > div table th:first-of-type,
        [data-testid="stDataFrame"] > div > div > div > div > div table td:first-of-type {
            position: sticky !important;
            left: 0 !important;
            background-color: white !important;
            z-index: 10 !important;
            box-shadow: 2px 0px 3px rgba(0,0,0,0.1) !important;
            min-width: 100px !重要;
        }
        
        /* ヘッダーとプレイヤー列の交差部分 */
        [data-testid="stDataFrame"] div[data-testid="stTable"] table thead tr:first-child th:first-child,
        [data-testid="stDataFrame"] div[data-testid="stTable"] table thead tr:nth-child(2) th:first-child,
        [data-testid="stDataFrame"] > div > div > div > div > div table thead tr:first-child th:first-child,
        [data-testid="stDataFrame"] > div > div > div > div > div table thead tr:nth-child(2) th:first-child {
            z-index: 20 !important;
            background-color: #f0f2f6 !important;
        }
        
        /* すべてのヘッダーセルの背景色を設定 */
        [data-testid="stDataFrame"] div[data-testid="stTable"] table thead th,
        [data-testid="stDataFrame"] > div > div > div > div > div table thead th {
            background-color: #f0f2f6 !important;
            position: relative !important;
            z-index: 5 !important;
        }
        
        /* スクロールコンテナを指定 */
        [data-testid="stDataFrame"] > div {
            overflow-x: auto !important;
            max-width: 100% !important;
            display: block !important;
        }
        
        /* マルチインデックスヘッダー対応 */
        [data-testid="stDataFrame"] div[data-testid="stTable"] table tr th:first-child,
        [data-testid="stDataFrame"] > div > div > div > div > div table tr th:first-child {
            position: sticky !important;
            left: 0 !important;
            z-index: 20 !important;
        }
        
        /* スタイルの優先度を上げる */
        html body [data-testid="stDataFrame"] div[data-testid="stTable"] table td:first-of-type {
            position: sticky !重要;
            left: 0 !重要;
            background-color: white !重要;
        }
        </style>
    """, unsafe_allow_html=True)
