"""Cypher queries used by Rooted.

Convention: reads return plain dictionaries; writes return nothing.
FalkorDB does not store null properties, so empty values are represented as ''.
"""
from graph.db import execute, run


def _first(rows):
    return rows[0] if rows else None


def _flat(row, key):
    """Merge the row's extra columns into the main node dictionary."""
    if not row:
        return None
    data = dict(row[key])
    for k, v in row.items():
        if k != key:
            data[k] = v
    return data


def _flat_all(rows, key):
    return [_flat(r, key) for r in rows]


# ───────────────────────────── Schema ─────────────────────────────
def ensure_indexes():
    for label in ("Plant", "Session", "Observation", "CareEvent", "Task", "Handoff", "Agent", "Location", "Finding"):
        try:
            execute(f"CREATE INDEX FOR (n:{label}) ON (n.id)")
        except Exception:
            pass  # The index already exists.


def base_ready() -> bool:
    rows = run("MATCH (a:Agent) RETURN count(a) AS n")
    return bool(rows) and rows[0]["n"] >= 3


# ───────────────────────────── Base (User / Agents / Procedures / Locations) ─────────────────────────────
def upsert_user(user_id, name):
    execute("MERGE (u:User {id:$id}) SET u.name=$name", {"id": user_id, "name": name})


def upsert_agent(agent_id, name, agent_type, description):
    execute(
        "MERGE (a:Agent {id:$id}) SET a.name=$name, a.agent_type=$type, a.description=$desc, a.status='active'",
        {"id": agent_id, "name": name, "type": agent_type, "desc": description},
    )


def list_agents():
    return [r["a"] for r in run("MATCH (a:Agent) RETURN a")]


def upsert_procedure(proc_id, trigger, action, agent_id, description):
    execute(
        "MATCH (a:Agent {id:$agent}) "
        "MERGE (pr:Procedure {id:$id}) "
        "SET pr.trigger=$trigger, pr.action=$action, pr.description=$desc "
        "MERGE (pr)-[:ASSIGNED_TO]->(a)",
        {"id": proc_id, "trigger": trigger, "action": action, "agent": agent_id, "desc": description},
    )


def list_procedures():
    rows = run(
        "MATCH (pr:Procedure)-[:ASSIGNED_TO]->(a:Agent) "
        "RETURN pr, a.name AS agent_name, a.id AS agent_id ORDER BY pr.id"
    )
    return _flat_all(rows, "pr")


def procedure_target(trigger):
    rows = run(
        "MATCH (pr:Procedure {trigger:$t})-[:ASSIGNED_TO]->(a:Agent) RETURN a.id AS agent_id LIMIT 1",
        {"t": trigger},
    )
    return rows[0]["agent_id"] if rows else None


def upsert_location(loc_id, name, light):
    execute(
        "MERGE (l:Location {id:$id}) SET l.name=$name, l.light=$light",
        {"id": loc_id, "name": name, "light": light},
    )


def list_locations():
    return [r["l"] for r in run("MATCH (l:Location) RETURN l ORDER BY l.name")]


# ───────────────────────────── Plants ─────────────────────────────
def create_plant(plant_id, name, species, created_at, photo="", owner_id="user_demo"):
    execute(
        "MATCH (u:User {id:$owner}) "
        "CREATE (p:Plant {id:$id, name:$name, species:$species, created_at:$created_at, status:'healthy', photo:$photo}) "
        "CREATE (u)-[:OWNS]->(p)",
        {"owner": owner_id, "id": plant_id, "name": name, "species": species, "created_at": created_at, "photo": photo},
    )


def list_plants():
    return [r["p"] for r in run("MATCH (p:Plant) RETURN p ORDER BY p.created_at ASC")]


def get_plant(plant_id):
    return _first([r["p"] for r in run("MATCH (p:Plant {id:$id}) RETURN p", {"id": plant_id})])


def delete_plant(plant_id):
    """Remove a plant and its exclusive records while preserving agents, sessions, and locations."""
    for direction, relationship, label in (
        ("out", "HAS_OBSERVATION", "Observation"),
        ("out", "RECEIVED_CARE", "CareEvent"),
        ("in", "ABOUT", "Task"),
        ("in", "ABOUT", "Handoff"),
        ("in", "ABOUT", "Finding"),
    ):
        if direction == "out":
            query = f"MATCH (p:Plant {{id:$id}})-[:{relationship}]->(n:{label}) DETACH DELETE n"
        else:
            query = f"MATCH (n:{label})-[:{relationship}]->(p:Plant {{id:$id}}) DETACH DELETE n"
        execute(query, {"id": plant_id})
    execute("MATCH (p:Plant {id:$id}) DETACH DELETE p", {"id": plant_id})


def set_plant_status(plant_id, status):
    execute("MATCH (p:Plant {id:$id}) SET p.status=$status", {"id": plant_id, "status": status})


def get_plant_location(plant_id):
    rows = run("MATCH (:Plant {id:$id})-[:CURRENTLY_LOCATED_AT]->(l:Location) RETURN l LIMIT 1", {"id": plant_id})
    return rows[0]["l"] if rows else None


def set_plant_location(plant_id, loc_id, name, light=""):
    execute("MATCH (:Plant {id:$pid})-[r:CURRENTLY_LOCATED_AT]->(:Location) DELETE r", {"pid": plant_id})
    execute(
        "MERGE (l:Location {id:$lid}) ON CREATE SET l.name=$name, l.light=$light "
        "WITH l MATCH (p:Plant {id:$pid}) MERGE (p)-[:CURRENTLY_LOCATED_AT]->(l)",
        {"pid": plant_id, "lid": loc_id, "name": name, "light": light},
    )
    if light:
        execute("MATCH (l:Location {id:$lid}) SET l.light=$light", {"lid": loc_id, "light": light})


# ───────────────────────────── Sessions ─────────────────────────────
def create_session(session_id, number, started_at, run_id=""):
    execute(
        "CREATE (:Session {id:$id, number:$number, started_at:$started_at, ended_at:'', status:'active', "
        "run_id:$run_id})",
        {"id": session_id, "number": number, "started_at": started_at, "run_id": run_id},
    )


def get_last_session():
    rows = run("MATCH (s:Session) RETURN s ORDER BY s.number DESC LIMIT 1")
    return rows[0]["s"] if rows else None


def end_session(session_id, ended_at):
    execute(
        "MATCH (s:Session {id:$id}) SET s.status='ended', s.ended_at=$at",
        {"id": session_id, "at": ended_at},
    )


def link_sessions(previous_id, next_id):
    execute(
        "MATCH (a:Session {id:$a}), (b:Session {id:$b}) MERGE (a)-[:FOLLOWED_BY]->(b)",
        {"a": previous_id, "b": next_id},
    )


def list_sessions():
    return [r["s"] for r in run("MATCH (s:Session) RETURN s ORDER BY s.number ASC")]


# ───────────────────────────── Observations ─────────────────────────────
def create_observation(obs_id, plant_id, agent_id, session_id, soil, leaf, growth, pests, note, recorded_at):
    execute(
        "MATCH (p:Plant {id:$plant_id}), (a:Agent {id:$agent_id}), (s:Session {id:$session_id}) "
        "CREATE (o:Observation {id:$id, soil_status:$soil, leaf_status:$leaf, new_growth:$growth, "
        "pests_visible:$pests, note:$note, recorded_at:$recorded_at, is_current:true}) "
        "CREATE (p)-[:HAS_OBSERVATION]->(o) "
        "CREATE (a)-[:RECORDED]->(o) "
        "CREATE (o)-[:RECORDED_IN]->(s)",
        {"plant_id": plant_id, "agent_id": agent_id, "session_id": session_id, "id": obs_id,
         "soil": soil, "leaf": leaf, "growth": growth, "pests": pests, "note": note, "recorded_at": recorded_at},
    )


def get_observation(obs_id):
    rows = run(
        "MATCH (o:Observation {id:$id}) OPTIONAL MATCH (o)-[:RECORDED_IN]->(s:Session) "
        "RETURN o, s.number AS session_number",
        {"id": obs_id},
    )
    return _flat(_first(rows), "o")


def latest_observation(plant_id, current_only=False):
    """Return the latest observation (PDF operation: 'Get latest observation')."""
    where = "WHERE o.is_current = true" if current_only else ""
    rows = run(
        f"MATCH (plant:Plant {{id:$plant_id}})-[:HAS_OBSERVATION]->(o:Observation) {where} "
        "OPTIONAL MATCH (o)-[:RECORDED_IN]->(s:Session) "
        "RETURN o, s.number AS session_number ORDER BY o.recorded_at DESC LIMIT 1",
        {"plant_id": plant_id},
    )
    return _flat(_first(rows), "o")


def current_observation(plant_id):
    return latest_observation(plant_id, current_only=True)


def previous_current_observation(plant_id, exclude_id):
    rows = run(
        "MATCH (:Plant {id:$plant_id})-[:HAS_OBSERVATION]->(o:Observation) "
        "WHERE o.is_current = true AND o.id <> $exclude RETURN o ORDER BY o.recorded_at DESC LIMIT 1",
        {"plant_id": plant_id, "exclude": exclude_id},
    )
    return rows[0]["o"] if rows else None


def supersede(new_id, old_id, at):
    execute(
        "MATCH (n:Observation {id:$new}), (o:Observation {id:$old}) "
        "MERGE (n)-[r:SUPERSEDES]->(o) SET r.at=$at, o.is_current=false, n.is_current=true",
        {"new": new_id, "old": old_id, "at": at},
    )


def list_observations(plant_id="", limit=100):
    rows = run(
        "MATCH (p:Plant)-[:HAS_OBSERVATION]->(o:Observation) WHERE $plant_id = '' OR p.id = $plant_id "
        "OPTIONAL MATCH (o)-[:RECORDED_IN]->(s:Session) "
        "OPTIONAL MATCH (ag:Agent)-[:RECORDED]->(o) "
        "RETURN o, p.name AS plant_name, p.id AS plant_id, s.number AS session_number, ag.name AS agent_name "
        f"ORDER BY o.recorded_at DESC LIMIT {int(limit)}",
        {"plant_id": plant_id},
    )
    return _flat_all(rows, "o")


def list_supersessions(plant_id=""):
    return run(
        "MATCH (p:Plant)-[:HAS_OBSERVATION]->(n:Observation)-[r:SUPERSEDES]->(o:Observation) "
        "WHERE $plant_id = '' OR p.id = $plant_id "
        "OPTIONAL MATCH (n)-[:RECORDED_IN]->(s:Session) "
        "RETURN r.at AS ts, p.name AS plant_name, p.id AS plant_id, s.number AS session_number, "
        "n.id AS new_id, o.id AS old_id",
        {"plant_id": plant_id},
    )


# ───────────────────────────── Care events ─────────────────────────────
def create_care_event(care_id, plant_id, agent_id, session_id, action, note, performed_at, recorded_at, location=""):
    execute(
        "MATCH (p:Plant {id:$plant_id}), (a:Agent {id:$agent_id}), (s:Session {id:$session_id}) "
        "CREATE (c:CareEvent {id:$id, action_type:$action, note:$note, performed_at:$performed_at, "
        "recorded_at:$recorded_at, location:$location}) "
        "CREATE (p)-[:RECEIVED_CARE]->(c) "
        "CREATE (a)-[:RECORDED]->(c) "
        "CREATE (c)-[:OCCURRED_IN]->(s)",
        {"plant_id": plant_id, "agent_id": agent_id, "session_id": session_id, "id": care_id,
         "action": action, "note": note, "performed_at": performed_at, "recorded_at": recorded_at,
         "location": location},
    )


def get_care_event(care_id):
    rows = run(
        "MATCH (c:CareEvent {id:$id}) OPTIONAL MATCH (c)-[:OCCURRED_IN]->(s:Session) "
        "RETURN c, s.number AS session_number",
        {"id": care_id},
    )
    return _flat(_first(rows), "c")


def latest_care(plant_id, action=""):
    """Return the latest care event (PDF operation: 'Get latest care'); `action` filters by type."""
    rows = run(
        "MATCH (plant:Plant {id:$plant_id})-[:RECEIVED_CARE]->(care:CareEvent) "
        "WHERE $action = '' OR care.action_type = $action "
        "OPTIONAL MATCH (care)-[:OCCURRED_IN]->(s:Session) "
        "RETURN care, s.number AS session_number ORDER BY care.performed_at DESC LIMIT 1",
        {"plant_id": plant_id, "action": action},
    )
    return _flat(_first(rows), "care")


def list_care_events(plant_id="", limit=100):
    rows = run(
        "MATCH (p:Plant)-[:RECEIVED_CARE]->(c:CareEvent) WHERE $plant_id = '' OR p.id = $plant_id "
        "OPTIONAL MATCH (c)-[:OCCURRED_IN]->(s:Session) "
        "OPTIONAL MATCH (ag:Agent)-[:RECORDED]->(c) "
        "RETURN c, p.name AS plant_name, p.id AS plant_id, s.number AS session_number, ag.name AS agent_name "
        f"ORDER BY c.performed_at DESC LIMIT {int(limit)}",
        {"plant_id": plant_id},
    )
    return _flat_all(rows, "c")


# ───────────────────────────── Tasks ─────────────────────────────
def create_task(task_id, plant_id, agent_id, session_id, task_type, title, reason, created_at):
    execute(
        "MATCH (p:Plant {id:$plant_id}), (a:Agent {id:$agent_id}), (s:Session {id:$session_id}) "
        "CREATE (t:Task {id:$id, task_type:$task_type, title:$title, status:'pending', created_at:$at, "
        "updated_at:$at, completed_at:'', reason:$reason}) "
        "CREATE (a)-[:CREATED]->(t) "
        "CREATE (t)-[:ABOUT]->(p) "
        "CREATE (t)-[:CREATED_IN]->(s)",
        {"plant_id": plant_id, "agent_id": agent_id, "session_id": session_id, "id": task_id,
         "task_type": task_type, "title": title, "reason": reason, "at": created_at},
    )


def add_evidence(task_id, label, evidence_id):
    if label not in ("Observation", "CareEvent"):
        raise ValueError(f"Invalid evidence label: {label}")
    execute(
        f"MATCH (t:Task {{id:$task_id}}), (e:{label} {{id:$eid}}) MERGE (t)-[:BASED_ON]->(e)",
        {"task_id": task_id, "eid": evidence_id},
    )


def find_pending_task(plant_id, task_type):
    rows = run(
        "MATCH (t:Task {status:'pending', task_type:$task_type})-[:ABOUT]->(:Plant {id:$plant_id}) RETURN t LIMIT 1",
        {"plant_id": plant_id, "task_type": task_type},
    )
    return rows[0]["t"] if rows else None


def update_task(task_id, reason, at):
    execute("MATCH (t:Task {id:$id}) SET t.reason=$reason, t.updated_at=$at", {"id": task_id, "reason": reason, "at": at})


def pending_tasks(plant_id=""):
    """Return pending tasks, oldest first (PDF operation: 'Get pending tasks')."""
    rows = run(
        "MATCH (t:Task {status:'pending'})-[:ABOUT]->(p:Plant) WHERE $plant_id = '' OR p.id = $plant_id "
        "OPTIONAL MATCH (t)-[:CREATED_IN]->(s:Session) "
        "RETURN t, p.id AS plant_id, p.name AS plant_name, p.photo AS plant_photo, s.number AS created_session "
        "ORDER BY t.created_at ASC",
        {"plant_id": plant_id},
    )
    return _flat_all(rows, "t")


def list_tasks(status=""):
    rows = run(
        "MATCH (t:Task)-[:ABOUT]->(p:Plant) WHERE $status = '' OR t.status = $status "
        "OPTIONAL MATCH (t)-[:CREATED_IN]->(cs:Session) "
        "OPTIONAL MATCH (t)-[:COMPLETED_IN]->(ds:Session) "
        "RETURN t, p.id AS plant_id, p.name AS plant_name, p.photo AS plant_photo, "
        "cs.number AS created_session, ds.number AS completed_session "
        "ORDER BY t.created_at DESC",
        {"status": status},
    )
    return _flat_all(rows, "t")


def complete_task(task_id, session_id, at, observation_id=""):
    execute(
        "MATCH (t:Task {id:$id}), (s:Session {id:$session}) "
        "SET t.status='completed', t.completed_at=$at, t.updated_at=$at "
        "MERGE (t)-[:COMPLETED_IN]->(s)",
        {"id": task_id, "session": session_id, "at": at},
    )
    if observation_id:
        execute(
            "MATCH (t:Task {id:$id}), (o:Observation {id:$obs}) MERGE (t)-[:RESOLVED_BY]->(o)",
            {"id": task_id, "obs": observation_id},
        )


def task_evidence_ids(task_id):
    return [r["id"] for r in run("MATCH (:Task {id:$id})-[:BASED_ON]->(e) RETURN e.id AS id", {"id": task_id})]


def task_evidence(task_id):
    """Return task evidence with the session in which each item occurred."""
    rows = run(
        "MATCH (t:Task {id:$id})-[:BASED_ON]->(e) "
        "OPTIONAL MATCH (e)-[:OCCURRED_IN]->(s1:Session) "
        "OPTIONAL MATCH (e)-[:RECORDED_IN]->(s2:Session) "
        "RETURN e, s1.number AS n1, s2.number AS n2",
        {"id": task_id},
    )
    out = []
    for r in rows:
        e = r["e"]
        kind = "care" if "CareEvent" in e.get("_labels", []) else "observation"
        out.append({"kind": kind, "data": e, "session_number": r["n1"] if r["n1"] is not None else r["n2"]})
    return out


def explain_task(task_id):
    """PDF operation: 'Explain why the task exists'."""
    rows = run(
        "MATCH (agent:Agent)-[:CREATED]->(task:Task {id:$task_id}) "
        "MATCH (task)-[:ABOUT]->(plant:Plant) RETURN agent, task, plant",
        {"task_id": task_id},
    )
    return _first(rows)


# ───────────────────────────── Handoffs ─────────────────────────────
def create_handoff(handoff_id, source_id, target_id, plant_id, session_id, reason, created_at):
    execute(
        "MATCH (src:Agent {id:$src}), (dst:Agent {id:$dst}), (p:Plant {id:$plant_id}), (s:Session {id:$session_id}) "
        "CREATE (h:Handoff {id:$id, reason:$reason, created_at:$at, status:'pending', outcome:'', completed_at:''}) "
        "CREATE (src)-[:INITIATED]->(h) "
        "CREATE (h)-[:TARGETS]->(dst) "
        "CREATE (h)-[:ABOUT]->(p) "
        "CREATE (h)-[:OCCURRED_IN]->(s)",
        {"src": source_id, "dst": target_id, "plant_id": plant_id, "session_id": session_id,
         "id": handoff_id, "reason": reason, "at": created_at},
    )


def complete_handoff(handoff_id, outcome, at):
    execute(
        "MATCH (h:Handoff {id:$id}) SET h.status='completed', h.outcome=$outcome, h.completed_at=$at",
        {"id": handoff_id, "outcome": outcome, "at": at},
    )


def complete_open_handoffs(plant_id, target_id, outcome, at):
    execute(
        "MATCH (h:Handoff {status:'pending'})-[:TARGETS]->(:Agent {id:$target}) "
        "MATCH (h)-[:ABOUT]->(:Plant {id:$plant_id}) "
        "SET h.status='completed', h.outcome=$outcome, h.completed_at=$at",
        {"target": target_id, "plant_id": plant_id, "outcome": outcome, "at": at},
    )


def list_handoffs(plant_id="", limit=200):
    rows = run(
        "MATCH (src:Agent)-[:INITIATED]->(h:Handoff)-[:TARGETS]->(dst:Agent) "
        "MATCH (h)-[:ABOUT]->(p:Plant) WHERE $plant_id = '' OR p.id = $plant_id "
        "OPTIONAL MATCH (h)-[:OCCURRED_IN]->(s:Session) "
        "RETURN h, src.name AS source, src.id AS source_id, dst.name AS target, dst.id AS target_id, "
        "p.name AS plant_name, s.number AS session_number "
        f"ORDER BY h.created_at ASC LIMIT {int(limit)}",
        {"plant_id": plant_id},
    )
    return _flat_all(rows, "h")


# ───────────────────────────── Context / statistics / search ─────────────────────────────
def get_plant_context(plant_id):
    """PDF operation: 'Retrieve cross-session context'."""
    rows = run(
        "MATCH (plant:Plant {id: $plant_id}) "
        "OPTIONAL MATCH (plant)-[:RECEIVED_CARE]->(care:CareEvent) "
        "OPTIONAL MATCH (care)-[:OCCURRED_IN]->(careSession:Session) "
        "OPTIONAL MATCH (plant)-[:HAS_OBSERVATION]->(observation:Observation) "
        "OPTIONAL MATCH (observation)-[:RECORDED_IN]->(observationSession:Session) "
        "OPTIONAL MATCH (task:Task {status: 'pending'})-[:ABOUT]->(plant) "
        "RETURN plant, collect(DISTINCT care) AS cares, collect(DISTINCT careSession) AS care_sessions, "
        "collect(DISTINCT observation) AS observations, "
        "collect(DISTINCT observationSession) AS observation_sessions, collect(DISTINCT task) AS tasks",
        {"plant_id": plant_id},
    )
    return _first(rows)


def counts():
    def n(q):
        rows = run(q)
        return rows[0]["n"] if rows else 0

    return {
        "plants": n("MATCH (p:Plant) RETURN count(p) AS n"),
        "pending": n("MATCH (t:Task {status:'pending'}) RETURN count(t) AS n"),
        "care": n("MATCH (c:CareEvent) RETURN count(c) AS n"),
        "observations": n("MATCH (o:Observation) RETURN count(o) AS n"),
    }


def search(text):
    q = text.strip()
    if not q:
        return {"plants": [], "tasks": [], "observations": []}
    params = {"q": q}
    plants = [r["p"] for r in run(
        "MATCH (p:Plant) WHERE toLower(p.name) CONTAINS toLower($q) OR toLower(p.species) CONTAINS toLower($q) RETURN p",
        params)]
    tasks = _flat_all(run(
        "MATCH (t:Task)-[:ABOUT]->(p:Plant) WHERE toLower(t.title) CONTAINS toLower($q) "
        "OR toLower(t.reason) CONTAINS toLower($q) RETURN t, p.name AS plant_name", params), "t")
    observations = _flat_all(run(
        "MATCH (p:Plant)-[:HAS_OBSERVATION]->(o:Observation) WHERE toLower(o.note) CONTAINS toLower($q) "
        "RETURN o, p.name AS plant_name", params), "o")
    return {"plants": plants, "tasks": tasks, "observations": observations}


# ───────────────────────────── Graph reasoning ─────────────────────────────
def resolve_plant(name):
    """Resolve a name or ID against the graph. None means unknown plant; no reasoning query is run."""
    rows = run(
        "MATCH (p:Plant) WHERE toLower(p.name) = toLower($name) OR p.id = $name RETURN p LIMIT 1",
        {"name": str(name).strip()},
    )
    return rows[0]["p"] if rows else None


def create_finding(finding_id, plant_id, agent_id, session_id, key, text, payload, at):
    """Memory uses graph nodes: an agent's conclusion becomes (Finding)-[:ABOUT]->(Plant)."""
    execute(
        "MATCH (p:Plant {id:$plant}), (a:Agent {id:$agent}), (s:Session {id:$session}) "
        "CREATE (f:Finding {id:$id, key:$key, text:$text, payload:$payload, at:$at}) "
        "CREATE (f)-[:ABOUT]->(p) CREATE (a)-[:RECORDED]->(f) CREATE (f)-[:RECORDED_IN]->(s)",
        {"plant": plant_id, "agent": agent_id, "session": session_id, "id": finding_id,
         "key": key, "text": text, "payload": payload, "at": at},
    )


def latest_finding(plant_id, key):
    rows = run(
        "MATCH (f:Finding {key:$key})-[:ABOUT]->(:Plant {id:$plant}) "
        "OPTIONAL MATCH (f)-[:RECORDED_IN]->(s:Session) "
        "RETURN f, s.number AS session_number ORDER BY f.at DESC LIMIT 1",
        {"plant": plant_id, "key": key},
    )
    return _flat(_first(rows), "f")


def list_findings(plant_id, limit=10):
    rows = run(
        "MATCH (f:Finding)-[:ABOUT]->(:Plant {id:$plant}) "
        "OPTIONAL MATCH (f)-[:RECORDED_IN]->(s:Session) "
        f"RETURN f, s.number AS session_number ORDER BY f.at DESC LIMIT {int(limit)}",
        {"plant": plant_id},
    )
    return _flat_all(rows, "f")


def latest_activity(plant_id) -> str:
    """Return the timestamp of the latest plant activity (observation, care, or task)."""
    stamps = []
    for q in (
        "MATCH (:Plant {id:$id})-[:HAS_OBSERVATION]->(o:Observation) RETURN o.recorded_at AS ts ORDER BY ts DESC LIMIT 1",
        "MATCH (:Plant {id:$id})-[:RECEIVED_CARE]->(c:CareEvent) RETURN c.recorded_at AS ts ORDER BY ts DESC LIMIT 1",
        "MATCH (t:Task)-[:ABOUT]->(:Plant {id:$id}) RETURN t.updated_at AS ts ORDER BY ts DESC LIMIT 1",
    ):
        rows = run(q, {"id": plant_id})
        if rows:
            stamps.append(rows[0]["ts"])
    return max(stamps) if stamps else ""
