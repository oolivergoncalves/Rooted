"""Care Agent: records completed care actions and hands context to the Coordinator."""
from datetime import date, datetime

from agents import coordinator_agent
from agents.vocab import CARE_AGENT, CARE_KEYS, to_key, to_label
from graph import queries
from services import handoff_service
from services.utils import new_id, now_iso, slugify


def register_care(plant_id: str, session_id: str, action: str, note: str = "",
                  performed_on: date | None = None, location: str = "", light: str = "") -> dict:
    key = to_key(action)
    if key not in CARE_KEYS:
        raise ValueError(f"Invalid care action: {action!r}")

    now = datetime.now()
    if performed_on is None or performed_on == now.date():
        performed_at = now.isoformat(timespec="microseconds")
    else:  # For a past date, use noon.
        performed_at = datetime.combine(performed_on, datetime.min.time()).replace(hour=12).isoformat()

    care_id = new_id("care")
    location = (location or "").strip() if key == "moved" else ""
    queries.create_care_event(care_id, plant_id, CARE_AGENT, session_id, key, (note or "").strip(),
                              performed_at, now_iso(), location)

    if location:  # Semantic memory: the plant's current location.
        queries.set_plant_location(plant_id, f"loc_{slugify(location)}", location, (light or "").strip())

    handoff = handoff_service.create_handoff(
        CARE_AGENT, "care_recorded", plant_id, session_id,
        f"New care event recorded: {to_label(key)}",
    )
    result = coordinator_agent.evaluate_context(plant_id, session_id, "care", care_id, handoff["id"])
    return {"care_id": care_id, "handoff": handoff, "coordinator": result}
