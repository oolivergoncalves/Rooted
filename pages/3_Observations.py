"""New Observation form for the Observation Agent."""
import streamlit as st

from agents import observation_agent
from agents.vocab import LEAF_OPTIONS, SOIL_OPTIONS, YES_NO_UNKNOWN
from graph import queries
from services import task_service
from services.utils import session_label
from ui import layout

session = layout.setup()
layout.page_header(session, "New Observation", "Describe what you see. The Observation Agent only records it — no diagnosis.",
                   title_class="greet care-greet")

st.markdown('<div style="height: 1rem"></div>', unsafe_allow_html=True)

with st.container(key="obs-plant-selector"):
    plant = layout.plant_select("Plant")
with st.container(key="panel_obs_form"):
    with st.form("observation_form"):
        c1, c2 = st.columns(2)
        soil = c1.radio("Soil condition", SOIL_OPTIONS, index=3, horizontal=True)
        leaves = c2.radio("Leaves", LEAF_OPTIONS, index=3, horizontal=True)
        c3, c4 = st.columns(2)
        growth = c3.radio("New growth", YES_NO_UNKNOWN, index=2, horizontal=True)
        pests = c4.radio("Visible pests", YES_NO_UNKNOWN, index=2, horizontal=True)
        note = st.text_input("Note (optional)", placeholder="New leaf beginning to open")
        submitted = st.form_submit_button("Save observation", type="primary")

if submitted:
    out = observation_agent.register_observation(plant["id"], session["id"], soil, leaves, growth, pests, note)
    st.success(f"Observation saved for {plant['name']} in {session_label(session['number'])}.")
    st.info("Observation Agent → HANDOFF_TO → Coordinator Agent  ·  " + out["handoff"]["reason"])
    layout.show_coordinator_result(out["coordinator"])
    for t in queries.pending_tasks(plant["id"]):
        if t["title"] in out["coordinator"]["created"] + out["coordinator"]["updated"]:
            info = task_service.explain_task(t["id"])
            with st.container(key="panel_why"):
                st.markdown('<div class="ptitle">Why was this follow-up created?</div>', unsafe_allow_html=True)
                st.markdown('<div class="why">' + "".join(f"<p>{l}</p>" for l in info["lines"]) + "</div>",
                            unsafe_allow_html=True)
