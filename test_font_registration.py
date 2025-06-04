#!/usr/bin/env python3
"""フォント登録をテストするスクリプト"""

import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def test_font_registration():
    """フォント登録をテストする"""
    font_path = "ipaexg.ttf"
    
    print(f"フォントファイルのテスト: {font_path}")
    print(f"絶対パス: {os.path.abspath(font_path)}")
    print(f"存在確認: {os.path.exists(font_path)}")
    
    if os.path.exists(font_path):
        try:
            # フォント登録を試行
            pdfmetrics.registerFont(TTFont('IPAexGothic', font_path))
            print("✓ フォント登録成功!")
            
            # 登録されたフォントの確認
            registered_fonts = pdfmetrics.getRegisteredFontNames()
            print(f"登録済みフォント数: {len(registered_fonts)}")
            
            if 'IPAexGothic' in registered_fonts:
                print("✓ IPAexGothic フォントが正常に登録されました")
            else:
                print("✗ IPAexGothic フォントの登録に失敗しました")
                
        except Exception as e:
            print(f"✗ フォント登録エラー: {e}")
            print(f"エラータイプ: {type(e).__name__}")
    else:
        print("✗ フォントファイルが見つかりません")

if __name__ == "__main__":
    test_font_registration()
