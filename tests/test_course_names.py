from modules import models


def test_blank_course_name_is_not_queried_or_created(monkeypatch):
    class UnexpectedClient:
        def table(self, _name):
            raise AssertionError("空白のコース名でDBへ問い合わせてはいけません")

    monkeypatch.setattr(models, "supabase", UnexpectedClient())

    assert models.get_course_by_name("   ") is None
    assert models.create_course("\t") is None
