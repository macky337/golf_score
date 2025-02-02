# pages/08_member_registration.py

import streamlit as st
from modules.db import SessionLocal
from modules.models import Member, HandicapMatch, Score  # Score を追加

def member_registration_page():
    """メンバー登録ページ"""
    st.title("Member Registration")

    # 入力フォーム
    name_input = st.text_input("New Member Name", value="")

    if st.button("Register"):
        if name_input.strip() == "":
            st.warning("Member name cannot be empty.")
        else:
            # DBに接続してINSERT
            session = SessionLocal()
            new_member = Member(name=name_input.strip())
            session.add(new_member)
            session.commit()
            session.close()
            st.success(f"New member '{name_input}' has been registered.")
    
    st.subheader("Current Member List")
    show_member_list()

# show_member_list 関数の修正例（メンバー削除時に関連する HandicapMatch レコードも削除）
def show_member_list():
    """登録済みメンバー一覧を表示する"""
    session = SessionLocal()
    members = session.query(Member).all()
    session.close()

    if not members:
        st.info("No members registered.")
    else:
        for member in members:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(member.name)
            with col2:
                if st.button("削除", key=f"delete_{member.member_id}"):
                    session = SessionLocal()
                    # 先に関連する Score レコードを削除する
                    session.query(Score).filter(
                        Score.member_id == member.member_id
                    ).delete(synchronize_session=False)
                    # 次に関連する HandicapMatch レコードを削除する
                    session.query(HandicapMatch).filter(
                        (HandicapMatch.player_1_id == member.member_id) | 
                        (HandicapMatch.player_2_id == member.member_id)
                    ).delete(synchronize_session=False)
                    # 最後に Member レコードを削除する
                    member_to_delete = session.query(Member).filter_by(member_id=member.member_id).first()
                    if member_to_delete:
                        session.delete(member_to_delete)
                        # メンバー削除処理の修正例
                        session.commit()
                        st.success(f"Member '{member.name}' has been deleted.")
                        session.close()
                        # st.experimental_rerun() が存在しない場合は st.stop() で処理を終了
                        if hasattr(st, "experimental_rerun"):
                            st.experimental_rerun()
                        else:
                            st.stop()

# Streamlitのマルチページ構成の場合、以下のように記述
# ページとして表示されるためには、このファイルをpagesフォルダに置くだけでOK
def run():
    member_registration_page()

# 通常、Streamlitのマルチページではファイル名先頭にN_をつけるだけで
# stのPageが自動的に生成されるため、直接呼ぶには:
if __name__ == "__main__":
    member_registration_page()
