"""Rooted CSS theme with moss green, cream, and pastel cards."""

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600&family=Fraunces:opsz,wght@9..144,500;9..144,600&family=DM+Sans:wght@400;500;600&display=swap');
@font-face { font-family:'Espuma Pro Book'; src:local('Espuma Pro Book'),local('EspumaPro-Book'); font-style:normal; font-weight:400; }
@font-face { font-family:'Espuma Pro Bold'; src:local('Espuma Pro Bold'),local('EspumaPro-Bold'); font-style:normal; font-weight:700; }

:root{
  --bg:#f6f5ee; --sidebar:#ecebde; --card:#fffefb; --line:#e8e6d9;
  --ink:#1d2b22; --muted:#6c7569; --green:#2f5d3a; --green-d:#244a2f;
  --mint:#e3eee4; --amber:#fbeed6; --amber-d:#b9791c; --sky:#e2ecf3; --lav:#e9e7f5;
  --red-bg:#fde8e6; --red:#b83a2f;
}
html, body, .stApp, [class*="css"] { font-family:'DM Sans', system-ui, sans-serif; color:var(--ink); }
.stApp { background:linear-gradient(180deg,#f8f7f0 0%,#f1f0e5 100%); }
[data-testid="stHeader"] { background:transparent; }
[data-testid="stSidebarNav"] { display:none; }
.block-container { padding-top:1.2rem; padding-bottom:3rem; max-width:1480px; }
h1,h2,h3,.serif { font-family:'Fraunces', Georgia, serif !important; color:var(--ink); letter-spacing:-.01em; }

/* ── sidebar ── */
section[data-testid="stSidebar"] { background:var(--sidebar); border-right:1px solid var(--line); }
section[data-testid="stSidebar"] > div { padding-top:0 !important; }
section[data-testid="stSidebar"] [data-testid="stSidebarContent"],
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] { padding-top:0 !important; }
section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] {
  height:0 !important; min-height:0 !important; padding:0 !important; margin:0 !important;
}
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] { margin-top:0 !important; }
.brand { display:flex; align-items:center; margin:0 0 .1rem; }
.brand img { display:block; width:100%; max-width:220px; height:auto; object-fit:contain; mix-blend-mode:multiply; }
.brand .fallback { font-family:'Fraunces',serif; font-size:2.1rem; line-height:1; font-weight:600; color:#1f3d2b; }
.by { font-size:.82rem; color:var(--muted); margin-top:.15rem; }
.tagline { color:var(--muted); font-size:.86rem; margin:.4rem 0 1.1rem; }
a[data-testid="stPageLink-NavLink"] { border-radius:12px; padding:.5rem .8rem; color:var(--ink); }
a[data-testid="stPageLink-NavLink"]:hover { background:rgba(47,93,58,.08); }
a[data-testid="stPageLink-NavLink"][aria-current="page"] { background:#dfe3d2; font-weight:600; }
.sess-pill { display:inline-flex; gap:6px; align-items:center; background:#fff; border:1px solid var(--line);
  border-radius:999px; padding:.25rem .7rem; font-size:.8rem; color:var(--green); margin:.8rem 0 .4rem; }
.sess-pill i { width:8px; height:8px; border-radius:50%; background:#4aa35e; display:inline-block; }
.mascot { width:100%; border-radius:16px; margin-top:.8rem; mix-blend-mode:multiply; }
section[data-testid="stSidebar"] .stButton > button { width:100%; }
section[data-testid="stSidebar"] div[class*="st-key-sidebar-new-session-button"] .stButton {
  display:flex; justify-content:center;
}
section[data-testid="stSidebar"] div[class*="st-key-sidebar-new-session-button"] .stButton > button {
  width:85% !important;
}

/* ── Buttons ── */
.stButton > button, .stFormSubmitButton > button { border-radius:12px; border:1px solid var(--line); font-weight:600; }
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"],
button[data-testid="stBaseButton-primary"], button[data-testid="stBaseButton-primaryFormSubmit"] {
  background:var(--green-d); color:#fff; border-color:var(--green-d); }
.stButton > button[kind="primary"]:hover, button[data-testid="stBaseButton-primary"]:hover { background:#1c3a25; border-color:#1c3a25; }

/* ── Panels (st.container(key="panel_*")) ── */
div[class*="st-key-panel"] { background:var(--card); border:1px solid var(--line); border-radius:20px;
  padding:1rem 1.15rem 1.1rem; box-shadow:0 1px 3px rgba(60,70,40,.05); margin-bottom:.9rem; }
.ptitle { font-family:'Fraunces',serif; font-size:1.22rem; font-weight:600; margin:.1rem 0 .5rem; }
.upcoming-title, .agent-title, .activity-title, .plant-memory-title, .recent-care-title {
  font-family:'Espuma Pro Bold','EspumaPro-Bold',sans-serif !important;
  font-size:1.22rem !important; font-weight:700; line-height:1.2;
}
div[class*="st-key-plant-details-selector"] [data-testid="stWidgetLabel"],
div[class*="st-key-plant-details-selector"] [data-testid="stWidgetLabel"] p,
div[class*="st-key-obs-plant-selector"] [data-testid="stWidgetLabel"],
div[class*="st-key-obs-plant-selector"] [data-testid="stWidgetLabel"] p,
div[class*="st-key-memory-plant-selector"] [data-testid="stWidgetLabel"],
div[class*="st-key-memory-plant-selector"] [data-testid="stWidgetLabel"] p,
div[class*="st-key-history-plant-selector"] [data-testid="stWidgetLabel"],
div[class*="st-key-history-plant-selector"] [data-testid="stWidgetLabel"] p {
  font-family:'Espuma Pro Bold','EspumaPro-Bold',sans-serif !important;
  font-size:1.22rem !important; font-weight:700;
}
div[class*="st-key-panel_context"] [data-testid="stMetricValue"] {
  font-family:'Espuma Pro Bold','EspumaPro-Bold',sans-serif !important;
  font-weight:700;
}
div[class*="st-key-panel_context"] [data-testid="stMetric"] { text-align:center; }
div[class*="st-key-panel_context"] [data-testid="stMetricLabel"] {
  min-height:2.6rem; display:flex; align-items:flex-end; justify-content:center; text-align:center;
}
div[class*="st-key-panel_context"] [data-testid="stMetricValue"] {
  min-height:3rem; display:flex; align-items:center; justify-content:center;
}
.page-sub { color:var(--muted); font-size:1.02rem; margin-top:-.4rem; }
.ask-tip { color:var(--muted); font-size:.8rem; font-style:italic; margin-top:-.55rem; margin-bottom:.6rem; }
.greet { font-family:'Cormorant Garamond',Georgia,serif; font-size:2.6rem; font-weight:600; line-height:1.1; margin:0; }
.home-greet, .my-plants-title, .care-greet {
  font-family:'Espuma Pro Book','EspumaPro-Book',sans-serif !important; font-weight:400;
}

/* ── header ── */
.user-chip { display:flex; justify-content:flex-end; padding-top:.4rem; }
.user-chip .av { width:42px; height:42px; border-radius:50%; background:#1f3d2b; color:#fff; display:flex;
  align-items:center; justify-content:center; font-weight:600; margin-left:10px; }
.user-chip .meta { text-align:right; }
.user-chip b { display:block; font-size:.95rem; }
.user-chip span { color:var(--muted); font-size:.8rem; }
.user-chip .garden-name { display:block; color:var(--muted); font-size:.8rem; }
div[class*="st-key-session-idle-note"] [data-testid="stCaptionContainer"],
div[class*="st-key-session-idle-note"] [data-testid="stCaptionContainer"] p {
  text-align:center; font-style:italic;
}
.garden-delete-title { font-family:'Espuma Pro Book','EspumaPro-Book',sans-serif !important;
  font-size:1.22rem !important; font-weight:400 !important; }
div[data-testid="stDialog"] h2, div[role="dialog"] h2 {
  font-family:'Espuma Pro Book','EspumaPro-Book',sans-serif !important; font-weight:400 !important;
}
div[class*="st-key-ask-examples"] [data-testid^="stBaseButton"] {
  min-height:3rem; height:auto; padding:.45rem .65rem; white-space:normal;
}
div[class*="st-key-ask-examples"] [data-testid^="stBaseButton"] p {
  white-space:normal; overflow-wrap:anywhere; line-height:1.2; text-align:center;
}

/* ── stat cards ── */
.stat { display:flex; gap:14px; align-items:center; padding:1rem 1.2rem; border-radius:18px; }
.dashboard-gap { height:1rem; }
.stat .ico { width:54px; height:54px; border-radius:50%; display:flex; align-items:center; justify-content:center;
  font-size:1.5rem; background:rgba(255,255,255,.65); }
.stat .num { font-family:'Espuma Pro Bold','EspumaPro-Bold',sans-serif; font-size:2rem; font-weight:700; line-height:1; }
.stat .lbl { color:#3f4a42; font-size:.95rem; }
.t-mint{background:var(--mint)} .t-amber{background:var(--amber)} .t-sky{background:var(--sky)} .t-lav{background:var(--lav)}

/* ── chips ── */
.chip { display:inline-block; border-radius:999px; padding:.18rem .65rem; font-size:.76rem; font-weight:600; white-space:nowrap; }
.c-green{background:var(--mint);color:var(--green)} .c-amber{background:var(--amber);color:var(--amber-d)}
.c-red{background:var(--red-bg);color:var(--red)} .c-gray{background:#efeee6;color:var(--muted)}
.c-blue{background:var(--sky);color:#3d6a85}

/* ── plant card ── */
.pcard { border:1px solid var(--line); border-radius:16px; padding:.7rem; background:#fff; display:flex; gap:.7rem; min-height:215px; }
.pcard.embedded { position:relative; height:250px; box-sizing:border-box;
  border:0; border-radius:0; padding:0; background:transparent; min-height:0; }
div[class*="st-key-plant-card-"] { border:1px solid var(--line); border-radius:16px; padding:.8rem;
  background:#fff; margin-bottom:.9rem; height:280px; min-height:280px; max-height:280px;
  box-sizing:border-box; overflow:hidden; position:relative; }
div[class*="st-key-plant-card-"] .stVerticalBlock { gap:.5rem !important; }
div[class*="st-key-plant-card-"] .stButton > button { width:100%; }
div[class*="st-key-delete-plant-"] { position:absolute; right:.5rem; bottom:.5rem; z-index:5; }
div[class*="st-key-delete-plant-"] .stButton > button,
div[class*="st-key-delete-plant-"] [data-testid^="stBaseButton"] {
  width:18px !important; height:18px !important; min-height:18px !important; max-height:18px !important;
  padding:0 !important; border-radius:50%; background:rgba(255,255,255,.94);
  border:1px solid var(--line); color:var(--red); font-size:.7rem !important; line-height:18px !important;
  transform:scaleY(1); transform-origin:center;
}
.pcard.embedded .nm, .pcard.embedded .sp,
.pcard.embedded .row b { display:-webkit-box; -webkit-box-orient:vertical; overflow:hidden; }
.pcard.embedded .nm { -webkit-line-clamp:1; }
.pcard.embedded .sp, .pcard.embedded .row b { -webkit-line-clamp:2; }
.pcard.embedded .foot { position:absolute; left:calc(84px + .7rem); bottom:.6rem; margin:0; }
.pcard .pic { width:84px; flex:none; } .pcard .pic img, .pcard .pic .ph { width:84px; height:150px; object-fit:cover;
  border-radius:12px; background:var(--mint); display:flex; align-items:center; justify-content:center; font-size:2rem; }
.pcard .nm { font-weight:600; font-size:1.02rem; } .pcard .sp { color:var(--muted); font-size:.82rem; margin-bottom:.35rem; }
.pcard .row { font-size:.78rem; color:var(--muted); margin-top:.45rem; line-height:1.25; }
.pcard .row b { display:block; color:var(--ink); font-weight:500; }
.pcard .foot { margin-top:.6rem; }

/* ── listas ── */
.trow { display:flex; gap:.8rem; align-items:center; padding:.7rem .4rem; border-top:1px solid var(--line); }
.trow:first-of-type { border-top:none; }
.trow .tic { width:38px; height:38px; border-radius:10px; background:#f3b43c; color:#fff; display:flex;
  align-items:center; justify-content:center; font-size:1.1rem; flex:none; }
.trow .tt { font-weight:600; } .trow .ts { color:var(--muted); font-size:.85rem; }
.trow .plant { display:flex; gap:.5rem; align-items:center; font-size:.82rem; margin-left:auto; min-width:150px; }
.trow .plant img { width:34px; height:34px; object-fit:cover; border-radius:8px; }
div[class*="st-key-panel_tasks"] .trow {
  display:grid; grid-template-columns:38px minmax(0,1fr) minmax(150px,190px) max-content;
}
div[class*="st-key-panel_tasks"] .trow > div:nth-child(2) { min-width:0; }
div[class*="st-key-panel_tasks"] .trow .plant { width:100%; min-width:0; margin-left:0; box-sizing:border-box; }
div[class*="st-key-panel_tasks"] .trow .plant img { flex:none; }
.arow { display:flex; gap:.8rem; align-items:center; padding:.55rem 0; }
.arow .aic { width:44px; height:44px; border-radius:50%; background:#6c8b6e; color:#fff; display:flex;
  align-items:center; justify-content:center; font-size:1.2rem; flex:none; }
.arow .an { font-weight:600; } .arow .ad { color:var(--muted); font-size:.82rem; }
.act { display:flex; gap:.8rem; padding:.55rem 0; }
.act .aic { width:38px; height:38px; border-radius:50%; background:#dfe8ee; display:flex; align-items:center;
  justify-content:center; flex:none; }
.act .at { font-weight:600; } .act .ad { color:var(--muted); font-size:.86rem; } .act .am { color:#8a9187; font-size:.78rem; }
.tip { border-radius:20px; padding:1.4rem 1.6rem; color:#fff; background:linear-gradient(110deg,#33402f 0%,#4f5a43 55%,#7d806a 100%); }
.tip .k { opacity:.85; font-size:.85rem; } .tip h3 { color:#fff; margin:.2rem 0 .3rem; font-size:1.55rem; }
.tip .q { float:right; font-family:'Fraunces',serif; font-size:1.05rem; opacity:.9; text-align:left; max-width:230px; }

/* ── Explanations and flows ── */
.why { background:#f4f8f2; border:1px solid #d9e6d6; border-radius:14px; padding:.8rem 1rem; }
.why p { margin:.15rem 0; }
.flow { border:1px solid var(--line); border-radius:14px; padding:.7rem .9rem; background:#fff; }
.flow .who { font-weight:600; } .flow .what { color:var(--muted); font-size:.9rem; }
.arrow { text-align:center; color:var(--green); font-size:1.1rem; line-height:1; margin:.2rem 0; }
.sess-head { font-family:'Espuma Pro Bold','EspumaPro-Bold',sans-serif; font-size:1.15rem; font-weight:700; }
.ev { padding:.3rem 0; } .ev .pl { color:var(--muted); }
"""
