"""Coordinator Agent: connects care events, observations, tasks, and sessions.

It evaluates only the history recorded in the graph; it does not decide how to care for a plant.
Rules are transparent and describe Rooted's workflow, not botanical recommendations:

  Rule 1  observation after care       -> create or update a follow-up task
  Rule 2  avoid duplicate tasks         -> update the pending task of the same type
  Rule 3  new observation updates context -> current observation + SUPERSEDES
  Rule 4  follow-up completed           -> complete the task and record the session
  Extra   yellow or fallen leaves       -> create an inspection task (Home layout)
  Extra   plant moved                   -> create a location follow-up task
"""
from agents.vocab import (CARE_AGENT, COORDINATOR_AGENT, OBSERVATION_AGENT, describe_observation)
from graph import queries
from services import handoff_service, task_service
from services.utils import now_iso

MOIST = {"moist", "wet"}
LEAF_ISSUES = {"some_yellow", "fallen"}


def _answers(task: dict, obs: dict, evidence_ids: list[str]) -> bool:
    """Rule 4: does the new observation answer the pending task?"""
    if obs["id"] in evidence_ids:
        return False
    if task["task_type"] == "soil_check":
        return obs.get("soil_status", "unknown") != "unknown"
    if task["task_type"] == "leaf_inspection":
        return obs.get("leaf_status", "unknown") != "unknown"
    return False  # location_followup is completed manually


def _record(result: dict, task: dict):
    if task["created"]:
        result["created"].append(task["title"])
        result["actions"].append(f"Created task: {task['title']}")
    else:
        result["updated"].append(task["title"])
        result["actions"].append(f"Updated existing task: {task['title']}")


def evaluate_context(plant_id: str, session_id: str, trigger: str, subject_id: str = "",
                     handoff_id: str | None = None) -> dict:
    plant = queries.get_plant(plant_id)
    result = {"actions": [], "created": [], "updated": [], "completed": [], "outcome": ""}
    new_obs = queries.get_observation(subject_id) if trigger == "observation" else None
    new_care = queries.get_care_event(subject_id) if trigger == "care" else None

    if new_obs:
        # Rule 3: make the new observation current and preserve the previous one.
        previous = queries.previous_current_observation(plant_id, new_obs["id"])
        if previous:
            queries.supersede(new_obs["id"], previous["id"], now_iso())
            result["actions"].append(
                f"New observation is now current; {describe_observation(previous).lower()} was superseded")
        # Rule 4: does the observation answer a pending task?
        for task in queries.pending_tasks(plant_id):
            if _answers(task, new_obs, queries.task_evidence_ids(task["id"])):
                task_service.complete_task(task["id"], session_id, new_obs["id"])
                result["completed"].append(task["title"])
                result["actions"].append(f"Completed task: {task['title']}")

    # A moved plant gets a location follow-up.
    if new_care and new_care["action_type"] == "moved":
        _record(result, task_service.create_or_update_task(
            plant, session_id, "location_followup",
            "The plant was moved. A later observation will show how it is doing in the new spot.",
            [("CareEvent", new_care["id"])]))

    # Rule 1 (Rule 2 is handled by task_service).
    if new_obs or (new_care and new_care["action_type"] == "watered"):
        watering = queries.latest_care(plant_id, "watered")
        current = queries.current_observation(plant_id)
        if (watering and current and current["recorded_at"] > watering["performed_at"]
                and current.get("soil_status") in MOIST):
            _record(result, task_service.create_or_update_task(
                plant, session_id, "soil_check",
                f"A {current['soil_status']}-soil observation was recorded after watering.",
                [("CareEvent", watering["id"]), ("Observation", current["id"])]))

    if new_obs and new_obs.get("leaf_status") in LEAF_ISSUES:
        what = "Yellow leaves were" if new_obs["leaf_status"] == "some_yellow" else "Fallen leaves were"
        _record(result, task_service.create_or_update_task(
            plant, session_id, "leaf_inspection", f"{what} observed.", [("Observation", new_obs["id"])]))

    _refresh_plant_status(plant_id)

    if result["actions"]:
        result["outcome"] = "; ".join(result["actions"])
    elif trigger == "care" and new_care and new_care["action_type"] == "watered":
        result["outcome"] = "Awaiting a later observation"
    elif trigger == "care":
        result["outcome"] = "Care recorded; no follow-up needed"
    else:
        result["outcome"] = "Context updated; no follow-up needed"

    if handoff_id:
        handoff_service.complete_handoff(handoff_id, result["outcome"])
    return result


def _refresh_plant_status(plant_id: str):
    """Set the status label using only user-provided information; do not diagnose."""
    obs = queries.current_observation(plant_id)
    needs = bool(obs) and (obs.get("leaf_status") in LEAF_ISSUES or obs.get("pests_visible") == "yes")
    queries.set_plant_status(plant_id, "needs_attention" if needs else "healthy")


def resume_session(session_id: str) -> list[dict]:
    """Hand off pending tasks to a new session and request updated information."""
    handoffs, seen = [], set()
    for task in queries.pending_tasks():
        if task["plant_id"] in seen:
            continue
        seen.add(task["plant_id"])
        handoffs.append(handoff_service.create_handoff(
            COORDINATOR_AGENT, "session_started", task["plant_id"], session_id,
            f"Pending task retrieved: {task['title']}", target_id=OBSERVATION_AGENT))
    return handoffs


def answer_question(question: str, session_id: str, plant_hint: str = "", depth: int = 4) -> dict:
    """Answer by traversing the graph with the fixed tool catalog; the model does not write Cypher."""
    from agents import graph_reasoner  # Delayed import.

    return graph_reasoner.ask(question, session_id, plant_hint, depth)
