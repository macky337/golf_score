import streamlit as st
import datetime
from modules.db import SessionLocal
from modules.models import Round, Member, Score, HandicapMatch  # HandicapMatch を import
import itertools

def run():
    """ラウンドの設定ページ"""
    st.title("Round Setup")
    st.write("Set up a new round with date, course, and players.")

    # 1) ラウンド情報の入力フォーム
    date_played = st.date_input("Date of Round", value=datetime.date.today())

    # 過去のラウンドから、使用済みのコース名を取得
    session = SessionLocal()
    past_courses = session.query(Round.course_name).distinct().all()
    session.close()
    past_course_list = [course for (course,) in past_courses if course]

    # 選択肢に「新規入力」を追加
    course_options = ["新規入力"] + past_course_list

    selected_option = st.selectbox("Select Course Name", course_options)
    # 選択肢が「新規入力」以外の場合は、削除ボタンを表示
    if selected_option != "新規入力":
        if st.button("Delete Selected Course"):
            session = SessionLocal()
            try:
                session.query(Round).filter(Round.course_name == selected_option).delete()
                session.commit()
                st.success(f"Course '{selected_option}' has been deleted from past courses. Please refresh the page.")
            except Exception as e:
                session.rollback()
                st.error(f"削除時にエラーが発生しました: {e}")
            finally:
                session.close()
        course_name = selected_option
    else:
        course_name = st.text_input("Course Name", value="Sample Golf Club")

    num_players = st.selectbox("Number of Players", [3, 4], index=1)

    # 2) DBから既存メンバーを取得し、参加者を選択
    session = SessionLocal()
    all_members = session.query(Member).all()
    session.close()

    # メンバー名 -> メンバーID の辞書
    member_dict = {m.name: m.member_id for m in all_members}

    selected_members = st.multiselect(
        "Select participants", 
        options=list(member_dict.keys())
    )

    # 3) ハンデキャップの設定
    st.subheader("Handicap Settings")
    match_handicaps = []
    for i in range(len(selected_members)):
        for j in range(len(selected_members)):
            if i != j:
                player1 = selected_members[i]
                player2 = selected_members[j]
                handicap = st.number_input(
                    f"{player1} → {player2}",
                    min_value=0,
                    max_value=50,
                    step=1,
                    value=0,
                    key=f"{player1}_to_{player2}"
                )
                match_handicaps.append({
                    "player1": player1,
                    "player2": player2,
                    "handicap": handicap
                })

    # 4) 特定のマッチの集計方法の選択（例外設定）
    st.subheader("Match Calculation Method")
    st.write("For the following matches, use the total score (18 holes) for match calculation (instead of front/back separately):")
    selected_matches = []
    if selected_members:
        # 選択された参加者から全組み合わせを生成
        for pair in itertools.combinations(selected_members, 2):
            checkbox_label = f"{pair[0]} vs {pair[1]}"
            if st.checkbox(checkbox_label):
                selected_matches.append(checkbox_label)
    
    # 5) 「Start Round」ボタン
    if st.button("Start Round"):
        if len(selected_members) < 2:
            st.error("少なくとも2人の参加者を選択してください。")
        else:
            session = SessionLocal()
            try:
                # roundsテーブルへINSERT
                new_round = Round(
                    date_played=date_played,
                    course_name=course_name.strip(),
                    num_players=num_players,
                    has_extra=False,
                    finalized=False
                )
                session.add(new_round)
                session.commit()

                round_id = new_round.round_id  # 作成されたラウンドのID

                # scoresテーブルへ各メンバー分のスコア枠をINSERT
                for member_name in selected_members:
                    member_id = member_dict[member_name]
                    new_score = Score(
                        round_id=round_id,
                        member_id=member_id,
                        front_score=0,
                        back_score=0,
                        extra_score=0,
                        front_putt=0,
                        back_putt=0,
                        extra_putt=0,
                        front_game_pt=0,
                        back_game_pt=0,
                        extra_game_pt=0
                    )
                    session.add(new_score)
                session.commit()

                # HandicapMatch テーブルにマッチ設定をINSERT
                for mh in match_handicaps:
                    p1_id = member_dict[mh["player1"]]
                    p2_id = member_dict[mh["player2"]]
                    new_match = HandicapMatch(
                        round_id=round_id,
                        player_1_id=p1_id,
                        player_2_id=p2_id,
                        player_1_to_2=mh["handicap"] if p1_id < p2_id else 0,
                        player_2_to_1=mh["handicap"] if p2_id < p1_id else 0
                    )
                    session.add(new_match)
                session.commit()

                # 例外設定：チェックされたマッチは、totalスコアで判定する
                if selected_matches:
                    st.session_state.total_only_pairs = selected_matches

                session.close()

                st.success(f"New round created! Round ID = {round_id}")
                st.info(f"Participants: {', '.join(selected_members)}")
                st.info("Match handicaps have been set:")
                for mh in match_handicaps:
                    st.write(f"- {mh['player1']} → {mh['player2']}: {mh['handicap']}")
            except Exception as e:
                session.rollback()
                st.error(f"エラーが発生しました: {e}")
            finally:
                session.close()

if __name__ == "__main__":
    run()
