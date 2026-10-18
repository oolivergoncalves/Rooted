"""History timeline grouped by session."""
import streamlit as st

from graph import queries
from services import history_service
from services.utils import session_label
from ui import layout

session = layout.setup()
layout.page_header(session, "History", "Everything that happened, session by session.",
                   title_class="greet care-greet")

st.markdown('<div style="height: 1rem"></div>', unsafe_allow_html=True)

plants = queries.list_plants()
options = [""] + [p["id"] for p in plants]
names = {p["id"]: p["name"] for p in plants}
with st.container(key="history-plant-selector"):
    choice = st.selectbox("Plant", options, format_func=lambda i: names.get(i, "All plants"))

events = history_service.build_events(choice)
by_session: dict = {}
for e in events:
    by_session.setdefault(e["session_number"], []).append(e)

sessions = {s["number"]: s for s in queries.list_sessions()}
if not by_session:
    st.write("No history yet. Record care or an observation to start the timeline.")
for number in sorted(by_session, key=lambda n: (n is None, n)):
    with st.container(key=f"panel_session_{number}"):
        status = sessions.get(number, {}).get("status", "")
        st.markdown(f'<div class="sess-head">{session_label(number)} '
                    f'<span style="font-size:.8rem;color:#6c7569">{"· active" if status == "active" else ""}</span></div>',
                    unsafe_allow_html=True)
        for e in by_session[number]:
            who = f"<span class='pl'>{e['plant']} —</span> " if not choice else ""
            st.markdown(f"<div class='ev'>• {who}{e['text']}</div>", unsafe_allow_html=True)
