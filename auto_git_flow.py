# filepath: c:\Users\user\Documents\GitHub\golf_score\auto_git_flow.py
import subprocess
import datetime
import os
import sys
import locale

# システムのエンコーディングを確認
system_encoding = locale.getpreferredencoding()
print(f"システムのエンコーディング: {system_encoding}")

def run_git_command(cmd, cwd=None):
    print(f"$ {' '.join(cmd)}")
    try:
        # Windows環境ではcp932エンコーディングを使用
        encoding = 'cp932' if sys.platform == 'win32' else 'utf-8'
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding=encoding)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        if result.returncode != 0:
            raise Exception(f"Command failed: {' '.join(cmd)}")
        return result
    except UnicodeDecodeError as e:
        print(f"エンコーディングエラー: {e}")
        # エンコーディングエラーが発生した場合、バイナリモードで実行し直す
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=False)
        if result.stdout:
            try:
                print(result.stdout.decode('utf-8', errors='replace'))
            except:
                print("stdout出力をデコードできませんでした")
        if result.stderr:
            try:
                print(result.stderr.decode('utf-8', errors='replace'))
            except:
                print("stderr出力をデコードできませんでした")
        if result.returncode != 0:
            raise Exception(f"Command failed: {' '.join(cmd)}")
        return result

# 変更ファイル一覧を取得し、分かりやすい日本語でコミットメッセージを自動生成
def generate_commit_message():
    try:
        result = subprocess.run(["git", "status", "-s"], capture_output=True, text=True, encoding='cp932' if sys.platform == 'win32' else 'utf-8')
        changed = result.stdout.strip().splitlines()
        if not changed:
            return "変更なし"
        
        # ファイルの種類別にカウント
        added_files = []
        modified_files = []
        deleted_files = []
        renamed_files = []
        
        for line in changed:
            status = line[:2].strip()
            path = line[3:].strip()
            
            if status == '??':
                added_files.append(path)
            elif status in ['M', 'MM', 'AM']:
                modified_files.append(path)
            elif status == 'D':
                deleted_files.append(path)
            elif status in ['R', 'RM']:
                renamed_files.append(path)
        
        # コミットメッセージの構築
        parts = []
        
        # ファイル種別に応じてアイコンとメッセージを追加
        if added_files:
            action = "✨ 新機能:"
            if len(added_files) == 1:
                parts.append(f"{action} {added_files[0]} を追加")
            else:
                parts.append(f"{action} {len(added_files)}個のファイルを追加")
        
        if modified_files:
            action = "🔧 機能改善:"
            if len(modified_files) == 1:
                filename = modified_files[0]
                if filename.endswith('.py'):
                    parts.append(f"{action} {filename} を更新")
                else:
                    parts.append(f"{action} {filename} を更新")
            else:
                # 主要なファイルタイプを特定
                py_files = [f for f in modified_files if f.endswith('.py')]
                if py_files and len(py_files) == len(modified_files):
                    # 機能別にグループ化
                    score_files = [f for f in py_files if 'スコア' in f or 'score' in f.lower()]
                    admin_files = [f for f in py_files if '管理' in f or 'admin' in f.lower()]
                    
                    if score_files:
                        parts.append(f"{action} スコア関連機能を更新")
                    elif admin_files:
                        parts.append(f"{action} 管理機能を更新")
                    else:
                        parts.append(f"{action} {len(py_files)}個のPythonファイルを更新")
                else:
                    parts.append(f"{action} {len(modified_files)}個のファイルを更新")
        
        if deleted_files:
            if len(deleted_files) == 1:
                parts.append(f"🗑️ {deleted_files[0]} を削除")
            else:
                parts.append(f"🗑️ {len(deleted_files)}個のファイルを削除")
        
        if renamed_files:
            if len(renamed_files) == 1:
                parts.append(f"📝 {renamed_files[0]} をリネーム")
            else:
                parts.append(f"📝 {len(renamed_files)}個のファイルをリネーム")
        
        # メッセージを結合（最初の項目のみ使用してシンプルに）
        if parts:
            main_msg = parts[0]
            if len(parts) > 1:
                additional_count = len(parts) - 1
                if additional_count == 1:
                    main_msg += " ほか1件の変更"
                else:
                    main_msg += f" ほか{additional_count}件の変更"
        else:
            main_msg = "📝 ファイルを更新"
        
        # 日付を付与
        now = datetime.datetime.now().strftime("%Y/%m/%d %H:%M")
        return f"{main_msg} ({now})"
    except Exception as e:
        print(f"コミットメッセージ生成中にエラーが発生しました: {e}")
        # エラーが発生した場合は簡易メッセージを返す
        now = datetime.datetime.now().strftime("%Y/%m/%d %H:%M")
        return f"📝 ファイル更新 ({now})"

def main():
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("🚀 Git フローを開始します...\n")
    
    # 1. 変更ファイルをステージング
    print("📋 ステップ 1: 変更ファイルをステージングエリアに追加")
    run_git_command(["git", "add", "."], cwd=repo_dir)
    
    # 2. コミット実行
    print("\n💾 ステップ 2: 変更をコミット")
    commit_msg = generate_commit_message()
    print(f"📝 コミットメッセージ: {commit_msg}")
    run_git_command(["git", "commit", "-m", commit_msg], cwd=repo_dir)
    
    # 3. developブランチにプッシュ
    print("\n🔄 ステップ 3: developブランチに変更をプッシュ")
    try:
        run_git_command(["git", "push"], cwd=repo_dir)
    except Exception as e:
        print("\n⚠️ プッシュに失敗しました。Git操作を中止します。")
        print("現在の状態を確認し、手動で修正してください。")
        print("以下のコマンドを実行することで、リモートの変更を取り込むことができます:")
        print("  git pull --rebase")
        print("コンフリクトが発生した場合は、コンフリクトを解決してから:")
        print("  git rebase --continue")
        print("  git push")
        return
    
    # 4. mainブランチに切り替え
    print("\n🌟 ステップ 4: mainブランチに切り替え")
    run_git_command(["git", "checkout", "main"], cwd=repo_dir)
    
    # 5. mainブランチの最新版を取得
    print("\n⬇️ ステップ 5: mainブランチの最新版を取得")
    run_git_command(["git", "pull", "origin", "main"], cwd=repo_dir)
    
    # 6. developブランチをmainにマージ
    print("\n🔀 ステップ 6: developブランチをmainにマージ")
    run_git_command(["git", "merge", "develop"], cwd=repo_dir)
    
    # 7. mainブランチにプッシュ
    print("\n⬆️ ステップ 7: mainブランチに変更をプッシュ")
    run_git_command(["git", "push", "origin", "main"], cwd=repo_dir)
    
    # 8. developブランチに戻る
    print("\n🔄 ステップ 8: developブランチに戻る")
    run_git_command(["git", "checkout", "develop"], cwd=repo_dir)
    
    print("\n✅ === Git フロー完了！ ===")
    print("🎉 すべての変更がmainブランチに正常にマージされました。")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        print("Gitワークフローは中断されました。")
