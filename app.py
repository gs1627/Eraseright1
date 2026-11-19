import html as _html
import importlib
import copy
from collections import Counter

import streamlit as st
import pandas as pd

from database.db import initialize_database

import tools.discovery as discovery_module
import agents.decision_agent as decision_module
import agents.review_agent as review_module
import tools.executor as executor_module
import tools.audit as audit_module
import tools.certificate as certificate_module
import tools.dashboard as dashboard_module
import tools.lifecycle as lifecycle_module


# ---------------- MODULE RELOADING ----------------

for module in [
    discovery_module,
    decision_module,
    review_module,
    executor_module,
    audit_module,
    certificate_module,
    dashboard_module,
    lifecycle_module
]:
    importlib.reload(module)


# ---------------- PAGE CONFIGURATION ----------------

st.set_page_config(
    page_title="EraseRight",
    page_icon="🛡️",
    layout="wide"
)


# ---------------- DATABASE INITIALIZATION ----------------

initialize_database()
audit_module.initialize_audit_table()


# ---------------- CONSTANTS ----------------

P_OVERVIEW = "Overview Dashboard"
P_SUBMIT = "Submit Privacy Request"
P_AI = "AI Decision Analysis"
P_APPROVAL = "Human Approval Centre"
P_LIFECYCLE = "Request Lifecycle"
P_AUDIT = "Audit History"
P_CERT = "Certificates & Reports"

PAGES = [
    (P_OVERVIEW, ":material/dashboard:"),
    (P_SUBMIT, ":material/upload_file:"),
    (P_AI, ":material/psychology:"),
    (P_APPROVAL, ":material/how_to_reg:"),
    (P_LIFECYCLE, ":material/timeline:"),
    (P_AUDIT, ":material/history:"),
    (P_CERT, ":material/verified:"),
]

# Only these actions can ever be approved or sent to the executor.
DESTRUCTIVE_ACTIONS = ("DELETE", "ANONYMIZE")

ERASURE = "Erasure Request"
ACCESS = "Access Request"


# ---------------- SESSION STATE ----------------

defaults = {
    "records": [],
    "decisions": [],
    "request_type": "",
    "request_details": {},
    "review_result": None,
    "review_acknowledged": False,
    "execution_results": [],
    "verification_results": [],
    "execution_completed": False,
    "audit_saved": False,
    "request_id": "",
    # UI-only state
    "active_page": P_OVERVIEW,
    "flash": None,
    "demo_mode": False,
    "demo_step": 0,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =====================================================
#                    STYLING
# =====================================================

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
:root{
--bg:#F5F7FA; --card:#FFFFFF; --primary:#176B87; --accent:#14B8A6;
--text:#172B3A; --muted:#64748B; --ok:#16A34A; --warn:#D97706; --err:#DC2626;
--line:#E2E8F0;
--primary-tint:#E8F3F7; --accent-tint:#E6F7F5; --ok-tint:#E8F6EC;
--warn-tint:#FDF3E3; --err-tint:#FDECEC; --slate-tint:#EEF2F6;
--shadow:0 1px 2px rgba(23,43,58,.04),0 6px 18px rgba(23,43,58,.05);
}
.stApp{background:var(--bg); color:var(--text);}
.stApp, .stApp .stMarkdown, .stApp button, .stApp input, .stApp textarea, .stApp label{
font-family:'Inter',-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
}
[data-testid="stHeader"]{background:transparent;}
#MainMenu, footer, .stDeployButton{visibility:hidden;}
.block-container{padding-top:1.4rem; padding-bottom:3rem; max-width:1320px;}
.stApp button p{color:inherit !important;}

/* ---------- sidebar ---------- */
[data-testid="stSidebar"]{background:#FFFFFF; border-right:1px solid var(--line);}
[data-testid="stSidebar"] .block-container, [data-testid="stSidebarContent"]{padding-top:1rem;}
.er-side-brand{display:flex; align-items:center; gap:12px; padding:4px 4px 18px 4px;}
.er-side-name{font-weight:700; font-size:1.15rem; color:var(--text); line-height:1.2;}
.er-side-sub{font-size:.78rem; color:var(--muted);}
.er-side-label{font-size:.78rem; color:var(--muted); font-weight:500; padding:0 6px 6px 6px;}
.er-side-card{margin-top:22px; padding:14px 16px; border:1px solid var(--line); border-radius:14px; background:var(--bg);}
.er-side-card-title{font-size:.78rem; color:var(--muted); margin-bottom:6px;}
.er-side-card-main{font-weight:600; font-size:.92rem; color:var(--text);}
.er-side-card-sub{font-size:.8rem; color:var(--muted); margin-top:2px;}
[data-testid="stSidebar"] .stButton > button{
justify-content:flex-start; text-align:left; border:1px solid transparent !important;
background:transparent !important; color:var(--text) !important; font-weight:500;
padding:.55rem .8rem; border-radius:10px; box-shadow:none;
}
[data-testid="stSidebar"] .stButton > button:hover{background:var(--slate-tint) !important; color:var(--primary) !important;}
[data-testid="stSidebar"] button[kind="primary"],
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"]{
background:var(--primary-tint) !important; color:var(--primary) !important;
border:1px solid #C9E2EA !important; font-weight:600; box-shadow:inset 3px 0 0 var(--accent);
}

/* ---------- top bar ---------- */
.er-topbar{
display:flex; align-items:center; justify-content:space-between; gap:16px; flex-wrap:wrap;
background:linear-gradient(115deg,#FFFFFF 0%,#F0F8FA 100%); border:1px solid #DCEAF0; border-radius:18px;
padding:16px 22px; box-shadow:var(--shadow); margin-bottom:24px;
}
.er-brand{display:flex; align-items:center; gap:14px;}
.er-name{font-weight:700; font-size:1.3rem; color:var(--text); line-height:1.15;}
.er-tag{font-size:.86rem; color:var(--muted);}
.er-status{
display:inline-flex; align-items:center; gap:8px; background:var(--ok-tint); color:#166534;
border:1px solid #BBE5C8; border-radius:999px; padding:6px 14px; font-size:.84rem; font-weight:600;
}
.er-dot{width:8px; height:8px; border-radius:50%; background:var(--ok); box-shadow:0 0 0 3px rgba(22,163,74,.18);}

/* ---------- page titles ---------- */
.er-page-head{margin:4px 0 22px 0; padding:18px 22px; background:linear-gradient(115deg,#FFFFFF 0%,#F1F8FA 100%); border:1px solid #DCEAF0; border-left:4px solid var(--accent); border-radius:16px; box-shadow:var(--shadow);}
.er-page-title{font-size:1.75rem; font-weight:750; color:var(--text); letter-spacing:-.025em;}
.er-page-sub{color:var(--muted); font-size:.94rem; margin-top:5px;}
.er-section{margin:26px 0 12px 0;}
.er-section-title{font-size:1.08rem; font-weight:650; font-weight:600; color:var(--text);}
.er-section-sub{font-size:.86rem; color:var(--muted); margin-top:2px;}
.er-muted{color:var(--muted);}

/* ---------- cards ---------- */
[class*="st-key-er_card_"]{
background:var(--card); border:1px solid var(--line); border-radius:16px;
padding:20px 22px; box-shadow:var(--shadow);
}
[data-testid="stForm"]{
background:var(--card); border:1px solid var(--line); border-radius:16px;
padding:22px 24px; box-shadow:var(--shadow);
}
[data-testid="stDataFrame"]{border:1px solid var(--line); border-radius:12px; overflow:hidden;}
[data-testid="stAlert"]{border-radius:12px;}
.er-panel{background:var(--card); border:1px solid var(--line); border-radius:16px; padding:20px 22px; box-shadow:var(--shadow);}
.er-panel-title{font-weight:600; font-size:1rem; margin-bottom:10px; color:var(--text);}
.er-steps-list{display:flex; flex-direction:column; gap:14px; margin-top:6px;}
.er-steps-item{display:flex; gap:12px; align-items:flex-start;}
.er-steps-num{
flex:0 0 26px; height:26px; border-radius:50%; background:var(--primary-tint); color:var(--primary);
display:flex; align-items:center; justify-content:center; font-size:.8rem; font-weight:600;
}
.er-steps-text{font-size:.9rem; color:var(--text);}
.er-steps-text span{display:block; color:var(--muted); font-size:.82rem;}

/* ---------- inputs & buttons ---------- */
.stTextInput input, .stSelectbox [data-baseweb="select"] > div{
background:#FFFFFF !important; border:1px solid var(--line) !important; border-radius:10px !important; color:var(--text) !important;
}
.stTextInput input:focus{border-color:var(--primary) !important; box-shadow:0 0 0 3px rgba(23,107,135,.15) !important;}
.stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] > button{
border-radius:10px; font-weight:600; border:1px solid var(--line); background:#FFFFFF; color:var(--text);
transition:border-color .15s ease, color .15s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover{border-color:var(--primary); color:var(--primary);}
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"],
[data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primaryFormSubmit"],
button[kind="primaryFormSubmit"]{
background:var(--primary) !important; color:#FFFFFF !important; border:1px solid var(--primary) !important;
}
.stButton > button[kind="primary"]:hover, [data-testid="stBaseButton-primary"]:hover{background:#125A73 !important; color:#FFFFFF !important;}
.stButton > button:disabled{opacity:.5;}

/* ---------- metric tiles ---------- */
.er-tiles{display:grid; grid-template-columns:repeat(auto-fit,minmax(215px,1fr)); gap:14px;}
.er-tile{
display:flex; align-items:center; gap:14px; background:var(--card); border:1px solid var(--line);
border-radius:16px; padding:16px 18px; box-shadow:var(--shadow);
transition:transform .16s ease, box-shadow .16s ease, border-color .16s ease;
}
.er-tile:hover{transform:translateY(-2px); border-color:#C8DFE7; box-shadow:0 8px 24px rgba(23,43,58,.08);}
.er-ico{flex:0 0 42px; height:42px; border-radius:12px; display:flex; align-items:center; justify-content:center;}
.er-primary{background:var(--primary-tint); color:var(--primary);}
.er-accent{background:var(--accent-tint); color:#0F8F82;}
.er-ok{background:var(--ok-tint); color:var(--ok);}
.er-warn{background:var(--warn-tint); color:var(--warn);}
.er-err{background:var(--err-tint); color:var(--err);}
.er-slate{background:var(--slate-tint); color:var(--muted);}
.er-tile-val{font-size:1.65rem; font-weight:700; line-height:1.1; color:var(--text);}
.er-tile-lbl{font-size:.84rem; color:var(--muted); margin-top:2px;}

/* ---------- badges ---------- */
.er-badge{
display:inline-block; padding:3px 11px; border-radius:999px; font-size:.74rem; font-weight:600;
border:1px solid transparent; white-space:nowrap; letter-spacing:.01em;
}
.er-badge.er-primary{border-color:#C9E2EA;}
.er-badge.er-accent{border-color:#B8EBE5;}
.er-badge.er-ok{border-color:#BBE5C8;}
.er-badge.er-warn{border-color:#F3D9AE;}
.er-badge.er-err{border-color:#F6C4C4;}
.er-badge.er-slate{border-color:var(--line);}

/* ---------- progress bars & donut ---------- */
.er-bar{margin-bottom:16px;}
.er-bar-top{display:flex; justify-content:space-between; font-size:.88rem; margin-bottom:6px; color:var(--text);}
.er-bar-num{font-weight:600;}
.er-track{height:9px; background:var(--slate-tint); border-radius:999px; overflow:hidden;}
.er-fill{height:100%; border-radius:999px;}
.er-bg-primary{background:var(--primary);}
.er-bg-accent{background:var(--accent);}
.er-bg-ok{background:var(--ok);}
.er-bg-err{background:var(--err);}
.er-bg-warn{background:var(--warn);}
.er-donut-wrap{display:flex; align-items:center; gap:22px; flex-wrap:wrap;}
.er-donut{width:130px; height:130px; border-radius:50%; display:flex; align-items:center; justify-content:center;}
.er-donut-in{
width:92px; height:92px; border-radius:50%; background:#FFFFFF; display:flex; flex-direction:column;
align-items:center; justify-content:center;
}
.er-donut-in b{font-size:1.35rem; color:var(--text);}
.er-donut-in span{font-size:.74rem; color:var(--muted);}
.er-legend{display:flex; flex-direction:column; gap:8px; font-size:.88rem;}
.er-legend i{display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:8px;}

/* ---------- decision cards ---------- */
.er-dcard{
background:var(--card); border:1px solid var(--line); border-left:4px solid var(--line);
border-radius:14px; padding:18px 20px; box-shadow:var(--shadow); margin-bottom:14px;
transition:box-shadow .16s ease, transform .16s ease;
}
.er-dcard:hover{box-shadow:0 8px 22px rgba(23,43,58,.07); transform:translateY(-1px);}
.er-dcard.t-err{border-left-color:var(--err);}
.er-dcard.t-primary{border-left-color:var(--primary);}
.er-dcard.t-ok{border-left-color:var(--ok);}
.er-dcard.t-warn{border-left-color:var(--warn);}
.er-dhead, .er-arow{display:flex; justify-content:space-between; align-items:flex-start; gap:12px; flex-wrap:wrap;}
.er-dtitle{font-weight:600; font-size:1rem; color:var(--text);}
.er-dmeta{font-size:.84rem; color:var(--muted); margin-top:2px;}
.er-dbadges{display:flex; gap:8px; flex-wrap:wrap;}
.er-grid2{display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:18px; margin-top:14px;}
.er-lbl{font-size:.78rem; color:var(--muted); font-weight:500; margin-bottom:4px;}
.er-val{font-size:.9rem; color:var(--text); line-height:1.5;}
.er-quote{
font-size:.88rem; color:var(--text); line-height:1.5; background:var(--bg);
border:1px solid var(--line); border-radius:10px; padding:10px 12px;
}
.er-reason{font-size:.9rem; color:var(--text); line-height:1.5; margin:10px 0 4px 0;}
.er-dcard details{margin-top:12px; border-top:1px solid var(--line); padding-top:10px;}
.er-dcard summary{cursor:pointer; font-size:.86rem; font-weight:600; color:var(--primary);}
.er-dcard details div{font-size:.88rem; line-height:1.55; margin-top:8px; color:var(--text);}
.er-foot{font-size:.78rem; color:var(--muted); margin-top:10px;}

/* ---------- review agent ---------- */
.er-flow{display:flex; align-items:stretch; gap:10px; flex-wrap:wrap; margin-bottom:6px;}
.er-flow-step{
flex:1; min-width:180px; border:1px solid var(--line); border-radius:12px; padding:10px 14px; background:#FFFFFF;
}
.er-flow-step b{display:block; font-size:.88rem; color:var(--text);}
.er-flow-step span{font-size:.8rem; color:var(--muted);}
.er-flow-step.review{border-color:#B8EBE5; background:var(--accent-tint);}
.er-flow-sep{align-self:center; color:var(--muted); font-size:1.1rem;}
.er-issue{
background:var(--warn-tint); border:1px solid #F3D9AE; border-radius:10px;
padding:10px 14px; font-size:.88rem; margin-bottom:8px; color:var(--text);
}
.er-risk{
background:var(--err-tint); border:1px solid #F6C4C4; border-radius:10px;
padding:10px 14px; font-size:.88rem; margin-bottom:8px; color:var(--text);
}
.er-note{
background:var(--primary-tint); border:1px solid #C9E2EA; border-radius:10px;
padding:10px 14px; font-size:.86rem; color:var(--text); margin-top:10px;
}

/* ---------- lifecycle ---------- */
.er-step{display:flex; gap:16px; position:relative; padding-bottom:14px;}
.er-step:last-child{padding-bottom:0;}
.er-step:not(:last-child)::before{
content:""; position:absolute; left:17px; top:38px; bottom:-2px; width:2px; background:var(--line);
}
.er-step.done:not(:last-child)::before{background:var(--ok);}
.er-node{
flex:0 0 36px; height:36px; border-radius:50%; display:flex; align-items:center; justify-content:center;
font-weight:600; font-size:.85rem; border:2px solid var(--line); background:#FFFFFF; color:var(--muted); z-index:1;
}
.er-step.done .er-node{background:var(--ok); border-color:var(--ok); color:#FFFFFF;}
.er-step.prog .er-node{border-color:var(--primary); color:var(--primary); background:var(--primary-tint); box-shadow:0 0 0 4px rgba(23,107,135,.12);}
.er-step.rev .er-node{border-color:var(--err); color:var(--err); background:var(--err-tint);}
.er-step.na .er-node{border-style:dashed;}
.er-step-body{
flex:1; background:var(--card); border:1px solid var(--line); border-radius:12px; padding:12px 16px;
display:flex; justify-content:space-between; align-items:center; gap:12px; flex-wrap:wrap;
}
.er-step-title{font-weight:600; font-size:.95rem; color:var(--text);}
.er-step-desc{font-size:.84rem; color:var(--muted); margin-top:2px;}
.er-mini{display:grid; grid-template-columns:repeat(auto-fit,minmax(118px,1fr)); gap:10px;}
.er-mini-item{background:var(--card); border:1px solid var(--line); border-top:3px solid var(--line); border-radius:12px; padding:10px 12px;}
.er-mini-item.done{border-top-color:var(--ok);}
.er-mini-item.prog{border-top-color:var(--primary);}
.er-mini-item.rev{border-top-color:var(--err);}
.er-mini-title{font-size:.8rem; font-weight:600; color:var(--text); min-height:2.2em;}
.er-mini-status{font-size:.74rem; color:var(--muted); margin-top:4px;}

/* ---------- misc ---------- */
.er-empty{
background:var(--card); border:1px dashed #CBD5E1; border-radius:16px; padding:34px 24px; text-align:center;
}
.er-empty b{display:block; font-size:1rem; color:var(--text); margin-bottom:4px;}
.er-empty span{font-size:.9rem; color:var(--muted);}
.er-summary{display:flex; gap:28px; flex-wrap:wrap;}
.er-summary div b{display:block; font-size:.78rem; color:var(--muted); font-weight:500;}
.er-summary div span{font-size:.95rem; font-weight:600; color:var(--text);}
.er-footer{margin-top:36px; padding-top:16px; border-top:1px solid var(--line); font-size:.8rem; color:var(--muted); line-height:1.6;}
</style>
"""


# =====================================================
#                  UI HELPERS
# =====================================================

def md(markup):
    """Render an HTML snippet. Lines are stripped so Markdown never treats
    indentation as a code block."""
    flat = " ".join(line.strip() for line in markup.strip().splitlines())
    st.markdown(flat, unsafe_allow_html=True)


def esc(value):
    text = "" if value is None else str(value)
    return _html.escape(text).replace("$", "&#36;")


def fmt_text(value, empty="Not provided"):
    """Safely turn strings, lists and dicts into HTML."""
    if value is None or value == "" or value == [] or value == {}:
        return f'<span class="er-muted">{esc(empty)}</span>'

    if isinstance(value, dict):
        return "<br>".join(
            f"<b>{esc(k)}:</b> {esc(v)}" for k, v in value.items()
        )

    if isinstance(value, (list, tuple)):
        return "<br>".join(f"• {fmt_text(item)}" for item in value)

    return esc(value).replace("\n", "<br>")


ICONS = {
    "requests": '<path d="M5 4h10l4 4v12H5z"/><path d="M15 4v4h4"/><path d="M9 13h6M9 17h6"/>',
    "records": '<ellipse cx="12" cy="6" rx="7" ry="3"/><path d="M5 6v6c0 1.7 3.1 3 7 3s7-1.3 7-3V6"/><path d="M5 12v6c0 1.7 3.1 3 7 3s7-1.3 7-3v-6"/>',
    "approved": '<circle cx="12" cy="12" r="9"/><path d="m8 12.5 3 3 5-6"/>',
    "delete": '<path d="M4 7h16"/><path d="M9 7V4h6v3"/><path d="M6 7l1 13h10l1-13"/>',
    "anonymize": '<path d="M3 12s3.5-6 9-6 9 6 9 6-3.5 6-9 6-9-6-9-6z"/><circle cx="12" cy="12" r="2.5"/><path d="M4 20 20 4"/>',
    "verified": '<path d="M12 3 5 6v5c0 4.5 3 8 7 10 4-2 7-5.5 7-10V6z"/><path d="m9 12 2.2 2.2L15 10"/>',
    "pending": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "rejected": '<circle cx="12" cy="12" r="9"/><path d="m9 9 6 6M15 9l-6 6"/>',
    "failed": '<path d="M12 4 3 20h18z"/><path d="M12 10v4M12 17v.5"/>',
    "check": '<path d="m5 12.5 4.5 4.5L19 7.5"/>',
}


def svg(name, size=20, stroke=1.8):
    path = ICONS.get(name, "")
    return (
        f'<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" '
        f'stroke="currentColor" stroke-width="{stroke}" stroke-linecap="round" '
        f'stroke-linejoin="round">{path}</svg>'
    )


def logo(size=44):
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 40 40" fill="none">'
        '<rect width="40" height="40" rx="11" fill="#176B87"/>'
        '<path d="M20 8.5 29 12v7.2c0 5.3-3.6 9.6-9 11.3-5.4-1.7-9-6-9-11.3V12l9-3.5z" '
        'fill="#FFFFFF" stroke="#FFFFFF" stroke-width="1.6" stroke-linejoin="round"/>'
        '<path d="m15.6 20.2 3.2 3.2 5.6-6.4" stroke="#14B8A6" stroke-width="2.4" '
        'stroke-linecap="round" stroke-linejoin="round"/></svg>'
    )


def badge(text, tone):
    return f'<span class="er-badge er-{tone}">{esc(text)}</span>'


ACTION_TONES = {
    "DELETE": "err",
    "ANONYMIZE": "primary",
    "RETAIN": "ok",
    "REVIEW_REQUIRED": "warn",
}

STATUS_TONES = {
    "APPROVED": "ok",
    "REJECTED": "err",
    "PENDING": "warn",
    "RETENTION_CONFIRMED": "ok",
    "FLAGGED_FOR_REVIEW": "warn",
}


def action_tone(action):
    key = str(action or "").upper().replace(" ", "_")
    return ACTION_TONES.get(key, "slate")


def action_badge(action):
    label = str(action or "UNKNOWN").upper().replace("_", " ")
    return badge(label, action_tone(action))


def status_badge(status):
    key = str(status or "PENDING").upper().replace(" ", "_")
    return badge(key.replace("_", " "), STATUS_TONES.get(key, "slate"))


def page_header(title, subtitle):
    md(
        f'<div class="er-page-head"><div class="er-page-title">{esc(title)}</div>'
        f'<div class="er-page-sub">{esc(subtitle)}</div></div>'
    )


def section_title(title, sub=""):
    sub_html = f'<div class="er-section-sub">{esc(sub)}</div>' if sub else ""
    md(
        f'<div class="er-section"><div class="er-section-title">{esc(title)}</div>'
        f"{sub_html}</div>"
    )


def empty_state(title, text):
    md(f'<div class="er-empty"><b>{esc(title)}</b><span>{esc(text)}</span></div>')


def card(key):
    """Keyed container styled as a white card. Falls back gracefully on
    Streamlit versions that do not support container keys."""
    try:
        return st.container(key=f"er_card_{key}")
    except TypeError:
        return st.container(border=True)


def tiles(items):
    cells = []
    for label, value, tone, icon in items:
        cells.append(
            f'<div class="er-tile"><div class="er-ico er-{tone}">{svg(icon)}</div>'
            f'<div><div class="er-tile-val">{esc(value)}</div>'
            f'<div class="er-tile-lbl">{esc(label)}</div></div></div>'
        )
    md(f'<div class="er-tiles">{"".join(cells)}</div>')


def progress_rows(rows):
    total = sum(value for _, value, _ in rows)
    out = []
    for label, value, tone in rows:
        pct = (value / total * 100) if total else 0
        out.append(
            f'<div class="er-bar"><div class="er-bar-top"><span>{esc(label)}</span>'
            f'<span class="er-bar-num">{value} <span class="er-muted">({pct:.0f}%)</span></span></div>'
            f'<div class="er-track"><div class="er-fill er-bg-{tone}" style="width:{pct:.1f}%"></div></div></div>'
        )
    return "".join(out)


def bar_chart(df, color="#14B8A6"):
    try:
        st.bar_chart(df, color=color, height=250)
    except TypeError:
        st.bar_chart(df)


def go_to(page):
    st.session_state["active_page"] = page


def start_guided_demo():
    """Load a fictional, read-only scenario. No database mutation or execution occurs."""
    ss = st.session_state
    if not ss.get("demo_mode"):
        backup_keys = [
            "records", "decisions", "request_type", "request_details",
            "review_result", "review_acknowledged", "execution_results",
            "verification_results", "execution_completed", "audit_saved",
            "request_id", "active_page", "flash",
        ]
        ss["demo_backup"] = {key: copy.deepcopy(ss.get(key)) for key in backup_keys}

    ss["demo_mode"] = True
    ss["demo_step"] = 0
    ss["request_type"] = ERASURE
    ss["request_details"] = {
        "name": "Alex Demo",
        "email": "alex.demo@example.test",
        "customer_id": "DEMO-1001",
        "request_type": ERASURE,
    }
    ss["records"] = [
        {
            "id": "DEMO-001", "name": "Alex Demo", "email": "alex.demo@example.test",
            "customer_id": "DEMO-1001", "data_type": "Customer Profile",
            "source": "Customer DB", "match_status": "EXACT MATCH",
            "identity_evidence": "Email and customer ID agree",
            "description": "Fictional customer profile; no retention hold is present in this scenario.",
        },
        {
            "id": "DEMO-002", "name": "Alex Demo", "email": "alex.demo@example.test",
            "customer_id": "DEMO-1001", "data_type": "Support Ticket",
            "source": "Support DB", "match_status": "EXACT MATCH",
            "identity_evidence": "Email and customer ID agree",
            "description": "Fictional support ticket; the scenario allows a non-identifying analytics copy.",
        },
        {
            "id": "DEMO-003", "name": "Alex D.", "email": "unknown@example.test",
            "customer_id": "UNKNOWN", "data_type": "Archived Record",
            "source": "Archive DB", "match_status": "POSSIBLE MATCH",
            "identity_evidence": "Identifiers are incomplete or conflicting; manual verification required",
            "description": "Fictional archive record with uncertain identity; no destructive action is safe.",
        },
    ]

    # These are deliberately labelled as demo-fixture passages, not real law or
    # the organisation's actual retention policy. They demonstrate the RAG flow.
    ss["decisions"] = decision_module.build_demo_decisions(ss["records"])
    ss["review_result"] = {
        "status": "PASSED",
        "summary": (
            "Independent safeguard review passed. Two exact-match records have policy-fixture-based "
            "proposals for human consideration; the uncertain archive match is blocked from execution."
        ),
        "issues": [
            "DEMO-003 is a possible identity match and must be verified before any action."
        ],
        "recommendations": [
            {"record_id": "DEMO-001", "recommendation": "Review the illustrative deletion proposal and approve only after checking the real policy."},
            {"record_id": "DEMO-002", "recommendation": "Confirm the anonymization method removes direct and indirect identifiers."},
            {"record_id": "DEMO-003", "recommendation": "Keep on hold; resolve identity mismatch manually."},
        ],
        "risks": [
            "Demo policy passages are illustrative fixtures, not legal advice or an actual organisational policy.",
            "No live LLM call, database write, deletion, anonymization, audit insert or certificate issuance occurs in Demo Mode.",
        ],
    }
    ss["review_acknowledged"] = False
    ss["execution_results"] = []
    ss["verification_results"] = []
    ss["execution_completed"] = False
    ss["audit_saved"] = False
    ss["request_id"] = "DEMO-ER-2026-001"
    ss.pop("execute_confirmation", None)
    ss["active_page"] = P_AI


def advance_demo_step():
    pages = [P_AI, P_APPROVAL, P_LIFECYCLE, P_AUDIT, P_CERT]
    ss = st.session_state
    next_step = min(ss.get("demo_step", 0) + 1, len(pages) - 1)
    ss["demo_step"] = next_step
    ss["active_page"] = pages[next_step]


def reset_demo():
    ss = st.session_state
    backup = ss.pop("demo_backup", {})
    for key, value in backup.items():
        ss[key] = value
    ss["demo_mode"] = False
    ss["demo_step"] = 0
    ss.pop("execute_confirmation", None)
    if not backup:
        ss["active_page"] = P_OVERVIEW


def goto_button(label, page, key, primary=True):
    st.button(
        label,
        key=key,
        type="primary" if primary else "secondary",
        on_click=go_to,
        args=(page,),
    )


# =====================================================
#                  DATA HELPERS
# =====================================================

def destructive_pending(decisions):
    return sum(
        1 for d in decisions
        if d.get("action") in DESTRUCTIVE_ACTIONS
        and d.get("approval_status", "PENDING") == "PENDING"
    )


def destructive_approved(decisions):
    return [
        d for d in decisions
        if d.get("action") in DESTRUCTIVE_ACTIONS
        and d.get("approval_status") == "APPROVED"
    ]


def build_lifecycle():
    """Nine-stage tracker built on lifecycle_module.get_request_lifecycle.
    Stage statuses come from real session/database state only."""

    ss = st.session_state

    base = lifecycle_module.get_request_lifecycle(
        records=ss["records"],
        decisions=ss["decisions"],
        execution_results=ss["execution_results"],
        verification_results=ss["verification_results"],
        execution_completed=ss["execution_completed"],
        audit_saved=ss["audit_saved"]
    )

    by_name = {item["stage"]: item for item in base}
    has_request = bool(ss["request_details"])
    is_access = ss["request_type"] == ACCESS

    def pick(source_name, title):
        item = by_name.get(source_name)
        if not item:
            return {"stage": title, "status": "PENDING", "description": "Waiting."}
        return {
            "stage": title,
            "status": item["status"],
            "description": item["description"],
        }

    stages = [
        pick("Request Submitted", "Request Submitted"),
        pick("Record Discovery", "Record Discovery"),
        pick("AI Decision Analysis", "AI Decision"),
    ]

    if not has_request:
        stages[0] = {
            "stage": "Request Submitted",
            "status": "PENDING",
            "description": "No request has been submitted yet.",
        }

    review = ss["review_result"]

    if not has_request:
        review_stage = {
            "stage": "Independent AI Review",
            "status": "PENDING",
            "description": "Waiting for a request.",
        }
    elif is_access:
        review_stage = {
            "stage": "Independent AI Review",
            "status": "NOT REQUIRED",
            "description": "Independent review applies to erasure requests only.",
        }
    elif review:
        if review.get("status") == "PASSED":
            review_stage = {
                "stage": "Independent AI Review",
                "status": "COMPLETED",
                "description": "Review Agent passed the proposed decisions.",
            }
        else:
            review_stage = {
                "stage": "Independent AI Review",
                "status": "REVIEW REQUIRED",
                "description": "Review Agent flagged issues for human attention.",
            }
    else:
        review_stage = {
            "stage": "Independent AI Review",
            "status": "PENDING",
            "description": "Waiting for the independent review.",
        }

    stages.append(review_stage)

    stages.append(pick("Human Approval", "Human Approval"))
    stages.append(pick("Action Execution", "Execution"))
    stages.append(pick("Post-Execution Verification", "Verification"))

    if ss["audit_saved"]:
        stages.append({
            "stage": "Audit Logging",
            "status": "COMPLETED",
            "description": f"Audit log saved (request {str(ss['request_id'])[:8]}).",
        })
        stages.append({
            "stage": "Certificate Generation",
            "status": "COMPLETED",
            "description": "Erasure certificate is available for download.",
        })
    else:
        stages.append({
            "stage": "Audit Logging",
            "status": "PENDING",
            "description": "Waiting for completed processing.",
        })
        stages.append({
            "stage": "Certificate Generation",
            "status": "PENDING",
            "description": "Available after audit logging.",
        })

    # Access requests never go through approval, execution or audit.
    if has_request and is_access:
        for index in (4, 5, 6, 7, 8):
            stages[index] = {
                "stage": stages[index]["stage"],
                "status": "NOT REQUIRED",
                "description": "Not applicable to access requests.",
            }

    return stages


LIFECYCLE_CLASS = {
    "COMPLETED": "done",
    "IN PROGRESS": "prog",
    "REVIEW REQUIRED": "rev",
    "NOT REQUIRED": "na",
    "PENDING": "",
}

LIFECYCLE_TONE = {
    "COMPLETED": "ok",
    "IN PROGRESS": "primary",
    "REVIEW REQUIRED": "err",
    "NOT REQUIRED": "slate",
    "PENDING": "slate",
}


def render_timeline(stages):
    rows = []
    for number, stage in enumerate(stages, start=1):
        status = stage["status"]
        css = LIFECYCLE_CLASS.get(status, "")
        tone = LIFECYCLE_TONE.get(status, "slate")
        node = svg("check", 16, 2.6) if status == "COMPLETED" else str(number)
        rows.append(
            f'<div class="er-step {css}"><div class="er-node">{node}</div>'
            f'<div class="er-step-body"><div><div class="er-step-title">{esc(stage["stage"])}</div>'
            f'<div class="er-step-desc">{esc(stage["description"])}</div></div>'
            f'{badge(status, tone)}</div></div>'
        )
    md(f'<div>{"".join(rows)}</div>')


def render_mini_lifecycle(stages):
    items = []
    for stage in stages:
        status = stage["status"]
        css = LIFECYCLE_CLASS.get(status, "")
        items.append(
            f'<div class="er-mini-item {css}"><div class="er-mini-title">{esc(stage["stage"])}</div>'
            f'<div class="er-mini-status">{esc(status.title())}</div></div>'
        )
    md(f'<div class="er-mini">{"".join(items)}</div>')


# =====================================================
#                REQUEST PROCESSING
# =====================================================

def process_request(request_type, name, email, customer_id):
    """Original discovery -> decision -> independent review workflow.
    Returns True when the request was processed."""

    try:
        with st.spinner("Discovering personal records..."):

            records = discovery_module.discover_records(
                name=name,
                email=email,
                customer_id=customer_id
            )

        # Strong identity matching: an identifier match is not enough when
        # another supplied identifier conflicts with the record.
        requested_email = (email or "").strip().casefold()
        requested_id = (customer_id or "").strip().casefold()

        for record in records:
            record_email = (record.get("email") or "").strip().casefold()
            record_id = str(record.get("customer_id") or "").strip().casefold()

            email_match = bool(requested_email and record_email and requested_email == record_email)
            id_match = bool(requested_id and record_id and requested_id == record_id)
            email_conflict = bool(requested_email and record_email and requested_email != record_email)
            id_conflict = bool(requested_id and record_id and requested_id != record_id)

            exact_match = (email_match or id_match) and not (email_conflict or id_conflict)
            record["match_status"] = "EXACT MATCH" if exact_match else "POSSIBLE MATCH"
            record["identity_evidence"] = (
                "Email and customer ID agree" if email_match and id_match
                else "One stable identifier matches and no supplied identifier conflicts" if exact_match
                else "Identifiers are incomplete or conflicting; manual verification required"
            )

        st.session_state["records"] = records

        st.session_state["request_type"] = request_type

        st.session_state["request_details"] = {
            "name": name,
            "email": email,
            "customer_id": customer_id,
            "request_type": request_type
        }

        # Reset previous request state
        st.session_state["decisions"] = []
        st.session_state["review_result"] = None
        st.session_state["review_acknowledged"] = False

        st.session_state["execution_results"] = []
        st.session_state["verification_results"] = []

        st.session_state["execution_completed"] = False
        st.session_state["audit_saved"] = False
        st.session_state["request_id"] = ""

        # Any earlier execution confirmation must never carry over.
        st.session_state.pop("execute_confirmation", None)

        if records and request_type == ERASURE:

            with st.spinner("Retrieving policy evidence and generating AI decision analysis..."):

                decisions = decision_module.decide_actions(
                    records,
                    request_type=request_type
                )

            for decision in decisions:

                record = next(
                    (
                        r for r in records
                        if r["id"] == decision["record_id"]
                    ),
                    None
                )

                if record and record["match_status"] != "EXACT MATCH":

                    decision["action"] = "REVIEW_REQUIRED"
                    decision["approval_status"] = "FLAGGED_FOR_REVIEW"
                    decision["reason"] = (
                        "Identity is uncertain or identifiers conflict. "
                        "No deletion or anonymization is permitted until a human verifies the subject."
                    )
                    decision["risk_flags"] = list(decision.get("risk_flags") or []) + [
                        "Identity verification required"
                    ]
                    decision["next_step"] = "Verify identity using an authoritative identifier before reconsidering this record."

            st.session_state["decisions"] = decisions

        elif records and request_type == ACCESS:
            # Access requests only produce a data-access report. They must never
            # receive destructive AI proposals or enter the erasure workflow.
            st.session_state["decisions"] = []

            # ---------------- INDEPENDENT REVIEW ----------------

            if request_type == ERASURE:

                policy_evidence = [
                    {
                        "record_id": decision.get("record_id"),
                        "evidence": decision.get("policy_evidence")
                    }
                    for decision in decisions
                    if decision.get("policy_evidence")
                ]

                with st.spinner(
                    "Independent Review Agent is checking decisions..."
                ):

                    review_result = review_module.review_decisions(
                        records=records,
                        decisions=decisions,
                        policy_evidence=policy_evidence
                    )

                st.session_state["review_result"] = review_result

        return True

    except Exception as error:
        st.error(f"The request could not be processed: {error}")
        return False


def run_execution():
    """Original execution -> verification -> audit logging workflow.
    Only approved DELETE / ANONYMIZE decisions ever reach the executor."""

    ss = st.session_state

    # Defence in depth: Demo Mode must never reach the real executor.
    if ss.get("demo_mode"):
        return

    # Hard gates: erasure request, review acknowledged, not already executed.
    if (
        ss["request_type"] != ERASURE
        or not ss["review_acknowledged"]
        or ss["execution_completed"]
    ):
        return

    executable = destructive_approved(ss["decisions"])

    if not executable:
        return

    with st.spinner("Executing actions and verifying results..."):

        results = executor_module.execute_approved_actions(executable)

        verification = executor_module.verify_execution(results)

        ss["execution_results"] = results
        ss["verification_results"] = verification

        details = ss["request_details"]

        request_id = audit_module.save_audit_log(
            requester_name=details["name"],
            requester_email=details["email"],
            customer_id=details["customer_id"],
            request_type=details["request_type"],
            decisions=ss["decisions"],
            execution_results=results,
            verification_results=verification
        )

        ss["request_id"] = request_id
        ss["audit_saved"] = True
        ss["execution_completed"] = True


# =====================================================
#                  SHARED RENDERERS
# =====================================================

def render_topbar():
    md(
        f'<div class="er-topbar"><div class="er-brand">{logo(46)}'
        '<div><div class="er-name">EraseRight</div>'
        '<div class="er-tag">Intelligent Data Subject Request Fulfilment System</div></div></div>'
        '<div class="er-status"><span class="er-dot"></span>AI Protection Active</div></div>'
    )


def render_sidebar():
    ss = st.session_state

    with st.sidebar:

        md(
            f'<div class="er-side-brand">{logo(38)}<div><div class="er-side-name">EraseRight</div>'
            '<div class="er-side-sub">Privacy request operations</div></div></div>'
        )

        if st.button(
            "▶ Start Guided Demo",
            key="start_guided_demo",
            type="primary",
            use_container_width=True,
        ):
            start_guided_demo()
            st.rerun()

        if ss.get("demo_mode"):
            demo_pages = [P_AI, P_APPROVAL, P_LIFECYCLE, P_AUDIT, P_CERT]
            demo_names = ["AI Decision Analysis", "Human Approval Centre", "Request Lifecycle", "Audit History", "Certificates & Reports"]
            step = ss.get("demo_step", 0)
            md('<div class="er-side-label">Guided demo · synthetic data</div>')
            st.caption(f"Step {step + 1} of {len(demo_pages)}: {demo_names[step]}")
            if step < len(demo_pages) - 1:
                st.button("Next demo step →", key="next_demo_step", use_container_width=True, on_click=advance_demo_step)
            else:
                st.success("Demo walkthrough complete.")
            st.button("Exit demo", key="exit_demo", use_container_width=True, on_click=reset_demo)

        md('<div class="er-side-label">Workspace</div>')

        for index, (label, icon) in enumerate(PAGES):

            options = dict(
                key=f"nav_{index}",
                use_container_width=True,
                type="primary" if ss["active_page"] == label else "secondary",
                on_click=go_to,
                args=(label,),
            )

            try:
                st.button(label, icon=icon, **options)
            except Exception:
                st.button(label, **options)

        # Current request summary
        details = ss["request_details"]

        if not details:
            main = "No active request"
            sub = "Submit a privacy request to begin."
        else:
            if ss["audit_saved"]:
                state = "Completed"
            elif ss["execution_completed"]:
                state = "Executed"
            else:
                state = "In progress"

            main = f"{state}: {details.get('request_type', '')}"
            pending = destructive_pending(ss["decisions"])
            sub = (
                f"{esc(details.get('name', ''))}. "
                f"{len(ss['records'])} records, {pending} awaiting approval."
            )

        md(
            '<div class="er-side-card"><div class="er-side-card-title">Current request</div>'
            f'<div class="er-side-card-main">{esc(main)}</div>'
            f'<div class="er-side-card-sub">{sub if details else esc(sub)}</div></div>'
        )


def render_footer():
    md(
        '<div class="er-footer">EraseRight. Intelligent Data Subject Request Fulfilment System.<br>'
        "Demonstration using synthetic data. Human approval is required before erasure "
        "execution. This prototype does not establish legal compliance.</div>"
    )


def records_frame(group, action_by_id):
    df = pd.DataFrame(group)

    if "id" in df.columns and action_by_id:
        df["proposed_action"] = df["id"].map(action_by_id)

    if "match_status" in df.columns:
        ordered = ["match_status"] + [c for c in df.columns if c != "match_status"]
        df = df[ordered]

    return df


def render_discovery(records, decisions):
    action_by_id = {d.get("record_id"): d.get("action") for d in decisions}

    exact, possible, uncertain = [], [], []

    for record in records:

        action = action_by_id.get(record.get("id"))

        if action is not None and action not in (*DESTRUCTIVE_ACTIONS, "RETAIN"):
            uncertain.append(record)
        elif record.get("match_status") == "POSSIBLE MATCH":
            possible.append(record)
        else:
            exact.append(record)

    tiles([
        ("Records discovered", len(records), "primary", "records"),
        ("Exact identity matches", len(exact), "ok", "approved"),
        ("Possible identity matches", len(possible), "warn", "pending"),
        ("Uncertain, verification needed", len(uncertain), "err", "failed"),
    ])

    groups = [
        (
            "Exact identity matches",
            "Matched on email or customer ID. Eligible for AI action proposals.",
            exact,
            "ok",
        ),
        (
            "Possible identity matches",
            "No email or customer ID match. Held for human verification and never deleted automatically.",
            possible,
            "warn",
        ),
        (
            "Uncertain records requiring verification",
            "The AI could not reach a firm DELETE, ANONYMIZE or RETAIN decision.",
            uncertain,
            "err",
        ),
    ]

    for title, sub, group, tone in groups:

        section_title(title, sub)

        if group:
            st.dataframe(
                records_frame(group, action_by_id),
                use_container_width=True,
                hide_index=True
            )
        else:
            md(f'<div class="er-muted" style="font-size:.9rem">No records in this category.</div>')


def render_execution_results(prefix):
    results = st.session_state["execution_results"]
    verification = st.session_state["verification_results"]

    section_title("Execution results")

    if results:
        st.dataframe(
            pd.DataFrame(results),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No approved actions were executed.")

    section_title("Post-execution verification")

    if verification:

        st.dataframe(
            pd.DataFrame(verification),
            use_container_width=True,
            hide_index=True
        )

        verified_count = sum(
            1 for item in verification
            if item.get("verification") == "VERIFIED"
        )

        failed_count = sum(
            1 for item in verification
            if item.get("verification") == "FAILED"
        )

        tiles([
            ("Verified", verified_count, "ok", "verified"),
            ("Failed", failed_count, "err", "failed"),
        ])

    else:
        st.info("No verification results are available.")


def render_access_report(key):
    records = st.session_state["records"]

    if st.session_state["request_type"] != ACCESS or not records:
        return

    section_title(
        "Access request report",
        "Download the personal data discovered for this access request."
    )

    report = pd.DataFrame(records)

    st.download_button(
        label="Download Access Report (CSV)",
        data=report.to_csv(index=False),
        file_name="eraseright_access_report.csv",
        mime="text/csv",
        use_container_width=True,
        key=key
    )


# =====================================================
#                  PAGE: OVERVIEW
# =====================================================

def page_overview():
    page_header(
        "Overview dashboard",
        "A clear snapshot of privacy-request processing and safeguard status."
    )

    metrics = dashboard_module.get_dashboard_metrics()

    # Keep the landing page intentionally minimal: no activity charts,
    # outcome graphs, recent-activity tables or lifecycle panels.
    tiles([
        ("Total Requests", metrics["total_requests"], "primary", "requests"),
        ("Records Reviewed", metrics["total_records_reviewed"], "primary", "records"),
        ("Verified Actions", metrics["verified_actions"], "ok", "verified"),
        ("Pending Reviews", metrics["pending_actions"], "warn", "pending"),
    ])

    st.write("")
    with card("overview_intro"):
        md(
            '<div class="er-panel-title">Privacy request operations</div>'
            '<div class="er-section-sub" style="margin-top:6px">'
            'Submit an access or erasure request, discover matching records, '
            'review policy-grounded AI recommendations, and complete the process '
            'with human approval, verification and an auditable record.'
            '</div>'
        )
        col1, col2 = st.columns(2)
        with col1:
            st.button(
                "Start a privacy request", key="overview_start_request",
                type="primary", use_container_width=True,
                on_click=go_to, args=(P_SUBMIT,)
            )
        with col2:
            st.button(
                "▶ Start guided demo", key="overview_start_demo",
                use_container_width=True, on_click=start_guided_demo
            )


# =====================================================
#                  PAGE: SUBMIT REQUEST
# =====================================================

def page_submit():
    page_header(
        "Submit privacy request",
        "Capture a data subject request and discover matching personal records."
    )

    flash = st.session_state.get("flash")

    if flash:
        kind, message = flash
        if kind == "success":
            st.success(message)
        else:
            st.info(message)
        st.session_state["flash"] = None

    form_col, info_col = st.columns([3, 2])

    with form_col:

        with st.form("privacy_request_form"):

            request_type = st.selectbox(
                "Request type",
                [ERASURE, ACCESS]
            )

            name = st.text_input(
                "Full name",
                placeholder="Enter full name"
            )

            email = st.text_input(
                "Email address",
                placeholder="Enter email address"
            )

            customer_id = st.text_input(
                "Customer ID",
                placeholder="Enter customer ID"
            )

            submitted = st.form_submit_button(
                "Submit Request",
                type="primary",
                use_container_width=True
            )

    with info_col:
        md(
            '<div class="er-panel"><div class="er-panel-title">What happens after you submit</div>'
            '<div class="er-steps-list">'
            '<div class="er-steps-item"><div class="er-steps-num">1</div><div class="er-steps-text">Record discovery'
            '<span>Matching records are found across the data sources.</span></div></div>'
            '<div class="er-steps-item"><div class="er-steps-num">2</div><div class="er-steps-text">AI decision'
            '<span>Each record receives a proposed action and policy evidence.</span></div></div>'
            '<div class="er-steps-item"><div class="er-steps-num">3</div><div class="er-steps-text">Independent review'
            '<span>A separate agent checks the proposals for erasure requests.</span></div></div>'
            '<div class="er-steps-item"><div class="er-steps-num">4</div><div class="er-steps-text">Human approval'
            '<span>Nothing is deleted or anonymized until you approve and confirm.</span></div></div>'
            '</div></div>'
        )

    if submitted:

        if not name.strip() or not email.strip() or not customer_id.strip():

            st.error("Please fill in all required fields.")

        else:

            ok = process_request(
                request_type,
                name.strip(),
                email.strip(),
                customer_id.strip()
            )

            if ok:

                if st.session_state["records"]:
                    st.session_state["flash"] = (
                        "success",
                        "Privacy request processed successfully."
                    )
                else:
                    st.session_state["flash"] = (
                        "info",
                        "Request processed. No matching records were found."
                    )

                st.rerun()

    records = st.session_state["records"]
    decisions = st.session_state["decisions"]

    if records:

        section_title(
            "Discovery results",
            f"{len(records)} matching records found for this request."
        )

        render_discovery(records, decisions)

        st.write("")

        if decisions:
            goto_button(
                "Continue to AI Decision Analysis",
                P_AI,
                "submit_continue"
            )

        render_access_report("dl_access_submit")

    elif st.session_state["request_details"]:
        empty_state(
            "No matching records",
            "No personal records matched the details provided."
        )


# =====================================================
#                  PAGE: AI DECISION ANALYSIS
# =====================================================

def render_decision_card(decision):
    action = decision.get("action")
    tone = action_tone(action)

    analysis = decision.get("ai_analysis")
    analysis_html = ""

    if analysis:
        analysis_html = (
            f"<details><summary>AI analysis</summary><div>{fmt_text(analysis)}</div></details>"
        )

    llm_html = ""

    if decision.get("llm_status"):
        llm_html = f'<div class="er-foot">AI status: {esc(decision["llm_status"])}</div>'

    confidence = decision.get("confidence")
    confidence_html = (
        f'<div class="er-foot">Confidence: {float(confidence):.0%}</div>'
        if isinstance(confidence, (int, float)) else ""
    )
    source = decision.get("policy_source")
    source_html = f'<div class="er-foot">Evidence source: {esc(source)}</div>' if source else ""
    risks = decision.get("risk_flags") or []
    if isinstance(risks, str):
        risks = [risks]
    risk_html = (
        '<div class="er-note"><b>Risk checks:</b> ' + fmt_text(risks) + '</div>'
        if risks else ""
    )
    next_step = decision.get("next_step")
    next_html = (
        f'<div class="er-foot"><b>Recommended next step:</b> {esc(next_step)}</div>'
        if next_step else ""
    )

    md(
        f'<div class="er-dcard t-{tone}"><div class="er-dhead"><div>'
        f'<div class="er-dtitle">Record #{esc(decision.get("record_id"))}</div>'
        f'<div class="er-dmeta">{esc(decision.get("data_type", "Unknown type"))} '
        f'from {esc(decision.get("source", "unknown source"))}</div></div>'
        f'<div class="er-dbadges">{action_badge(action)}'
        f'{status_badge(decision.get("approval_status", "PENDING"))}</div></div>'
        '<div class="er-grid2">'
        f'<div><div class="er-lbl">Reason</div><div class="er-val">{fmt_text(decision.get("reason"))}</div></div>'
        '<div><div class="er-lbl">Retrieved policy evidence</div>'
        f'<div class="er-quote">{fmt_text(decision.get("policy_evidence"), "No relevant policy passage retrieved. The safe outcome is review, not an assumed legal rule.")}</div>'
        f'{source_html}</div>'
        f'</div>{confidence_html}{risk_html}{next_html}{analysis_html}{llm_html}</div>'
    )


def render_review_panel():
    review = st.session_state["review_result"]

    with card("review"):

        md(
            '<div class="er-panel-title">Independent Review Agent</div>'
            '<div class="er-flow">'
            '<div class="er-flow-step"><b>Decision Agent</b><span>Proposes an action for each record</span></div>'
            '<div class="er-flow-sep">&#8594;</div>'
            '<div class="er-flow-step review"><b>Review Agent</b><span>Evaluates those proposals independently</span></div>'
            '<div class="er-flow-sep">&#8594;</div>'
            '<div class="er-flow-step"><b>Human reviewer</b><span>Makes the final decision</span></div>'
            '</div>'
        )

        if not review:
            st.error(
                "Independent review result is unavailable. "
                "Do not proceed with approval."
            )
            return

        passed = review.get("status") == "PASSED"

        md(
            '<div class="er-lbl" style="margin-top:14px">Review status</div>'
            + badge("PASSED" if passed else "REVIEW REQUIRED", "ok" if passed else "warn")
        )

        md(
            '<div class="er-lbl" style="margin-top:14px">Overall review summary</div>'
            f'<div class="er-val">{fmt_text(review.get("summary"), "No summary available.")}</div>'
        )

        issues = review.get("issues", [])

        if issues:
            md('<div class="er-lbl" style="margin-top:14px">Issues identified</div>')
            md("".join(f'<div class="er-issue">{fmt_text(issue)}</div>' for issue in issues))

        recommendations = review.get("recommendations", [])

        if recommendations:
            md('<div class="er-lbl" style="margin-top:14px">Recommendations</div>')
            st.dataframe(
                pd.DataFrame(recommendations),
                use_container_width=True,
                hide_index=True
            )

        risks = review.get("risks") or review.get("potential_risks")

        md('<div class="er-lbl" style="margin-top:14px">Potential risks</div>')

        if risks:
            if not isinstance(risks, (list, tuple)):
                risks = [risks]
            md("".join(f'<div class="er-risk">{fmt_text(risk)}</div>' for risk in risks))
        else:
            md('<div class="er-val er-muted">The Review Agent did not report additional risks.</div>')

        md(
            '<div class="er-note">The Review Agent cannot approve or execute actions. '
            "Human approval is still mandatory.</div>"
        )


def page_ai():
    page_header(
        "AI decision analysis",
        "Proposed actions, reasoning and policy evidence, followed by an independent review."
    )

    decisions = st.session_state["decisions"]

    if st.session_state.get("demo_mode"):
        st.info("DEMO MODE · Fictional records and offline decision examples. Policy passages are labelled demo fixtures; no live LLM call, database write, deletion, anonymization or certificate issuance occurs.")

    if not decisions:
        empty_state(
            "No AI decisions yet",
            "Submit a privacy request with matching records to generate decisions."
        )
        st.write("")
        goto_button("Go to Submit Privacy Request", P_SUBMIT, "ai_to_submit")
        return

    counts = Counter(d.get("action") for d in decisions)
    review_required = sum(
        n for action, n in counts.items()
        if action not in (*DESTRUCTIVE_ACTIONS, "RETAIN")
    )

    tiles([
        ("Proposed deletions", counts.get("DELETE", 0), "err", "delete"),
        ("Proposed anonymizations", counts.get("ANONYMIZE", 0), "primary", "anonymize"),
        ("Retain", counts.get("RETAIN", 0), "ok", "approved"),
        ("Review required", review_required, "warn", "pending"),
    ])

    section_title(
        "Decision Agent recommendations",
        "One card per discovered record."
    )

    for decision in decisions:
        render_decision_card(decision)

    section_title(
        "Independent review",
        "Evaluated separately from the Decision Agent."
    )

    if st.session_state["request_type"] == ERASURE:
        render_review_panel()
    else:
        st.info(
            "Independent review applies to erasure requests. "
            "Access requests do not change any records."
        )

    st.write("")

    if st.session_state["request_type"] == ERASURE:
        goto_button("Continue to Human Approval Centre", P_APPROVAL, "ai_continue")


# =====================================================
#                  PAGE: HUMAN APPROVAL
# =====================================================

def page_approval():
    page_header(
        "Human approval centre",
        "Every deletion or anonymization needs your explicit approval and final confirmation."
    )

    ss = st.session_state
    decisions = ss["decisions"]

    if not decisions:
        empty_state(
            "Nothing to approve",
            "Submit a privacy request with matching records first."
        )
        st.write("")
        goto_button("Go to Submit Privacy Request", P_SUBMIT, "appr_to_submit")
        return

    if ss["request_type"] != ERASURE:
        st.info(
            "Human approval applies to erasure requests only. "
            "This access request does not modify any records."
        )
        return

    # ---------------- REVIEW ACKNOWLEDGEMENT ----------------

    review_available = ss["review_result"] is not None

    with card("ack"):

        md('<div class="er-panel-title">Independent review acknowledgement</div>')

        if review_available:

            ss["review_acknowledged"] = st.checkbox(
                "I have reviewed the independent AI findings and "
                "will make the final approval decision myself.",
                value=ss["review_acknowledged"],
                key="review_acknowledgement_checkbox",
                disabled=ss["execution_completed"]
            )

        else:
            st.error(
                "Approval is disabled because the independent review "
                "has not completed."
            )

        if ss["review_acknowledged"]:
            st.success(
                "Review acknowledged. You can now make individual "
                "approval or rejection decisions."
            )

        md(
            '<div class="er-note">Only approved actions can be executed. '
            "Records marked RETAIN or REVIEW REQUIRED can never be approved for deletion.</div>"
        )

    locked = (not ss["review_acknowledged"]) or ss["execution_completed"]

    # ---------------- RECORD CARDS ----------------

    section_title("Record decisions", "Approve or reject each proposed action.")

    for index, decision in enumerate(decisions):

        record_id = decision.get("record_id")
        action = decision.get("action")
        current_status = decision.get("approval_status", "PENDING")
        destructive = action in DESTRUCTIVE_ACTIONS

        with card(f"approval_{record_id}_{index}"):

            md(
                f'<div class="er-arow"><div><div class="er-dtitle">Record #{esc(record_id)}</div>'
                f'<div class="er-dmeta">{esc(decision.get("data_type", "Unknown type"))} '
                f'from {esc(decision.get("source", "unknown source"))}</div></div>'
                f'<div class="er-dbadges">{action_badge(action)}{status_badge(current_status)}</div></div>'
                f'<div class="er-reason">{fmt_text(decision.get("reason"))}</div>'
            )

            col1, col2, _ = st.columns([1, 1, 2])

            if destructive:

                with col1:
                    if st.button(
                        "Approve",
                        key=f"approve_{record_id}",
                        type="primary",
                        disabled=locked,
                        use_container_width=True
                    ):
                        ss["decisions"][index]["approval_status"] = "APPROVED"
                        st.rerun()

                with col2:
                    if st.button(
                        "Reject",
                        key=f"reject_{record_id}",
                        disabled=locked,
                        use_container_width=True
                    ):
                        ss["decisions"][index]["approval_status"] = "REJECTED"
                        st.rerun()

            else:

                with col1:
                    if st.button(
                        "Confirm Retention",
                        key=f"retain_{record_id}",
                        type="primary",
                        disabled=locked,
                        use_container_width=True
                    ):
                        ss["decisions"][index]["approval_status"] = "RETENTION_CONFIRMED"
                        st.rerun()

                with col2:
                    if st.button(
                        "Flag for Review",
                        key=f"flag_{record_id}",
                        disabled=locked,
                        use_container_width=True
                    ):
                        ss["decisions"][index]["approval_status"] = "FLAGGED_FOR_REVIEW"
                        st.rerun()

                st.caption(
                    "This record requires human review and is never sent to the executor."
                )

    # ---------------- APPROVAL SUMMARY ----------------

    decisions = ss["decisions"]

    approved_count = len(destructive_approved(decisions))
    rejected_count = sum(
        1 for d in decisions if d.get("approval_status") == "REJECTED"
    )
    pending_count = destructive_pending(decisions)
    retained_count = sum(
        1 for d in decisions if d.get("approval_status") == "RETENTION_CONFIRMED"
    )
    flagged_count = sum(
        1 for d in decisions if d.get("approval_status") == "FLAGGED_FOR_REVIEW"
    )

    section_title("Approval summary")

    tiles([
        ("Approved", approved_count, "ok", "approved"),
        ("Rejected", rejected_count, "err", "rejected"),
        ("Pending", pending_count, "warn", "pending"),
        ("Retention confirmed", retained_count, "primary", "verified"),
        ("Flagged for review", flagged_count, "warn", "failed"),
    ])

    # ---------------- EXECUTION ----------------

    if ss.get("demo_mode"):
        section_title("Execution preview", "The guided demo never changes records or writes to the database.")
        st.info("Execution is intentionally disabled in Demo Mode. You can practise approving or rejecting the fictional proposals, but no DELETE or ANONYMIZE operation will run.")

    elif not ss["execution_completed"]:

        section_title(
            "Execute approved actions",
            "Final step. Requires your explicit confirmation."
        )

        with card("execute"):

            if approved_count > 0 and pending_count == 0:

                to_delete = sum(
                    1 for d in destructive_approved(decisions)
                    if d.get("action") == "DELETE"
                )
                to_anonymize = approved_count - to_delete

                st.warning(
                    "Execution will permanently delete or anonymize "
                    "approved records in the demonstration database. "
                    f"This run will delete {to_delete} and anonymize {to_anonymize} record(s)."
                )

                confirm = st.checkbox(
                    "I confirm that the approved actions should be executed.",
                    key="execute_confirmation"
                )

                if st.button(
                    "Execute Approved Actions",
                    type="primary",
                    key="execute_button",
                    disabled=(
                        not confirm
                        or not ss["review_acknowledged"]
                    ),
                    use_container_width=True
                ):

                    run_execution()

                    st.success(
                        "Execution, verification and audit logging completed."
                    )

                    st.rerun()

            elif pending_count > 0:

                st.info("Resolve all pending approvals before execution.")

            else:

                st.info("No approved actions are available for execution.")

    # ---------------- RESULTS ----------------

    else:

        render_execution_results("approval")

        st.write("")

        if ss["audit_saved"]:
            goto_button(
                "View certificate and reports",
                P_CERT,
                "appr_to_cert"
            )


# =====================================================
#                  PAGE: LIFECYCLE
# =====================================================

def page_lifecycle():
    page_header(
        "Request lifecycle",
        "Each stage reflects what has actually been completed for the current request."
    )

    ss = st.session_state
    details = ss["request_details"]

    if details:

        request_id = str(ss["request_id"])[:8] if ss["request_id"] else "Not yet assigned"

        with card("lifecycle_summary"):
            md(
                '<div class="er-summary">'
                f'<div><b>Requester</b><span>{esc(details.get("name"))}</span></div>'
                f'<div><b>Customer ID</b><span>{esc(details.get("customer_id"))}</span></div>'
                f'<div><b>Request type</b><span>{esc(details.get("request_type"))}</span></div>'
                f'<div><b>Records discovered</b><span>{len(ss["records"])}</span></div>'
                f'<div><b>Request ID</b><span>{esc(request_id)}</span></div>'
                '</div>'
            )

    else:
        st.info("No request is active. All stages are pending until a request is submitted.")

    section_title("Progress")

    render_timeline(build_lifecycle())


# =====================================================
#                  PAGE: AUDIT HISTORY
# =====================================================

def page_audit():
    page_header(
        "Audit history",
        "Searchable record of every completed request, decision, execution and verification."
    )

    if st.session_state.get("demo_mode"):
        st.info("DEMO PREVIEW: this is an illustrative audit entry. It is not saved to the audit database.")
        st.dataframe(pd.DataFrame([{
            "Request ID": "DEMO-ER-2026-001",
            "Requester": "Alex Demo",
            "Customer ID": "DEMO-1001",
            "Request type": "Erasure Request",
            "Timestamp": "Simulated",
            "Decisions": "1 DELETE, 1 ANONYMIZE, 1 RETAIN",
            "Execution results": "Not executed in demo mode",
            "Verification": "Not run",
            "Verification status": "SIMULATION ONLY",
        }]), use_container_width=True, hide_index=True)
        st.caption("In a real request, this page displays persistent audit records after execution and verification.")
        return

    activity = dashboard_module.get_recent_audit_activity(limit=1000)

    if not activity:
        empty_state(
            "No audit records are available yet",
            "Audit entries are created when an approved erasure request is executed."
        )
        return

    rows = []

    for item in activity:

        decisions = item["decisions"]
        executions = item["execution_results"]
        verifications = item["verification_results"]

        action_counts = Counter(d.get("action", "UNKNOWN") for d in decisions)
        decisions_text = ", ".join(
            f"{count} {action}" for action, count in action_counts.items()
        ) or "None"

        executed_ok = sum(1 for r in executions if r.get("status") == "SUCCESS")
        execution_text = (
            f"{executed_ok} succeeded, {len(executions) - executed_ok} other"
            if executions else "None executed"
        )

        verified_n = sum(1 for r in verifications if r.get("verification") == "VERIFIED")
        failed_n = sum(1 for r in verifications if r.get("verification") == "FAILED")

        if failed_n:
            verification_state = "Failed"
        elif verified_n:
            verification_state = "Verified"
        else:
            verification_state = "None"

        rows.append({
            "Request ID": item["request_id"],
            "Requester": item["requester"],
            "Customer ID": item["customer_id"],
            "Request type": item["request_type"],
            "Timestamp": item["created_at"],
            "Decisions": decisions_text,
            "Execution results": execution_text,
            "Verification": f"{verified_n} verified, {failed_n} failed",
            "Verification status": verification_state,
        })

    table = pd.DataFrame(rows)

    with card("audit_filters"):

        c1, c2, c3 = st.columns([2, 1, 1])

        search = c1.text_input(
            "Search",
            placeholder="Request ID, requester or customer ID",
            key="audit_search"
        )

        type_options = ["All"] + sorted(table["Request type"].dropna().unique().tolist())
        chosen_type = c2.selectbox("Request type", type_options, key="audit_type")

        chosen_status = c3.selectbox(
            "Verification status",
            ["All", "Verified", "Failed", "None"],
            key="audit_status"
        )

    filtered = table

    if search.strip():
        needle = search.strip().lower()
        mask = (
            filtered["Request ID"].astype(str).str.lower().str.contains(needle, regex=False)
            | filtered["Requester"].astype(str).str.lower().str.contains(needle, regex=False)
            | filtered["Customer ID"].astype(str).str.lower().str.contains(needle, regex=False)
        )
        filtered = filtered[mask]

    if chosen_type != "All":
        filtered = filtered[filtered["Request type"] == chosen_type]

    if chosen_status != "All":
        filtered = filtered[filtered["Verification status"] == chosen_status]

    section_title(
        "Audit log",
        f"Showing {len(filtered)} of {len(table)} entries."
    )

    st.dataframe(
        filtered.drop(columns=["Verification status"]),
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        "Download audit log (CSV)",
        data=filtered.to_csv(index=False),
        file_name="eraseright_audit_log.csv",
        mime="text/csv",
        key="dl_audit"
    )

    if len(filtered):

        section_title("Request detail", "Inspect the full record of a single request.")

        selected = st.selectbox(
            "Request",
            filtered["Request ID"].tolist(),
            key="audit_detail_select"
        )

        chosen = next(
            (item for item in activity if item["request_id"] == selected),
            None
        )

        if chosen:

            tab1, tab2, tab3 = st.tabs(
                ["Decisions", "Execution results", "Verification results"]
            )

            for tab, data, label in (
                (tab1, chosen["decisions"], "decisions"),
                (tab2, chosen["execution_results"], "execution results"),
                (tab3, chosen["verification_results"], "verification results"),
            ):
                with tab:
                    if data:
                        st.dataframe(
                            pd.DataFrame(data),
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.info(f"No {label} were recorded for this request.")


# =====================================================
#                  PAGE: CERTIFICATES
# =====================================================

def page_certificates():
    page_header(
        "Certificates and reports",
        "Erasure certificates and access reports for the current request."
    )

    ss = st.session_state
    details = ss["request_details"]

    if ss.get("demo_mode"):
        st.info("DEMO PREVIEW: no erasure was executed, so no real erasure certificate has been issued.")
        with card("demo_certificate_preview"):
            md('<div class="er-panel-title">Certificate preview</div>')
            md('<div class="er-summary"><div><b>Demo request</b><span>DEMO-ER-2026-001</span></div><div><b>Requester</b><span>Alex Demo</span></div><div><b>Customer ID</b><span>DEMO-1001</span></div><div><b>Execution status</b><span>Not executed · read-only demo</span></div><div><b>Verification</b><span>Not run</span></div></div>')
        st.caption("A real certificate becomes available only after human approval, execution, verification and audit logging.")
        return

    if not details:
        empty_state(
            "No request in this session",
            "Submit and complete a privacy request to generate a certificate."
        )
        st.write("")
        goto_button("Go to Submit Privacy Request", P_SUBMIT, "cert_to_submit")
        return

    if ss["request_type"] == ACCESS:
        section_title(
            "Request details",
            "Access requests produce a data report instead of an erasure certificate."
        )

        with card("cert_access"):
            md(
                '<div class="er-summary">'
                f'<div><b>Requester</b><span>{esc(details.get("name"))}</span></div>'
                f'<div><b>Customer ID</b><span>{esc(details.get("customer_id"))}</span></div>'
                f'<div><b>Records discovered</b><span>{len(ss["records"])}</span></div>'
                '</div>'
            )

        render_access_report("dl_access_reports")
        return

    if not (ss["execution_completed"] and ss["audit_saved"]):
        empty_state(
            "Certificate not available yet",
            "A certificate is generated after approved actions are executed and the audit log is saved."
        )
        st.write("")
        goto_button("Go to Human Approval Centre", P_APPROVAL, "cert_to_approval")
        return

    results = ss["execution_results"]
    verification = ss["verification_results"]
    decisions = ss["decisions"]

    section_title("Request details")

    with card("cert_details"):
        md(
            '<div class="er-summary">'
            f'<div><b>Request ID</b><span>{esc(ss["request_id"])}</span></div>'
            f'<div><b>Requester</b><span>{esc(details.get("name"))}</span></div>'
            f'<div><b>Email</b><span>{esc(details.get("email"))}</span></div>'
            f'<div><b>Customer ID</b><span>{esc(details.get("customer_id"))}</span></div>'
            f'<div><b>Request type</b><span>{esc(details.get("request_type"))}</span></div>'
            '</div>'
        )

    section_title("Processing summary")

    executed_ok = sum(1 for r in results if r.get("status") == "SUCCESS")
    verified_n = sum(1 for v in verification if v.get("verification") == "VERIFIED")
    failed_n = sum(1 for v in verification if v.get("verification") == "FAILED")

    tiles([
        ("Records reviewed", len(decisions), "primary", "records"),
        ("Approved actions", len(destructive_approved(decisions)), "ok", "approved"),
        ("Executed successfully", executed_ok, "accent", "delete"),
        ("Verified", verified_n, "ok", "verified"),
        ("Failed verification", failed_n, "err", "failed"),
    ])

    render_execution_results("certificate")

    section_title("Erasure certificate", "PDF record of this request, its execution and verification.")

    with card("cert_download"):

        try:
            certificate = certificate_module.generate_certificate(
                request_id=ss["request_id"],
                requester_name=details["name"],
                requester_email=details["email"],
                customer_id=details["customer_id"],
                request_type=details["request_type"],
                decisions=ss["decisions"],
                execution_results=results,
                verification_results=verification
            )

            st.success("Request execution and audit logging completed.")

            st.download_button(
                label="Download Erasure Certificate (PDF)",
                data=certificate,
                file_name=(
                    f"EraseRight_Certificate_"
                    f"{str(ss['request_id'])[:8]}.pdf"
                ),
                mime="application/pdf",
                use_container_width=True,
                type="primary",
                key="dl_certificate"
            )

        except Exception as error:
            st.error(f"The certificate could not be generated: {error}")


# =====================================================
#                       MAIN
# =====================================================

PAGE_RENDERERS = {
    P_OVERVIEW: page_overview,
    P_SUBMIT: page_submit,
    P_AI: page_ai,
    P_APPROVAL: page_approval,
    P_LIFECYCLE: page_lifecycle,
    P_AUDIT: page_audit,
    P_CERT: page_certificates,
}

st.markdown(CSS, unsafe_allow_html=True)

render_sidebar()
render_topbar()

if st.session_state.get("demo_mode"):
    st.warning("GUIDED DEMO MODE · Fictional data only · No database writes or destructive actions")

PAGE_RENDERERS.get(st.session_state["active_page"], page_overview)()

render_footer()