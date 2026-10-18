from agents import care_agent
from graph import queries
from services import session_service

MONSTERA = "plant_monstera"


def test_register_watering_creates_event_and_handoff():
    s1 = session_service.start_session()
    out = care_agent.register_care(MONSTERA, s1["id"], "Watered", "one cup")
    care = queries.latest_care(MONSTERA)
    assert care["action_type"] == "watered" and care["session_number"] == 1
    handoffs = queries.list_handoffs(MONSTERA)
    assert handoffs[-1]["source_id"] == "care_agent" and handoffs[-1]["target_id"] == "coordinator_agent"
    assert handoffs[-1]["status"] == "completed"
    assert out["coordinator"]["outcome"] == "Awaiting a later observation"
    assert queries.pending_tasks(MONSTERA) == []


def test_moved_updates_location_and_creates_followup():
    s1 = session_service.start_session()
    care_agent.register_care("plant_snake_plant", s1["id"], "Moved", location="Bedroom", light="Low light")
    assert queries.get_plant_location("plant_snake_plant")["name"] == "Bedroom"
    tasks = queries.pending_tasks("plant_snake_plant")
    assert [t["task_type"] for t in tasks] == ["location_followup"]


def test_invalid_action_is_rejected():
    s1 = session_service.start_session()
    try:
        care_agent.register_care(MONSTERA, s1["id"], "Sang to it")
        assert False, "should have raised"
    except ValueError:
        pass
