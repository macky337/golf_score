"""
スマホ/PC対応の入力ヘルパー関数
"""
import streamlit as st
import streamlit.components.v1 as components


def close_sidebar_on_mobile():
    """
    スマホでサイドバーを閉じ、共通ボトムナビゲーションを表示する。
    """
    from modules.mobile_navigation import render_mobile_navigation

    render_mobile_navigation()


def inject_numeric_keyboard_css():
    """
    スマホでテンキーを表示させるためのメタタグとCSSを注入
    より確実にテンキーを表示させるため、複数の方法を組み合わせる
    """
    # メタタグでモバイル最適化
    st.markdown("""
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    """, unsafe_allow_html=True)
    
    # CSSとJavaScriptで数値入力を最適化
    st.markdown("""
    <style>
    /* 数値入力フィールドのスタイル調整 */
    input[type="number"] {
        -webkit-appearance: none;
        -moz-appearance: textfield;
        font-size: 16px !important; /* iOS zoomを防ぐ */
    }
    /* スピナーを非表示 */
    input[type="number"]::-webkit-inner-spin-button,
    input[type="number"]::-webkit-outer-spin-button {
        -webkit-appearance: none;
        margin: 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # JavaScriptで動的に属性を追加（より積極的なアプローチ）
    components.html("""
    <script>
    (function() {
        function setNumericKeyboard() {
            // 親ウィンドウのinput要素にアクセス
            try {
                const parentDoc = window.parent.document;
                const inputs = parentDoc.querySelectorAll('input[type="number"]');
                
                inputs.forEach(function(input) {
                    const min = parseFloat(input.getAttribute('min') || '0');
                    
                    // 既にイベントリスナーが追加されているかチェック
                    if (input.hasAttribute('data-auto-select-added')) {
                        return;
                    }
                    input.setAttribute('data-auto-select-added', 'true');
                    
                    // min値が負の場合はフルキーボード、それ以外はテンキー
                    if (min < 0) {
                        // マイナス入力が必要なフィールド
                        input.removeAttribute('inputmode');
                        input.removeAttribute('pattern');
                    } else {
                        // 0以上の数字のみ（テンキー表示）
                        input.setAttribute('inputmode', 'numeric');
                        input.setAttribute('pattern', '[0-9]*');
                    }
                    
                    // フォーカス時の処理
                    input.addEventListener('focus', function() {
                        const min = parseFloat(this.getAttribute('min') || '0');
                        
                        // キーボードタイプの設定
                        if (min < 0) {
                            this.removeAttribute('inputmode');
                            this.removeAttribute('pattern');
                        } else {
                            this.setAttribute('inputmode', 'numeric');
                            this.setAttribute('pattern', '[0-9]*');
                        }
                        
                        // フォーカス時に全選択（上書きモード）
                        // 少し遅延させてキーボード表示後に実行
                        setTimeout(() => {
                            this.select();
                        }, 50);
                    }, true);
                    
                    // クリック時も全選択
                    input.addEventListener('click', function() {
                        this.select();
                    }, true);
                });
            } catch(e) {
                console.log('Could not access parent document:', e);
            }
        }
        
        // 複数のタイミングで実行
        setNumericKeyboard();
        setTimeout(setNumericKeyboard, 100);
        setTimeout(setNumericKeyboard, 500);
        setTimeout(setNumericKeyboard, 1000);
        
        // MutationObserverで継続的に監視
        if (window.parent && window.parent.document) {
            const observer = new MutationObserver(setNumericKeyboard);
            try {
                observer.observe(window.parent.document.body, {
                    childList: true,
                    subtree: true
                });
            } catch(e) {
                console.log('Observer error:', e);
            }
        }
    })();
    </script>
    """, height=0)


def inject_numeric_keyboard_css_optimized():
    """
    最適化版：1回のみ実行するテンキー対応JavaScript
    iPhoneでの固まり問題を解決
    """
    # CSSのみ（軽量）
    st.markdown("""
    <style>
    /* 数値入力フィールドのスタイル調整 */
    input[type="number"] {
        -webkit-appearance: none;
        -moz-appearance: textfield;
        font-size: 16px !important; /* iOS zoomを防ぐ */
    }
    /* スピナーを非表示 */
    input[type="number"]::-webkit-inner-spin-button,
    input[type="number"]::-webkit-outer-spin-button {
        -webkit-appearance: none;
        margin: 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 最適化されたJavaScript（1回のみ実行、エラーハンドリング強化）
    components.html("""
    <script>
    (function() {
        try {
            // 親ウィンドウが存在するかチェック
            if (!window.parent || !window.parent.document) {
                console.log('Parent window not accessible');
                return;
            }
            
            const parentDoc = window.parent.document;
            
            // グローバルフラグで重複実行を防止
            if (parentDoc._keyboardOptimizationApplied) {
                return;
            }
            parentDoc._keyboardOptimizationApplied = true;
            
            function optimizeInput(input) {
                try {
                    // 既に最適化済みならスキップ
                    if (input.dataset.keyboardOptimized) return;
                    input.dataset.keyboardOptimized = 'true';
                    
                    const minValue = parseFloat(input.getAttribute('min') || '0');
                    
                    // inputmodeの設定
                    if (minValue >= 0) {
                        input.setAttribute('inputmode', 'numeric');
                        input.setAttribute('pattern', '[0-9]*');
                    } else {
                        input.removeAttribute('inputmode');
                        input.removeAttribute('pattern');
                    }
                    
                    // 全選択イベント（1回のみ登録）
                    if (!input.dataset.selectListenerAdded) {
                        input.dataset.selectListenerAdded = 'true';
                        input.addEventListener('focus', function() { 
                            setTimeout(() => {
                                try { this.select(); } catch(e) {}
                            }, 50); 
                        });
                        input.addEventListener('click', function() { 
                            try { this.select(); } catch(e) {}
                        });
                    }
                } catch(e) {
                    console.log('Error optimizing input:', e);
                }
            }
            
            function applyOptimization() {
                try {
                    const inputs = parentDoc.querySelectorAll('input[type="number"]');
                    inputs.forEach(optimizeInput);
                } catch(e) {
                    console.log('Error in applyOptimization:', e);
                }
            }
            
            // 初回実行
            applyOptimization();
            
            // 軽量なMutationObserver（新規要素のみ監視）
            try {
                const observer = new MutationObserver(function(mutations) {
                    try {
                        for (const mutation of mutations) {
                            for (const node of mutation.addedNodes) {
                                if (node.nodeType === 1) {
                                    if (node.tagName === 'INPUT' && node.type === 'number') {
                                        optimizeInput(node);
                                    } else if (node.querySelector) {
                                        const inputs = node.querySelectorAll('input[type="number"]');
                                        if (inputs.length > 0) {
                                            inputs.forEach(optimizeInput);
                                        }
                                    }
                                }
                            }
                        }
                    } catch(e) {
                        console.log('Error in MutationObserver callback:', e);
                    }
                });
                
                observer.observe(parentDoc.body, {
                    childList: true,
                    subtree: true
                });
            } catch(e) {
                console.log('Error creating MutationObserver:', e);
            }
        } catch(e) {
            console.log('Error in keyboard optimization script:', e);
        }
    })();
    </script>
    """, height=0)


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
        # 現在のモードを表示（わかりやすく）
        if st.session_state.get('is_mobile_device', False):
            current_mode = "📱 スマホモード"
            button_label = "💻 PCモードへ"
        else:
            current_mode = "💻 PCモード"
            button_label = "📱 スマホモードへ"
        
        # 現在のモードを表示
        st.caption(f"現在: {current_mode}")
        
        # 切り替えボタン
        if st.button(button_label, key="toggle_mode_btn"):
            st.session_state.is_mobile_device = not st.session_state.get('is_mobile_device', False)
            st.rerun()


def smart_number_input(label, key, min_value=0, max_value=100, default_value=0, step_buttons=None):
    """
    スマホ/PC対応の数値入力ウィジェット
    自動的にテンキーを表示
    
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
    
    # テンキー表示用のJavaScriptを注入（1回のみ実行）
    if '_keyboard_injected' not in st.session_state:
        inject_numeric_keyboard_css()
        st.session_state._keyboard_injected = True
    
    if is_mobile():
        # スマホモード: テンキー対応の入力フィールド
        st.session_state[key] = st.number_input(
            label,
            min_value=min_value,
            max_value=max_value,
            value=st.session_state[key],
            step=1,
            key=f"{key}_mobile",
            help="📱 数字をタップして入力できます"
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
