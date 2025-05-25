## 1. 必要ファイルの準備

1. プロジェクトルートに `requirements.txt` を用意  
   ```text
   # 例として以下の依存を記載
   streamlit
   pandas
   supabase
   python-dotenv
   reportlab
   streamlit-extras
   ```
2. `Procfile` を追加  
   ```Procfile
   web: streamlit run main.py --server.port=$PORT --server.address=0.0.0.0
   ```

## 4. デプロイ設定の確認
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
