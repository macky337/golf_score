import streamlit as st
import os

st.title("Calculation Logic")
# Updated path: look one level up for CALCULATION_LOGIC.md
md_path = os.path.join(os.path.dirname(__file__), "..", "CALCULATION_LOGIC.md")
if os.path.exists(md_path):
    with open(md_path, "r", encoding="utf-8") as f:
        st.markdown(f.read(), unsafe_allow_html=True)
else:
    st.error("CALCULATION_LOGIC.mdファイルが見つかりません。")
