"""Tasks: persistent follow-ups and the evidence behind each one."""
import streamlit as st

from graph import queries
from services import task_service
from services.utils import fmt_datetime, session_label
from ui import components as c
from ui import layout

session = layout.setup()
layout.page_header(session, "Tasks", "Follow-ups stay here across sessions until a new observation answers them.",
                   title_class="greet care-greet")

st.markdown('<div style="height: 1rem"></div>', unsafe_allow_html=True)

tab_pending, tab_done, tab_all = st.tabs(["Pending", "Completed", "All"])


def render(tasks, prefix):
    if not tasks:
        st.write("Nothing here yet.")
        return
    for t in tasks:
        with st.container(key=f"panel_{prefix}_{t['id']}"):
            st.markdown(c.task_row(t), unsafe_allow_html=True)
            if t["status"] == "completed":
                st.caption(f"Completed in {session_label(t['completed_session'])} · "
                           f"{fmt_datetime(t['completed_at'])}. The history behind it is preserved.")
            with st.expander("Why was this follow-up created?"):
                info = task_service.explain_task(t["id"])
                st.markdown('<div class="why">' + "".join(f"<p>{l}</p>" for l in info["lines"]) + "</div>",
                            unsafe_allow_html=True)
                st.caption("Evidence: " + ", ".join(
                    f"{e['kind']} {e['data']['id']} ({session_label(e['session_number'])})" for e in info["evidence"]))
            if t["status"] == "pending":
                b1, b2, _ = st.columns([1, 1, 3])
                if b1.button("Mark as done", key=f"done_{prefix}_{t['id']}"):
                    task_service.complete_task(t["id"], session["id"])
                    st.rerun()
                if t["task_type"] != "location_followup":
                    st.caption("Tip: recording a new observation completes this follow-up automatically.")


with tab_pending:
    render(queries.list_tasks("pending"), "p")
with tab_done:
    render(queries.list_tasks("completed"), "d")
with tab_all:
    render(queries.list_tasks(), "a")
