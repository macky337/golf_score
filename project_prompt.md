# プロジェクト概要
このプロジェクトでは、ゴルフのスコア計算ツールを開発します。4人または3人でゴルフをする際に、握りの計算を自動化することを目指します。事前にルール（個人対個人ごとのハンデ・参加者名など）を設定し、最終的なスコアを入力すると自動で計算してくれるツールを作成します。
## 目的
このプロジェクトの目的は、Pythonを使ったスコアデータをもとに勝敗と点数計算するツールを開発することです。

## 進捗
- [ ] 必要なライブラリのインストール
- [ ] データ収集
- [ ] データの前処理
- [ ] モデルの作成

## 詳細なプロンプト
1. 設定画面で当日のplayer名を登録、4人または3人を確定する。
2. 設定画面では、例えばplayer-A、player-Bへはハンデをハーフ5渡すとか、player-A、player-Cにハンデをハーフ３渡すなどその日の個別設定する。
3. 前半プレー終了後、前半の各自スコア、パット数を入力する。また、エキストラホール（追加でもうハーフ回る）を追加するかを決定する。その場合は、追加9ホール分の結果も入力できるようにする。
4. 18ホールまたは、27ホール終了後、すべての結果を入力完了したら、それぞれのスコアの勝敗、ハーフごとの最小パット数、それに伴う得点を集計し一覧表を作成する。
5. 一覧表の保存（PDFやJPG）する。
6. 詳細なルールは別途作成し、それをもとにロジックを考える。
7. 詳細なルールは以下の通り
    - 4人のplayerのそれぞれの前半9ホール・後半9ホール・合計のネットスコアの小さいほうが勝ち、それぞれ前半・後半・合計それぞれのポイント10点。Max30点
    - パター数は前半9ホール・後半9ホールそれぞれの最小ストローク（グロス）の少ないほうが勝ち、最小ストロークが1名の場合、他の3名からそれぞれ10ポイント、合計30ポイント獲得、同点2名の場合は、2名がそれぞれ10ポイント獲得、3名の場合もそれぞれ10ポイント獲得する。全員同点の場合はドローで0ポイント
    - 例外として対戦メンバーごとのルールを設定することができるようにする。例えばplayer-A、player-Bさんは前半後半ごとではなく、合計18ホールの勝ち負けで10ポイントの獲得を判定するように設定することができるようにする。
    - 前半9ホール・後半9ホールそれぞれのニヤピン・ドラコン・バーディ賞などをplayerがそれぞれカウントし前半9ホール・後半9ホール・エキストラホールがある場合はそれぞれのポイントを各自が集計し、それをもとに集計する。
    - 最終的に、表形式でそれぞれのスコア、ポイントを計算し表示する。これらをゲームポイントとする。
    - 自分の得点×３から他のメンバーの得点を引くことで自分のポイントが算出される。それぞれのplayerごとに計算する。これを集計ポイントとする
    - 検算として、それぞれのplayerのポイントの合計は必ずプラスマイナス０となるよう確認する。
    - 表形式の項目名はplayer-A,player-B,player-C,player-D(3人の場合はplayer-Cまで)、カラム名は、player,前半スコア、後半スコア、合計スコア、（あればエキストラ9ホールのスコア）、前半スコア勝敗ポイント、後半スコアポイント、合計スコアポイント、あればエキストラホールスコアポイント、ゲームポイント前半、ゲームポイント後半、（エキストラホールのゲームポイント）、合計ポイント、集計ポイント
    - どこのゴルフ場でプレイしたかをDBに含めてください。

## 使用イメージ
1. ゴルフ場に到着したら、代表者がこのアプリを立ち上げログインします。
2. 代表者は、設定画面で当日の日付、ゴルフ場、メンバー、既存メンバーは、選択して当日のプレイメンバーとして登録する。新規メンバーは、新規に登録する。マッチ形式で、誰が誰にいくつハーフハンデキャップをいくつ渡すかをを登録します。
3. 前半9ホール終了後、前半9ホールのスコア入力画面で、各playerのスコア、パットストローク、ゲームポイントを登録する。その時点での途中経過を表形式で表示します。
4. 後半9ホール終了後、後半9ホールのスコア入力画面で、スコア、パットストローク数、ゲームポイントを入力します。入力後、結果を表形式で表示します。エキストラホールがある場合は、エキストラホールがあることをチェックして次へ進み、エキストラ9ホールが終了後、エキストラ9ホールのスコア入力画面で、スコア、パットストローク数、ゲームポイントを入力します。入力後、結果を表形式で表示します。
5. 結果が間違えていなければ、結果をDBに登録します。結果に間違いがあれば、戻るボタンで、前半9ホール、後半9ホール、エキストラホールのいずれかに戻り、修正します。
6. 間違いがなければ、ゲームを確定し、最終結果を表形式で表示します。配布用にPDF,または、JPGで保存しLINEなどに投稿できるようにします。
7. すべて完了後に、アプリを終了ます。管理者用画面を作成し、過去データの修正や、事前にplayer、ゴルフ場などの登録ができるようにします。



> これはプロジェクトの最初のステップです。


以下では、**スマートフォンでの利用を想定**した場合の画面構成と、**Streamlit + SQLite** での実装手順を、7つのステップ（使用イメージに沿う形）で具体的にまとめます。  
マッチ形式での「ハーフハンデ渡し」「パット数によるポイント付与」「前半／後半／エキストラのスコア入力」「PDF/JPG出力」「過去データ参照・管理」といった要件を考慮しています。

---
# 1. 画面構成の概要

## (A) ログイン画面
- **画面1: ログイン画面**  
  1. ユーザー（代表者）がスマホでアプリを開き、ログインID/パスワードを入力。  
  2. 成功するとメインメニュー（サイドバー or メイン画面）へ遷移。  

## (B) 今日のラウンド設定
- **画面2: ラウンド設定画面**  
  1. 日付、ゴルフ場名を入力・選択  
  2. 参加メンバーを選択（既存メンバーリストから）または新規登録  
  3. 人数（3人 or 4人など）を指定  
  4. **マッチ形式**でペアごとに「誰が誰に何打ハーフハンデを渡すか」を登録  
     - 例: A→Bに5打, B→Cに3打, A→Cに2打 … のように入力  
  5. 「次へ」ボタンで前半スコア入力画面へ移動  

## (C) 前半スコア入力
- **画面3: 前半スコア入力画面**  
  1. 各プレイヤーごとに「前半9ホールのスコア」および「パット数」を入力  
  2. ニヤピン・ドラコン・バーディ等の「ゲームポイント」も入力可  
  3. 入力完了 → 「途中経過を計算する」ボタンで計算→テーブル表示  
     - 表示内容: ネットスコア（＝grossスコア - ハーフハンデ）で比較し、最小者に+10pt（同点複数なら全員±0pt）  
     - パット数最小者が1名なら+30, 2名同点なら残り2名-10, 3名同点なら残り1名-30 (4人プレイの場合)  
       - 3人の場合は 2名同点最小→+10、残り1名-20 など  
  4. 「次へ」 or 「後半入力画面へ進む」ボタン

## (D) 後半スコア入力
- **画面4: 後半スコア入力画面**  
  1. 各プレイヤーの「後半9ホールスコア」「後半パット数」「ゲームポイント」を入力  
  2. 「途中経過を計算する」ボタン→結果テーブルを表示  
     - 前半結果＋後半結果を合算した「暫定合計ポイント」表示  
  3. エキストラホール（追加9ホール）有無のチェックボックス  
     - あればチェックを付ける → 「エキストラ入力画面へ」ボタン  
     - なければ → 「最終結果の確認へ」ボタン  

## (E) エキストラ9ホールスコア入力 (任意)
- **画面5: エキストラ9ホール入力画面** (必要時のみ)  
  1. 同様に「スコア」「パット数」「ゲームポイント」を入力  
  2. 「途中経過を計算」ボタン→前半+後半+エキストラの合計を表示  
  3. 「最終結果の確認へ」ボタン

## (F) 最終結果の確認・保存
- **画面6: 結果確認・保存画面**  
  1. 今回のマッチ形式における最終ポイントを表形式で表示  
  2. 入力ミスがあれば「戻る」ボタンで前半/後半/エキストラ各画面へ戻り修正  
  3. 確定ボタンを押すと、データベースに結果を登録し、**PDFまたはJPGで出力**できるUIを用意  
     - StreamlitでPDFを生成する場合は `pdfkit` や `reportlab` 等を組み合わせる  
     - JPG化（画像キャプチャ）する場合は、SeleniumやPILを使った「画面キャプチャ」の仕組みを組むか、あるいはHtml2Image等のライブラリを組み合わせる  
  4. 生成されたPDF/JPGをダウンロードできる or 一時的にサーバー保存し、そのURLを取得 → LINEなどでシェア  

## (G) 過去データ参照／管理画面 (管理者用)
- **画面7: 過去ラウンド一覧＋詳細表示画面**  
  1. 過去に登録したラウンドを一覧表示 (日付, ゴルフ場, メンバーなど)  
  2. 選択すると詳細スコア・ポイントを表示  
  3. 管理者のみ「修正」や「削除」が可能  
  4. 新しいメンバーやゴルフ場を事前に登録する画面もここで提供  

---

# 2. 実装手順の例

## 2-1. 開発環境とライブラリ準備

1. **Python & Streamlit のインストール**  
   ```bash
   pip install streamlit
   pip install pandas
   pip install sqlalchemy   # DB操作向け(ORM)
   # PDF化 or 画像化が必要な場合:
   pip install pdfkit       # 例: PDFKit
   pip install wkhtmltopdf  # OS依存要件
   # or pip install reportlab
   ```
2. **SQLite** を使うための準備  
   - SQLiteは標準ライブラリでもOK。ORMには `SQLAlchemy` を使うと便利

## 2-2. データベース設計とテーブル定義

最低限、以下を用意します:

1. **members テーブル**  
   - メンバーID, 名前, 既存or新規区分, ハンデ情報など  
2. **rounds テーブル**  
   - ラウンドID, 日付, ゴルフ場名, 参加人数, (エキストラ有無) など  
3. **match_handicap テーブル**  
   - `round_id` + `playerA_id` + `playerB_id` + `half_hcp`  
   - 誰が誰に何打ハーフハンデを渡すか、ペア単位で記録  
4. **scores テーブル**  
   - ラウンドID, メンバーID, 前半スコア, 後半スコア, エキストラスコア, 各パット数, 各ゲームポイント, 計算後の最終ポイントなど

## 2-3. Streamlitアプリの画面構成

Streamlitは**1つのスクリプトで複数ページ**を作る場合、`st.sidebar` のセレクトボックスや `st.experimental_singleton` などを活用して**ページ遷移を疑似的に実装**します。  
公式には 1ファイル = 1ページ が基本ですが、**マルチページ構成**のやり方もあります。  
本例では**サイドバー**で画面切り替えをする一例を示します。

```python
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
# from ... import pdfkit, etc.

# 例: DB接続
engine = create_engine("sqlite:///golf_app.db", echo=False)

def main():
    st.set_page_config(page_title="Golf Score App", layout="centered")

    # --- サイドバーで画面選択 ---
    menu = ["ログイン", "今日のラウンド設定", "前半スコア入力", "後半スコア入力", 
            "エキストラスコア入力", "結果確認", "過去データ参照・管理"]
    choice = st.sidebar.selectbox("メニュー", menu)

    if choice == "ログイン":
        login_page()
    elif choice == "今日のラウンド設定":
        round_setup_page()
    elif choice == "前半スコア入力":
        front_score_page()
    elif choice == "後半スコア入力":
        back_score_page()
    elif choice == "エキストラスコア入力":
        extra_score_page()
    elif choice == "結果確認":
        result_confirm_page()
    elif choice == "過去データ参照・管理":
        admin_page()

if __name__ == "__main__":
    main()
```

### 2-3-1. ログイン画面 (画面1)

```python
def login_page():
    st.title("ログイン")
    user_id = st.text_input("User ID")
    password = st.text_input("Password", type="password")
    if st.button("ログイン"):
        # 認証ロジックを実装
        st.success("ログイン成功")
        st.experimental_set_query_params(page="今日のラウンド設定")  # 次のページに移動
```

*(厳密なユーザ管理が必要なら、SQLiteにusersテーブルを作ってPWハッシュ認証するなど)*

### 2-3-2. 今日のラウンド設定 (画面2)

```python
def round_setup_page():
    st.title("今日のラウンド設定")
    # 日付, ゴルフ場名入力
    round_date = st.date_input("ラウンド日")
    course_name = st.text_input("ゴルフ場名")

    # 既存メンバーの取得と選択
    # new_member_name = st.text_input("新規メンバー入力")
    # あるいは複数人まとめて追加など
    
    # 参加人数 (3 or 4)
    num_players = st.selectbox("参加人数", [3,4], index=1) 

    # 誰が誰にいくつのハーフHCPを渡すか (マッチ方式)
    # 例: playersの名前を選択できるセレクトボックス複数で定義

    if st.button("次へ"):
        # ラウンド情報をDBに登録
        # ハーフHCP情報をmatch_handicapテーブルに登録
        st.experimental_set_query_params(page="前半スコア入力")
```

### 2-3-3. 前半スコア入力 (画面3)

```python
def front_score_page():
    st.title("前半スコア入力")

    # DBから本ラウンドに登録されたプレイヤーの一覧を取得
    # for each player, スコア/パット/ゲームPTを入力
    # 例:
    players = ["player-A", "player-B", "player-C", "player-D"]  # 実際はDBから
    
    score_data = {}
    for p in players:
        st.subheader(p)
        score_data[p+"_front_score"] = st.number_input(f"{p} スコア(前半)", min_value=0, max_value=60)
        score_data[p+"_front_putt"]  = st.number_input(f"{p} パット数(前半)", min_value=0, max_value=36)
        score_data[p+"_front_game_pt"] = st.number_input(f"{p} ゲームポイント(前半)", min_value=0)

    if st.button("途中経過を計算"):
        # 計算ロジック:
        # 1. 各プレイヤーのネットスコア = front_score - half_hcp
        # 2. 最小ネットスコア判定 → +10 (同点複数なら全員±0)
        # 3. パット数最少者の判定 → +30 or 2名同点→ 残り-10 etc...
        st.write("計算結果をここに表示(仮)")
        # テーブル形式で途中経過
        # st.table(df_calculated)
    
    if st.button("後半スコア入力へ"):
        st.experimental_set_query_params(page="後半スコア入力")
```

### 2-3-4. 後半スコア入力 (画面4)

同様に後半スコア／パット／ゲームポイント入力を行い、**計算ボタン→途中経過表示**→「エキストラへ」 or 「最終結果へ」ボタン。  
エキストラ有無はチェックボックスかセレクトボックスで分岐。

### 2-3-5. エキストラスコア入力 (画面5) - 任意

必要な場合のみ表示。ロジック・UIは前半/後半とほぼ同じ。

### 2-3-6. 結果確認・保存 (画面6)

```python
def result_confirm_page():
    st.title("結果確認")

    # DBから当日のラウンド情報＋スコア情報を集計
    # → 表形式で最終結果を表示
    
    st.write("最終結果一覧 (テーブル表示)")
    # st.table(final_result_df)

    if st.button("修正"):
        # 前半/後半/エキストラへ戻る
        # st.experimental_set_query_params(page="前半スコア入力") 等
        pass

    if st.button("確定して保存"):
        # DBに確定フラグを立てる or final_resultテーブルにINSERT
        st.success("結果を保存しました")

        # PDF or JPG生成
        if st.button("PDFで出力"):
            # PDF生成ロジック (pdfkit/reportlab等)
            pass
        if st.button("JPGで出力"):
            # 画面キャプチャ(ライブラリ) or HTML→画像変換
            pass

        st.info("LINEなどで共有可能です")
```

### 2-3-7. 過去データ参照・管理 (画面7)

```python
def admin_page():
    st.title("過去データ参照・管理")

    # 過去のラウンド一覧を表示
    # e.g. df_rounds = SELECT * FROM rounds ORDER BY date DESC
    # st.table(df_rounds)

    # 詳細ボタンを押すと該当ラウンドのスコア詳細を表示
    # 修正／削除も可能にする

    # 事前にplayer,ゴルフ場を登録できるUI
    st.subheader("新規プレイヤー登録")
    new_player = st.text_input("名前")
    if st.button("登録"):
        # membersテーブルINSERT
        st.success("登録しました")
```

---

# 3. 計算ロジックのポイント

1. **ハーフハンデ計算**:  
   - `net_score = gross_score - half_hcp`  
   - ペアごとに違うハンデを渡す場合、**1対1のマッチ結果**をすべて集計する方法もありますが、今回の要件では「前半／後半／エキストラごとの最小ネットスコアに+10」とあるため、  
     - 「各プレイヤーが誰から何打もらうか」を合計し、**実質“総ハーフHCP”をそのプレイヤーのgross_scoreから引いた値**を算出して比較する形が想定されます。  
   - 3人／4人でロジックが分かれるため、**人数分のハーフHCP合計を事前に算出**し、スコア入力時にそれを差し引き。

2. **前半／後半／エキストラの最小ネットスコア → +10pt, 同点複数 → 全員±0pt**  
   - 同点の場合は誰も+10を得ず、0ptという解釈。

3. **パット数のポイント** (4人の場合)  
   - 1名のみが最少 → +30  
   - 2名同点最少 → それ以外の2名は -10  
   - 3名同点最少 → 残り1名は -30  
   - 全員同点 → 0  (特記事項がなければ全員0)  

   3人プレイの場合:  
   - 2名同点最少 → その2名 +10, 残り1名 -20  
   - 全員同点 → 全員0  

4. **ニヤピン・ドラコン・バーディ賞**などはユーザー入力した数値をそのまま加算する想定

5. **最終合計ポイント**  
   - 前半、後半、エキストラ分の**「スコア勝敗ポイント」 + 「パットポイント」 + 「ゲームポイント」**を合計  
   - ルールによっては「自分の得点×3 - 他プレイヤーの合計」→集計Pt を計算する方法もあるため、必要に応じて最終ページで算出

---

# 4. スマホ画面への最適化

- **Streamlitのレイアウト**: `st.set_page_config(layout="centered")` やサイドバーの使い方調整  
- **各入力項目を縦長に配置**し、スマホの幅に合わせる  
  - `st.columns()` で横並びは最小限にし、1列ベースで見やすくする  
- **ボタンの配置**: 前後ボタンを画面下部に大きく配置  
- **PDF/JPG 出力**: スマホでもタップしやすいサイズのボタンを用意  

---

# 5. PDF・JPG 出力の実装例

1. **PDF**  
   - `pdfkit` でHTMLをPDFに変換 → `st.download_button` でユーザーにダウンロードさせる  
   - または `reportlab` でPythonコードによるPDF生成  
2. **JPG**  
   - **Html2Image** や **Selenium + headless Chrome** などを使い、結果ページHTMLを画像化  
   - 一時的にファイルを保存し、`st.download_button` でダウンロード or ボタン押下でLINE共有URLに飛ばすなど

---

# 6. 過去データ参照機能

- **rounds テーブル**から「日付順」「ゴルフ場」「参加者」を一覧表示  
- 行を選択すると、そのラウンドのスコア詳細ページへ遷移  
- **修正** が必要なら、そのラウンドの前半スコア／後半スコアなどを再入力して再計算  
  - 再度「確定ボタン」を押すとDBをUPDATE  

---

# 7. まとめ

1. **画面数（機能別）**  
   - ログイン画面  
   - ラウンド設定画面  
   - 前半スコア入力画面  
   - 後半スコア入力画面  
   - エキストラスコア入力画面（任意）  
   - 結果確認・保存画面  
   - 過去データ参照・管理画面  

2. **Streamlit** を使い、**SQLite**でデータを管理しつつ、**モバイルファースト**でUIを設計する  
3. **マッチ形式のハーフハンデ**・**パットポイントロジック**・**ゲームポイント**を入力時に計算する  
4. **最終結果はDBに保存**し、**PDF/JPGで出力**してLINE等で共有可能にする  
5. **過去データ参照**や管理者用の画面も備え、運用・管理しやすくする  

以上の流れで、携帯（スマートフォン）利用を想定したゴルフスコアアプリを開発できます。


以下は、Streamlit + SQLite を使ってゴルフスコアアプリを開発する際の、例示的なディレクトリ構成の一例です。
開発規模や運用方針に応じて適宜アレンジしてください。

csharp
コピーする
編集する
golf_app/
├── README.md                   # プロジェクト概要やセットアップ手順などを記載
├── requirements.txt            # 必要ライブラリをまとめて管理 (例: streamlit, sqlalchemy, pdfkit 等)
├── data/
│   └── golf_app.db             # SQLite データベースファイル (初期は空ファイル or 後で自動生成)
├── main.py                     # Streamlitアプリのエントリポイント (単ページ構成の場合)
├── pages/                      # Streamlitのマルチページ構成にする場合、各ページを配置
│   ├── 01_ログイン.py
│   ├── 02_今日のラウンド設定.py
│   ├── 03_前半スコア入力.py
│   ├── 04_後半スコア入力.py
│   ├── 05_エキストラスコア入力.py
│   ├── 06_結果確認.py
│   └── 07_過去データ参照_管理.py
├── modules/                    # アプリ全体で使用する共通ロジックやDB操作、計算処理などをまとめるフォルダ
│   ├── __init__.py
│   ├── db.py                   # DB接続 (SQLAlchemy セッション作成など)
│   ├── models.py               # SQLAlchemy で定義するテーブル（ORMモデル）クラス群
│   ├── calculations.py         # スコアやポイントの計算ロジックをまとめる
│   └── pdf_export.py           # PDFや画像出力に関連する関数を置く (reportlab, pdfkit 等)
├── static/                     # 静的ファイル (CSS, 画像など)
│   ├── css/
│   │   └── style.css
│   └── images/
│       └── logo.png
└── scripts/                    # 初期データ投入スクリプトやメンテナンス用スクリプトを置く
    └── init_db.py              # DBの初期化やテストデータ投入のためのスクリプト
各ディレクトリの説明
golf_app/

プロジェクトのルートディレクトリ。
README.md にプロジェクトの概要やセットアップ手順を書いておくと、他メンバーや後日参照に便利。
requirements.txt

このファイルに streamlit, sqlalchemy, pdfkit, reportlab など、必要なPythonライブラリを一覧で記載
pip install -r requirements.txt でまとめてインストール可能
data/

データベースファイルや、CSVインポート用ファイルなどを置く
SQLiteの .db ファイルをここに保存
main.py

単ページ構成の場合、Streamlitアプリのメインスクリプトとして使用
マルチページ構成の場合は、pages/ 内の各ページに分割し、main.py はトップレベルの案内やランディングページとして利用
pages/

Streamlitのマルチページモードを使う場合に、各画面（ログイン／ラウンド設定／前半スコア入力 など）を .py ファイルごとに分ける
ファイル名の頭に番号を振るとサイドバーでの並び順を制御できる
modules/

共通処理やビジネスロジックをまとめるフォルダ
例:
db.py: SQLiteへの接続やSQLAlchemyのセッションを作成するモジュール
models.py: SQLAlchemyで定義する Member, Round, Score, MatchHandicap などのORMクラスをまとめる
calculations.py: スコアやハーフHCPの引き算、最少パット判定 +30/-10 等のロジック実装
pdf_export.py: PDFや画像ファイルへの出力（pdfkit, reportlab など）を行う関数群
static/

画像やCSS、JavaScriptなどの静的ファイルを配置する場所
StreamlitでCSSを読み込む場合は st.markdown や st.write でHTMLを埋め込んで読み込むか、テーマ機能を利用する
scripts/

本番前の初期データ投入やDBマイグレーションなど、一時的に使うスクリプトを保管
init_db.py では models.py のメタデータから Base.metadata.create_all(engine) を呼び出し、データベースを初期化したり、サンプルデータを投入したりできる
このようにディレクトリを整理することで、画面（UI）ロジックとビジネスロジック（計算・DB操作）、静的アセット等が分かりやすく管理でき、チーム開発や保守がスムーズになります。


ディレクトリ構成を修正
golf_score/
├── README.md                      # プロジェクトの概要、セットアップ手順、使用方法など
├── requirements.txt               # 必要なPythonライブラリを列挙 (streamlit, sqlalchemy, pdfkit 等)
├── main.py                        # Streamlitのエントリーポイント (トップページ、共通処理など)
├── data/
│   └── golf_app.db               # SQLiteのDBファイル (初期は空 or 後で作成される)
├── pages/                         # Streamlitのマルチページ用ディレクトリ
│   ├── 01_login.py               # ログイン機能
│   ├── 02_round_setup.py         # 日付・ゴルフ場・メンバー選択、ハンデ設定など
│   ├── 03_front_score_input.py   # 前半スコア・パット数・ゲームポイント入力
│   ├── 04_back_score_input.py    # 後半スコア・パット数・ゲームポイント入力
│   ├── 05_extra_score_input.py   # エキストラホール（追加9H）のスコア入力
│   ├── 06_result_confirm.py      # 途中経過や最終結果の確認・DB登録
│   └── 07_history_management.py  # 過去ラウンド結果一覧・詳細表示・修正機能など
├── modules/                       # 共通モジュール (DB接続, 計算ロジック, PDF生成など)
│   ├── __init__.py
│   ├── db.py                     # DB接続設定やSQLAlchemyセッション管理
│   ├── models.py                 # SQLAlchemyのORMモデル定義 (Member, Score, Round, etc.)
│   ├── calculations.py           # スコア比較・ハンデ計算・パットポイントなどのロジック
│   └── pdf_export.py             # PDF/JPG出力機能 (pdfkit, reportlab 等)
├── static/                        # 静的ファイル (CSS, 画像等) 
│   ├── css/
│   │   └── style.css
│   └── images/
│       └── logo.png
└── scripts/                       # 初期化やメンテ用スクリプトを配置
    └── init_db.py                # DB初期化・テストデータ投入用スクリプト


以下は、Streamlit + SQLite でゴルフスコアアプリ（golf_app.db）を構築するうえで想定されるテーブル構成の一例です。
ここでは、ログイン情報を管理する users テーブル、プレイヤー情報を管理する members テーブル、ラウンド設定やマッチ形式のハンデ情報、各プレイヤーのスコアを保存するためのテーブルを提示しています。
実際のプロジェクト要件に合わせてカラム名や型を調整してください。

1. users (ログイン管理)
カラム名	型	説明
user_id	INTEGER (PK)	主キー (AUTOINCREMENT)
username	TEXT (UNIQUE)	ログインID、ユニーク制約
password_hash	TEXT	パスワードのハッシュ値
created_at	DATETIME	ユーザー登録日時
is_admin	BOOLEAN	管理者権限を持つユーザーかどうか
用途: アプリへログインする代表者や管理者を管理
必要に応じて、メールアドレス・権限区分など追加
2. members (プレイヤー管理)
カラム名	型	説明
member_id	INTEGER (PK)	主キー (AUTOINCREMENT)
name	TEXT	プレイヤーの名前
base_handicap	INTEGER	(任意) 通常時の基本ハンデなどがあれば記録
is_active	BOOLEAN	現在アクティブかどうか
created_at	DATETIME	登録日時
用途: アプリで扱うプレイヤー(メンバー)を一元管理
当日のラウンドでは、このテーブルの中から参加者を選択する
3. rounds (ラウンド情報)
カラム名	型	説明
round_id	INTEGER (PK)	主キー (AUTOINCREMENT)
date_played	DATE	ラウンド日
course_name	TEXT	ゴルフ場名
num_players	INTEGER	今回のラウンドの参加人数 (3 or 4など)
has_extra	BOOLEAN	エキストラ9ホールの有無
created_at	DATETIME	ラウンド設定の作成日時
finalized	BOOLEAN	ラウンド結果が最終確定済みかどうか (True/False)
用途: 1ラウンド(ゴルフプレー1回分)を管理するテーブル
num_players や has_extra でスコア入力画面を切り替える
finalized が True になったら結果を変更できない等の運用ルールを設定可能
4. match_handicap (マッチ形式のハンデ設定)
カラム名	型	説明
match_handicap_id	INTEGER (PK)	主キー (AUTOINCREMENT)
round_id	INTEGER	rounds.round_id への外部キー
giver_id	INTEGER	members.member_id (ハンデを渡す側のプレイヤー)
receiver_id	INTEGER	members.member_id (ハンデを受け取る側のプレイヤー)
half_hcp	INTEGER	渡すハーフハンデ（例：5打、3打…）
用途: 「A→Bに5打、A→Cに3打…」など、ペア単位でハンデを管理する
1対1のペアごとにレコードを作り、giver_id と receiver_id で誰が誰にハンデを渡すかを定義
例:
round_id = 10（10回目のラウンド）
giver_id = 1 (member_id=1 のプレイヤー)
receiver_id = 2 (member_id=2 のプレイヤー)
half_hcp = 5 → 「プレイヤー1 は プレイヤー2 にハーフ5打のハンデを渡す」
5. scores (スコア情報)
カラム名	型	説明
score_id	INTEGER (PK)	主キー (AUTOINCREMENT)
round_id	INTEGER	rounds.round_id への外部キー (どのラウンドか)
member_id	INTEGER	members.member_id への外部キー (どのプレイヤーか)
front_score	INTEGER	前半9ホールのグロススコア
back_score	INTEGER	後半9ホールのグロススコア
extra_score	INTEGER	エキストラ9ホールのグロススコア (無ければ NULL)
front_putt	INTEGER	前半9ホールのパット数
back_putt	INTEGER	後半9ホールのパット数
extra_putt	INTEGER	エキストラ9ホールのパット数 (無ければ NULL)
front_game_pt	INTEGER	ニヤピン・ドラコン・バーディ等、前半9ホールでのゲームポイント合計
back_game_pt	INTEGER	後半9ホールでのゲームポイント合計
extra_game_pt	INTEGER	エキストラ9ホールでのゲームポイント合計
net_front_score	INTEGER	前半のネットスコア(= front_score - ハンデ合計)
net_back_score	INTEGER	後半のネットスコア(= back_score - ハンデ合計)
net_extra_score	INTEGER	エキストラのネットスコア(= extra_score - ハンデ合計)
score_points	INTEGER	スコア勝敗によるポイント(+10/-10等)を前半・後半・エキストラで合計したもの
putt_points	INTEGER	パット数によるポイント(+30/-10等)を前半・後半・エキストラで合計したもの
total_game_pt	INTEGER	front_game_pt + back_game_pt + extra_game_pt (ニヤピン等のゲームポイント合計)
total_points	INTEGER	最終合計ポイント(= score_points + putt_points + total_game_pt などルールに応じて計算)
final_calc	INTEGER	自分の得点×(人数-1) - 他プレイヤー合計 など、最終の「精算ポイント」を必要なら保持
用途: 各ラウンド・各プレイヤーのスコア詳細を記録
ネットスコアやスコア勝敗ポイント、パット数による加点/減点もここにまとめて計算・更新
途中経過では一時的に net_front_score などが NULL でもOK。最終確定後にUPDATEする、という運用も可能
補足
「誰が誰に +10/-10 を与えるか」をペアごとに計算して反映する場合、テーブルに細分化して持つこともできますが、最終的にプレイヤー個人が得たトータルの加点/減点合計をこのテーブルのフィールドに保存しておくと、後で集計・表示しやすくなります。
テーブル間のリレーション図 (概念)
scss
コピーする
編集する
users (1)           members (多)
                └─> scores (多) --(belongs_to)--> rounds (1)
                          |           
                          └-> match_handicap (多) <--(also belongs_to) rounds (1)
users: ログイン用（admin, general user管理など）
members: ゴルフプレイヤー個人情報
rounds: 1つのゴルフラウンド（当日のプレー）
scores: (round_id, member_id) を持ち、各メンバーのスコア＆ポイントを記録
match_handicap: (round_id, giver_id, receiver_id, half_hcp) のセットでハーフハンデを管理
まとめ
users: ログイン/認証用 (必要に応じて省略可能)
members: ゴルフプレイヤー管理
rounds: 1ラウンドあたりの情報 (日付、ゴルフ場、人数など)
match_handicap: ペアごとのハンデ設定
scores: 各プレイヤーのスコア・パット数・ポイント計算結果
この構成により、

ラウンドに紐づく複数のプレイヤー(members)のスコアを scores テーブルで一括管理し、
ペア対戦のハンデ情報は match_handicap テーブルに格納、
最終的に勝敗ポイントやパットポイント、ニヤピン等のゲームポイントを scores に合算して「最終ポイント」を算出しやすくなります。
実際の運用では、アプリの要件(例: 途中経過の保存方法、引き分け時の処理、複数ラウンドの集計など)に応じてカラムや外部キーの設定を細かく調整してください。


# 計算ロジック

  ## game pt
    -front game pt合計
    -back game pt合計
    -extra game pt合計
    -total game pt = front game pt + back game pt + extra game pt
    
    ### game ptの計算
      各自のtotal game ptで自分の取り分を計算する。
　　    -4人の場合
　　　　  自分の獲得total game pt
　　    -3人の場合
　　　　  自分の獲得total game pt * 2 - (他のplayerのtotal game pt）


  ## much pt
    ###　勝利の判定
　　  -scoreが小さいほうが勝利

    ### ロジック
　　  -ペアごとに違うハンデを渡すため、1対1のmuch結果をすべて集計する方法を採用してください。
      -front score/back score/total scoreで判定する。ペアごとに勝利した結果、→ 勝者は+10pt, 同点は、両者±0pt、敗者は‐10pt獲得する。  
      -それぞれfront score/back score/total scoreそれぞれのポイント10点とする。Max30点
      -extra scoreがある場合は、extra scoreの勝者にさらに+10ptを加えmax+40とする。

      #### total scoreのみで戦うにチェックが入っている（true)の場合のロジック
　　    -total scoreでのみ判定する。→ 勝者+10pt, 同点は両者±0pt敗者は‐10ptでMax10ptを獲得する。
        -extra scoreがある場合はextra scoreの勝敗で10pt判定する、勝者+10pt, 同点は両者±0pt敗者は‐10ptを加え、
        -Max10pt,total score+10pt extra score+10pt 合計max+20ptとする。

  ## put pt
    ### 4人の場合  
     - 1名のみが最少 → +30pt  
     - 2名同点最少 → それ以外の2名は -10pt  
     - 3名同点最少 → 残り1名は -30pt  
     - 全員同点 → 0pt    
  
    ### 3人の場合)
     - 1名のみが最少 → +20pt  
     - 2名同点最少 → それ以外の1名は -20pt  
     - 全員同点 → 0pt    

    ### 各個人ポイントを計算する
     - put pt総合計
     - playerのput ptのtotalを計算する


  ## 総ポイント
    ### 各playerのgame pt + much pt＋put ptを合計したものが総合計ptとして計算する。
    ### 表形式にまとめる