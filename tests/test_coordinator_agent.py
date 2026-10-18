"""End-to-end version of the primary PDF scenario across three sessions."""
from agents import care_agent, observation_agent
from graph import queries
from services import session_service, task_service

M = "plant_monstera"


def test_main_scenario_three_sessions():
    # Session 1: care is recorded.
    s1 = session_service.start_session()
    care_agent.register_care(M, s1["id"], "Watered")
    assert queries.pending_tasks(M) == []

    # Session 2: a later observation creates a persistent task with evidence.
    s2 = session_service.start_session()
    observation_agent.register_observation(M, s2["id"], soil_status="Moist")
    pending = queries.pending_tasks(M)
    assert len(pending) == 1 and pending[0]["task_type"] == "soil_check"
    assert pending[0]["created_session"] == 2
    evidence = queries.task_evidence(pending[0]["id"])
    assert {e["kind"] for e in evidence} == {"care", "observation"}
    explanation = task_service.explain_task(pending[0]["id"])
    assert "Watering was recorded in Session 01." in explanation["lines"]
    assert "Moist soil was observed afterward in Session 02." in explanation["lines"]

    # Session 3: the task remains pending and the Coordinator notifies the Observation Agent.
    s3 = session_service.start_session()
    assert len(queries.pending_tasks(M)) == 1
    resume = [h for h in queries.list_handoffs(M) if h["source_id"] == "coordinator_agent"]
    assert resume and resume[-1]["target_id"] == "observation_agent"

    # A new observation supersedes the previous one and completes the task.
    observation_agent.register_observation(M, s3["id"], soil_status="Dry")
    assert queries.pending_tasks(M) == []
    done = queries.list_tasks("completed")
    assert len(done) == 1 and done[0]["completed_session"] == 3
    assert queries.current_observation(M)["soil_status"] == "dry"
    assert len(queries.list_supersessions(M)) == 1
    assert len(queries.list_observations(M)) == 2  # No observations were deleted.
    assert len(queries.list_sessions()) == 3


def test_no_duplicate_pending_tasks():
    s1 = session_service.start_session()
    care_agent.register_care(M, s1["id"], "Watered")
    observation_agent.register_observation(M, s1["id"], soil_status="Moist")
    observation_agent.register_observation(M, s1["id"], soil_status="Wet")
    assert len([t for t in queries.pending_tasks(M) if t["task_type"] == "soil_check"]) == 1


def test_dry_soil_after_watering_creates_no_task():
    s1 = session_service.start_session()
    care_agent.register_care(M, s1["id"], "Watered")
    observation_agent.register_observation(M, s1["id"], soil_status="Dry")
    assert queries.pending_tasks(M) == []


def test_sessions_are_chained():
    session_service.start_session()
    session_service.start_session()
    rows = queries.list_sessions()
    assert [s["number"] for s in rows] == [1, 2] and rows[0]["status"] == "ended"
