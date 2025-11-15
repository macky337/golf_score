import streamlit as st

st.title("テスト画面")
st.write("この画面が表示されれば接続成功です")

number = st.number_input("数値入力テスト", min_value=0, max_value=100, value=0)
st.write(f"入力値: {number}")

if st.button("テストボタン"):
    st.success("ボタンが押されました！")
