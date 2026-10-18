"""Graph reasoning used by the Coordinator Agent.

Flow: router selects a tool → arguments are validated against the graph → memory (Finding) →
parameterized traversal → answer with path and trace → sentence verification → save Finding.

Every result has one of four outcomes:
  answered_with_path  | answered_from_memory | not_in_graph | unknown_entity
"""
import json
import re
import time

from agents import llm, router
from agents.vocab import COORDINATOR_AGENT
from graph import queries, tools
from services.utils import new_id, now_iso

OUTCOMES = {
    "answered_with_path": ("Answered with a path", "green"),
    "answered_from_memory": ("Answered from memory", "blue"),
    "not_in_graph": ("Not in the graph", "amber"),
    "unknown_entity": ("Unknown plant", "red"),
}
NEGATIONS = re.compile(r"\b(no|not|nothing|none|unknown|isn't|hasn't|haven't|without)\b", re.I)


def accepts(sentence: str, answer: dict, plants: list[str]) -> tuple[bool, str]:
    """Every plant or session named in the sentence must have come from the graph result."""
    allowed = {e.lower() for e in answer["entities"]}
    for name in plants:
        if re.search(rf"\b{re.escape(name)}\b", sentence, re.I) and name.lower() not in allowed:
            return False, f"named plants not in the result: {name}"
    extra = {int(n) for n in re.findall(r"[Ss]ession\s+0*(\d+)", sentence)} - set(answer["sessions"])
    if extra:
        return False, f"mentioned sessions not in the result: {sorted(extra)}"
    if answer["outcome"] in ("not_in_graph", "unknown_entity") and not NEGATIONS.search(sentence):
        return False, "claimed an answer when the graph had none"
    return True, "ok"


def _answer(base: dict, outcome: str, sentence: str, **extra) -> dict:
    return {**base, "outcome": outcome, "label": OUTCOMES[outcome][0], "tone": OUTCOMES[outcome][1],
            "sentence": sentence, **extra}


def ask(question: str, session_id: str, plant_hint: str = "", depth: int = tools.MAX_DEPTH) -> dict:
    question = (question or "").strip()
    plants = [p["name"] for p in queries.list_plants()]
    route = router.choose(question, plants, plant_hint, depth)
    base = {"question": question, "tool": route["tool"], "route_source": route["source"], "trace": [],
            "paths": [], "facts": [], "entities": [], "sessions": [], "learned_at": "", "learned_session": None,
            "sentence_source": "graph", "check": "ok"}

    # 1) Validate against the graph: an unknown name prevents reasoning queries from running.
    try:
        clean = tools.validate(route["tool"], route["args"])
    except tools.UnknownEntity as e:
        who = f"“{e.name}” is not a plant in the graph" if e.name else "No plant was named"
        return _answer(base, "unknown_entity", f"{who}, so no query was run.")
    except tools.ToolError as e:
        return _answer(base, "not_in_graph", f"The request could not be validated: {e}. No query was run.")

    plant, spec, key = clean["plant"], tools.TOOLS[route["tool"]], tools.cache_key(route["tool"], clean)
    cacheable = spec["kind"] == "traversal"

    # 2) Check memory first: a Finding is valid only if no newer plant activity exists.
    if cacheable:
        finding = queries.latest_finding(plant["id"], key)
        if finding and finding["at"] > queries.latest_activity(plant["id"]):
            payload = json.loads(finding["payload"])
            return _answer({**base, **payload}, "answered_from_memory", finding["text"],
                           learned_at=finding["at"], learned_session=finding.get("session_number"))

    # 3) Run and time a parameterized traversal.
    started = time.perf_counter()
    result = spec["fn"](**clean)
    shown_args = {k: (v["name"] if k == "plant" else v) for k, v in clean.items()}
    trace = [{"tool": route["tool"], "args": shown_args,
              "ms": round((time.perf_counter() - started) * 1000, 1), "rows": result["rows"]}]
    payload = {k: result[k] for k in ("paths", "facts", "entities", "sessions")}
    base = {**base, **payload, "trace": trace}

    if result["rows"] == 0:
        return _answer(base, "not_in_graph", result["summary"])
    outcome = "answered_from_memory" if spec["kind"] == "memory" else "answered_with_path"
    answer = _answer(base, outcome, result["summary"])

    # 4) The optional LLM only drafts the sentence; verify it against the result.
    if llm.available():
        candidate = llm.phrase(question, payload)
        if candidate:
            ok, why = accepts(candidate, answer, plants)
            if ok:
                answer.update(sentence=candidate, sentence_source="llm")
            else:
                answer["check"] = f"LLM sentence rejected ({why}); using the sentence built from the rows"

    # 5) Memory is stored as graph nodes: save what was established.
    if cacheable:
        queries.create_finding(new_id("finding"), plant["id"], COORDINATOR_AGENT, session_id, key,
                               answer["sentence"], json.dumps(payload), now_iso())
    return answer
