import sys
import os

# モジュールのインポートパスを追加（より確実な方法）
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import streamlit as st
from modules.db import supabase

st.set_page_config(page_title="エキストラスコア修正確認", page_icon="✅", layout="wide")

st.title("✅ エキストラスコア修正確認テスト")

st.markdown("""
## 🔧 修正内容
1. **セッション状態の初期化問題を修正**
   - ラウンドごとの初期化フラグを導入
   - データベース値の一度だけの初期化を保証
   
2. **フォームの初期値設定を修正**
   - `st.number_input`に`value`パラメータを追加
   - セッション状態の値がフォームに確実に反映される
   
3. **デバッグ情報の強化**
   - セッション状態キーの存在確認
   - 詳細な値追跡とデバッグ情報表示

## 🧪 テスト手順
1. このページでテスト用のラウンドを選択
2. エキストラスコア入力ページに移動
3. 値を入力して保存
4. 保存後の値が0にならないことを確認
""")

# テスト用のラウンド情報を取得
st.header("1. テスト用ラウンドの選択")

try:
    # 最新のラウンドを取得（エキストラホール有効なもの）
    rounds_result = supabase.table('rounds').select(
        'round_id, date_played, course_name, has_extra, finalized, num_players'
    ).order('round_id', desc=True).limit(10).execute()
    
    if rounds_result.data:
        st.success(f"✓ 最新の10ラウンドを取得しました")
        
        for round_data in rounds_result.data:
            col1, col2, col3, col4 = st.columns([1, 2, 1, 1])
            
            with col1:
                st.write(f"**ID: {round_data['round_id']}**")
            
            with col2:
                st.write(f"{round_data['date_played']} - {round_data['course_name']}")
            
            with col3:
                extra_icon = "🎯" if round_data.get('has_extra') else "❌"
                st.write(f"Extra: {extra_icon}")
            
            with col4:
                if round_data.get('has_extra') and not round_data.get('finalized'):
                    if st.button(f"テスト", key=f"test_{round_data['round_id']}"):
                        st.session_state.active_round_id = round_data['round_id']
                        st.success(f"ラウンドID {round_data['round_id']} を選択しました")
                        st.info("サイドバーから「エキストラスコア入力」を選択してください")
                else:
                    final_text = "確定済み" if round_data.get('finalized') else "Extra無効"
                    st.write(f"⚠️ {final_text}")
            
            st.write("---")
    else:
        st.warning("ラウンドデータが見つかりません")

except Exception as e:
    st.error(f"❌ エラー: {e}")

# セッション状態の確認
st.header("2. セッション状態の確認")

if st.button("セッション状態を表示"):
    st.write("**現在のセッション状態:**")
    
    # アクティブなラウンドID
    if "active_round_id" in st.session_state:
        st.write(f"✓ アクティブラウンドID: {st.session_state.active_round_id}")
    else:
        st.write("❌ アクティブラウンドIDが設定されていません")
    
    # エキストラスコア関連のキー
    extra_keys = [key for key in st.session_state.keys() if 'extra_' in key]
    if extra_keys:
        st.write(f"**エキストラスコア関連キー ({len(extra_keys)}個):**")
        for key in sorted(extra_keys):
            st.write(f"- {key}: {st.session_state[key]}")
    else:
        st.write("エキストラスコア関連のセッション状態はありません")

# テスト用データの作成
st.header("3. テスト用データの作成")

if st.button("テスト用ラウンドを作成"):
    try:
        # テスト用ラウンドを作成
        import datetime
        test_date = datetime.date.today().strftime('%Y-%m-%d')
        
        test_round_data = {
            'date_played': test_date,
            'course_name': 'テスト用コース (エキストラスコア修正確認)',
            'has_extra': True,
            'finalized': False,
            'num_players': 4
        }
        
        # ラウンドを挿入
        round_result = supabase.table('rounds').insert(test_round_data).execute()
        
        if round_result.data:
            new_round_id = round_result.data[0]['round_id']
            st.success(f"✅ テスト用ラウンドを作成しました (ID: {new_round_id})")
            
            # テスト用のスコアデータも作成
            test_members = [1, 2, 3, 4]  # 仮のメンバーID
            
            for member_id in test_members:
                score_data = {
                    'round_id': new_round_id,
                    'member_id': member_id,
                    'front_score': 45,
                    'back_score': 47,
                    'front_putt': 18,
                    'back_putt': 19,
                    'extra_score': 0,
                    'extra_putt': 0,
                    'extra_game_pt': 0
                }
                
                supabase.table('score').insert(score_data).execute()
            
            st.success(f"✅ {len(test_members)}人のスコアデータを作成しました")
            st.info(f"ラウンドID {new_round_id} でエキストラスコアのテストができます")
            
            # セッション状態にも設定
            st.session_state.active_round_id = new_round_id
            
        else:
            st.error("❌ テスト用ラウンドの作成に失敗しました")
            
    except Exception as e:
        st.error(f"❌ エラーが発生しました: {e}")
        st.exception(e)

st.write("---")

st.info("""
💡 **テスト手順:**
1. 上記でテスト用ラウンドを作成するか、既存のラウンドを選択
2. サイドバーから「エキストラスコア入力」を選択
3. 各プレイヤーの値を入力（例: スコア=5, パット=2, GP=10）
4. 「スコアを保存」ボタンを押す
5. 保存後、入力した値が表示されているか確認
6. 再度ページをリロードして、値が保持されているか確認

**修正前の問題:** 保存すると全員の値が0になっていた
**修正後の期待値:** 入力した値が正しく保存され、表示される
""")
