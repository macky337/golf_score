import sys
import os

# モジュールのインポートパスを追加（より確実な方法）
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import streamlit as st
import pandas as pd
import datetime
import numpy as np
from modules.db import supabase
from modules.supabase_client import get_supabase_client  # supabase_client から直接インポート
import calendar
from streamlit_extras.switch_page_button import switch_page
import plotly.express as px
import plotly.graph_objects as go

# ページ設定
st.set_page_config(
    page_title="ポイント集計 - Golf Score App",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def run():
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.title("ポイント集計")
    with col2:
        if st.button("🏠 Home"):
            switch_page("main")

    # 3つのタブを作成
    tab1, tab2, tab3, tab4 = st.tabs(["通算成績", "年度別集計", "月間集計", "集計検証"])
    
    with tab1:
        show_all_time_statistics()
    
    with tab2:
        show_yearly_statistics()
    
    with tab3:
        show_monthly_statistics()
    
    with tab4:
        verify_point_balance()

def get_all_scores():
    """すべての確定済みスコアデータを取得"""
    try:
        # スコアデータとround_resultsデータを取得（確定済みラウンドのみに絞り込み）
        # スコアデータ取得
        scores = supabase.table('score').select(
            '*, rounds(date_played, course_name, finalized), member(name)'
        ).eq('rounds.finalized', True).execute()
        
        if not scores.data:
            return []
            
        # round_resultsテーブルからポイントデータを取得
        round_results = supabase.table('round_results').select('*').execute()
        round_results_data = {}
        
        # 検索を高速化するためのインデックス作成
        if round_results.data:
            for result in round_results.data:
                member_id = result.get('member_id')
                round_id = result.get('round_id')
                if member_id and round_id:
                    key = f"{round_id}_{member_id}"
                    round_results_data[key] = result

        # 有効なスコアデータのみをフィルタリング
        filtered_scores = []
        for score in scores.data:
            # 無効なデータはスキップ
            if not score.get('rounds') or not score.get('member') or not score['member'].get('name'):
                continue
                
            # round_resultsから対応するデータを取得
            round_id = score.get('round_id')
            member_id = score.get('member_id')
            result_key = f"{round_id}_{member_id}"
              # round_resultsからポイント成分を取得してtotal_ptを計算
            round_result = round_results_data.get(result_key, {})
            match_pt = round_result.get('match_pt', 0) or 0
            putt_pt = round_result.get('putt_pt', 0) or 0
            total_game_pt = round_result.get('total_game_pt', 0) or 0
            score['total_pt'] = match_pt + putt_pt + total_game_pt
            
            filtered_scores.append(score)
        
        # デバッグ出力
        print(f"取得したスコア数: {len(filtered_scores)}")
        return filtered_scores

    except Exception as e:
        st.error(f"スコアデータの取得中にエラーが発生しました: {str(e)}")
        print(f"スコアデータ取得エラー詳細: {str(e)}")
        return []

def aggregate_player_points(scores):
    """プレイヤーごとのポイントを集計（シンプル版）"""
    player_points = {}
    
    for score in scores:
        player_name = score['member']['name']
        
        if player_name not in player_points:
            player_points[player_name] = {
                'Total Pt': 0,
                'Rounds': 0
            }
        
        # total_ptのみ集計
        player_points[player_name]['Total Pt'] += score['total_pt']
        player_points[player_name]['Rounds'] += 1

    return player_points

def create_summary_dataframe(player_points):
    """集計結果からシンプルなDataFrameを作成"""
    # DataFrameに変換
    df = pd.DataFrame.from_dict(player_points, orient='index')
    
    # 平均ポイントを計算
    df['Avg Total Pt'] = (df['Total Pt'] / df['Rounds']).round(2)
    
    # プレイヤー名をインデックスから列に移動
    df = df.reset_index().rename(columns={'index': 'Player'})
    
    # 列の順序を設定（シンプル版）
    columns = ['Player', 'Rounds', 'Total Pt', 'Avg Total Pt']
    df = df[columns]
    
    # Total Ptの降順でソート
    df = df.sort_values('Total Pt', ascending=False)
    
    return df

def show_all_time_statistics():
    """全期間の通算成績を表示（シンプル版）"""
    st.subheader("通算成績")
    
    # すべてのスコアを取得
    all_scores = get_all_scores()
    
    if not all_scores:
        st.info("スコアデータが見つかりません。")
        return
    
    # プレイヤーごとに集計
    player_points = aggregate_player_points(all_scores)
    
    if not player_points:
        st.info("集計可能なデータが見つかりません。")
        return
    
    # DataFrameに変換
    df = create_summary_dataframe(player_points)
    
    # 結果の表示
    st.markdown("### 全期間通算成績")
    
    # データフレームの表示（数値を見やすく整形）
    formatted_df = df.copy()
    formatted_df['Total Pt'] = formatted_df['Total Pt'].map('{:+d}'.format)
    formatted_df['Rounds'] = formatted_df['Rounds'].map('{:d}'.format)
    formatted_df['Avg Total Pt'] = formatted_df['Avg Total Pt'].map('{:+.2f}'.format)
    
    st.dataframe(
        formatted_df,
        column_config={
            "Player": "プレイヤー",
            "Rounds": "ラウンド数",
            "Total Pt": "Total Pt 合計",
            "Avg Total Pt": "Total Pt 平均"
        },
        use_container_width=True
    )
    
    # Total Ptのグラフ表示
    st.subheader("累計ポイント")
    
    fig = go.Figure()
    
    # Total Ptのみ表示（シンプル版）
    fig.add_trace(go.Bar(
        x=df['Player'],
        y=df['Total Pt'],
        name='Total Pt',
        text=df['Total Pt'].apply(lambda x: f"{x:+d}"),
        textposition='auto',
        marker_color='rgba(50, 171, 96, 0.7)',
        marker_line_color='rgba(50, 171, 96, 1)',
        marker_line_width=1.5
    ))
    
    fig.update_layout(
        xaxis_title='プレイヤー',
        yaxis_title='ポイント',
        title='プレイヤー別合計ポイント'
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_yearly_statistics():
    """年度別の集計結果を表示（シンプル版）"""
    st.subheader("年度別集計")
    
    # すべてのスコアを取得
    all_scores = get_all_scores()
    
    if not all_scores:
        st.info("スコアデータが見つかりません。")
        return
    
    # スコアから年度の一覧を作成
    years = set()
    for score in all_scores:
        if score['rounds']['date_played']:
            year = score['rounds']['date_played'].split('-')[0]
            years.add(year)
    
    if not years:
        st.info("集計可能な年度のデータが見つかりません。")
        return
    
    # 年度の選択
    selected_year = st.selectbox(
        "年度を選択",
        options=sorted(years, reverse=True)
    )
    
    if selected_year:
        # 選択した年度のスコアをフィルタリング
        year_scores = [
            score for score in all_scores
            if score['rounds']['date_played'] and score['rounds']['date_played'].startswith(selected_year)
        ]
        
        if not year_scores:
            st.info(f"{selected_year}年度のデータが見つかりません。")
            return
        
        # プレイヤーごとに集計
        player_points = aggregate_player_points(year_scores)
        
        if not player_points:
            st.info(f"{selected_year}年度の集計可能なデータが見つかりません。")
            return
        
        # DataFrameに変換
        df = create_summary_dataframe(player_points)
        
        # 結果の表示
        st.markdown(f"### {selected_year}年度 集計結果")
        
        # データフレームの表示（数値を見やすく整形）
        formatted_df = df.copy()
        formatted_df['Total Pt'] = formatted_df['Total Pt'].map('{:+d}'.format)
        formatted_df['Rounds'] = formatted_df['Rounds'].map('{:d}'.format)
        formatted_df['Avg Total Pt'] = formatted_df['Avg Total Pt'].map('{:+.2f}'.format)
        
        st.dataframe(
            formatted_df,
            column_config={
                "Player": "プレイヤー",
                "Rounds": "ラウンド数",
                "Total Pt": "Total Pt 合計",
                "Avg Total Pt": "Total Pt 平均"
            },
            use_container_width=True
        )
        
        # Total Ptのグラフ表示
        st.subheader("合計ポイント分布")
        
        fig = go.Figure()
        
        # Total Ptのみ表示（シンプル版）
        fig.add_trace(go.Bar(
            x=df['Player'],
            y=df['Total Pt'],
            name='Total Pt',
            text=df['Total Pt'].apply(lambda x: f"{x:+d}"),
            textposition='auto',
            marker_color='rgba(50, 171, 96, 0.7)',
            marker_line_color='rgba(50, 171, 96, 1)',
            marker_line_width=1.5
        ))
        
        fig.update_layout(
            xaxis_title='プレイヤー',
            yaxis_title='ポイント',
            title=f'{selected_year}年度 プレイヤー別合計ポイント'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 月別の推移グラフ
        st.subheader("月別推移")
        
        # スコアを月別に分類
        monthly_data = {}
        for score in year_scores:
            if not score['rounds']['date_played']:
                continue
                
            date_parts = score['rounds']['date_played'].split('-')
            if len(date_parts) >= 2:
                month = int(date_parts[1])
                player = score['member']['name']
                
                if month not in monthly_data:
                    monthly_data[month] = {}
                
                if player not in monthly_data[month]:
                    monthly_data[month][player] = {
                        'Total Pt': 0,
                        'Rounds': 0
                    }
                
                # Total Ptの集計
                monthly_data[month][player]['Total Pt'] += score.get('total_pt', 0)
                monthly_data[month][player]['Rounds'] += 1
          # 月別データをDataFrameに変換
        monthly_records = []
        for month, players in monthly_data.items():
            # プレイヤーを名前順でソート
            for player, stats in sorted(players.items()):
                monthly_records.append({
                    'Month': month,
                    'Player': player,
                    'Total Pt': stats['Total Pt'],
                    'Rounds': stats['Rounds']
                })
        
        if monthly_records:
            monthly_df = pd.DataFrame(monthly_records)
            
            # 月の名前を追加
            month_names = {
                1: '1月', 2: '2月', 3: '3月', 4: '4月', 5: '5月', 6: '6月',
                7: '7月', 8: '8月', 9: '9月', 10: '10月', 11: '11月', 12: '12月'
            }
            monthly_df['Month Name'] = monthly_df['Month'].map(month_names)

            # --- 追加: 月順でソート ---
            monthly_df = monthly_df.sort_values("Month")
            # --- ここまで追加 ---

            # Total Ptの月別推移グラフ
            fig3 = px.line(
                monthly_df,
                x='Month',
                y='Total Pt',
                color='Player',
                markers=True,
                title=f'{selected_year}年度 Total Pt 月別推移',
                labels={'Month': '月', 'Total Pt': 'Total Pt', 'Player': 'プレイヤー'}
            )
            
            fig3.update_layout(
                xaxis=dict(
                    tickmode='array',
                    tickvals=list(range(1, 13)),
                    ticktext=[month_names[m] for m in range(1, 13)]
                )
            )
            
            st.plotly_chart(fig3, use_container_width=True)
            
            # 月別のポイント詳細表
            st.subheader("月別ポイント詳細")
            
            monthly_pivot = pd.pivot_table(
                monthly_df,
                values='Total Pt',
                index='Player',
                columns='Month',
                aggfunc='sum',
                fill_value=0
            )
            
            # 月の列を1月から12月の順に並べ替え
            all_months = list(range(1, 13))
            existing_months = [m for m in all_months if m in monthly_pivot.columns]
            monthly_pivot = monthly_pivot[existing_months]
            
            # 月名に変更
            monthly_pivot.columns = [month_names[m] for m in monthly_pivot.columns]
            
            # 合計列を追加
            monthly_pivot['合計'] = monthly_pivot.sum(axis=1)
            
            # 合計の降順でソート
            monthly_pivot = monthly_pivot.sort_values('合計', ascending=False)
            
            # 表示用にフォーマット
            formatted_pivot = monthly_pivot.copy()
            for col in formatted_pivot.columns:
                formatted_pivot[col] = formatted_pivot[col].map('{:+d}'.format)
            
            st.dataframe(
                formatted_pivot,
                use_container_width=True
            )
            
        else:
            st.info(f"{selected_year}年度の月別データが見つかりません。")

def show_monthly_statistics():
    """月間集計結果を表示（シンプル版）"""
    st.subheader("月間集計")
    
    # すべてのスコアを取得
    all_scores = get_all_scores()
    
    if not all_scores:
        st.info("スコアデータが見つかりません。")
        return
    
    # スコアから年度と月の一覧を作成
    year_months = set()
    for score in all_scores:
        if score['rounds']['date_played']:
            date_parts = score['rounds']['date_played'].split('-')
            if len(date_parts) >= 2:
                year = date_parts[0]
                month = date_parts[1]
                year_months.add(f"{year}-{month}")
    
    if not year_months:
        st.info("集計可能な月間データが見つかりません。")
        return
    
    # 年月を降順で並べ替え
    sorted_year_months = sorted(year_months, reverse=True)
    
    # 年月の選択
    selected_year_month = st.selectbox(
        "年月を選択",
        options=sorted_year_months,
        format_func=lambda x: f"{x.split('-')[0]}年{int(x.split('-')[1])}月"
    )
    
    if selected_year_month:
        year, month = selected_year_month.split('-')
        
        # 選択した年月のスコアをフィルタリング
        month_scores = [
            score for score in all_scores
            if score['rounds']['date_played'] and score['rounds']['date_played'].startswith(f"{year}-{month}")
        ]
        
        if not month_scores:
            st.info(f"{year}年{month}月のデータが見つかりません。")
            return
        
        # プレイヤーごとに集計
        player_points = aggregate_player_points(month_scores)
        
        if not player_points:
            st.info(f"{year}年{month}月の集計可能なデータが見つかりません。")
            return
        
        # DataFrameに変換
        df = create_summary_dataframe(player_points)
        
        # 結果の表示
        st.markdown(f"### {year}年{month}月 集計結果")
        
        # データフレームの表示（数値を見やすく整形）
        formatted_df = df.copy()
        formatted_df['Total Pt'] = formatted_df['Total Pt'].map('{:+d}'.format)
        formatted_df['Rounds'] = formatted_df['Rounds'].map('{:d}'.format)
        formatted_df['Avg Total Pt'] = formatted_df['Avg Total Pt'].map('{:+.2f}'.format)
        
        st.dataframe(
            formatted_df,
            column_config={
                "Player": "プレイヤー",
                "Rounds": "ラウンド数",
                "Total Pt": "Total Pt 合計",
                "Avg Total Pt": "Total Pt 平均"
            },
            use_container_width=True
        )
        
        # Total Ptのグラフ表示
        st.subheader("合計ポイント分布")
        
        fig = go.Figure()
        
        # Total Ptのみ表示（シンプル版）
        fig.add_trace(go.Bar(
            x=df['Player'],
            y=df['Total Pt'],
            name='Total Pt',
            text=df['Total Pt'].apply(lambda x: f"{x:+d}"),
            textposition='auto',
            marker_color='rgba(50, 171, 96, 0.7)',
            marker_line_color='rgba(50, 171, 96, 1)',
            marker_line_width=1.5
        ))
        
        fig.update_layout(
            xaxis_title='プレイヤー',
            yaxis_title='ポイント',
            title=f'{year}年{month}月 プレイヤー別合計ポイント'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # ラウンド別の詳細データ
        st.subheader("ラウンド別詳細")
        
        # ラウンド情報を抽出
        rounds_data = {}
        for score in month_scores:
            round_id = score['round_id']
            if round_id not in rounds_data:
                rounds_data[round_id] = {
                    'date': score['rounds']['date_played'],
                    'course': score['rounds']['course_name'],
                    'players': {}
                }
            
            player = score['member']['name']
            rounds_data[round_id]['players'][player] = {
                'Total Pt': score.get('total_pt', 0)
            }        
        # ラウンド順に表示
        sorted_rounds = sorted(rounds_data.items(), key=lambda x: x[1]['date'])
        for round_id, round_info in sorted_rounds:
            st.markdown(f"#### {round_info['date']} - {round_info['course']}")
            round_records = []
            # プレイヤーを名前順でソート
            for player, stats in sorted(round_info['players'].items()):
                round_records.append({
                    'プレイヤー': player,
                    'Total Pt': stats['Total Pt']
                })
            
            round_df = pd.DataFrame(round_records)
            round_df = round_df.sort_values('Total Pt', ascending=False)
            
            # 表示用にフォーマット
            formatted_round_df = round_df.copy()
            formatted_round_df['Total Pt'] = formatted_round_df['Total Pt'].map('{:+d}'.format)
            
            st.dataframe(
                formatted_round_df,
                use_container_width=True
            )

def verify_point_balance():
    """各種集計期間でのポイント合計値が0かどうかを検証する（シンプル版）"""
    st.subheader("ポイント集計検証")
    
    # すべてのスコアを取得
    all_scores = get_all_scores()
    
    if not all_scores:
        st.info("スコアデータが見つかりません。")
        return
    
    # 全期間の検証のみシンプルに実装
    with st.expander("全期間の検証"):
        # 全期間のポイント集計
        all_total_pt = sum(s.get('total_pt', 0) for s in all_scores)
        
        # 表示
        st.markdown(f"### 全期間ポイント合計")
        st.markdown(f"- Total Pt: **{all_total_pt:+d}**")
        
        # プレイヤー別の合計
        player_totals = {}
        for score in all_scores:
            player = score['member']['name']
            if player not in player_totals:
                player_totals[player] = {
                    'Total Pt': 0,
                    'Rounds': 0
                }
            
            player_totals[player]['Total Pt'] += score.get('total_pt', 0)
            player_totals[player]['Rounds'] += 1
        
        # プレイヤー別の合計をDataFrameとして表示
        player_df = pd.DataFrame.from_dict(player_totals, orient='index').reset_index()
        player_df.columns = ['Player', 'Total Pt', 'Rounds']
        
        # データ型を整数に変換
        player_df['Total Pt'] = player_df['Total Pt'].astype(int)
        
        # 表示用にフォーマット
        formatted_player_df = player_df.copy()
        formatted_player_df['Total Pt'] = formatted_player_df['Total Pt'].map('{:+d}'.format)
        
        # 合計を追加
        sums = player_df.sum().to_frame().T
        sums['Player'] = 'Total'
        formatted_sums = sums.copy()
        formatted_sums['Total Pt'] = formatted_sums['Total Pt'].map('{:+d}'.format)
        
        # 合計行を追加して表示
        formatted_result = pd.concat([formatted_player_df, formatted_sums]).reset_index(drop=True)
        st.dataframe(formatted_result, use_container_width=True)
        
        # バランス確認
        if abs(all_total_pt) < 0.01:
            st.success("✅ 全期間でのポイントバランスは正常です。")
        else:
            st.error(f"❌ 全期間でのポイントバランスが取れていません。（Total Pt: {all_total_pt}）")

if __name__ == "__main__":
    run()