import subprocess
import datetime
import os

def run_git_command(cmd, cwd=None):
    print(f"$ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    if result.returncode != 0:
        raise Exception(f"Command failed: {' '.join(cmd)}")

# 変更ファイル一覧を取得し、分かりやすい日本語でコミットメッセージを自動生成

def generate_commit_message():
    result = subprocess.run(["git", "status", "-s"], capture_output=True, text=True)
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
        filename = os.path.basename(path)
        
        if status == 'A':
            added_files.append(filename)
        elif status == 'M':
            modified_files.append(filename)
        elif status == 'D':
            deleted_files.append(filename)
        elif status in ['R', 'RM']:
            renamed_files.append(filename)
        else:
            modified_files.append(filename)
    
    # メッセージの構築
    parts = []
    
    if added_files:
        if len(added_files) == 1:
            parts.append(f"✨ {added_files[0]} を新規追加")
        else:
            parts.append(f"✨ {len(added_files)}個のファイルを新規追加")
    
    if modified_files:
        # ファイル名から推測される変更内容
        if any('fix' in f.lower() or 'bug' in f.lower() or 'エラー' in f or 'バグ' in f for f in modified_files):
            action = "🐛 バグ修正:"
        elif any('test' in f.lower() or 'テスト' in f for f in modified_files):
            action = "🧪 テスト:"
        elif any('config' in f.lower() or 'setting' in f.lower() or '設定' in f for f in modified_files):
            action = "⚙️ 設定変更:"
        elif any('.py' in f for f in modified_files):
            action = "🔧 機能改善:"
        else:
            action = "📝 更新:"
        
        if len(modified_files) == 1:
            # 特定のファイル名に基づいてより具体的なメッセージを生成
            filename = modified_files[0]
            if 'スコア' in filename or 'score' in filename.lower():
                parts.append(f"{action} スコア機能を更新")
            elif 'ハンディ' in filename or 'handicap' in filename.lower():
                parts.append(f"{action} ハンディキャップ機能を更新")
            elif '管理' in filename or 'admin' in filename.lower():
                parts.append(f"{action} 管理画面を更新")
            elif '結果' in filename or 'result' in filename.lower():
                parts.append(f"{action} 結果表示機能を更新")
            elif 'main' in filename.lower():
                parts.append(f"{action} メイン機能を更新")
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
    run_git_command(["git", "push"], cwd=repo_dir)
    
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
    main()
