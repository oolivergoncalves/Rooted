import pytest

from agents import observation_agent
from graph import queries
from services import session_service

PEACE_LILY = "plant_peace_lily"


def test_register_observation_is_structured_and_current():
    s1 = session_service.start_session()
    observation_agent.register_observation(PEACE_LILY, s1["id"], "Moist", "Normal", "Yes", "No", "New leaf")
    obs = queries.current_observation(PEACE_LILY)
    assert obs["soil_status"] == "moist" and obs["leaf_status"] == "normal"
    assert obs["new_growth"] == "yes" and obs["is_current"] is True
    assert obs["session_number"] == 1


def test_yellow_leaves_create_inspection_task_and_flag_plant():
    s1 = session_service.start_session()
    observation_agent.register_observation(PEACE_LILY, s1["id"], leaf_status="Some yellow")
    assert [t["task_type"] for t in queries.pending_tasks(PEACE_LILY)] == ["leaf_inspection"]
    assert queries.get_plant(PEACE_LILY)["status"] == "needs_attention"


def test_invalid_values_are_rejected():
    s1 = session_service.start_session()
    with pytest.raises(ValueError):
        observation_agent.register_observation(PEACE_LILY, s1["id"], soil_status="Soggy")
