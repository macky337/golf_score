# pages/06_result_confirmation.py

import streamlit as st
import pandas as pd
from modules.db import SessionLocal
from modules.models import Round, Score, Member, HandicapMatch

def run():
    st.title("Result Confirmation")

    session = SessionLocal()

    # 1) 未確定ラウンドの取得
    active_round = session.query(Round).filter_by(finalized=False).order_by(Round.round_id.desc()).first()
    if not active_round:
        st.warning("No active round found. Please set up a round first.")
        session.close()
        return

    st.write(f"**Round ID**: {active_round.round_id}, **Course**: {active_round.course_name}")

    # 2) ラウンドのスコアとプレイヤー情報を取得
    score_rows = (
        session.query(Score)
        .join(Member, Score.member_id == Member.member_id)
        .filter(Score.round_id == active_round.round_id)
        .all()
    )

    if not score_rows:
        st.warning("No participants found for this round.")
        session.close()
        return

    # 3) ハンディキャップの取得
    handicaps = {}
    matches = session.query(HandicapMatch).filter(HandicapMatch.round_id == active_round.round_id).all()
    for match in matches:
        p1 = match.player_1_id
        p2 = match.player_2_id
        handicaps[(p1, p2)] = match.player_1_to_2  # p1 → p2 に渡すハンデ
        handicaps[(p2, p1)] = match.player_2_to_1  # p2 → p1 に渡すハンデ

    # 3-1) ペアごとのハンディキャップ辞書を作成
    # それぞれの組み合わせに対して、player_1_to_2 と player_2_to_1 を格納する
    handicap_dict = {}
    for match in matches:
        handicap_dict[(match.player_1_id, match.player_2_id)] = match.player_1_to_2
        handicap_dict[(match.player_2_id, match.player_1_id)] = match.player_2_to_1

    # 4) スコアデータの作成
    result_data = []
    for sc in score_rows:
        total_score = sc.front_score + sc.back_score + (sc.extra_score if sc.extra_score else 0)
        total_putt = sc.front_putt + sc.back_putt + (sc.extra_putt if sc.extra_putt else 0)
        total_game_points = sc.front_game_pt + sc.back_game_pt + (sc.extra_game_pt if sc.extra_game_pt else 0)
        handicap = handicaps.get((sc.member_id, sc.member_id), 0)  # 自分自身に渡されたハンデ
        net_score = total_score - (handicap / 2)  # ハンデを考慮したネットスコア

        result_data.append({
            'Player': sc.member.name,
            'Member ID': sc.member_id,
            'Front Score': sc.front_score,
            'Back Score': sc.back_score,
            'Extra Score': sc.extra_score if sc.extra_score else 0,
            'Total Score': total_score,
            'Handicap': handicap,
            'Net Score': net_score,
            'Front Putt': sc.front_putt,
            'Back Putt': sc.back_putt,
            'Extra Putt': sc.extra_putt if sc.extra_putt else 0,
            'Total Putt': total_putt,
            'Total Game Points': total_game_points
        })

    # 5) DataFrameに変換して表示
    df = pd.DataFrame(result_data)
    st.dataframe(df)

    # 6) 勝敗と得点の計算
    # 既に作成済みの handicap_dict を使用
    # handicap_dict = { (match.player_1_id, match.player_2_id): match.player_1_to_2, ... }
    
    match_results = []
    for i, row in enumerate(result_data):
        for j, opponent in enumerate(result_data):
            if i != j:
                # 各対戦ごとのハンデキャップ取得（入力された値そのまま）
                handicap_1_to_2 = handicap_dict.get((row['Member ID'], opponent['Member ID']), 0)
                handicap_2_to_1 = handicap_dict.get((opponent['Member ID'], row['Member ID']), 0)
                
                # ネットスコア計算：Total Score からハンデキャップをそのまま差し引く
                net_score_1 = row['Total Score'] - handicap_1_to_2
                net_score_2 = opponent['Total Score'] - handicap_2_to_1
                
                if net_score_1 < net_score_2:
                    outcome = f"{row['Player']} wins"
                elif net_score_1 > net_score_2:
                    outcome = f"{opponent['Player']} wins"
                else:
                    outcome = "Draw"
                
                match_results.append(f"{row['Player']} vs {opponent['Player']} : {net_score_1} - {net_score_2} | {outcome}")
    
    # total_points の初期化（各プレイヤーの得点を0に設定）
    total_points = { row['Player']: 0 for row in result_data }

    # ゲームポイントの加算
    for row in result_data:
        total_points[row['Player']] += row['Total Game Points']

    # df の Total Points カラムへ反映
    for i, row in enumerate(result_data):
        df.loc[i, 'Total Points'] = total_points[row['Player']]

    st.write("Match Results:")
    for result in match_results:
        st.write(result)

    # ゲームポイントの加算
    for i, row in enumerate(result_data):
        total_points[row['Player']] += row['Total Game Points']

    # パット数の勝敗計算の前に参加者数を定義
    num_players = len(result_data)

    # パット数の勝敗
    min_putts = min(r['Total Putt'] for r in result_data)
    min_putts_players = [r['Player'] for r in result_data if r['Total Putt'] == min_putts]

    if num_players == 4:
        if len(min_putts_players) == 1:
            for i, row in enumerate(result_data):
                if row['Player'] in min_putts_players:
                    total_points[row['Player']] += 30
                else:
                    total_points[row['Player']] -= 10
        elif len(min_putts_players) == 2:
            for i, row in enumerate(result_data):
                if row['Player'] in min_putts_players:
                    total_points[row['Player']] += 10
                else:
                    total_points[row['Player']] -= 10
        elif len(min_putts_players) == 3:
            for i, row in enumerate(result_data):
                if row['Player'] in min_putts_players:
                    total_points[row['Player']] += 10
                else:
                    total_points[row['Player']] -= 30
    elif num_players == 3:
        if len(min_putts_players) == 1:
            for i, row in enumerate(result_data):
                if row['Player'] in min_putts_players:
                    total_points[row['Player']] += 20
                else:
                    total_points[row['Player']] -= 10
        elif len(min_putts_players) == 2:
            for i, row in enumerate(result_data):
                if row['Player'] in min_putts_players:
                    total_points[row['Player']] += 10
                else:
                    total_points[row['Player']] -= 20

    # ゲームポイントの加算
    for i, row in enumerate(result_data):
        total_points[row['Player']] += row['Total Game Points']

    # 最終得点をテーブルに追加
    for i, row in enumerate(result_data):
        df.loc[i, 'Total Points'] = total_points[row['Player']]

    st.write("Calculated Total Points for each player:")
    st.dataframe(df)

    # Match Results の表示（例）
    st.write("Match Results:")
    for result in match_results:
        st.write(result)

    # 設定画面に戻るリンクを修正（正しいファイル名に変更）
    st.markdown("[Return to Round Setup](pages/02_round_setup.py)")

    # 7) ラウンド結果を最終化
    if st.button("Finalize Results"):
        active_round.finalized = True
        session.commit()
        session.close()
        st.success("Results have been finalized.")

if __name__ == "__main__":
    run()
