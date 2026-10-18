"""My Plants: plant cards and their recorded history."""
import streamlit as st

from agents.vocab import describe_observation, to_label
from graph import queries
from services import plant_service
from services.utils import fmt_datetime, session_label
from ui import components as c
from ui import layout

session = layout.setup()
layout.page_header(session, "My Plants", "Every plant keeps its own history.", title_class="greet my-plants-title")


@st.dialog("Remove plant?")
def confirm_remove_plant(plant_id: str, plant_name: str):
    st.write(f"Remove **{plant_name}** and permanently delete its care history, observations, tasks, and agent records?")
    cancel, confirm = st.columns(2)
    with cancel:
        if st.button("Cancel", use_container_width=True):
            st.rerun()
    with confirm:
        if st.button("Remove plant", type="primary", use_container_width=True):
            plant_service.delete_plant(plant_id)
            if st.session_state.get("selected_plant") == plant_id:
                st.session_state.pop("selected_plant", None)
            st.rerun()


_, add_col = st.columns([5, 1])
with add_col:
    if st.button("＋ Add Plant", type="primary", use_container_width=True, key="add_plant_top"):
        layout.add_plant_dialog()

summaries = plant_service.all_summaries()
cols = st.columns(3)
for col, s in zip(cols * ((len(summaries) // 3) + 1), summaries):
    with col:
        pid = s["plant"]["id"]
        with st.container(key=f"plant-card-{pid}"):
            if st.button("×", key=f"delete-plant-{pid}", help=f"Remove {s['plant']['name']}"):
                confirm_remove_plant(pid, s["plant"]["name"])
            info_col, actions_col = st.columns([1.8, 1], gap="small")
            with info_col:
                st.markdown(c.plant_card(s, embedded=True), unsafe_allow_html=True)
            with actions_col:
                if st.button("Record care", key=f"care_{pid}", use_container_width=True):
                    st.session_state["selected_plant"] = pid
                    st.switch_page("pages/2_Plant_Care.py")
                if st.button("Observe", key=f"obs_{pid}", use_container_width=True):
                    st.session_state["selected_plant"] = pid
                    st.switch_page("pages/3_Observations.py")

if not summaries:
    st.info("No plants in this garden yet. Use Add Plant to create one.")
    st.stop()

with st.container(key="plant-details-selector"):
    plant = layout.plant_select("Plant Details")
pid = plant["id"]

with st.container(key="panel_detail"):
    loc = queries.get_plant_location(pid)
    st.markdown(f'<div class="ptitle plant-memory-title">{plant["name"]} — memory</div>', unsafe_allow_html=True)
    st.caption(f"{plant.get('species', '')} · "
               + (f"Located at {loc['name']} ({loc.get('light', 'light not informed')}, as informed by you)"
                  if loc else "Location not set"))

    t1, t2, t3 = st.tabs(["Observations", "Care events", "Pending follow-ups"])
    with t1:
        obs = queries.list_observations(pid)
        if not obs:
            st.write("No observations yet.")
        for o in obs:
            tag = "🟢 current" if o.get("is_current") else "⚪ superseded"
            st.markdown(f"**{describe_observation(o)}** — {tag}  \n"
                        f"<span style='color:#6c7569'>{session_label(o['session_number'])} · "
                        f"{fmt_datetime(o['recorded_at'])}"
                        f"{' · ' + o['note'] if o.get('note') else ''}</span>", unsafe_allow_html=True)
    with t2:
        care = queries.list_care_events(pid)
        if not care:
            st.write("No care recorded yet.")
        for e in care:
            st.markdown(f"**{to_label(e['action_type'])}** — {session_label(e['session_number'])} · "
                        f"{fmt_datetime(e['performed_at'])}{' · ' + e['note'] if e.get('note') else ''}")
    with t3:
        tasks = queries.pending_tasks(pid)
        if not tasks:
            st.write("No pending follow-ups.")
        for t in tasks:
            st.markdown(f"**{t['title']}** — created in {session_label(t['created_session'])}  \n{t['reason']}")
