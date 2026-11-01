# Golf Score App

ゴルフコンペのスコア、ハンディキャップ、ゲームポイント、結果PDFを管理する Streamlit アプリです。スマホに保存したGolf Networkのスコア画像を読み取り、候補を確認して入力できます。

## 主な機能

- ラウンド設定、参加メンバー、ゴルフ場、対戦ハンディキャップの登録
- OUT／IN／エキストラのスコア・パット・ゲームポイント入力
- マッチ対戦、パット、ゲームポイントの集計と結果確認
- 結果PDFの生成、ラウンド確定、ポイント集計
- スコアカード画像のOCR候補を確認してOUT／IN／エキストラ入力欄へ反映
- 管理画面での修正、バックアップ、復元、ポイント診断

## 基本操作

通常の入力は次の順で行います。

1. 「ラウンド設定」で日付、ゴルフ場、参加メンバー、ハンディキャップを保存します。
2. 「フロントスコア入力」「バックスコア入力」で画像を読み取り、候補を確認して保存します。
3. 必要な場合だけ「エキストラスコア入力」で画像を読み取り、確認して保存します。
4. 「結果確認」で内容を確認し、PDFを生成してラウンドを確定します。

### 電波が弱い場所での入力

1. 現地でGolf Networkのスコア画像をスマホへ保存します。
2. 通信できる場所でアプリを開きます。
3. OUT／IN／必要な場合はエキストラの入力画面で、保存した画像を読み取ります。
4. 候補を元画像と照合し、必要な箇所を手入力で修正して保存します。

画像読取りとSupabaseへの保存にはインターネット接続が必要です。JSONファイルによるオフライン同期は使用しません。

## ローカル起動

Python 3 と仮想環境を用意し、依存関係をインストールします。

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

`.env` に最低限、次を設定します。値はリポジトリにコミットしません。

```text
SUPABASE_URL=...
SUPABASE_KEY=...
APP_USERNAME=...
APP_PASSWORD=...
ADMIN_PASSWORD=...
```

起動コマンドです。

```bash
.venv/bin/streamlit run main.py --server.address 127.0.0.1 --server.port 8502
```

### スコアカード画像の読み取り

OUT／IN／エキストラ入力画面の「画像からスコアを読み取る」から、Golf Networkのスコアカード画像を選択できます。対象はそれぞれ1〜9番、10〜18番、19〜27番です。JPG／JPEG／PNG／WEBPの画像を選択すると、画像対応AIが対象9ホールの合計スコア・パット・ゲームポイントを候補として表示します。縦向きの表は自動で横向きに補正します。

カメラ撮影ではなく、端末に保存した画像ファイルを選択する仕様です。候補は自動保存されないため、元画像と照合してから「候補を入力欄へ反映」を押し、通常の保存操作をしてください。画像読取りにはインターネット接続、OpenAI APIの利用可能なクレジット、およびRailway環境変数 `OPENAI_API_KEY` が必要です。

ブラウザで `http://localhost:8502` を開きます。

## デプロイ

Railway は [railway.toml](railway.toml) を使い、`main.py` を Streamlit で起動します。GitHub の `main` へpushすると、RailwayのGitHub連携による自動デプロイが始まります。

Railway Variables に、ローカルと同じ認証・Supabase関連の環境変数を設定してください。

計算結果の保存・ラウンド確定・ラウンド作成・スコア一括更新をDBトランザクションで処理し、公開API権限を閉じるため、アプリをデプロイする前にSupabase SQL Editorで `sql/atomic_round_save.sql`、`sql/atomic_score_writes.sql`、`sql/fix_security.sql` を実行してください。`atomic_score_writes.sql` は既存の採番シーケンスも現在の最大IDに合わせて初期化します。

### 競技ルール設定の初期化

管理画面からマッチ配点・パット配点を変更するには、Supabase SQL Editorで次を一度実行します。

```text
sql/add_competition_rules.sql
```

これにより、新規ラウンド用の標準ルールと、ラウンド作成時のルール保存列が追加されます。作成済みラウンドは従来の配点を維持します。バックアップ復元RPCも最新版にする場合は、続けて `sql/atomic_backup_restore.sql` を実行します。

## 構成

- `main.py`：ホーム画面
- `pages/`：ラウンド設定、スコア入力、結果、管理などの画面
- `modules/`：認証、DB、集計、PDF、共通UI処理
- `sql/`：SupabaseのDB設定・移行用
- `tests/`：自動テスト

`scripts/update_release_metadata.py` はコミット時のバージョン・変更履歴更新に使用します。`scripts/check_env.py` はローカル環境の設定確認用です。
