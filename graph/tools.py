"""Fixed catalog of graph reasoning tools.

Approach described in "How to Build an Agent That Reasons Over a Graph":
  1. The agent (or LLM) never writes Cypher; it selects a tool and supplies typed arguments.
  2. Queries are parameterized. Model text is never concatenated into them.
     Depth is a validated integer capped at MAX_DEPTH, so it can be used in `*1..N`.
  3. Names are resolved against the graph before any traversal.
  4. Each tool returns the traversed path (`nodes(path)`), not only the result.
"""
from agents.vocab import CARE_KEYS, CARE_NOUN, describe_observation, to_key, to_label
from graph import queries
from graph.db import run
from services.utils import fmt_short, session_label

MAX_DEPTH = 4


class UnknownEntity(Exception):
    def __init__(self, name):
        super().__init__(str(name))
        self.name = name


class ToolError(Exception):
    pass


# ───────────────────────────── Cypher for each tool ─────────────────────────────
WHY_CARE = """
MATCH path = (ag:Agent)-[:CREATED]->(t:Task {status:'pending'})-[:BASED_ON]->(e:CareEvent)-[:OCCURRED_IN]->(s:Session)
MATCH (t)-[:ABOUT]->(:Plant {id:$pid})
RETURN nodes(path) AS chain, t.created_at AS at ORDER BY at
"""
WHY_OBS = """
MATCH path = (ag:Agent)-[:CREATED]->(t:Task {status:'pending'})-[:BASED_ON]->(e:Observation)-[:RECORDED_IN]->(s:Session)
MATCH (t)-[:ABOUT]->(:Plant {id:$pid})
RETURN nodes(path) AS chain, t.created_at AS at ORDER BY at
"""
SINCE = """
MATCH (c:CareEvent {id:$care_id})-[:OCCURRED_IN]->(s1:Session)
MATCH (:Plant {id:$pid})-[:HAS_OBSERVATION]->(o:Observation)-[:RECORDED_IN]->(s2:Session)
WHERE o.recorded_at > c.performed_at
OPTIONAL MATCH trail = (s1)-[:FOLLOWED_BY*1..__N__]->(s2)
RETURN c, o, s1.number AS from_session, s2.number AS to_session, nodes(trail) AS hops, o.recorded_at AS at
ORDER BY at
"""
HISTORY = """
MATCH (:Plant {id:$pid})-[:HAS_OBSERVATION]->(cur:Observation {is_current:true})
MATCH path = (cur)-[:SUPERSEDES*1..__N__]->(old:Observation)
RETURN nodes(path) AS chain
"""
HANDOFFS = """
MATCH path = (a:Agent)-[:INITIATED]->(h:Handoff)-[:TARGETS]->(b:Agent)
MATCH (h)-[:ABOUT]->(:Plant {id:$pid})
OPTIONAL MATCH (h)-[:OCCURRED_IN]->(s:Session)
RETURN nodes(path) AS chain, h.outcome AS outcome, s.number AS session_number, h.created_at AS at
ORDER BY at
"""


def node_label(n: dict) -> str:
    kinds = n.get("_labels", [])
    kind = kinds[0] if kinds else ""
    if kind in ("Agent", "Plant"):
        return n["name"]
    if kind == "Task":
        return n["title"]
    if kind == "Session":
        return session_label(n["number"])
    if kind == "CareEvent":
        return CARE_NOUN.get(n.get("action_type", "other"), "Care")
    if kind == "Observation":
        return describe_observation(n)
    if kind == "Handoff":
        return n.get("reason", "Handoff")
    return str(n.get("id", "?"))


def _result(plant, paths=(), facts=(), sessions=(), entities=(), summary="", empty=""):
    paths, facts = [list(p) for p in paths], list(facts)
    rows = len(paths) + len(facts)
    names = {plant["name"], *entities}
    for p in paths:
        names.update(p)
    return {"rows": rows, "paths": paths, "facts": facts, "sessions": sorted({int(s) for s in sessions}),
            "entities": sorted(names), "summary": summary if rows else empty}


# ───────────────────────────── Tools ─────────────────────────────
def why_follow_up(plant, **_):
    """Why does a pending task exist? Path: agent → task → evidence → session."""
    chains = []
    for q in (WHY_CARE, WHY_OBS):
        chains += [r["chain"] for r in run(q, {"pid": plant["id"]})]
    paths, by_task, sessions = [], {}, set()
    for ag, task, ev, sess in chains:
        paths.append([node_label(n) for n in (ag, task, ev, sess)])
        by_task.setdefault((task["title"], ag["name"]), []).append(f"{node_label(ev)} ({node_label(sess)})")
        sessions.add(sess["number"])
    parts = [f"{title} was created by the {agent}, based on " + " and ".join(ev) + "."
             for (title, agent), ev in by_task.items()]
    return _result(plant, paths=paths, sessions=sessions, entities=[t for t, _ in by_task], summary=" ".join(parts),
                   empty=f"No pending follow-up is recorded for {plant['name']}. That may mean nothing needs "
                         f"checking, or that nothing has been recorded yet.")


def what_happened_since(plant, action="watered", depth=MAX_DEPTH, **_):
    """What was recorded after care across sessions (FOLLOWED_BY*1..N)."""
    care = queries.latest_care(plant["id"], action)
    if not care:
        return _result(plant, empty=f"No “{to_label(action)}” care is recorded for {plant['name']}, "
                                    f"so there is nothing to follow from.")
    rows = run(SINCE.replace("__N__", str(int(depth))), {"pid": plant["id"], "care_id": care["id"]})
    paths, sessions, found = [], set(), []
    for r in rows:
        s1, s2, hops = r["from_session"], r["to_session"], r["hops"]
        if s1 != s2 and not hops:  # Beyond the requested traversal depth.
            continue
        mid = [node_label(n) for n in hops] if hops else [session_label(s1)]
        what = describe_observation(r["o"])
        paths.append([node_label(r["c"])] + mid + [what])
        sessions.update({s1, s2})
        found.append(f"{what} in {session_label(s2)}")
    noun = CARE_NOUN.get(action, "Care").lower()
    sessions.add(care["session_number"])
    return _result(plant, paths=paths, sessions=sessions,
                   summary=f"After {noun} in {session_label(care['session_number'])}, the graph shows: "
                           + "; ".join(found) + f" (following up to {int(depth)} session hop(s)).",
                   empty=f"Nothing was recorded after {noun} in {session_label(care['session_number'])} "
                         f"within {int(depth)} session hop(s). That is not the same as nothing happening.")


def observation_history(plant, depth=MAX_DEPTH, **_):
    """Chain of superseded observations (SUPERSEDES*1..N), from current to previous."""
    chains = [r["chain"] for r in run(HISTORY.replace("__N__", str(int(depth))), {"pid": plant["id"]})]
    if not chains:
        return _result(plant, empty=f"No observation of {plant['name']} has been superseded yet, "
                                    f"so there is no earlier state to compare.")
    labels, sessions = [], set()
    for n in max(chains, key=len):
        o = queries.get_observation(n["id"])
        labels.append(f"{describe_observation(o)} · {session_label(o['session_number'])}")
        sessions.add(o["session_number"])
    return _result(plant, paths=[labels], sessions=sessions,
                   summary=f"Current observation: {labels[0]}. It superseded, most recent first: "
                           + "; ".join(labels[1:]) + ".")


def handoff_trail(plant, **_):
    """Show which agent handed context to which agent (Agent → Handoff → Agent)."""
    rows = run(HANDOFFS, {"pid": plant["id"]})
    paths, sessions, parts = [], set(), []
    for r in rows:
        src, h, dst = r["chain"]
        paths.append([node_label(src), node_label(h), node_label(dst)])
        if r["session_number"] is not None:
            sessions.add(r["session_number"])
        parts.append(f"{src['name']} → {dst['name']} ({session_label(r['session_number'])}): "
                     f"{r.get('outcome') or 'pending'}")
    return _result(plant, paths=paths, sessions=sessions, summary="Handoffs: " + "; ".join(parts[-5:]) + ".",
                   empty=f"No handoff has been recorded for {plant['name']} yet.")


def recall(plant, **_):
    """Recall what earlier sessions established, with the date and session."""
    pid, facts, sessions, entities = plant["id"], [], set(), []
    obs, care = queries.current_observation(pid), queries.latest_care(pid)
    if obs:
        facts.append(f"Latest observation: {describe_observation(obs)} ({session_label(obs['session_number'])}, "
                     f"{fmt_short(obs['recorded_at'])})")
        sessions.add(obs["session_number"])
    if care:
        facts.append(f"Last care: {CARE_NOUN.get(care['action_type'], 'Care')} "
                     f"({session_label(care['session_number'])}, {fmt_short(care['performed_at'])})")
        sessions.add(care["session_number"])
    loc = queries.get_plant_location(pid)
    if loc:
        facts.append(f"Located at {loc['name']} (light as informed by you: {loc.get('light') or 'not informed'})")
        entities.append(loc["name"])
    for t in queries.pending_tasks(pid):
        facts.append(f"Pending: {t['title']} (created in {session_label(t['created_session'])})")
        sessions.add(t["created_session"])
        entities.append(t["title"])
    return _result(plant, facts=facts, sessions=sessions, entities=entities,
                   summary=f"For {plant['name']}, the graph remembers: " + "; ".join(facts) + ".",
                   empty=f"Nothing has been recorded for {plant['name']} yet.")


# ───────────────────────────── Catalog and validation ─────────────────────────────
TOOLS = {
    "why_follow_up": {"fn": why_follow_up, "args": {"plant": "plant_name"}, "kind": "traversal",
                      "doc": "Why does a pending task exist? Walks agent → task → evidence → session.",
                      "cypher": [WHY_CARE, WHY_OBS]},
    "what_happened_since": {"fn": what_happened_since,
                            "args": {"plant": "plant_name", "action": "care_action", "depth": "int<=4"},
                            "kind": "traversal",
                            "doc": "What was recorded after a care action, across sessions.", "cypher": [SINCE]},
    "observation_history": {"fn": observation_history, "args": {"plant": "plant_name", "depth": "int<=4"},
                            "kind": "traversal", "doc": "Chain of superseded observations.", "cypher": [HISTORY]},
    "handoff_trail": {"fn": handoff_trail, "args": {"plant": "plant_name"}, "kind": "traversal",
                      "doc": "Which agent handed context to which.", "cypher": [HANDOFFS]},
    "recall": {"fn": recall, "args": {"plant": "plant_name"}, "kind": "memory",
               "doc": "What earlier sessions already established.", "cypher": []},
}


def validate(tool: str, raw: dict) -> dict:
    """Validate arguments against the graph and catalog types; raises UnknownEntity or ToolError."""
    spec = TOOLS.get(tool)
    if not spec:
        raise ToolError(f"Unknown tool: {tool!r}")
    clean = {}
    for arg, kind in spec["args"].items():
        value = raw.get(arg)
        if kind == "plant_name":
            plant = queries.resolve_plant(value) if value else None
            if not plant:
                raise UnknownEntity(value or "")
            clean[arg] = plant
        elif kind == "care_action":
            key = to_key(value or "watered")
            if key not in CARE_KEYS:
                raise ToolError(f"Invalid care action: {value!r}")
            clean[arg] = key
        elif kind.startswith("int"):
            try:
                clean[arg] = max(1, min(int(value if value is not None else MAX_DEPTH), MAX_DEPTH))
            except (TypeError, ValueError):
                raise ToolError(f"Invalid {arg}: {value!r}")
    return clean


def cache_key(tool: str, clean: dict) -> str:
    extras = "|".join(f"{k}={v}" for k, v in sorted(clean.items()) if k != "plant")
    return f"{tool}|{extras}"
