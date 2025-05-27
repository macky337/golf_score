# セキュリティインシデント報告書

## 概要
GitGuardianによってSupabase JWT トークンの公開リポジトリへの漏洩が検出されました。

## 影響範囲
- **漏洩したトークン**: Supabase Anonymous Key
- **公開期間**: 複数コミットにわたって漏洩
- **アクセス範囲**: パブリックリポジトリへの読み取り専用アクセス

## 実施した対応

### 1. 即座の対応 ✅
- [x] `.streamlit/secrets.toml` をGitリポジトリから削除
- [x] `.gitignore` に `.streamlit/` ディレクトリを追加
- [x] セキュリティ修正をリモートリポジトリにプッシュ

### 2. 必要な追加対応 🔴 **緊急**

#### A. Supabaseダッシュボードでの対応
1. **Supabaseプロジェクト設定にアクセス**:
   - URL: https://sukqpdycjfdkzfuquhsp.supabase.co
   - ダッシュボード: https://app.supabase.com

2. **APIキーの再生成**:
   - Settings > API で現在のanon keyを無効化
   - 新しいanon keyを生成
   - 必要に応じてRLSポリシーの見直し

#### B. アプリケーション設定の更新
1. **新しいキーでの設定**:
   ```toml
   # .streamlit/secrets.toml (ローカルのみ)
   [supabase]
   url = "https://sukqpdycjfdkzfuquhsp.supabase.co"
   key = "新しく生成されたANON_KEY"
   ```

2. **本番環境の更新**:
   - Streamlit Cloud の Secrets に新しいキーを設定

### 3. セキュリティ強化策

#### A. Git履歴のクリーンアップ（オプション）
```bash
# 完全な履歴削除が必要な場合
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch .streamlit/secrets.toml' \
  --prune-empty --tag-name-filter cat -- --all
```

#### B. 将来の予防策
- [x] `.gitignore` による秘密情報の除外
- [ ] pre-commit フックの設定
- [ ] CI/CDでのシークレット検証

## タイムライン
- **検出時刻**: GitGuardian アラート受信時
- **対応開始**: 即座
- **初期対応完了**: `.streamlit/secrets.toml` 削除およびプッシュ完了
- **残課題**: Supabaseキーの再生成（要手動実施）

## リスク評価
- **リスクレベル**: 中程度
- **理由**: 
  - Anonymous Keyのため直接的な書き込み権限なし
  - RLS (Row Level Security) により適切にアクセス制御されている可能性
  - ただし、予期しない読み取りアクセスが発生した可能性

## 推奨アクション
1. **即座にSupabaseキーを再生成** 🔴
2. データベースのアクセスログ確認
3. RLSポリシーの見直し
4. 今後の秘密情報管理プロセス改善

---
**注意**: この報告書も機密情報を含む可能性があるため、適切に管理してください。
