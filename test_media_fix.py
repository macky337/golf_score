"""
Railway 404エラー修正のテストスクリプト
メディア配信機能の動作確認用
"""
import os
import tempfile
import time
from modules.media_utils import get_media_directory, save_temporary_file, cleanup_old_files
from modules.url_handler import validate_filename, is_facebook_crawler, create_media_url

def test_media_infrastructure():
    """メディアインフラストラクチャのテスト"""
    print("🔍 メディアインフラストラクチャテスト開始")
    
    # 1. メディアディレクトリの取得テスト
    try:
        media_dir = get_media_directory()
        print(f"✅ メディアディレクトリ: {media_dir}")
        
        # ディレクトリの存在確認
        if os.path.exists(media_dir):
            print("✅ ディレクトリが存在します")
        else:
            print("❌ ディレクトリが存在しません")
            
    except Exception as e:
        print(f"❌ メディアディレクトリ取得エラー: {e}")
    
    # 2. テストファイルの作成と保存
    try:
        test_content = b"Test PDF content"
        test_filename = save_temporary_file(test_content, "test", ".pdf")
        print(f"✅ テストファイル作成: {test_filename}")
        
        # ファイルが実際に作成されたか確認
        test_path = os.path.join(media_dir, test_filename)
        if os.path.exists(test_path):
            print("✅ ファイルが正常に保存されました")
            # テストファイルを削除
            os.remove(test_path)
            print("✅ テストファイルを削除しました")
        else:
            print("❌ ファイルが保存されませんでした")
            
    except Exception as e:
        print(f"❌ ファイル保存テストエラー: {e}")
    
    # 3. ファイル名検証テスト
    test_cases = [
        ("test.pdf", True),
        ("../test.pdf", False),
        ("test/file.pdf", False),
        ("test.txt", False),
        ("valid_file_123.pdf", True)
    ]
    
    print("\n🔍 ファイル名検証テスト:")
    for filename, expected in test_cases:
        is_valid, result = validate_filename(filename)
        status = "✅" if is_valid == expected else "❌"
        print(f"{status} {filename}: {is_valid} (期待値: {expected})")
    
    # 4. クリーンアップテスト
    try:
        cleanup_old_files()
        print("✅ クリーンアップ機能が正常に動作しました")
    except Exception as e:
        print(f"❌ クリーンアップエラー: {e}")

def test_url_handling():
    """URL処理機能のテスト"""
    print("\n🔍 URL処理機能テスト開始")
    
    # 環境変数を一時的に設定してテスト
    test_environments = [
        {
            'REQUEST_URI': '/media/test_file.pdf',
            'HTTP_USER_AGENT': 'Mozilla/5.0'
        },
        {
            'REQUEST_URI': '/media/another_file.pdf',
            'HTTP_USER_AGENT': 'facebookexternalhit/1.1;line-poker/1.0'
        },
        {
            'PATH_INFO': '/media/path_info_test.pdf',
            'HTTP_USER_AGENT': 'twitterbot'
        }
    ]
    
    # 現在の環境変数を保存
    original_env = {}
    for key in ['REQUEST_URI', 'HTTP_USER_AGENT', 'PATH_INFO']:
        original_env[key] = os.getenv(key)
    
    try:
        for i, test_env in enumerate(test_environments):
            print(f"\nテストケース {i+1}:")
            
            # テスト環境変数を設定
            for key, value in test_env.items():
                os.environ[key] = value
            
            # URL処理機能をテスト
            from modules.url_handler import extract_media_path_from_url, is_facebook_crawler
            
            filename = extract_media_path_from_url()
            is_crawler = is_facebook_crawler()
            
            print(f"  抽出されたファイル名: {filename}")
            print(f"  Facebookクローラー: {is_crawler}")
            print(f"  User-Agent: {test_env.get('HTTP_USER_AGENT', 'None')}")
            
        print("✅ URL処理テスト完了")
        
    except Exception as e:
        print(f"❌ URL処理テストエラー: {e}")
    
    finally:
        # 環境変数を復元
        for key, value in original_env.items():
            if value is None:
                if key in os.environ:
                    del os.environ[key]
            else:
                os.environ[key] = value

def test_integration():
    """統合テスト"""
    print("\n🔍 統合テスト開始")
    
    try:
        # 実際のワークフローをシミュレート
        
        # 1. PDFファイルの生成シミュレート
        test_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        filename = save_temporary_file(test_content, "integration_test", ".pdf")
        print(f"✅ PDFファイル生成シミュレート: {filename}")
        
        # 2. URLの生成
        media_url = create_media_url(filename)
        print(f"✅ メディアURL生成: {media_url}")
        
        # 3. ファイルの検証
        is_valid, validated = validate_filename(filename)
        if is_valid:
            print(f"✅ ファイル検証成功: {validated}")
        else:
            print(f"❌ ファイル検証失敗: {validated}")
        
        # 4. ファイルの存在確認
        media_dir = get_media_directory()
        file_path = os.path.join(media_dir, filename)
        
        if os.path.exists(file_path):
            print("✅ ファイルが存在します")
            
            # ファイルの詳細情報
            file_size = os.path.getsize(file_path)
            file_mtime = os.path.getmtime(file_path)
            file_age = time.time() - file_mtime
            
            print(f"  ファイルサイズ: {file_size} bytes")
            print(f"  ファイル年齢: {file_age:.2f} seconds")
            print(f"  有効期限内: {'Yes' if file_age < 24*3600 else 'No'}")
            
            # テストファイルを削除
            os.remove(file_path)
            print("✅ テストファイルを削除しました")
            
        else:
            print("❌ ファイルが存在しません")
        
        print("✅ 統合テスト完了")
        
    except Exception as e:
        print(f"❌ 統合テストエラー: {e}")

def main():
    """メインテスト実行"""
    print("🚀 Railway 404エラー修正テスト実行")
    print("=" * 50)
    
    test_media_infrastructure()
    test_url_handling()
    test_integration()
    
    print("\n" + "=" * 50)
    print("✅ 全テスト完了")
    print("\n📋 次のステップ:")
    print("1. git add .")
    print("2. git commit -m 'Fix Railway 404 media access - v1.0.214'")
    print("3. git push")
    print("4. Railway で自動デプロイを確認")
    print("5. https://golfscore-production.up.railway.app/media/[filename].pdf でテスト")

if __name__ == "__main__":
    main()
