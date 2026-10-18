"""Synthetic MVP data.

Uso:
    python -m graph.seed                  # Base data only (user, agents, plants)
    python -m graph.seed --reset          # Delete the graph and recreate the base data
    python -m graph.seed --reset --demo 3 # Base data plus the full three-session scenario
    python -m graph.seed --reset --demo 2 # Stop at Session 02 with a task still pending
"""
import argparse

from agents.vocab import (AGENT_DESCRIPTIONS, AGENT_ORDER, CARE_AGENT, COORDINATOR_AGENT, OBSERVATION_AGENT)
from graph import db, queries
from services.utils import now_iso

USER_ID = "user_demo"

LOCATIONS = [
    ("loc_living_room", "Living room", "Indirect light"),
    ("loc_bedroom", "Bedroom", "Low light"),
    ("loc_near_window", "Near the window", "Bright indirect light"),
    ("loc_kitchen", "Kitchen", "Varies by spot"),
    ("loc_bathroom", "Bathroom", "Low to indirect light"),
    ("loc_home_office", "Home office", "Varies by spot"),
    ("loc_balcony", "Balcony", "Bright light"),
    ("loc_patio", "Patio", "Bright outdoor light"),
    ("loc_garden", "Garden", "Outdoor light"),
    ("loc_greenhouse", "Greenhouse", "Bright filtered light"),
]
PLANTS = [
    ("plant_monstera", "Monstera", "Monstera deliciosa", "monstera", "loc_living_room"),
    ("plant_snake_plant", "Snake Plant", "Sansevieria trifasciata", "snake", "loc_living_room"),
    ("plant_peace_lily", "Peace Lily", "Spathiphyllum", "peace_lily", "loc_living_room"),
]
PROCEDURES = [
    ("proc_observation", "observation_recorded", "handoff_to_coordinator",
     "New observation recorded → hand context to the Coordinator Agent"),
    ("proc_care", "care_recorded", "handoff_to_coordinator",
     "New care event recorded → hand context to the Coordinator Agent"),
    ("proc_task_done", "task_completed", "update_status_keep_history",
     "Task completed → update status and preserve history"),
    ("proc_session", "session_started", "retrieve_pending_tasks",
     "New session started → retrieve pending tasks and ask for new observations"),
]


def ensure_base(sample_plants: bool | None = None):
    """Ensure base data exists; sample plants are only added to the default garden."""
    if sample_plants is None:
        sample_plants = not db.current_tenant()
    queries.ensure_indexes()
    queries.upsert_user(USER_ID, "CapybaraBR")
    for agent_id in AGENT_ORDER:
        name, desc = AGENT_DESCRIPTIONS[agent_id]
        queries.upsert_agent(agent_id, name, agent_id.replace("_agent", ""), desc)
    for proc_id, trigger, action, desc in PROCEDURES:
        queries.upsert_procedure(proc_id, trigger, action, COORDINATOR_AGENT, desc)
    for loc_id, name, light in LOCATIONS:
        queries.upsert_location(loc_id, name, light)
    for pid, name, species, photo, loc_id in (PLANTS if sample_plants else []):
        if not queries.get_plant(pid):
            queries.create_plant(pid, name, species, now_iso(), photo, USER_ID)
            loc = next(l for l in LOCATIONS if l[0] == loc_id)
            queries.set_plant_location(pid, loc[0], loc[1], loc[2])


def seed_demo(upto: int = 3):
    """Run the primary and secondary scenarios through the agents."""
    from agents import care_agent, observation_agent
    from services import session_service

    ensure_base()
    s1 = session_service.start_session()
    care_agent.register_care("plant_monstera", s1["id"], "Watered", "Used approximately one cup of water")
    care_agent.register_care("plant_snake_plant", s1["id"], "Moved", "Moved to the bedroom", location="Bedroom", light="Low light")
    if upto < 2:
        return
    s2 = session_service.start_session()
    observation_agent.register_observation("plant_monstera", s2["id"], "Moist", "Normal", "Yes", "No",
                                           "Soil is still moist, no visible pests.")
    observation_agent.register_observation("plant_snake_plant", s2["id"], "Unknown", "Normal", "Unknown", "No",
                                           "Bedroom gets less light than the living room.")
    observation_agent.register_observation("plant_peace_lily", s2["id"], "Moist", "Some yellow", "No", "No",
                                           "Some yellow leaves were observed.")
    if upto < 3:
        return
    s3 = session_service.start_session()
    observation_agent.register_observation("plant_monstera", s3["id"], "Dry", "Normal", "Yes", "No",
                                           "Checked the soil, now it is dry.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="delete the graph first")
    parser.add_argument("--demo", type=int, choices=[1, 2, 3], help="load the scenario through session N")
    args = parser.parse_args()
    if args.reset:
        db.reset_graph()
    ensure_base()
    if args.demo:
        seed_demo(args.demo)
    print(f"Graph '{db.graph_name()}' ready.", "Demo loaded." if args.demo else "")
