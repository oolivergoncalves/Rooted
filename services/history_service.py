"""Build the History and Recent Activity timelines from the graph."""
from agents.vocab import CARE_PAST, describe_observation, to_label
from graph import queries


def build_events(plant_id: str = "") -> list[dict]:
    events = []
    for c in queries.list_care_events(plant_id):
        action = c.get("action_type", "other")
        text = f"{c['plant_name']} {CARE_PAST.get(action, 'care recorded')}"
        if action == "moved" and c.get("location"):
            text += f" to {c['location']}"
        events.append({
            "kind": "environment" if action == "moved" else "care",
            "ts": c["recorded_at"], "plant": c["plant_name"], "session_number": c["session_number"],
            "agent": c.get("agent_name", "Care Agent"), "text": text,
            "title": "Environment updated" if action == "moved" else "Care action registered",
            "detail": c.get("note") or to_label(action) + (f" · {c['location']}" if c.get("location") else ""),
        })
    for o in queries.list_observations(plant_id):
        events.append({
            "kind": "observation", "ts": o["recorded_at"], "plant": o["plant_name"],
            "session_number": o["session_number"], "agent": o.get("agent_name", "Observation Agent"),
            "text": f"{describe_observation(o)} observed", "title": "New observation recorded",
            "detail": o.get("note") or describe_observation(o),
        })
    for h in queries.list_handoffs(plant_id):
        events.append({
            "kind": "handoff", "ts": h["created_at"], "plant": h["plant_name"],
            "session_number": h["session_number"], "agent": h["source"],
            "text": f"{h['source']} handed context to {h['target']}", "title": "Handoff", "detail": h.get("reason", ""),
        })
    for s in queries.list_supersessions(plant_id):
        events.append({
            "kind": "superseded", "ts": s["ts"], "plant": s["plant_name"], "session_number": s["session_number"],
            "agent": "Coordinator Agent", "text": "Previous observation superseded",
            "title": "Observation superseded", "detail": "The newer observation is now the current one.",
        })
    for t in queries.list_tasks():
        if plant_id and t["plant_id"] != plant_id:
            continue
        events.append({
            "kind": "task_created", "ts": t["created_at"], "plant": t["plant_name"],
            "session_number": t["created_session"], "agent": "Coordinator Agent",
            "text": f"Task created: {t['title']}", "title": "Task created", "detail": t.get("reason", ""),
        })
        if t["status"] == "completed" and t.get("completed_at"):
            events.append({
                "kind": "task_completed", "ts": t["completed_at"], "plant": t["plant_name"],
                "session_number": t["completed_session"], "agent": "Coordinator Agent",
                "text": f"Task completed: {t['title']}", "title": "Task completed", "detail": t["title"],
            })
    events.sort(key=lambda e: e["ts"])
    return events


def recent(limit: int = 4) -> list[dict]:
    shown = [e for e in build_events() if e["kind"] not in ("handoff", "superseded")]
    return list(reversed(shown))[:limit]
