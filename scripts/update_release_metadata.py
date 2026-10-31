"""直近コミットの内容をもとに、バージョンと変更履歴を更新する。"""

import datetime
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
VERSION_FILE = ROOT / "version.json"
CHANGELOG_FILE = ROOT / "CHANGELOG.md"
JST = datetime.timezone(datetime.timedelta(hours=9))


def commit_subject():
    """直近コミットの件名を取得する。"""
    return subprocess.check_output(
        ["git", "log", "-1", "--pretty=%s"], cwd=ROOT, text=True
    ).strip()


def update_release_metadata(subject=None, now=None):
    """パッチ番号と変更履歴の先頭エントリーを更新する。"""
    now = now or datetime.datetime.now(JST)
    subject = subject or commit_subject()
    version = json.loads(VERSION_FILE.read_text(encoding="utf-8"))
    version["patch"] = int(version["patch"]) + 1
    version["last_updated"] = now.strftime("%Y-%m-%d")
    VERSION_FILE.write_text(
        json.dumps(version, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    entry = (
        f"## [{version['last_updated']}] v{version['major']}.{version['minor']}.{version['patch']}\n\n"
        "### 更新\n\n"
        f"- {subject}\n\n"
    )
    changelog = CHANGELOG_FILE.read_text(encoding="utf-8")
    header = "# 変更履歴\n\n"
    if not changelog.startswith(header):
        raise ValueError("CHANGELOG.md の先頭形式が正しくありません")
    CHANGELOG_FILE.write_text(header + entry + changelog[len(header):], encoding="utf-8")
    return version


if __name__ == "__main__":
    updated = update_release_metadata()
    print(f"Release metadata updated: v{updated['major']}.{updated['minor']}.{updated['patch']}")
