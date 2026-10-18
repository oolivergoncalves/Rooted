"""Settings for the database connection and garden management."""
import streamlit as st

from graph import db
from ui import layout

session = layout.setup()
layout.page_header(session, "Settings", "Database connection and garden management.",
                   title_class="greet care-greet")

with st.container(key="panel_conn"):
    st.markdown('<div class="ptitle recent-care-title">FalkorDB</div>', unsafe_allow_html=True)
    st.write(f"Graph: `{db.graph_name()}`")
    st.write("Status: connected ✅")

with st.container(key="panel_tenant"):
    st.markdown('<div class="ptitle recent-care-title">Garden (isolated memory)</div>', unsafe_allow_html=True)
    st.caption("Each garden is its own FalkorDB graph (`rooted:<name>`), so memories never mix. "
               "Leave empty for the default garden.")
    garden = st.text_input("Garden name", value=st.session_state.get(
        "garden_name", st.session_state.get("tenant", "")), placeholder="default")
    if st.button("Create / switch garden"):
        layout.switch_garden(garden)


@st.dialog("Delete this garden?")
def confirm_delete_garden(name: str):
    if not name:  # The default garden is protected.
        st.rerun()
    st.warning(f"This permanently deletes the garden **{name}** and everything stored in it: plants, "
               "sessions, care, observations, tasks and handoffs. This cannot be undone.")
    c1, _, c2 = st.columns([1, 2, 1])
    if c1.button("Yes, delete it", type="primary", use_container_width=True):
        db.use_tenant(name)       # The dialog runs in isolation, so select the garden again before deleting it.
        db.reset_graph()          # Delete the entire rooted:<name> graph from FalkorDB.
        layout.switch_garden("")  # Return to the default garden.
    if c2.button("Cancel", use_container_width=True):
        st.rerun()


with st.container(key="panel_delete"):
    st.markdown('<div class="ptitle garden-delete-title">Delete this garden</div>', unsafe_allow_html=True)
    tenant = st.session_state.get("tenant", "")
    if not tenant:
        st.caption("The default garden is protected and cannot be deleted. "
                   "Create a new garden above to start from scratch.")
    else:
        st.caption(f"Deletes `{db.graph_name()}` and all of its data from FalkorDB.")
        if st.button("Delete garden"):
            confirm_delete_garden(tenant)
