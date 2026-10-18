from graph import queries
from services import session_service


def test_reload_reuses_session_but_restart_creates_a_new_one(monkeypatch):
    first = session_service.current_or_new_session()
    assert session_service.current_or_new_session()["id"] == first["id"]  # F5
    assert len(queries.list_sessions()) == 1

    monkeypatch.setattr(session_service, "RUN_ID", "another-run")  # Simulate closing and reopening the app.
    second = session_service.current_or_new_session()
    assert second["number"] == 2 and len(queries.list_sessions()) == 2
