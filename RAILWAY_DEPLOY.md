## 1. 必要ファイルの準備

1. プロジェクトルートに `requirements.txt` を用意  
   ```text
   # 例として以下の依存を記載
   streamlit==1.45.1
   pandas
   supabase
   python-dotenv
   reportlab
   streamlit-extras
   ```

2. `Procfile` を追加  
   ```Procfile
   web: streamlit run main.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
   ```

3. `.streamlit/config.toml` を設定
   ```toml
   [server]
   headless = true
   enableCORS = false
   enableXsrfProtection = false
   
   [browser]
   gatherUsageStats = false
   ```

## 2. Railway環境変数の設定

以下の環境変数をRailwayダッシュボードで設定：
- `SUPABASE_URL`: あなたのSupabaseプロジェクトURL
- `SUPABASE_KEY`: あなたのSupabaseプロジェクトAPIキー

## 3. デプロイ設定の確認
※以下のコマンドは**Railway のダッシュボード → Settings → Deploy → Build Command** に設定する例です。  
PowerShell などのローカル環境で実行するわけではありません。

```
# Build コマンド (Railway に登録)
pip install --upgrade pip
pip install -r requirements.txt
```

※Start コマンドはProcfileを参照して自動で実行されます。  
```Procfile
web: streamlit run main.py --server.port=$PORT --server.address=0.0.0.0
```
