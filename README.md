ゴルフスコア集計ツール (Golf Score App)
ゴルフのラウンド時に生じる「握り」や「ハンデ」を考慮したスコア集計を簡単に行うためのWebアプリです。
Flask で構築されており、スマートフォンでも操作しやすいレスポンシブデザインに拡張可能です。

1. 機能概要
プレイヤー数を選択 (3人/4人)
各プレイヤー名・ハンデ設定・特別ルール設定
例：ハンデを前半5/後半5に分割する
例：前半・後半 ではなく 18ホール合計だけで勝敗判定
スコア・パット数入力
前半9ホール、後半9ホール、およびエキストラ9ホール
勝敗・ポイント計算
前半/後半/合計ごとのネットスコア判定
パット数の最少ストローク判定
プレイヤー間の個別設定（特別ルール）にも対応
集計結果の一覧表示 & PDFダウンロード
今後の拡張
データベースに保存（現在はメモリ管理）
アカウント管理・認証
UI/UX向上
2. ディレクトリ構成
csharp
コピーする
編集する
golf_score_app/
├── app.py                 # Flaskアプリのメインファイル
├── requirements.txt       # 使用ライブラリ一覧
├── README.md              # このファイル
├── static/
│   └── style.css          # CSSファイル（任意で追加）
└── templates/
    ├── base.html          # 基本レイアウト
    ├── index.html         # トップページ
    ├── settings.html      # プレイヤー設定画面
    ├── score_input.html   # スコア入力画面
    ├── result.html        # 結果表示画面
    └── result_pdf.html    # PDF用テンプレート例（必要に応じて作成）
3. セットアップ手順
3-1. 環境の準備
Pythonのインストール
Python 3.x がインストールされていることを確認してください。

仮想環境の作成 (任意)

bash
コピーする
編集する
python3 -m venv venv
source venv/bin/activate
※ Windows の場合は venv\Scripts\activate を実行

3-2. 依存ライブラリのインストール
bash
コピーする
編集する
pip install -r requirements.txt
requirements.txtの中には以下のようなライブラリが含まれます。

Flask
(任意) PDF出力のための WeasyPrint など
インストール後に pip freeze > requirements.txt などで更新できます。

4. アプリの起動方法
開発用サーバを起動

bash
コピーする
編集する
python app.py
app.py で debug=True を設定している場合、コードを変更すると自動リロードされます。
ブラウザでアクセス

http://127.0.0.1:5000/
同一ネットワーク内のスマートフォンでも、PCのIPアドレスを指定してアクセス可能です。
5. 使用方法
トップページ (/)

「設定画面へ」ボタンから設定画面へ移動します。
プレイヤー設定 (/settings)

3人 or 4人を選択
各プレイヤーの名前とハンデを入力
必要に応じて「合計のみ判定」などの特別ルールにチェック
「次へ」ボタンでスコア入力画面へ移動
スコア入力 (/score_input)

前半/後半のスコアとパット数を入力
エクストラ9ホールを追加する場合はチェックし、同様に入力
「結果へ」ボタンで結果表示画面へ移動
結果表示 (/result)

各プレイヤーのネットスコア(前半/後半/合計) と、パット数などから計算したポイントを一覧表示
「PDFダウンロード」でPDFファイルを取得 (WeasyPrint等を利用する場合)
6. ポイント計算ロジック概要
calculate_points() 関数内で以下のように集計を実施しています。

ネットスコア

net_front = front_score - (handicap // 2)
net_back = back_score - (handicap // 2)
net_total = net_front + net_back
（※ハンデ計算方法はプロジェクトのルールに応じて調整）
スコア勝敗判定

前半/後半/合計で最小ネットスコアプレイヤーに 10pt
特別ルール(use_total_only=True)のプレイヤーは前半・後半を除外 など
パット勝敗判定

前半の最小パット数が単独1位 -> 30pt
同率複数 -> 各自10pt
後半も同様
合計ポイント

スコアの勝敗とパットの勝敗を合計し、total_points へ格納
7. 今後の拡張
UI/UX向上
Bootstrapなどでレスポンシブにし、スマホ対応を強化
データベース連携
SQLite や PostgreSQL への永続化でスコア履歴を管理
認証機能
複数ユーザーで使う場合の認証/ログイン
より複雑なルールへの対応
「前半/後半それぞれのハンデをさらにホールごとに振り分け」
「マッチプレー形式」の勝敗など
クラウドデプロイ
Render, Railway, Heroku などで簡単に公開可能
8. ライセンス
本プロジェクトは自由に変更・拡張できます。利用にあたっては自己責任でお願いします。

