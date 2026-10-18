"""Selects a tool and its arguments using an LLM when available, otherwise simple transparent rules."""
import re

from agents import llm
from graph.tools import MAX_DEPTH, TOOLS

IGNORE = {"rooted", "session", "coordinator", "observation", "care", "agent", "task", "monday", "i"}
ACTION_WORDS = {"fertiliz": "fertilized", "repot": "repotted", "moved": "moved", "rotat": "rotated",
                "clean": "cleaned_leaves", "water": "watered"}


def detect_plant(question: str, plants: list[str]) -> tuple[str | None, str | None]:
    """Return a known name and an unknown candidate. The graph is the source of truth."""
    low = question.lower()
    for name in sorted(plants, key=len, reverse=True):
        if re.search(rf"\b{re.escape(name.lower())}\b", low):
            return name, None
    for cand in re.findall(r"\b(?:the|my|about|for|of|on)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)", question):
        if cand.lower() not in IGNORE:
            return None, cand
    return None, None


def _by_rules(question: str) -> tuple[str, str]:
    q = question.lower()
    action = next((v for k, v in ACTION_WORDS.items() if k in q), "watered")
    if any(w in q for w in ("handoff", "hand off", "handed", "which agent", "who passed")):
        return "handoff_trail", action
    if any(w in q for w in ("change", "history", "previous", "superseded", "before", "used to", "earlier")):
        return "observation_history", action
    if any(w in q for w in ("why", "reason", "how come", "follow-up", "follow up")):
        return "why_follow_up", action
    if any(w in q for w in ("since", "after", "happened", "next")):
        return "what_happened_since", action
    return "recall", action


def choose(question: str, plants: list[str], plant_hint: str = "", depth: int = MAX_DEPTH) -> dict:
    known, unknown = detect_plant(question, plants)
    plant = known or unknown or plant_hint or ""
    if llm.available():
        picked = llm.choose_tool(question, TOOLS, plants)
        if picked:
            return {"tool": picked["tool"], "source": "llm",
                    "args": {"plant": known or picked.get("plant") or plant_hint or "",
                             "action": picked.get("action") or "watered",
                             "depth": picked.get("depth") or depth}}
    tool, action = _by_rules(question)
    return {"tool": tool, "source": "rules", "args": {"plant": plant, "action": action, "depth": depth}}
