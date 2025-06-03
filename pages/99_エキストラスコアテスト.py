import sys
import os

# モジュールのインポートパスを追加（より確実な方法）
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import streamlit as st
from modules.db import supabase

st.set_page_config(page_title="エキストラスコアテスト", page_icon="🧪", layout="wide")

st.title("🧪 エキストラスコア機能テスト")

# セクション1: ラウンドID 53の詳細確認
st.header("1. ラウンドID 53の詳細確認")

if st.button("ラウンドID 53をテスト"):
    try:
        # ラウンドID 53を検索
        round_53 = supabase.table('rounds').select('*').eq('round_id', 53).execute()
        
        if round_53.data:
            round_data = round_53.data[0]
            st.success("✓ ラウンドID 53が見つかりました")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("**ラウンド情報:**")
                st.json({
                    "round_id": round_data.get('round_id'),
                    "date_played": round_data.get('date_played'),
                    "course_name": round_data.get('course_name'),
                    "num_players": round_data.get('num_players'),
                    "has_extra": round_data.get('has_extra'),
                    "finalized": round_data.get('finalized')
                })
            
            with col2:
                # スコアデータを確認
                score_53 = supabase.table('score').select('*, member:member_id(name)').eq('round_id', 53).execute()
                if score_53.data:
                    st.write(f"**スコアデータ ({len(score_53.data)}件):**")
                    for score in score_53.data:
                        member_name = score['member']['name'] if score['member'] else f"Member {score['member_id']}"
                        st.write(f"👤 {member_name} (ID: {score['member_id']})")
                        st.write(f"  - Front: {score.get('front_score')}, Back: {score.get('back_score')}")
                        st.write(f"  - Extra: {score.get('extra_score')}, Putt: {score.get('extra_putt')}")
                        st.write(f"  - Game Pt: {score.get('extra_game_pt')}")
                        st.write("---")
                else:
                    st.warning("スコアデータが見つかりません")
                    
        else:
            st.error("ラウンドID 53が見つかりません")
            
            # 代替検索: 千葉関連のラウンド
            st.write("代替検索: 千葉関連のラウンド...")
            chiba_rounds = supabase.table('rounds').select('*').ilike('course_name', '%千葉%').execute()
            
            if chiba_rounds.data:
                st.success(f"✓ 千葉関連のラウンド: {len(chiba_rounds.data)}件")
                for round_data in chiba_rounds.data:
                    st.write(f"ID: {round_data['round_id']}, 日付: {round_data['date_played']}, コース: {round_data['course_name']}")
            else:
                st.warning("千葉関連のラウンドが見つかりません")
                
    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
        st.exception(e)

# セクション2: 最新のラウンド一覧
st.header("2. 最新のラウンド一覧")

if st.button("最新のラウンドを表示"):
    try:
        latest_rounds = supabase.table('rounds').select('round_id, date_played, course_name, has_extra, finalized, num_players').order('round_id', desc=True).limit(10).execute()
        
        if latest_rounds.data:
            st.success(f"✓ 最新の10ラウンド:")
            
            for r in latest_rounds.data:
                col1, col2, col3, col4 = st.columns([1, 2, 1, 1])
                with col1:
                    st.write(f"**ID: {r['round_id']}**")
                with col2:
                    st.write(f"{r['date_played']} - {r['course_name']}")
                with col3:
                    extra_status = "🎯" if r.get('has_extra') else "❌"
                    st.write(f"Extra: {extra_status}")
                with col4:
                    final_status = "✅" if r.get('finalized') else "⏳"
                    st.write(f"Final: {final_status}")
                
                # このラウンドにエキストラスコアボタンがあるかテスト
                if r.get('has_extra') and not r.get('finalized'):
                    if st.button(f"エキストラスコア入力をテスト (ID: {r['round_id']})", key=f"extra_{r['round_id']}"):
                        st.info(f"ラウンドID {r['round_id']} のエキストラスコア入力ページに移動できます")
                        
                st.write("---")
                
        else:
            st.warning("ラウンドが見つかりません")
            
    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
        st.exception(e)

# セクション3: データベース接続テスト
st.header("3. データベース接続テスト")

if st.button("データベース接続をテスト"):
    try:
        # 簡単なクエリでテスト
        test_result = supabase.table('rounds').select('count').execute()
        st.success("✓ データベース接続成功")
        st.write(f"ラウンドテーブルにアクセス可能")
        
        # テーブル一覧を取得
        members_count = supabase.table('members').select('count').execute()
        scores_count = supabase.table('score').select('count').execute()
        
        st.write("**テーブル状況:**")
        st.write(f"- Rounds: アクセス可能")
        st.write(f"- Members: アクセス可能")
        st.write(f"- Scores: アクセス可能")
        
    except Exception as e:
        st.error(f"❌ データベース接続エラー: {e}")
        st.exception(e)

st.write("---")
st.info("💡 このテストページは、エキストラスコア機能の問題を診断するために作成されました。")
st.info("管理画面の「エキストラスコア診断」タブも併せてご利用ください。")
