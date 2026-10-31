import json

from scripts import update_release_metadata as release


def test_release_metadata_increments_version_and_adds_changelog_entry(tmp_path, monkeypatch):
    version_file = tmp_path / "version.json"
    changelog_file = tmp_path / "CHANGELOG.md"
    version_file.write_text('{"major": 1, "minor": 0, "patch": 316}\n', encoding="utf-8")
    changelog_file.write_text("# 変更履歴\n\n既存の履歴\n", encoding="utf-8")
    monkeypatch.setattr(release, "VERSION_FILE", version_file)
    monkeypatch.setattr(release, "CHANGELOG_FILE", changelog_file)

    version = release.update_release_metadata(
        subject="テスト用の修正", now=release.datetime.datetime(2026, 11, 1, tzinfo=release.JST)
    )

    assert version["patch"] == 317
    assert json.loads(version_file.read_text(encoding="utf-8"))["patch"] == 317
    assert "## [2026-11-01] v1.0.317" in changelog_file.read_text(encoding="utf-8")
    assert "- テスト用の修正" in changelog_file.read_text(encoding="utf-8")
