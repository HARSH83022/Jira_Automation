import os

from app.api.reports import _delete_file_with_retry


def test_delete_file_retries_on_permission_error(monkeypatch, tmp_path):
    target = tmp_path / "report.xlsx"
    target.write_text("test")

    calls = {"count": 0}
    real_remove = os.remove

    def fake_remove(path):
        calls["count"] += 1
        if calls["count"] < 3:
            raise PermissionError("The report file is currently in use")
        real_remove(path)

    monkeypatch.setattr("app.api.reports.os.remove", fake_remove)

    _delete_file_with_retry(str(target))

    assert not target.exists()
    assert calls["count"] == 3
