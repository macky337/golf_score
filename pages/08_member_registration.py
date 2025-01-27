# pages/08_member_registration.py

import streamlit as st
from modules.db import SessionLocal
from modules.models import Member

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

def show_member_list():
    """登録済みメンバー一覧を表示する"""
    session = SessionLocal()
    members = session.query(Member).all()
    session.close()

    if not members:
        st.info("No members found.")
    else:
        # Streamlitでテーブル表示
        # 必要ならpandas DataFrameにして st.dataframe() でもOK
        for m in members:
            st.write(f"- ID: {m.member_id}, Name: {m.name}, Active: {m.is_active}")

# Streamlitのマルチページ構成の場合、以下のように記述
# ページとして表示されるためには、このファイルをpagesフォルダに置くだけでOK
def run():
    member_registration_page()

# 通常、Streamlitのマルチページではファイル名先頭にN_をつけるだけで
# stのPageが自動的に生成されるため、直接呼ぶには:
if __name__ == "__main__":
    member_registration_page()
