"""Rooted — Home / Dashboard."""
from datetime import datetime

import streamlit as st

from graph import queries
from services import history_service
from ui import components as c
from ui import layout

session = layout.setup()

hour = datetime.now().hour
greeting = "Good morning!" if hour < 12 else "Good afternoon!" if hour < 18 else "Good evening!"
counts = queries.counts()
pending = queries.pending_tasks()
attention = len(pending)
sub = (f"Your plants are doing great. {attention} task{'s' if attention != 1 else ''} need attention."
       if attention else "Your plants are doing great. All follow-ups are up to date.")

layout.page_header(session, greeting, sub, title_class="greet home-greet")

cols = st.columns(4)
cards = [("🍃", counts["plants"], "Plants", "mint"), ("📋", counts["pending"], "Pending Tasks", "amber"),
         ("🕒", counts["care"], "Total Care Events", "sky"), ("📈", counts["observations"], "Observations", "lav")]
for col, (icon, value, label, tone) in zip(cols, cards):
    col.markdown(c.stat_card(icon, value, label, tone), unsafe_allow_html=True)

st.markdown('<div class="dashboard-gap"></div>', unsafe_allow_html=True)

left, right = st.columns([2.1, 1], gap="medium")

with left:
    with st.container(key="panel_tasks"):
        h1, h2 = st.columns([7.5, 1], gap="small")
        h1.markdown('<div class="ptitle upcoming-title">Upcoming Tasks</div>', unsafe_allow_html=True)
        h2.page_link("pages/4_Tasks.py", label="View all")
        if pending:
            st.markdown("".join(c.task_row(t) for t in pending[:4]), unsafe_allow_html=True)
        else:
            st.write("No pending follow-ups. Record a care action or an observation to get started.")

    st.markdown(c.tip_banner(), unsafe_allow_html=True)
    st.page_link("pages/3_Observations.py", label="＋ Record an observation")

with right:
    with st.container(key="panel_agents"):
        h1, h2 = st.columns([1.8, 1], gap="small")
        h1.markdown('<div class="ptitle agent-title">Agent Status</div>', unsafe_allow_html=True)
        h2.page_link("pages/5_Agent_Memory.py", label="See details")
        from agents.vocab import AGENT_ORDER
        agents = {a["id"]: a for a in queries.list_agents()}
        st.markdown("".join(c.agent_row(agents[i]) for i in AGENT_ORDER if i in agents), unsafe_allow_html=True)

    with st.container(key="panel_activity"):
        h1, h2 = st.columns([2.5, 1], gap="small")
        h1.markdown('<div class="ptitle activity-title">Recent Activity</div>', unsafe_allow_html=True)
        h2.page_link("pages/6_History.py", label="View all")
        events = history_service.recent(4)
        if events:
            st.markdown("".join(c.activity_item(e) for e in events), unsafe_allow_html=True)
        else:
            st.write("Nothing recorded yet.")
