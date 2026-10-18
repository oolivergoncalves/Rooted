"""Shared page layout, session setup, sidebar, header, and dialogs."""
from datetime import datetime
from html import escape
import logging
from pathlib import Path
from uuid import uuid4

import streamlit as st

from graph import db, queries, seed
from services import plant_service, session_service
from services.utils import session_label
from ui.components import ASSETS, compact, img_uri
from ui.theme import CSS

NAV = [
    ("Home", "app.py", "home"),
    ("My Plants", "pages/1_My_Plants.py", "eco"),
    ("Tasks", "pages/4_Tasks.py", "check_box"),
    ("Agent Memory", "pages/5_Agent_Memory.py", "hub"),
    ("Ask the Graph", "pages/8_Ask_the_Graph.py", "account_tree"),
    ("History", "pages/6_History.py", "history"),
    ("Settings", "pages/7_Settings.py", "settings"),
]
logger = logging.getLogger(__name__)


def setup() -> dict:
    """Call at the top of each page. Returns the active Rooted session."""
    st.set_page_config(page_title="Rooted · Care rooted in memory", page_icon=str(ASSETS / "logo1.png"), layout="wide")
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)
    if "tenant" not in st.session_state:  # On first load, read the garden from the URL (?garden=maria).
        st.session_state["tenant"] = db.slug_tenant(st.query_params.get("garden", ""))
    tenant = st.session_state["tenant"]
    db.use_tenant(tenant)  # Each garden has an isolated graph.
    if st.query_params.get("garden", "") != tenant:  # Keep the URL in sync across reloads.
        if tenant:
            st.query_params["garden"] = tenant
        else:
            st.query_params.pop("garden", None)
    if not db.is_available():
        st.error("Could not connect to FalkorDB. Start it with `docker compose up -d` and reload this page.")
        st.stop()
    if not queries.base_ready():
        seed.ensure_base()
    if "session" not in st.session_state:  # Reloads reuse the session; restarting the app creates a new one.
        st.session_state["session"] = session_service.current_or_new_session()
    session = st.session_state["session"]
    _sidebar(session)
    added_plant = st.session_state.pop("plant_added", None)
    if added_plant:
        st.success(f"{added_plant} was added to this garden.")
    return session


def switch_garden(name: str):
    """Switch gardens (graphs) and start a session in the selected garden."""
    st.session_state["tenant"] = db.slug_tenant(name)
    st.session_state["garden_name"] = name.strip()
    for key in ("session", "answer", "selected_plant"):
        st.session_state.pop(key, None)
    st.rerun()


def _sidebar(session: dict):
    with st.sidebar:
        logo = img_uri("logo")
        st.markdown(compact(f"""
        <div class="brand">{f'<img src="{logo}" alt="Rooted">' if logo else '<span class="fallback">🌿 Rooted</span>'}</div>
        <div class="by">by CapybaraBR</div>
        <div class="tagline">Care rooted in memory.</div>"""), unsafe_allow_html=True)
        for label, path, icon in NAV:
            st.page_link(path, label=label, icon=f":material/{icon}:")
        gardens = db.list_gardens()
        current = st.session_state.get("tenant", "")
        if current not in gardens:
            gardens.append(current)
        choice = st.selectbox("Garden", gardens, index=gardens.index(current),
                              format_func=lambda g: g or "Home Garden")
        if choice != current:
            switch_garden(choice)
        st.markdown(f'<div class="sess-pill"><i></i>{session_label(session["number"])} active</div>',
                    unsafe_allow_html=True)
        with st.container(key="session-idle-note"):
            st.caption(f"A new session starts automatically after {session_service.IDLE_MINUTES // 60} hours "
                       "without activity. You can also start one now with the button.")
        with st.container(key="sidebar-new-session-button"):
            if st.button("Start New Session"):
                st.session_state["session"] = session_service.start_session()
                st.rerun()
        mascot = img_uri("capybara")
        if mascot:
            st.markdown(f'<img class="mascot" src="{mascot}">', unsafe_allow_html=True)


def page_header(session: dict, title: str, subtitle: str = "", title_class: str = "greet"):
    left, right = st.columns([3, 1.4])
    with left:
        st.markdown(f'<h1 class="{title_class}">{title}</h1>', unsafe_allow_html=True)
        if subtitle:
            st.markdown(f'<div class="page-sub">{subtitle}</div>', unsafe_allow_html=True)
    with right:
        now = datetime.now()
        garden = (st.session_state.get("garden_name") or st.session_state.get("tenant", "")).strip()
        garden_line = f'<span class="garden-name">{escape(garden)}</span>' if garden else ""
        st.markdown(compact(f"""
        <div class="user-chip"><div class="meta"><b>{now.strftime('%a, %b %d, %Y')}</b>
        <span>{session_label(session['number'])} &middot; {now.strftime('%I:%M %p')}</span>{garden_line}</div>
        <div class="av">CB</div></div>"""),
            unsafe_allow_html=True)

def plant_select(label: str = "Plant") -> dict:
    """Plant selector that remembers the selection across pages."""
    plants = queries.list_plants()
    if not plants:
        st.info("This garden has no plants yet. Press ＋ Add Plant to add the first one.")
        if st.button("＋ Add Plant", key="add_plant_empty", type="primary"):
            add_plant_dialog()
        st.stop()
    ids = [p["id"] for p in plants]
    names = {p["id"]: p["name"] for p in plants}
    default = st.session_state.get("selected_plant", ids[0])
    choice = st.selectbox(label, ids, index=ids.index(default) if default in ids else 0,
                          format_func=lambda i: names[i])
    st.session_state["selected_plant"] = choice
    return next(p for p in plants if p["id"] == choice)


@st.dialog("Add a plant")
def add_plant_dialog():
    name = st.text_input("Name", placeholder="e.g. Ficus")
    species = st.text_input("Species (optional)")
    photo = st.file_uploader("Plant photo (optional)", type=["png", "jpg", "jpeg", "webp"])
    for location_id, location_name, light in seed.LOCATIONS:
        queries.upsert_location(location_id, location_name, light)
    locs = queries.list_locations()
    loc = st.selectbox("Location", [""] + [l["id"] for l in locs],
                       format_func=lambda i: next((l["name"] for l in locs if l["id"] == i), "Not set"))
    if st.button("Save plant", type="primary"):
        if not name.strip():
            st.warning("Give the plant a name first.")
        else:
            photo_path = ""
            if photo is not None:
                extension = Path(photo.name).suffix.lower()
                upload_dir = ASSETS / "uploads"
                upload_dir.mkdir(parents=True, exist_ok=True)
                photo_path = f"uploads/{uuid4().hex}{extension}"
                (ASSETS / photo_path).write_bytes(photo.getvalue())
            try:
                plant = plant_service.add_plant(name, species, loc, photo=photo_path)
                if not plant:
                    raise RuntimeError("The plant was not returned after creation.")
            except Exception:
                logger.exception("Could not save a plant in graph %s", db.graph_name())
                st.error("The plant could not be saved. Check the FalkorDB connection and try again.")
            else:
                st.session_state["selected_plant"] = plant["id"]
                st.session_state["plant_added"] = plant["name"]
                st.rerun()


def show_coordinator_result(result: dict):
    """Show what the Coordinator Agent did after a handoff."""
    if result["actions"]:
        for a in result["actions"]:
            st.success(f"Coordinator Agent: {a}")
    else:
        st.info(f"Coordinator Agent: {result['outcome']}.")
