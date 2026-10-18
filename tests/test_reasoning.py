"""Graph reasoning agent: four outcomes, paths, traversal depth, and memory."""
import pytest

from agents import care_agent, coordinator_agent, observation_agent, router
from agents.graph_reasoner import accepts
from graph import queries
from services import session_service

M = "plant_monstera"


def _scenario_to_session(n):
    s = session_service.start_session()
    care_agent.register_care(M, s["id"], "Watered")
    if n >= 2:
        s = session_service.start_session()
        observation_agent.register_observation(M, s["id"], soil_status="Moist")
    if n >= 3:
        s = session_service.start_session()
        observation_agent.register_observation(M, s["id"], soil_status="Dry")
    return s


# ── Without a database ──
@pytest.mark.nodb
def test_sentence_check_rejects_invented_plant_and_session():
    answer = {"outcome": "answered_with_path", "entities": ["Monstera"], "sessions": [1, 2]}
    assert accepts("Monstera was watered in Session 01.", answer, ["Monstera", "Ficus"])[0]
    assert not accepts("Ficus needs water.", answer, ["Monstera", "Ficus"])[0]
    assert not accepts("Monstera changed in Session 07.", answer, ["Monstera"])[0]
    empty = {"outcome": "not_in_graph", "entities": ["Monstera"], "sessions": []}
    assert not accepts("Monstera is fine.", empty, ["Monstera"])[0]
    assert accepts("Nothing is recorded for Monstera.", empty, ["Monstera"])[0]


@pytest.mark.nodb
def test_router_detects_known_and_unknown_plants_and_tools():
    plants = ["Monstera", "Snake Plant"]
    assert router.detect_plant("Why is the Monstera task here?", plants) == ("Monstera", None)
    assert router.detect_plant("What about the Ficus?", plants) == (None, "Ficus")
    assert router._by_rules("Why was the task created?")[0] == "why_follow_up"
    assert router._by_rules("What happened since I watered it?")[0] == "what_happened_since"


# ── With a database ──
def test_unknown_plant_runs_no_tool():
    s = session_service.start_session()
    ans = coordinator_agent.answer_question("Why is the Ficus task pending?", s["id"])
    assert ans["outcome"] == "unknown_entity" and ans["trace"] == []


def test_why_follow_up_returns_the_path():
    _scenario_to_session(2)
    s = queries.get_last_session()
    ans = coordinator_agent.answer_question("Why was the Monstera task created?", s["id"])
    assert ans["outcome"] == "answered_with_path"
    assert any("Check Monstera soil" in p and "Watering" in p for p in ans["paths"])
    assert set(ans["sessions"]) == {1, 2}
    assert ans["trace"][0]["tool"] == "why_follow_up" and ans["trace"][0]["rows"] == 2


def test_empty_traversal_is_not_in_graph_not_safe():
    s = session_service.start_session()
    ans = coordinator_agent.answer_question("Why is there a task for the Snake Plant?", s["id"])
    assert ans["outcome"] == "not_in_graph" and "may mean" in ans["sentence"]


def test_depth_changes_the_answer():
    s = _scenario_to_session(3)
    shallow = coordinator_agent.answer_question("What happened to the Monstera since it was watered?", s["id"], depth=1)
    deep = coordinator_agent.answer_question("What happened to the Monstera since it was watered?", s["id"], depth=2)
    assert len(shallow["paths"]) == 1 and len(deep["paths"]) == 2


def test_memory_is_reused_until_something_new_happens():
    s = _scenario_to_session(2)
    q = "Why was the Monstera task created?"
    assert coordinator_agent.answer_question(q, s["id"])["outcome"] == "answered_with_path"
    again = coordinator_agent.answer_question(q, s["id"])
    assert again["outcome"] == "answered_from_memory" and again["learned_at"] and again["trace"] == []
    observation_agent.register_observation(M, s["id"], soil_status="Wet")
    assert coordinator_agent.answer_question(q, s["id"])["outcome"] == "answered_with_path"


def test_observation_history_follows_supersedes_chain():
    s = _scenario_to_session(3)
    ans = coordinator_agent.answer_question("How did the Monstera observations change?", s["id"])
    assert ans["outcome"] == "answered_with_path" and len(ans["paths"][0]) == 2
    assert "Dry soil" in ans["paths"][0][0] and "Moist soil" in ans["paths"][0][1]
