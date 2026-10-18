"""Task creation, deduplication, completion, and explanation."""
from agents.vocab import CARE_NOUN, COORDINATOR_AGENT, describe_observation
from graph import queries
from services.utils import new_id, now_iso, session_label

TASK_TYPES = {
    "soil_check": {"title": "Check {plant} soil", "short": "Check soil again", "icon": "💧"},
    "leaf_inspection": {"title": "Inspect {plant} leaves", "short": "Inspect leaves", "icon": "🍃"},
    "location_followup": {"title": "Observe {plant} after moving", "short": "Check new spot", "icon": "📍"},
}


def short_label(task_type: str) -> str:
    return TASK_TYPES.get(task_type, {}).get("short", "Follow up")


def create_or_update_task(plant: dict, session_id: str, task_type: str, reason: str, evidence: list[tuple[str, str]]):
    """Rule 2: update an existing pending task of the same type instead of duplicating it."""
    now = now_iso()
    title = TASK_TYPES[task_type]["title"].format(plant=plant["name"])
    existing = queries.find_pending_task(plant["id"], task_type)
    if existing:
        task_id, created = existing["id"], False
        queries.update_task(task_id, reason, now)
        title = existing.get("title", title)
    else:
        task_id, created = new_id("task"), True
        queries.create_task(task_id, plant["id"], COORDINATOR_AGENT, session_id, task_type, title, reason, now)
    for label, evidence_id in evidence:
        queries.add_evidence(task_id, label, evidence_id)
    return {"id": task_id, "title": title, "created": created}


def complete_task(task_id: str, session_id: str, observation_id: str = ""):
    """Mark a task complete and record the completion session while preserving history."""
    queries.complete_task(task_id, session_id, now_iso(), observation_id)


def explain_task(task_id: str):
    """Answer 'Why was this follow-up created?' using evidence from the graph."""
    base = queries.explain_task(task_id)
    if not base:
        return None
    evidence = queries.task_evidence(task_id)
    evidence.sort(key=lambda e: e["data"].get("recorded_at", ""))
    lines, has_care = [], False
    for ev in evidence:
        where = session_label(ev["session_number"])
        if ev["kind"] == "care":
            noun = CARE_NOUN.get(ev["data"].get("action_type", "other"), "Care")
            lines.append(f"{noun} was recorded in {where}.")
            has_care = True
        else:
            what = describe_observation(ev["data"])
            lines.append(f"{what} was observed {'afterward ' if has_care else ''}in {where}.")
    lines.append(f"The {base['agent']['name']} created a follow-up task.")
    return {**base, "evidence": evidence, "lines": lines}
