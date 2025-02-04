import streamlit as st
import datetime
import itertools
from modules.db import SessionLocal
from modules.models import Round, Member, Score, HandicapMatch

def run():
    st.title("Round Setup")
    st.write("Set up a new round with date, course, and players.")

    # 1) ラウンド情報の入力フォーム
    date_played = st.date_input("Date of Round", value=datetime.date.today())

    # 過去のラウンドから使用済みのコース名を取得
    session = SessionLocal()
    past_courses = session.query(Round.course_name).distinct().all()
    session.close()
    past_course_list = [course for (course,) in past_courses if course]

    # 選択肢に「新規入力」を追加
    course_options = ["新規入力"] + past_course_list
    selected_option = st.selectbox("Select Course Name", course_options)
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
    member_dict = {m.name: m.member_id for m in all_members}
    selected_members = st.multiselect("Select participants", options=list(member_dict.keys()))

    # 3) ハンデキャップおよび例外設定の入力
    st.subheader("Handicap & Match Calculation Settings")
    match_handicaps = []
    if len(selected_members) >= 2:
        for pair in itertools.combinations(selected_members, 2):
            st.markdown(f"#### {pair[0]} vs {pair[1]}")
            h1to2 = st.number_input(
                f"{pair[0]} → {pair[1]} Handicap",
                min_value=0, max_value=50, step=1, value=0,
                key=f"h_{pair[0]}_{pair[1]}"
            )
            h2to1 = st.number_input(
                f"{pair[1]} → {pair[0]} Handicap",
                min_value=0, max_value=50, step=1, value=0,
                key=f"h_{pair[1]}_{pair[0]}"
            )
            total_only = st.checkbox("Use total score for match calculation", key=f"total_only_{pair[0]}_{pair[1]}")
            match_handicaps.append({
                "player1": pair[0],
                "player2": pair[1],
                "handicap_1_to_2": h1to2,
                "handicap_2_to_1": h2to1,
                "total_only": total_only
            })
    else:
        st.info("ハンデキャップ設定は、参加者が2名以上選ばれた場合に利用可能です。")

    # 4) 「Start Round」ボタン
    if st.button("Start Round"):
        if len(selected_members) < 2:
            st.error("少なくとも2人の参加者を選択してください。")
        else:
            session = SessionLocal()
            try:
                # rounds テーブルへ新規ラウンドをINSERT
                new_round = Round(
                    date_played=date_played,
                    course_name=course_name.strip(),
                    num_players=num_players,
                    has_extra=False,
                    finalized=False
                )
                session.add(new_round)
                session.commit()
                round_id = new_round.round_id

                # 各メンバーのスコア枠を scores テーブルへINSERT
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
                        player_1_to_2=mh["handicap_1_to_2"],
                        player_2_to_1=mh["handicap_2_to_1"],
                        total_only=mh["total_only"]
                    )
                    session.add(new_match)
                session.commit()
                session.close()

                st.success(f"New round created! Round ID = {round_id}")
                st.info(f"Participants: {', '.join(selected_members)}")
                st.info("Match settings have been saved with the following handicap values and calculation methods:")
                for mh in match_handicaps:
                    calc_method = "Total Score Only" if mh["total_only"] else "Front/Back/Total"
                    st.write(f"- {mh['player1']} vs {mh['player2']}: {mh['handicap_1_to_2']} / {mh['handicap_2_to_1']} (Calculation: {calc_method})")
            except Exception as e:
                session.rollback()
                st.error(f"エラーが発生しました: {e}")
            finally:
                session.close()

if __name__ == "__main__":
    run()
