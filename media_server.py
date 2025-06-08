"""
メディアファイル配信サーバー
Streamlitアプリと併用してPDFファイルなどのメディアファイルを配信する
"""
import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import threading
import time
from modules.media_utils import get_media_directory

# FastAPIアプリケーションを作成
app = FastAPI(title="Golf Score Media Server", version="1.0.0")

# CORSミドルウェアを追加
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """ヘルスチェック用エンドポイント"""
    return {"message": "Golf Score Media Server is running"}

@app.get("/media/{filename}")
async def get_media_file(filename: str):
    """メディアファイルを配信するエンドポイント"""
    try:
        media_dir = get_media_directory()
        file_path = os.path.join(media_dir, filename)
        
        # ファイルの存在確認
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # セキュリティチェック: ディレクトリトラバーサル攻撃を防ぐ
        if not os.path.abspath(file_path).startswith(os.path.abspath(media_dir)):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # ファイルの年齢チェック（24時間以内）
        file_age = time.time() - os.path.getmtime(file_path)
        if file_age > 24 * 3600:  # 24時間
            raise HTTPException(status_code=410, detail="File expired")
        
        # ファイルタイプの判定
        if filename.endswith('.pdf'):
            media_type = 'application/pdf'
        elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
            media_type = 'image/jpeg'
        elif filename.endswith('.png'):
            media_type = 'image/png'
        else:
            media_type = 'application/octet-stream'
        
        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

def start_media_server():
    """メディアサーバーを別スレッドで起動"""
    port = int(os.getenv('MEDIA_SERVER_PORT', '8001'))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")

def start_media_server_async():
    """メディアサーバーを非同期で起動（バックグラウンド）"""
    server_thread = threading.Thread(target=start_media_server, daemon=True)
    server_thread.start()
    return server_thread

if __name__ == "__main__":
    # 直接実行された場合
    start_media_server()
