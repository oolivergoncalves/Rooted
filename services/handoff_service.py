"""Handoffs transfer context between agents (Agent -> Handoff -> Agent)."""
from agents.vocab import COORDINATOR_AGENT
from graph import queries
from services.utils import new_id, now_iso


def create_handoff(source_id, trigger, plant_id, session_id, reason, target_id=None):
    """Resolve the target from procedural memory (a Procedure node); defaults to the Coordinator."""
    target = target_id or queries.procedure_target(trigger) or COORDINATOR_AGENT
    handoff_id = new_id("handoff")
    queries.create_handoff(handoff_id, source_id, target, plant_id, session_id, reason, now_iso())
    return {"id": handoff_id, "source": source_id, "target": target, "reason": reason}


def complete_handoff(handoff_id, outcome):
    queries.complete_handoff(handoff_id, outcome, now_iso())


def close_open_handoffs(plant_id, target_id, outcome):
    queries.complete_open_handoffs(plant_id, target_id, outcome, now_iso())
