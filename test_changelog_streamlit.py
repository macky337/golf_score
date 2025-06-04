#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHANGELOG読み込み機能の単体テスト
"""

import streamlit as st
import os

def test_changelog_function():
    """show_changelog関数の動作をテスト"""
    st.title("🔧 CHANGELOG読み込みテスト")
    
    # パス情報の表示
    script_dir = os.path.dirname(os.path.abspath(__file__))
    changelog_path = os.path.join(script_dir, "CHANGELOG.md")
    
    st.subheader("📂 パス情報")
    st.code(f"スクリプトディレクトリ: {script_dir}")
    st.code(f"CHANGELOGパス: {changelog_path}")
    st.code(f"ファイル存在確認: {os.path.exists(changelog_path)}")
    
    # ディレクトリ内容の表示
    st.subheader("📁 ディレクトリ内容")
    try:
        files = os.listdir(script_dir)
        md_files = [f for f in files if f.endswith('.md')]
        st.write(f"MDファイル: {md_files}")
    except Exception as e:
        st.error(f"ディレクトリ読み込みエラー: {str(e)}")
    
    # CHANGELOG読み込みテスト
    st.subheader("📋 CHANGELOG読み込みテスト")
    try:
        if os.path.exists(changelog_path):
            with open(changelog_path, "r", encoding="utf-8") as f:
                changelog_content = f.read()
            
            st.success("✅ CHANGELOG読み込み成功！")
            st.write(f"ファイルサイズ: {len(changelog_content)} 文字")
            
            # 最初の500文字を表示
            st.subheader("📄 CHANGELOG内容（最初の500文字）")
            st.code(changelog_content[:500])
            
            # Expanderでの表示テスト
            st.subheader("🔍 Expanderでの表示テスト")
            with st.expander("📋 更新履歴"):
                st.markdown(changelog_content)
                
        else:
            st.error("❌ CHANGELOGファイルが見つかりません")
            
    except Exception as e:
        st.error(f"❌ CHANGELOG読み込みエラー: {str(e)}")
        
    # 修正後の関数テスト
    st.subheader("🛠️ 修正後のshow_changelog関数テスト")
    show_changelog_fixed()

def show_changelog_fixed():
    """修正されたshow_changelog関数"""
    try:
        with st.expander("📋 更新履歴（修正版）"):
            # スクリプトのディレクトリを基準にCHANGELOG.mdのパスを構築
            script_dir = os.path.dirname(os.path.abspath(__file__))
            changelog_path = os.path.join(script_dir, "CHANGELOG.md")
            
            if os.path.exists(changelog_path):
                with open(changelog_path, "r", encoding="utf-8") as f:
                    changelog = f.read()
                st.markdown(changelog)
            else:
                st.warning(f"CHANGELOG.mdファイルが見つかりません: {changelog_path}")
    except Exception as e:
        with st.expander("📋 更新履歴（修正版）"):
            st.error(f"更新履歴の読み込みに失敗しました: {str(e)}")
            # デバッグ情報を追加
            script_dir = os.path.dirname(os.path.abspath(__file__))
            changelog_path = os.path.join(script_dir, "CHANGELOG.md")
            st.code(f"探索パス: {changelog_path}")
            st.code(f"ファイル存在確認: {os.path.exists(changelog_path)}")
            if os.path.exists(script_dir):
                files = os.listdir(script_dir)
                st.code(f"ディレクトリ内容: {files}")

if __name__ == "__main__":
    test_changelog_function()
