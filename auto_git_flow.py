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

def check_git_status():
    """
    Gitの状態を確認し、問題があれば修正する
    """
    try:
        result = run_git_command(["git", "status"])
        
        # detached HEAD状態のチェック
        if "detached HEAD" in result.stdout or "HEAD detached" in result.stdout:
            print("\n⚠️ 警告: detached HEAD状態が検出されました！")
            if not fix_detached_head():
                return False
        
        # 現在のブランチを確認
        if "On branch" in result.stdout:
            branch = result.stdout.split("On branch")[1].split("\n")[0].strip()
            print(f"現在のブランチ: {branch}")
            return True
        
        return False
    except Exception as e:
        print(f"Git状態確認中にエラーが発生しました: {e}")
        return False

def fix_detached_head():
    """
    detached HEAD状態を修復する
    """
    print("\n===== detached HEAD状態を修復します =====")
    
    try:
        # 1. 変更を一時保存
        print("\n1. 変更を一時保存します...")
        run_git_command(["git", "stash"])
        
        # 2. 利用可能なブランチを確認
        print("\n2. 利用可能なブランチを確認します...")
        branch_result = run_git_command(["git", "branch"])
        branches = [b.strip().replace("* ", "") for b in branch_result.stdout.splitlines() if b.strip()]
        
        # 3. ターゲットブランチを決定
        target_branch = None
        if "develop" in branches:
            target_branch = "develop"
        elif "main" in branches:
            target_branch = "main"
        elif "master" in branches:
            target_branch = "master"
        
        if not target_branch:
            print("適切なブランチが見つかりません。修復を中止します。")
            return False
        
        # 4. ブランチに切り替え
        print(f"\n3. {target_branch}ブランチに切り替えます...")
        run_git_command(["git", "checkout", target_branch])
        
        # 5. 一時保存した変更を適用
        print("\n4. 保存した変更を適用します...")
        try:
            run_git_command(["git", "stash", "pop"])
        except Exception as e:
            print(f"変更の適用中にエラーが発生しましたが、ブランチの切り替えは成功しました: {e}")
        
        # 6. 状態を再確認
        status_result = run_git_command(["git", "status"])
        if "detached HEAD" in status_result.stdout or "HEAD detached" in status_result.stdout:
            print("修復に失敗しました。手動で対応してください。")
            return False
        
        print(f"\n✅ 正常に{target_branch}ブランチに復帰しました！")
        return True
    
    except Exception as e:
        print(f"\n❌ detached HEAD修復中にエラーが発生しました: {e}")
        print("以下の手順で手動修復を行ってください:")
        print("  git branch    # 利用可能なブランチを確認")
        print("  git checkout develop  # developブランチに切り替え")
        return False

# 変更ファイル一覧を取得し、分かりやすい日本語でコミットメッセージを自動生成
def generate_commit_message():
    try:
        # ステージングエリアの変更を確認
        result = subprocess.run(["git", "status", "-s"], capture_output=True, text=True, encoding='cp932' if sys.platform == 'win32' else 'utf-8')
        changed = result.stdout.strip().splitlines()
        if not changed:
            return None  # 変更がない場合はNoneを返す
        
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

def handle_conflicts():
    """
    マージ競合を処理する
    """
    print("\n⚠️ マージ競合が検出されました！")
    
    # 競合ファイルのリストを取得
    result = run_git_command(["git", "diff", "--name-only", "--diff-filter=U"])
    conflict_files = result.stdout.strip().split('\n')
    
    if not conflict_files or conflict_files[0] == '':
        print("競合ファイルが見つかりません。手動でチェックしてください。")
        return False
    
    print(f"以下のファイルに競合があります: {', '.join(conflict_files)}")
    
    # JSONファイルの競合を自動解決する
    for file in conflict_files:
        if file.endswith('.json'):
            print(f"\n自動でJSON競合を解決しようとしています: {file}")
            try:
                # version.jsonの場合はより高いバージョンを採用
                if file == 'version.json':
                    resolve_version_json_conflict()
                else:
                    print(f"{file}は自動解決に対応していません。手動で解決してください。")
            except Exception as e:
                print(f"自動解決に失敗しました: {e}")
                return False
        else:
            print(f"\n{file}は自動解決に対応していません。手動で解決してください。")
            return False
    
    # 解決済みファイルをステージングに追加
    print("\n解決済みのファイルをステージングに追加します")
    run_git_command(["git", "add", "."])
    
    return True

def resolve_version_json_conflict():
    """
    version.jsonのマージ競合を解決する
    常に大きいバージョン番号を採用する
    """
    try:
        # 競合しているファイルを読み込む
        with open('version.json', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 競合マーカーで分割
        parts = content.split('<<<<<<< HEAD')
        if len(parts) < 2:
            print("競合マーカーが見つかりません")
            return False
        
        head_part = parts[1].split('=======')
        ours = head_part[0].strip()
        
        theirs_part = head_part[1].split('>>>>>>>')
        theirs = theirs_part[0].strip()
        
        # 両方のバージョンからJSONデータを抽出
        import json
        try:
            ours_data = json.loads(ours)
        except json.JSONDecodeError:
            print("現在のバージョン情報が不正です")
            ours_data = {"major": 0, "minor": 0, "patch": 0}
        
        try:
            theirs_data = json.loads(theirs)
        except json.JSONDecodeError:
            print("リモートのバージョン情報が不正です")
            theirs_data = {"major": 0, "minor": 0, "patch": 0}
        
        # バージョン比較
        ours_version = (ours_data.get("major", 0), ours_data.get("minor", 0), ours_data.get("patch", 0))
        theirs_version = (theirs_data.get("major", 0), theirs_data.get("minor", 0), theirs_data.get("patch", 0))
        
        # 大きい方を採用
        if ours_version >= theirs_version:
            resolved_data = ours_data
        else:
            resolved_data = theirs_data
        
        # 最終更新日を現在に設定
        resolved_data["last_updated"] = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # 整形してファイルに書き込み
        with open('version.json', 'w', encoding='utf-8') as f:
            json.dump(resolved_data, f, indent=2, ensure_ascii=False)
        
        print(f"version.jsonを解決しました: バージョン {resolved_data['major']}.{resolved_data['minor']}.{resolved_data['patch']}")
        return True
    except Exception as e:
        print(f"version.jsonの競合解決中にエラーが発生しました: {e}")
        return False

def main():
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("🚀 Git フローを開始します...\n")
    
    # 0. Git状態を確認
    print("🔍 ステップ 0: Git状態を確認")
    if not check_git_status():
        print("\n❌ Git状態に問題があります。修正してから再度実行してください。")
        return
    
    # 1. 変更ファイルをステージング
    print("\n📋 ステップ 1: 変更ファイルをステージングエリアに追加")
    run_git_command(["git", "add", "."], cwd=repo_dir)
    
    # 2. コミット実行
    print("\n💾 ステップ 2: 変更をコミット")
    commit_msg = generate_commit_message()
    
    if commit_msg is None:
        print("📝 コミットする変更がありません。プッシュのみ実行します。")
        # プッシュのみ実行
        print("\n🔄 ステップ 3: developブランチに変更をプッシュ")
        try:
            run_git_command(["git", "push"], cwd=repo_dir)
        except Exception as e:
            print(f"\n⚠️ プッシュに失敗しました: {e}")
        
        print("\n✅ === プッシュ完了！ ===")
        return
    
    print(f"📝 コミットメッセージ: {commit_msg}")
    
    # コミットメッセージにダブルクォーテーションを追加
    commit_msg_quoted = f'"{commit_msg}"'
    run_git_command(["git", "commit", "-m", commit_msg_quoted], cwd=repo_dir)
    
    # 3. developブランチにプッシュ
    print("\n🔄 ステップ 3: developブランチに変更をプッシュ")
    try:
        run_git_command(["git", "push"], cwd=repo_dir)
    except Exception as e:
        print("\n⚠️ プッシュに失敗しました。リモートの変更を取り込みます。")
        try:
            # リモートの変更を取り込む
            print("\n🔄 リモートの変更を取り込んでいます...")
            run_git_command(["git", "pull", "--rebase"], cwd=repo_dir)
            
            # コンフリクトの確認
            status_result = run_git_command(["git", "status"], cwd=repo_dir)
            if "rebase in progress" in status_result.stdout:
                # コンフリクトがある場合
                if not handle_conflicts():
                    print("\n❌ 競合の自動解決に失敗しました。手動で解決してください。")
                    print("以下のコマンドを使用して競合を解決した後、リベースを継続できます:")
                    print("  git rebase --continue")
                    return
                
                # リベースを継続
                print("\n🔄 リベースを継続します...")
                run_git_command(["git", "rebase", "--continue"], cwd=repo_dir)
            
            # 再度プッシュを試みる
            print("\n🔄 変更をプッシュします...")
            run_git_command(["git", "push", "--force-with-lease"], cwd=repo_dir)
            
        except Exception as inner_e:
            print(f"\n❌ リモート変更の統合に失敗しました: {inner_e}")
            print("現在の状態を確認し、手動で修正してください。")
            return
    
    # 4. mainブランチに切り替え
    print("\n🌟 ステップ 4: mainブランチに切り替え")
    run_git_command(["git", "checkout", "main"], cwd=repo_dir)
    
    # 5. mainブランチの最新版を取得
    print("\n⬇️ ステップ 5: mainブランチの最新版を取得")
    run_git_command(["git", "pull", "origin", "main"], cwd=repo_dir)
    
    # 6. developブランチをmainにマージ
    print("\n🔀 ステップ 6: developブランチをmainにマージ")
    try:
        run_git_command(["git", "merge", "develop"], cwd=repo_dir)
    except Exception as e:
        print("\n⚠️ マージ中に競合が発生しました。")
        if not handle_conflicts():
            print("\n❌ 競合の自動解決に失敗しました。手動で解決してください。")
            print("競合を解決した後、以下のコマンドでマージを完了できます:")
            print("  git add .")
            print("  git commit -m \"マージ競合を解決\"")
            print("  git push origin main")
            return
        
        # マージを完了
        run_git_command(["git", "commit", "-m", "マージ競合を自動解決"], cwd=repo_dir)
    
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
