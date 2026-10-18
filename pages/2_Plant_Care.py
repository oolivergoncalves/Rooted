"""Record Care form for the Care Agent."""
from datetime import date

import streamlit as st

from agents import care_agent
from agents.vocab import CARE_ACTIONS, to_label
from graph import queries
from services.utils import fmt_datetime, session_label
from ui import layout

session = layout.setup()
layout.page_header(session, "Record Care", "The Care Agent saves what you did and hands the context to the Coordinator.",
                   title_class="greet care-greet")

st.markdown('<div style="height: 1rem"></div>', unsafe_allow_html=True)

left, right = st.columns([1.2, 1], gap="large")
with left:
    with st.container(key="panel_care_form"):
        plant = layout.plant_select("Plant")
        action = st.selectbox("Care action", CARE_ACTIONS)
        when = st.date_input("Date", value=date.today(), max_value=date.today())
        note = st.text_input("Optional note", placeholder="Used approximately one cup of water")
        location = light = ""
        if action == "Moved":
            location = st.text_input("New location", placeholder="e.g. Near the window")
            light = st.text_input("Light conditions (optional)", placeholder="e.g. Bright indirect light")
        if st.button("Record care", type="primary"):
            out = care_agent.register_care(plant["id"], session["id"], action, note, when, location, light)
            st.success(f"Care Agent recorded “{action}” for {plant['name']} in {session_label(session['number'])}.")
            st.info("Care Agent → HANDOFF_TO → Coordinator Agent  ·  Reason: " + out["handoff"]["reason"])
            layout.show_coordinator_result(out["coordinator"])

with right:
    with st.container(key="panel_care_recent"):
        st.markdown('<div class="ptitle recent-care-title">Recent care</div>', unsafe_allow_html=True)
        events = queries.list_care_events(plant["id"], limit=8)
        if not events:
            st.write("No care recorded for this plant yet.")
        for e in events:
            st.markdown(f"**{to_label(e['action_type'])}** · {session_label(e['session_number'])}  \n"
                        f"<span style='color:#6c7569'>{fmt_datetime(e['performed_at'])}"
                        f"{' · ' + e['note'] if e.get('note') else ''}</span>", unsafe_allow_html=True)
