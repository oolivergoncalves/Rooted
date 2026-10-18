"""Agent Memory: coordination panel, memory types, and graph paths."""
import streamlit as st

from graph import db, queries
from services import history_service
from services.utils import fmt_datetime, session_label
from ui import components as c
from ui import layout

session = layout.setup()
layout.page_header(session, "Agent Memory", "One shared graph. Three agents. Every handoff is kept.",
                   title_class="greet care-greet")

st.markdown('<div style="height: 1rem"></div>', unsafe_allow_html=True)

with st.container(key="memory-plant-selector"):
    plant = layout.plant_select("Plant")
pid = plant["id"]

with st.container(key="panel_coord"):
    st.markdown('<div class="ptitle recent-care-title">Coordination panel</div>', unsafe_allow_html=True)
    handoffs = queries.list_handoffs(pid)
    if not handoffs:
        st.write("No handoffs yet for this plant.")
    for h in handoffs:
        st.caption(f"{session_label(h['session_number'])} · {fmt_datetime(h['created_at'])}")
        st.markdown(c.flow_step(h["source"], h["reason"]) + c.ARROW +
                    c.flow_step(h["target"], h.get("outcome") or "Waiting to evaluate…"),
                    unsafe_allow_html=True)
        st.markdown("&nbsp;")

with st.container(key="panel_memtypes"):
    st.markdown('<div class="ptitle recent-care-title">Memory types</div>', unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["Episodic", "Semantic", "Procedural"])
    with t1:
        st.caption("Things that happened, and when.")
        for e in reversed(history_service.build_events(pid)):
            if e["kind"] in ("care", "environment", "observation", "task_created", "task_completed"):
                st.write(f"**{session_label(e['session_number'])}** — {e['text']}")
    with t2:
        st.caption("Stable facts the user told the agents.")
        loc = queries.get_plant_location(pid)
        st.write(f"• **{plant['name']}** is a registered plant ({plant.get('species') or 'species not informed'}).")
        if loc:
            st.write(f"• It is at **{loc['name']}**, with *{loc.get('light') or 'light not informed'}* (as informed by you).")
        findings = queries.list_findings(pid)
        if findings:
            st.caption("Findings the Coordinator wrote back after reasoning over the graph:")
        for f in findings:
            st.write(f"• {f['text']}  _({session_label(f['session_number'])}, {fmt_datetime(f['at'])})_")
    with t3:
        st.caption("What agents must do when an event happens.")
        for p in queries.list_procedures():
            st.write(f"• **{p['trigger']}** → {p['description']}  _(assigned to {p['agent_name']})_")

with st.container(key="panel_context"):
    st.markdown('<div class="ptitle recent-care-title">Cross-session context</div>', unsafe_allow_html=True)
    ctx = queries.get_plant_context(pid)
    if ctx:
        a, b, d, e = st.columns(4)
        a.metric("Care events", len(ctx["cares"]))
        b.metric("Observations", len(ctx["observations"]))
        d.metric("Pending tasks", len(ctx["tasks"]))
        e.metric("Sessions touched", len({s["id"] for s in ctx["care_sessions"] + ctx["observation_sessions"]}))
