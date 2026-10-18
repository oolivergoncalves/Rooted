"""Sessions: one session represents a visit to the app.

Rules:
 - F5 / switching gardens     -> continue the same session
 - "Start New Session" button -> start a new session
 - closing and reopening app  -> start a new session (RUN_ID changes at each server start)
"""
import os
import uuid

from graph import queries
from services.utils import now_iso

RUN_ID = uuid.uuid4().hex  # Identifies this app server run.
IDLE_MINUTES = int(os.getenv("ROOTED_IDLE_MINUTES", "1440"))  # Start a new visit after 24 hours of inactivity.


def start_session() -> dict:
    last = queries.get_last_session()
    now = now_iso()
    if last and last.get("status") == "active":
        queries.end_session(last["id"], now)
    number = (last["number"] if last else 0) + 1
    session_id = f"session_{number:02d}"
    queries.create_session(session_id, number, now, RUN_ID)
    if last:
        queries.link_sessions(last["id"], session_id)

    # Handoff for a new session: the Coordinator retrieves pending tasks.
    from agents import coordinator_agent  # Delayed import avoids a circular dependency.

    coordinator_agent.resume_session(session_id)
    return {"id": session_id, "number": number, "started_at": now}


def current_or_new_session() -> dict:
    """Reuse this app run's active session, or start a new one."""
    last = queries.get_last_session()
    if last and last.get("status") == "active" and last.get("run_id") == RUN_ID:
        return {"id": last["id"], "number": last["number"], "started_at": last["started_at"]}
    return start_session()
