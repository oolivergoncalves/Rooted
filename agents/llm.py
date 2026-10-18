"""Optional LLM: selects a tool and drafts a sentence. Core logic does not depend on it.

Enable it with ANTHROPIC_API_KEY (and `pip install anthropic`). Any failure returns None, and the
system falls back to rule-based routing and a sentence built from graph rows.
"""
import json
import os

from dotenv import load_dotenv

load_dotenv()
MODEL = os.getenv("ROOTED_LLM_MODEL", "claude-sonnet-5-5")


def available() -> bool:
    return bool(os.getenv("ANTHROPIC_API_KEY"))


def _ask(system: str, user: str, max_tokens: int = 300) -> str | None:
    try:
        import anthropic

        msg = anthropic.Anthropic().messages.create(
            model=MODEL, max_tokens=max_tokens, system=system, messages=[{"role": "user", "content": user}])
        return msg.content[0].text.strip()
    except Exception:
        return None


def choose_tool(question: str, tools: dict, plants: list[str]) -> dict | None:
    """The model only selects a tool and its arguments. It never writes Cypher."""
    catalogue = {name: {"args": s["args"], "about": s["doc"]} for name, s in tools.items()}
    system = ("You route a question about plant-care memory to exactly ONE tool. Reply with JSON only, no prose: "
              '{"tool": <tool name>, "plant": <plant name as the user wrote it>, "action": <care action or null>, '
              '"depth": <1-4>}. You never write queries.')
    text = _ask(system, json.dumps({"question": question, "plants": plants, "tools": catalogue}))
    if not text:
        return None
    try:
        data = json.loads(text.strip("`").removeprefix("json").strip())
        return data if isinstance(data, dict) and data.get("tool") in tools else None
    except (ValueError, TypeError):
        return None


def phrase(question: str, payload: dict) -> str | None:
    system = ("Answer in ONE short sentence using ONLY the JSON facts. Never mention a plant, task or session "
              "that is not in the JSON. If there are no paths or facts, say the graph has no answer.")
    return _ask(system, json.dumps({"question": question, **payload}), max_tokens=150)
