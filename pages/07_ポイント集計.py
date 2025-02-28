import streamlit as st
import pandas as pd
import datetime
import numpy as np
from modules.db import supabase
import calendar
from streamlit_extras.switch_page_button import switch_page
import plotly.express as px
import plotly.graph_objects as go

def run():
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.title("ポイント集計")
    with col2:
        if st.button("🏠 Home"):
            switch_page("Main")

    # 3つのタブを作成
    tab1, tab2, tab3 = st.tabs(["通算成績", "年度別集計", "月間集計"])
    
    with tab1:
        show_all_time_statistics()
    
    with tab2:
        show_yearly_statistics()
    
    with tab3:
        show_monthly_statistics()

def get_all_scores():
    """すべての確定済みスコアデータを取得"""
    try:
        # スコアデータを取得（確定済みラウンドのみに絞り込み）
        scores = supabase.table('score').select(
            '*, rounds(date_played, course_name, finalized), member(name)'
        ).eq('rounds.finalized', True).execute()
        
        if not scores.data:
            return []

        # 有効なスコアデータのみをフィルタリング
        filtered_scores = []
        for score in scores.data:
            # roundsやmember情報がない場合はスキップ
            if not score.get('rounds') or not score.get('member'):
                continue
                
            # 名前がないデータはスキップ
            if not score['member'].get('name'):
                continue
                
            # front_game_pt、back_game_pt、extra_game_pt、match_pt、put_pt、total_ptがNoneなら0に変換
            score['front_game_pt'] = score.get('front_game_pt') or 0
            score['back_game_pt'] = score.get('back_game_pt') or 0
            score['extra_game_pt'] = score.get('extra_game_pt') or 0
            score['match_pt'] = score.get('match_pt') or 0
            score['put_pt'] = score.get('put_pt') or 0
            
            # total_ptを再計算
            score['total_pt'] = (
                score['front_game_pt'] + 
                score['back_game_pt'] + 
                score['extra_game_pt'] + 
                score['match_pt'] + 
                score['put_pt']
            )
                
            filtered_scores.append(score)
        
        # デバッグ出力（開発中に確認するため）
        print(f"取得したスコア数: {len(filtered_scores)}")
        if filtered_scores:
            sample = filtered_scores[0]
            print(f"サンプルデータ: name={sample['member']['name']}, total_pt={sample['total_pt']}")
            
        return filtered_scores

    except Exception as e:
        st.error(f"スコアデータの取得中にエラーが発生しました: {str(e)}")
        print(f"スコアデータ取得エラー詳細: {str(e)}")
        if hasattr(e, 'details'):
            print(f"エラー詳細: {e.details}")
        return []

def aggregate_player_points(scores):
    """プレイヤーごとのポイントを集計"""
    player_points = {}
    
    for score in scores:
        player_name = score['member']['name']
        if not player_name:  # 名前が取得できなかったらスキップ
            continue
            
        if player_name not in player_points:
            player_points[player_name] = {
                'Game Pt': 0,
                'Match Pt': 0,
                'Put Pt': 0,
                'Total Pt': 0,
                'Rounds': 0
            }
        
        # ポイントの集計 (Noneの場合は0に置き換え)
        game_pt = (score.get('front_game_pt') or 0) + (score.get('back_game_pt') or 0) + (score.get('extra_game_pt') or 0)
        match_pt = score.get('match_pt') or 0
        put_pt = score.get('put_pt') or 0
        
        player_points[player_name]['Game Pt'] += game_pt
        player_points[player_name]['Match Pt'] += match_pt
        player_points[player_name]['Put Pt'] += put_pt
        player_points[player_name]['Total Pt'] += (game_pt + match_pt + put_pt)  # 合計を再計算
        player_points[player_name]['Rounds'] += 1

    # 集計結果がない場合は空の辞書を返す
    if not player_points:
        return {}
        
    return player_points

def create_summary_dataframe(player_points):
    """集計結果からDataFrameを作成"""
    # DataFrameに変換
    df = pd.DataFrame.from_dict(player_points, orient='index')
    
    # ラウンド数に応じてスコアを平均化（平均データを追加）
    df['Avg Game Pt'] = (df['Game Pt'] / df['Rounds']).round(2)
    df['Avg Match Pt'] = (df['Match Pt'] / df['Rounds']).round(2)
    df['Avg Put Pt'] = (df['Put Pt'] / df['Rounds']).round(2)
    df['Avg Total Pt'] = (df['Total Pt'] / df['Rounds']).round(2)
    
    # プレイヤー名をインデックスから列に移動
    df = df.reset_index().rename(columns={'index': 'Player'})
    
    # 列の順序を設定
    columns = [
        'Player', 'Rounds',
        'Game Pt', 'Avg Game Pt',
        'Match Pt', 'Avg Match Pt',
        'Put Pt', 'Avg Put Pt',
        'Total Pt', 'Avg Total Pt'
    ]
    df = df[columns]
    
    # Total Ptの降順でソート
    df = df.sort_values('Total Pt', ascending=False)
    
    return df

def show_all_time_statistics():
    """全期間の通算成績を表示"""
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
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if col in ['Game Pt', 'Match Pt', 'Put Pt', 'Total Pt']:
            formatted_df[col] = formatted_df[col].map('{:+d}'.format)
        elif col == 'Rounds':
            formatted_df[col] = formatted_df[col].map('{:d}'.format)
        else:  # 平均値
            formatted_df[col] = formatted_df[col].map('{:+.2f}'.format)
    
    st.dataframe(
        formatted_df,
        column_config={
            "Player": "プレイヤー",
            "Rounds": "ラウンド数",
            "Game Pt": "Game Pt 合計",
            "Avg Game Pt": "Game Pt 平均",
            "Match Pt": "Match Pt 合計",
            "Avg Match Pt": "Match Pt 平均",
            "Put Pt": "Put Pt 合計",
            "Avg Put Pt": "Put Pt 平均",
            "Total Pt": "Total Pt 合計",
            "Avg Total Pt": "Total Pt 平均"
        },
        use_container_width=True
    )
    
    # グラフ表示（合計ポイント）
    st.subheader("合計ポイント分布")
    
    # プロット用のデータを作成
    fig = go.Figure()
    
    # ポイントタイプごとに追加
    for i, pt_type in enumerate(['Game Pt', 'Match Pt', 'Put Pt']):
        fig.add_trace(go.Bar(
            x=df['Player'],
            y=df[pt_type],
            name=pt_type,
            text=df[pt_type].apply(lambda x: f"{x:+d}"),
            textposition='auto'
        ))
    
    fig.update_layout(
        barmode='group',
        xaxis_title='プレイヤー',
        yaxis_title='ポイント',
        title='ポイントタイプ別合計ポイント'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 平均ポイントのグラフ
    st.subheader("平均ポイント分布")
    
    fig2 = go.Figure()
    
    # ポイントタイプごとに追加
    for i, pt_type in enumerate(['Avg Game Pt', 'Avg Match Pt', 'Avg Put Pt']):
        fig2.add_trace(go.Bar(
            x=df['Player'],
            y=df[pt_type],
            name=pt_type.replace('Avg ', ''),
            text=df[pt_type].apply(lambda x: f"{x:+.2f}"),
            textposition='auto'
        ))
    
    fig2.update_layout(
        barmode='group',
        xaxis_title='プレイヤー',
        yaxis_title='平均ポイント',
        title='ポイントタイプ別平均ポイント'
    )
    
    st.plotly_chart(fig2, use_container_width=True)
    
    # Total Ptのランキングを表で表示
    st.subheader("Total Pt ランキング")
    ranking_df = df[['Player', 'Rounds', 'Total Pt', 'Avg Total Pt']].sort_values('Total Pt', ascending=False).reset_index(drop=True)
    ranking_df.index = ranking_df.index + 1  # 1から始まるインデックス
    
    # ランキング表示用にフォーマット
    ranking_formatted = ranking_df.copy()
    ranking_formatted['Total Pt'] = ranking_formatted['Total Pt'].map('{:+d}'.format)
    ranking_formatted['Avg Total Pt'] = ranking_formatted['Avg Total Pt'].map('{:+.2f}'.format)
    
    st.dataframe(
        ranking_formatted,
        column_config={
            "Player": "プレイヤー",
            "Rounds": "ラウンド数",
            "Total Pt": "Total Pt 合計",
            "Avg Total Pt": "Total Pt 平均"
        },
        use_container_width=True
    )

def show_yearly_statistics():
    """年度別の集計結果を表示"""
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
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col in ['Game Pt', 'Match Pt', 'Put Pt', 'Total Pt']:
                formatted_df[col] = formatted_df[col].map('{:+d}'.format)
            elif col == 'Rounds':
                formatted_df[col] = formatted_df[col].map('{:d}'.format)
            else:  # 平均値
                formatted_df[col] = formatted_df[col].map('{:+.2f}'.format)
        
        st.dataframe(
            formatted_df,
            column_config={
                "Player": "プレイヤー",
                "Rounds": "ラウンド数",
                "Game Pt": "Game Pt 合計",
                "Avg Game Pt": "Game Pt 平均",
                "Match Pt": "Match Pt 合計",
                "Avg Match Pt": "Match Pt 平均",
                "Put Pt": "Put Pt 合計",
                "Avg Put Pt": "Put Pt 平均",
                "Total Pt": "Total Pt 合計",
                "Avg Total Pt": "Total Pt 平均"
            },
            use_container_width=True
        )
        
        # 合計ポイントのグラフ表示
        st.subheader("合計ポイント分布")
        
        fig = go.Figure()
        
        # ポイントタイプごとに追加
        for i, pt_type in enumerate(['Game Pt', 'Match Pt', 'Put Pt']):
            fig.add_trace(go.Bar(
                x=df['Player'],
                y=df[pt_type],
                name=pt_type,
                text=df[pt_type].apply(lambda x: f"{x:+d}"),
                textposition='auto'
            ))
        
        fig.update_layout(
            barmode='group',
            xaxis_title='プレイヤー',
            yaxis_title='ポイント',
            title=f'{selected_year}年度 ポイントタイプ別合計ポイント'
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
                        'Game Pt': 0,
                        'Match Pt': 0,
                        'Put Pt': 0,
                        'Total Pt': 0,
                        'Rounds': 0
                    }
                
                # ポイントの集計
                monthly_data[month][player]['Game Pt'] += (score.get('front_game_pt') or 0) + (score.get('back_game_pt') or 0) + (score.get('extra_game_pt') or 0)
                monthly_data[month][player]['Match Pt'] += score.get('match_pt') or 0
                monthly_data[month][player]['Put Pt'] += score.get('put_pt') or 0
                # Total Ptを他のポイントの合計として計算
                monthly_data[month][player]['Total Pt'] = (
                    monthly_data[month][player]['Game Pt'] + 
                    monthly_data[month][player]['Match Pt'] + 
                    monthly_data[month][player]['Put Pt']
                )
                monthly_data[month][player]['Rounds'] += 1
        
        # 月別データをDataFrameに変換
        monthly_records = []
        for month, players in monthly_data.items():
            for player, stats in players.items():
                monthly_records.append({
                    'Month': month,
                    'Player': player,
                    'Game Pt': stats['Game Pt'],
                    'Match Pt': stats['Match Pt'],
                    'Put Pt': stats['Put Pt'],
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
    """月間集計結果を表示"""
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
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col in ['Game Pt', 'Match Pt', 'Put Pt', 'Total Pt']:
                formatted_df[col] = formatted_df[col].map('{:+d}'.format)
            elif col == 'Rounds':
                formatted_df[col] = formatted_df[col].map('{:d}'.format)
            else:  # 平均値
                formatted_df[col] = formatted_df[col].map('{:+.2f}'.format)
        
        st.dataframe(
            formatted_df,
            column_config={
                "Player": "プレイヤー",
                "Rounds": "ラウンド数",
                "Game Pt": "Game Pt 合計",
                "Avg Game Pt": "Game Pt 平均",
                "Match Pt": "Match Pt 合計",
                "Avg Match Pt": "Match Pt 平均",
                "Put Pt": "Put Pt 合計",
                "Avg Put Pt": "Put Pt 平均",
                "Total Pt": "Total Pt 合計",
                "Avg Total Pt": "Total Pt 平均"
            },
            use_container_width=True
        )
        
        # 合計ポイントのグラフ表示
        st.subheader("合計ポイント分布")
        
        fig = go.Figure()
        
        # ポイントタイプごとに追加
        for i, pt_type in enumerate(['Game Pt', 'Match Pt', 'Put Pt']):
            fig.add_trace(go.Bar(
                x=df['Player'],
                y=df[pt_type],
                name=pt_type,
                text=df[pt_type].apply(lambda x: f"{x:+d}"),
                textposition='auto'
            ))
        
        fig.update_layout(
            barmode='group',
            xaxis_title='プレイヤー',
            yaxis_title='ポイント',
            title=f'{year}年{month}月 ポイントタイプ別合計ポイント'
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
                'Game Pt': (score.get('front_game_pt') or 0) + (score.get('back_game_pt') or 0) + (score.get('extra_game_pt') or 0),
                'Match Pt': score.get('match_pt') or 0,
                'Put Pt': score.get('put_pt') or 0,
                'Total Pt': (score.get('front_game_pt') or 0) + (score.get('back_game_pt') or 0) + (score.get('extra_game_pt') or 0) + (score.get('match_pt') or 0) + (score.get('put_pt') or 0)
            }
        
        # ラウンド順に表示
        sorted_rounds = sorted(rounds_data.items(), key=lambda x: x[1]['date'])
        
        for round_id, round_info in sorted_rounds:
            st.markdown(f"#### {round_info['date']} - {round_info['course']}")
            
            round_records = []
            for player, stats in round_info['players'].items():
                round_records.append({
                    'プレイヤー': player,
                    'Game Pt': stats['Game Pt'],
                    'Match Pt': stats['Match Pt'],
                    'Put Pt': stats['Put Pt'],
                    'Total Pt': stats['Total Pt']
                })
            
            round_df = pd.DataFrame(round_records)
            round_df = round_df.sort_values('Total Pt', ascending=False)
            
            # 表示用にフォーマット
            formatted_round_df = round_df.copy()
            point_cols = ['Game Pt', 'Match Pt', 'Put Pt', 'Total Pt']
            for col in point_cols:
                formatted_round_df[col] = formatted_round_df[col].map('{:+d}'.format)
            
            st.dataframe(
                formatted_round_df,
                use_container_width=True
            )

if __name__ == "__main__":
    run()