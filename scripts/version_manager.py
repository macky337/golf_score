"""トップ画面のバージョン情報を読み込む互換モジュール。"""

import datetime
import json
from pathlib import Path


JST = datetime.timezone(datetime.timedelta(hours=9), name="JST")


def get_version_file_path():
    return Path(__file__).parent.parent / "version.json"


def get_default_version():
    return {
        "major": 1,
        "minor": 0,
        "patch": 0,
        "last_updated": datetime.datetime.now(JST).strftime("%Y-%m-%d"),
    }


def load_version():
    """version.jsonを読み込み、壊れている場合は安全な既定値を返す。"""
    try:
        with get_version_file_path().open("r", encoding="utf-8") as version_file:
            version_info = json.load(version_file)
        if not all(key in version_info for key in ("major", "minor", "patch", "last_updated")):
            raise ValueError("version.json has missing fields")
        return version_info
    except (OSError, ValueError, json.JSONDecodeError):
        return get_default_version()
