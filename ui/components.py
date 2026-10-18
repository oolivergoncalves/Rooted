"""Reusable HTML components for cards, rows, and chips."""
import base64
import mimetypes
import re
from functools import lru_cache
from html import escape as esc
from pathlib import Path

from agents.vocab import AGENT_DESCRIPTIONS, CARE_PAST, to_label
from services.task_service import TASK_TYPES, short_label
from services.utils import fmt_date, fmt_datetime, fmt_short, session_label

ASSETS = Path(__file__).resolve().parent.parent / "assets"


def compact(s: str) -> str:
    """Remove line breaks and indentation so Markdown does not render HTML as a code block."""
    return re.sub(r"\s*\n\s*", "", s).strip()


@lru_cache(maxsize=32)
def _read_image(path: str, mtime: float) -> str:
    image_path = Path(path)
    mime = mimetypes.guess_type(image_path.name)[0] or "application/octet-stream"
    return f"data:{mime};base64," + base64.b64encode(image_path.read_bytes()).decode()


def img_uri(name: str) -> str:
    if not name:
        return ""
    relative_path = Path(name)
    path = ASSETS / relative_path if relative_path.suffix else ASSETS / f"{name}.png"
    path = path.resolve()
    try:
        path.relative_to(ASSETS.resolve())
    except ValueError:
        return ""
    if not path.is_file():
        return ""
    return _read_image(str(path), path.stat().st_mtime)


def chip(text: str, tone: str = "gray") -> str:
    return f'<span class="chip c-{tone}">{esc(text)}</span>'


def stat_card(icon: str, value, label: str, tone: str) -> str:
    return compact(f'<div class="stat t-{tone}"><div class="ico">{icon}</div>'
                   f'<div><div class="num">{value}</div><div class="lbl">{esc(label)}</div></div></div>')


def plant_card(s: dict, embedded: bool = False) -> str:
    p = s["plant"]
    photo = img_uri(p.get("photo", ""))
    pic = f'<img src="{photo}">' if photo else '<div class="ph">🪴</div>'
    status = chip("✓ Healthy", "green") if p.get("status") == "healthy" else chip("Needs attention", "amber")

    care, obs = s["last_care"], s["last_obs"]
    care_txt = (f"{to_label(care['action_type'])} · {fmt_short(care['performed_at'])} · "
                f"S{int(care['session_number']):02d}") if care else "No care recorded yet"
    obs_txt = (f"{_obs_short(obs)} · {fmt_short(obs['recorded_at'])} · S{int(obs['session_number']):02d}"
               if obs else "No observation yet")

    card_class = "pcard embedded" if embedded else "pcard"
    footer = f'<div class="foot">{plant_foot(s)}</div>'
    return compact(f"""
    <div class="{card_class}"><div class="pic">{pic}</div><div style="flex:1;min-width:0">
      <div class="nm">{esc(p['name'])}</div><div class="sp">{esc(p.get('species',''))}</div>
      {status}
      <div class="row">💧 Last care<b>{esc(care_txt)}</b></div>
      <div class="row">🍃 Latest observation<b>{esc(obs_txt)}</b></div>
      {footer}</div></div>""")


def plant_foot(s: dict) -> str:
    if s["alert"]:
        return chip("● " + s["alert"], "red")
    if s["tasks"]:
        return chip(short_label(s["tasks"][0]["task_type"]), "amber")
    return chip("No pending tasks", "gray")

def _obs_short(obs: dict) -> str:
    soil = obs.get("soil_status", "unknown")
    if soil != "unknown":
        return f"Soil {soil}"
    leaf = obs.get("leaf_status", "unknown")
    return f"Leaves {leaf.replace('_', ' ')}" if leaf != "unknown" else "Observation"


def task_row(t: dict) -> str:
    icon = TASK_TYPES.get(t["task_type"], {}).get("icon", "✓")
    photo = img_uri(t.get("plant_photo", ""))
    img = f'<img src="{photo}">' if photo else ""
    return compact(f"""
    <div class="trow"><div class="tic">{icon}</div>
      <div><div class="tt">{esc(t['title'])}</div><div class="ts">{esc(t.get('reason',''))}</div></div>
      <div class="plant">{img}<div><b>{esc(t['plant_name'])}</b><br>
        <span style="color:var(--muted)">Created in {session_label(t.get('created_session'))}</span></div></div>
      {chip(t['status'].capitalize(), 'amber' if t['status']=='pending' else 'green')}</div>""")


AGENT_ICONS = {"observation_agent": "🔍", "care_agent": "💧", "coordinator_agent": "🔗"}


def agent_row(agent: dict) -> str:
    name, desc = AGENT_DESCRIPTIONS.get(agent["id"], (agent["name"], agent.get("description", "")))
    return compact(f"""
    <div class="arow"><div class="aic">{AGENT_ICONS.get(agent['id'],'🤖')}</div>
      <div style="flex:1"><div class="an">{esc(name)}</div><div class="ad">{esc(desc)}</div></div>
      {chip('● Active','green')}</div>""")


KIND_ICONS = {"observation": "🔍", "care": "💧", "environment": "☀️", "task_created": "✅", "task_completed": "✔️",
              "handoff": "🔁", "superseded": "♻️"}


def activity_item(e: dict) -> str:
    return compact(f"""
    <div class="act"><div class="aic">{KIND_ICONS.get(e['kind'],'•')}</div><div>
      <div class="at">{esc(e['title'])}</div><div class="ad">“{esc(e['detail'])}”</div>
      <div class="am">{esc(e['plant'])} • {fmt_datetime(e['ts'])}</div></div></div>""")


def tip_banner() -> str:
    return compact("""
    <div class="tip"><div class="q">“Small care today,<br>greener tomorrows.”</div>
      <div class="k">💡 Tip for today</div><h3>Observe, care, and let your plants grow.</h3>
      <div>Every observation helps our agents understand your plants better.</div></div>""")


def flow_step(who: str, what: str) -> str:
    return compact(f'<div class="flow"><div class="who">{esc(who)}</div><div class="what">{esc(what)}</div></div>')


ARROW = '<div class="arrow">↓</div>'
