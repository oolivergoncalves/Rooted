"""Vocabulary shared by agents, services, and the interface."""

OBSERVATION_AGENT = "observation_agent"
CARE_AGENT = "care_agent"
COORDINATOR_AGENT = "coordinator_agent"

SOIL_OPTIONS = ["Wet", "Moist", "Dry", "Unknown"]
LEAF_OPTIONS = ["Normal", "Some yellow", "Fallen", "Unknown"]
YES_NO_UNKNOWN = ["Yes", "No", "Unknown"]
CARE_ACTIONS = ["Watered", "Fertilized", "Repotted", "Moved", "Rotated", "Cleaned leaves", "Other"]


def to_key(label: str) -> str:
    return str(label).strip().lower().replace(" ", "_")


def to_label(key: str) -> str:
    return str(key).replace("_", " ").capitalize()


SOIL_KEYS = {to_key(x) for x in SOIL_OPTIONS}
LEAF_KEYS = {to_key(x) for x in LEAF_OPTIONS}
YNU_KEYS = {to_key(x) for x in YES_NO_UNKNOWN}
CARE_KEYS = {to_key(x) for x in CARE_ACTIONS}

CARE_NOUN = {
    "watered": "Watering", "fertilized": "Fertilizing", "repotted": "Repotting",
    "moved": "Moving", "rotated": "Rotating", "cleaned_leaves": "Leaf cleaning", "other": "Care",
}
CARE_PAST = {
    "watered": "watered", "fertilized": "fertilized", "repotted": "repotted",
    "moved": "moved", "rotated": "rotated", "cleaned_leaves": "leaves cleaned", "other": "care recorded",
}

AGENT_DESCRIPTIONS = {
    OBSERVATION_AGENT: ("Observation Agent", "Records plant conditions and changes."),
    CARE_AGENT: ("Care Agent", "Registers care actions (watering, etc.)."),
    COORDINATOR_AGENT: ("Coordinator Agent", "Connects memories and creates tasks."),
}
AGENT_ORDER = [OBSERVATION_AGENT, CARE_AGENT, COORDINATOR_AGENT]


def describe_observation(obs: dict) -> str:
    """Return a concise, neutral summary of the user's observation, without diagnosis."""
    parts = []
    soil = obs.get("soil_status", "unknown")
    if soil != "unknown":
        parts.append(f"{soil} soil")
    leaf = obs.get("leaf_status", "unknown")
    if leaf == "some_yellow":
        parts.append("some yellow leaves")
    elif leaf == "fallen":
        parts.append("fallen leaves")
    elif leaf == "normal" and not parts:
        parts.append("normal leaves")
    if obs.get("new_growth") == "yes":
        parts.append("new growth")
    if obs.get("pests_visible") == "yes":
        parts.append("visible pests")
    return ", ".join(parts).capitalize() if parts else "Observation"
