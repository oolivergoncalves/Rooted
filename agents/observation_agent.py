"""Observation Agent: turns user observations into structured memory.

It does not diagnose diseases, identify species, or evaluate photos;
it only records and provides context for human observations.
"""
from agents import coordinator_agent
from agents.vocab import (LEAF_KEYS, OBSERVATION_AGENT, SOIL_KEYS, YNU_KEYS, COORDINATOR_AGENT,
                          describe_observation, to_key)
from graph import queries
from services import handoff_service
from services.utils import new_id, now_iso


def _check(value: str, allowed: set, field: str) -> str:
    key = to_key(value or "unknown")
    if key not in allowed:
        raise ValueError(f"Invalid {field}: {value!r}")
    return key


def register_observation(plant_id: str, session_id: str, soil_status: str = "unknown",
                         leaf_status: str = "unknown", new_growth: str = "unknown",
                         pests_visible: str = "unknown", note: str = "") -> dict:
    soil = _check(soil_status, SOIL_KEYS, "soil condition")
    leaf = _check(leaf_status, LEAF_KEYS, "leaves")
    growth = _check(new_growth, YNU_KEYS, "new growth")
    pests = _check(pests_visible, YNU_KEYS, "visible pests")

    obs_id = new_id("obs")
    queries.create_observation(obs_id, plant_id, OBSERVATION_AGENT, session_id, soil, leaf, growth,
                               pests, (note or "").strip(), now_iso())

    # Resolve any information request handed off by the Coordinator when the session resumed.
    handoff_service.close_open_handoffs(plant_id, OBSERVATION_AGENT, "New observation supplied.")

    obs = queries.get_observation(obs_id)
    handoff = handoff_service.create_handoff(
        OBSERVATION_AGENT, "observation_recorded", plant_id, session_id,
        f"New observation recorded: {describe_observation(obs).lower()}",
    )
    result = coordinator_agent.evaluate_context(plant_id, session_id, "observation", obs_id, handoff["id"])
    return {"observation_id": obs_id, "handoff": handoff, "coordinator": result}
