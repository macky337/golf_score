#!/usr/bin/env python3
"""
すべてのページファイルにシステムパスを追加するスクリプト
"""
import os
import glob

def fix_page_imports():
    """ページファイルのインポートパスを修正"""
    pages_dir = "pages"
    
    # pagesディレクトリ内のすべての.pyファイルを取得
    page_files = glob.glob(os.path.join(pages_dir, "*.py"))
    
    for file_path in page_files:
        print(f"処理中: {file_path}")
        
        # ファイルを読み込み
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 既にパス追加コードがある場合はスキップ
        if "sys.path.append" in content:
            print(f"  スキップ: 既にパス追加済み")
            continue
        
        # インポート文を探す
        lines = content.split('\n')
        import_index = -1
        
        for i, line in enumerate(lines):
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                import_index = i
                break
        
        if import_index == -1:
            print(f"  スキップ: インポート文が見つかりません")
            continue
        
        # パス追加コードを挿入
        path_code = [
            "import sys",
            "import os",
            "# モジュールのインポートパスを追加",
            "sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))",
            ""
        ]
        
        # 既存のimport sys, import osがある場合は削除してから追加
        new_lines = []
        skip_next_empty = False
        
        for line in lines:
            if line.strip() == "import sys" or line.strip() == "import os":
                continue
            if line.strip() == "# モジュールのインポートパスを追加":
                skip_next_empty = True
                continue
            if skip_next_empty and line.strip() == "":
                skip_next_empty = False
                continue
            if "sys.path.append" in line:
                continue
            new_lines.append(line)
        
        # パス追加コードを最初のインポートの前に挿入
        final_lines = []
        path_added = False
        
        for i, line in enumerate(new_lines):
            if not path_added and (line.strip().startswith('import ') or line.strip().startswith('from ')):
                final_lines.extend(path_code)
                path_added = True
            final_lines.append(line)
        
        # ファイルに書き戻し
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(final_lines))
        
        print(f"  完了: パス追加コードを挿入")

if __name__ == "__main__":
    fix_page_imports()
    print("すべてのページファイルの修正が完了しました")
