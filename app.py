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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ---------- animations ---------- */
@keyframes pulseGlow{0%,100%{box-shadow:0 0 0 0 rgba(20,184,166,.45)}50%{box-shadow:0 0 0 8px rgba(20,184,166,0)}}
@keyframes shimmer{0%{background-position:-200% 0}100%{background-position:200% 0}}
@keyframes fadeInUp{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-4px)}}
@keyframes gradientShift{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}
@keyframes slideInLeft{from{opacity:0;transform:translateX(-16px)}to{opacity:1;transform:translateX(0)}}
@keyframes scaleIn{from{opacity:0;transform:scale(.95)}to{opacity:1;transform:scale(1)}}

:root{
--bg:#F0F4F8; --card:#FFFFFF; --primary:#0F5B78; --primary-light:#1A7FA3; --accent:#0D9488;
--text:#0F1D2B; --muted:#5B7083; --ok:#059669; --warn:#D97706; --err:#DC2626;
--line:#D8E2EC;
--primary-tint:rgba(15,91,120,.07); --accent-tint:rgba(13,148,136,.07); --ok-tint:rgba(5,150,105,.07);
--warn-tint:rgba(217,119,6,.07); --err-tint:rgba(220,38,38,.07); --slate-tint:rgba(91,112,131,.06);
--shadow-sm:0 1px 2px rgba(15,29,43,.04);
--shadow:0 1px 3px rgba(15,29,43,.04),0 8px 24px rgba(15,29,43,.06);
--shadow-lg:0 4px 6px rgba(15,29,43,.04),0 12px 40px rgba(15,29,43,.08);
--shadow-glow:0 4px 20px rgba(15,91,120,.12);
--glass:rgba(255,255,255,.72);
--glass-border:rgba(255,255,255,.5);
--radius:16px; --radius-lg:22px; --radius-sm:10px;
}
*{-webkit-font-smoothing:antialiased; -moz-osx-font-smoothing:grayscale;}
.stApp{background:var(--bg); color:var(--text); background-image:
  radial-gradient(ellipse 80% 60% at 10% 20%, rgba(15,91,120,.04) 0%, transparent 60%),
  radial-gradient(ellipse 60% 50% at 90% 80%, rgba(13,148,136,.04) 0%, transparent 60%);
  background-attachment:fixed;
}
.stApp, .stApp .stMarkdown, .stApp button, .stApp input, .stApp textarea, .stApp label{
font-family:'Inter',-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
}
[data-testid="stHeader"]{background:transparent !important; backdrop-filter:blur(12px); -webkit-backdrop-filter:blur(12px);}
#MainMenu, footer, .stDeployButton{visibility:hidden;}
.block-container{padding-top:1.4rem; padding-bottom:3rem; max-width:1320px;}
.stApp button p{color:inherit !important;}

/* ---------- sidebar ---------- */
[data-testid="stSidebar"]{
  background:linear-gradient(180deg,#FAFCFE 0%,#F3F7FB 40%,#EDF3F8 100%);
  border-right:1px solid var(--line); box-shadow:2px 0 24px rgba(15,29,43,.04);
}
[data-testid="stSidebar"] .block-container, [data-testid="stSidebarContent"]{padding-top:1rem;}
.er-side-brand{display:flex; align-items:center; gap:12px; padding:4px 4px 20px 4px; animation:fadeInUp .4s ease;}
.er-side-name{
  font-weight:800; font-size:1.2rem; line-height:1.2; letter-spacing:-.02em;
  background:linear-gradient(135deg,var(--primary) 0%,var(--accent) 100%);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
}
.er-side-sub{font-size:.76rem; color:var(--muted); font-weight:400; letter-spacing:.01em;}
.er-side-label{
  font-size:.68rem; color:var(--muted); font-weight:600; text-transform:uppercase; letter-spacing:.08em;
  padding:4px 8px 8px 8px; margin-top:4px;
}
.er-side-card{
  margin-top:22px; padding:16px 18px; border:1px solid var(--line); border-radius:var(--radius);
  background:var(--glass); backdrop-filter:blur(8px); -webkit-backdrop-filter:blur(8px);
  box-shadow:var(--shadow-sm);
}
.er-side-card-title{font-size:.7rem; color:var(--muted); margin-bottom:6px; font-weight:600; text-transform:uppercase; letter-spacing:.06em;}
.er-side-card-main{font-weight:700; font-size:.92rem; color:var(--text);}
.er-side-card-sub{font-size:.8rem; color:var(--muted); margin-top:3px; line-height:1.4;}
[data-testid="stSidebar"] .stButton > button{
  justify-content:flex-start; text-align:left; border:1px solid transparent !important;
  background:transparent !important; color:var(--muted) !important; font-weight:500;
  padding:.6rem .9rem; border-radius:var(--radius-sm); box-shadow:none;
  transition:all .2s cubic-bezier(.4,0,.2,1); font-size:.88rem;
}
[data-testid="stSidebar"] .stButton > button:hover{
  background:rgba(15,91,120,.06) !important; color:var(--primary) !important;
  transform:translateX(3px);
}
[data-testid="stSidebar"] button[kind="primary"],
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"]{
  background:linear-gradient(135deg,rgba(15,91,120,.1) 0%,rgba(13,148,136,.08) 100%) !important;
  color:var(--primary) !important;
  border:1px solid rgba(15,91,120,.18) !important; font-weight:700;
  box-shadow:inset 3px 0 0 var(--accent), var(--shadow-sm);
}

/* ---------- top bar ---------- */
.er-topbar{
  display:flex; align-items:center; justify-content:space-between; gap:16px; flex-wrap:wrap;
  background:linear-gradient(135deg,rgba(255,255,255,.85) 0%,rgba(240,248,250,.9) 100%);
  backdrop-filter:blur(16px); -webkit-backdrop-filter:blur(16px);
  border:1px solid rgba(220,234,240,.6); border-radius:var(--radius-lg);
  padding:18px 26px; box-shadow:var(--shadow); margin-bottom:28px;
  animation:fadeInUp .4s ease;
}
.er-brand{display:flex; align-items:center; gap:16px;}
.er-name{
  font-weight:800; font-size:1.4rem; line-height:1.15; letter-spacing:-.03em;
  background:linear-gradient(135deg,var(--primary) 0%,#0D9488 100%);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
}
.er-tag{font-size:.84rem; color:var(--muted); font-weight:400;}
.er-status{
  display:inline-flex; align-items:center; gap:9px;
  background:linear-gradient(135deg,rgba(5,150,105,.1) 0%,rgba(13,148,136,.08) 100%);
  color:#065F46; border:1px solid rgba(5,150,105,.2); border-radius:999px;
  padding:7px 16px; font-size:.82rem; font-weight:600; letter-spacing:.01em;
}
.er-dot{
  width:8px; height:8px; border-radius:50%; background:var(--ok);
  animation:pulseGlow 2s ease-in-out infinite;
}

/* ---------- page titles ---------- */
.er-page-head{
  margin:4px 0 26px 0; padding:22px 26px; position:relative; overflow:hidden;
  background:linear-gradient(135deg,rgba(255,255,255,.9) 0%,rgba(241,248,250,.95) 100%);
  backdrop-filter:blur(12px); -webkit-backdrop-filter:blur(12px);
  border:1px solid rgba(220,234,240,.5); border-left:4px solid var(--accent);
  border-radius:var(--radius-lg); box-shadow:var(--shadow);
  animation:fadeInUp .35s ease;
}
.er-page-head::after{
  content:''; position:absolute; top:-30px; right:-30px; width:120px; height:120px;
  border-radius:50%; background:linear-gradient(135deg,rgba(13,148,136,.06),rgba(15,91,120,.04));
  pointer-events:none;
}
.er-page-title{font-size:1.8rem; font-weight:800; color:var(--text); letter-spacing:-.03em;}
.er-page-sub{color:var(--muted); font-size:.92rem; margin-top:6px; font-weight:400;}
.er-section{margin:30px 0 14px 0; animation:fadeInUp .3s ease;}
.er-section-title{font-size:1.1rem; font-weight:700; color:var(--text); letter-spacing:-.01em;}
.er-section-sub{font-size:.85rem; color:var(--muted); margin-top:3px;}
.er-muted{color:var(--muted);}

/* ---------- cards ---------- */
[class*="st-key-er_card_"]{
  background:var(--glass); backdrop-filter:blur(12px); -webkit-backdrop-filter:blur(12px);
  border:1px solid rgba(216,226,236,.5); border-radius:var(--radius-lg);
  padding:22px 24px; box-shadow:var(--shadow);
  transition:box-shadow .2s ease, border-color .2s ease;
  animation:scaleIn .3s ease;
}
[class*="st-key-er_card_"]:hover{box-shadow:var(--shadow-lg); border-color:rgba(15,91,120,.12);}
[data-testid="stForm"]{
  background:var(--glass); backdrop-filter:blur(12px); -webkit-backdrop-filter:blur(12px);
  border:1px solid rgba(216,226,236,.5); border-radius:var(--radius-lg);
  padding:24px 26px; box-shadow:var(--shadow);
}
[data-testid="stDataFrame"]{border:1px solid var(--line); border-radius:14px; overflow:hidden; box-shadow:var(--shadow-sm);}
[data-testid="stAlert"]{border-radius:14px;}
.er-panel{
  background:var(--glass); backdrop-filter:blur(12px); -webkit-backdrop-filter:blur(12px);
  border:1px solid rgba(216,226,236,.5); border-radius:var(--radius-lg);
  padding:22px 24px; box-shadow:var(--shadow);
}
.er-panel-title{font-weight:700; font-size:1.05rem; margin-bottom:12px; color:var(--text); letter-spacing:-.01em;}
.er-steps-list{display:flex; flex-direction:column; gap:16px; margin-top:8px;}
.er-steps-item{display:flex; gap:14px; align-items:flex-start; animation:slideInLeft .3s ease both;}
.er-steps-item:nth-child(1){animation-delay:.05s;}
.er-steps-item:nth-child(2){animation-delay:.1s;}
.er-steps-item:nth-child(3){animation-delay:.15s;}
.er-steps-item:nth-child(4){animation-delay:.2s;}
.er-steps-num{
  flex:0 0 28px; height:28px; border-radius:50%;
  background:linear-gradient(135deg,var(--primary) 0%,var(--accent) 100%); color:#FFFFFF;
  display:flex; align-items:center; justify-content:center; font-size:.78rem; font-weight:700;
  box-shadow:0 2px 8px rgba(15,91,120,.2);
}
.er-steps-text{font-size:.9rem; color:var(--text); font-weight:500;}
.er-steps-text span{display:block; color:var(--muted); font-size:.82rem; font-weight:400; margin-top:1px;}

/* ---------- inputs & buttons ---------- */
.stTextInput input, .stSelectbox [data-baseweb="select"] > div{
  background:rgba(255,255,255,.8) !important; border:1.5px solid var(--line) !important;
  border-radius:var(--radius-sm) !important; color:var(--text) !important;
  transition:all .2s ease !important;
}
.stTextInput input:focus{
  border-color:var(--primary) !important;
  box-shadow:0 0 0 3px rgba(15,91,120,.1), 0 2px 8px rgba(15,91,120,.08) !important;
  background:#FFFFFF !important;
}
.stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] > button{
  border-radius:var(--radius-sm); font-weight:600; border:1.5px solid var(--line);
  background:#FFFFFF; color:var(--text);
  transition:all .2s cubic-bezier(.4,0,.2,1);
}
.stButton > button:hover, .stDownloadButton > button:hover{
  border-color:var(--primary); color:var(--primary);
  box-shadow:0 2px 8px rgba(15,91,120,.1); transform:translateY(-1px);
}
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"],
[data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primaryFormSubmit"],
button[kind="primaryFormSubmit"]{
  background:linear-gradient(135deg,var(--primary) 0%,var(--primary-light) 100%) !important;
  color:#FFFFFF !important; border:1px solid var(--primary) !important;
  box-shadow:0 2px 8px rgba(15,91,120,.2) !important;
}
.stButton > button[kind="primary"]:hover, [data-testid="stBaseButton-primary"]:hover{
  background:linear-gradient(135deg,#0A4A62 0%,var(--primary) 100%) !important; color:#FFFFFF !important;
  box-shadow:0 4px 16px rgba(15,91,120,.25) !important; transform:translateY(-1px);
}
.stButton > button:disabled{opacity:.45; cursor:not-allowed;}

/* ---------- metric tiles ---------- */
.er-tiles{display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:16px;}
.er-tile{
  display:flex; align-items:center; gap:16px; position:relative; overflow:hidden;
  background:var(--glass); backdrop-filter:blur(12px); -webkit-backdrop-filter:blur(12px);
  border:1px solid rgba(216,226,236,.5); border-radius:var(--radius-lg);
  padding:18px 20px; box-shadow:var(--shadow);
  transition:all .25s cubic-bezier(.4,0,.2,1);
  animation:scaleIn .3s ease both;
}
.er-tile:nth-child(1){animation-delay:0s;} .er-tile:nth-child(2){animation-delay:.05s;}
.er-tile:nth-child(3){animation-delay:.1s;} .er-tile:nth-child(4){animation-delay:.15s;}
.er-tile:nth-child(5){animation-delay:.2s;}
.er-tile::before{
  content:''; position:absolute; top:-20px; right:-20px; width:70px; height:70px;
  border-radius:50%; opacity:.5; pointer-events:none; transition:opacity .25s ease;
}
.er-tile:hover{
  transform:translateY(-3px); border-color:rgba(15,91,120,.15);
  box-shadow:var(--shadow-lg);
}
.er-tile:hover::before{opacity:.8;}
.er-ico{
  flex:0 0 46px; height:46px; border-radius:14px;
  display:flex; align-items:center; justify-content:center;
  box-shadow:var(--shadow-sm);
}
.er-primary{background:linear-gradient(135deg,rgba(15,91,120,.12),rgba(15,91,120,.06)); color:var(--primary);}
.er-accent{background:linear-gradient(135deg,rgba(13,148,136,.12),rgba(13,148,136,.06)); color:#0D9488;}
.er-ok{background:linear-gradient(135deg,rgba(5,150,105,.12),rgba(5,150,105,.06)); color:var(--ok);}
.er-warn{background:linear-gradient(135deg,rgba(217,119,6,.12),rgba(217,119,6,.06)); color:var(--warn);}
.er-err{background:linear-gradient(135deg,rgba(220,38,38,.12),rgba(220,38,38,.06)); color:var(--err);}
.er-slate{background:linear-gradient(135deg,rgba(91,112,131,.1),rgba(91,112,131,.05)); color:var(--muted);}
.er-tile-val{font-size:1.75rem; font-weight:800; line-height:1.1; color:var(--text); letter-spacing:-.02em;}
.er-tile-lbl{font-size:.82rem; color:var(--muted); margin-top:3px; font-weight:500;}

/* ---------- badges ---------- */
.er-badge{
  display:inline-block; padding:4px 12px; border-radius:999px; font-size:.72rem; font-weight:700;
  border:1px solid transparent; white-space:nowrap; letter-spacing:.03em; text-transform:uppercase;
}
.er-badge.er-primary{border-color:rgba(15,91,120,.2); background:rgba(15,91,120,.08);}
.er-badge.er-accent{border-color:rgba(13,148,136,.2); background:rgba(13,148,136,.08);}
.er-badge.er-ok{border-color:rgba(5,150,105,.2); background:rgba(5,150,105,.08);}
.er-badge.er-warn{border-color:rgba(217,119,6,.2); background:rgba(217,119,6,.08);}
.er-badge.er-err{border-color:rgba(220,38,38,.2); background:rgba(220,38,38,.08);}
.er-badge.er-slate{border-color:var(--line); background:var(--slate-tint);}

/* ---------- progress bars & donut ---------- */
.er-bar{margin-bottom:18px; animation:fadeInUp .3s ease both;}
.er-bar-top{display:flex; justify-content:space-between; font-size:.88rem; margin-bottom:7px; color:var(--text);}
.er-bar-num{font-weight:700;}
.er-track{height:10px; background:var(--slate-tint); border-radius:999px; overflow:hidden; box-shadow:inset 0 1px 2px rgba(0,0,0,.04);}
.er-fill{height:100%; border-radius:999px; transition:width .6s cubic-bezier(.4,0,.2,1);}
.er-bg-primary{background:linear-gradient(90deg,var(--primary),var(--primary-light));}
.er-bg-accent{background:linear-gradient(90deg,#0D9488,#14B8A6);}
.er-bg-ok{background:linear-gradient(90deg,#059669,#10B981);}
.er-bg-err{background:linear-gradient(90deg,#DC2626,#EF4444);}
.er-bg-warn{background:linear-gradient(90deg,#D97706,#F59E0B);}
.er-donut-wrap{display:flex; align-items:center; gap:24px; flex-wrap:wrap;}
.er-donut{width:130px; height:130px; border-radius:50%; display:flex; align-items:center; justify-content:center; box-shadow:var(--shadow);}
.er-donut-in{
  width:92px; height:92px; border-radius:50%; background:#FFFFFF; display:flex; flex-direction:column;
  align-items:center; justify-content:center; box-shadow:inset 0 1px 3px rgba(0,0,0,.04);
}
.er-donut-in b{font-size:1.35rem; color:var(--text); font-weight:800;}
.er-donut-in span{font-size:.74rem; color:var(--muted);}
.er-legend{display:flex; flex-direction:column; gap:9px; font-size:.88rem;}
.er-legend i{display:inline-block; width:11px; height:11px; border-radius:50%; margin-right:9px; box-shadow:0 1px 3px rgba(0,0,0,.12);}

/* ---------- decision cards ---------- */
.er-dcard{
  background:var(--glass); backdrop-filter:blur(10px); -webkit-backdrop-filter:blur(10px);
  border:1px solid rgba(216,226,236,.5); border-left:4px solid var(--line);
  border-radius:var(--radius-lg); padding:20px 22px; box-shadow:var(--shadow); margin-bottom:16px;
  transition:all .25s cubic-bezier(.4,0,.2,1);
  animation:fadeInUp .35s ease both;
}
.er-dcard:hover{box-shadow:var(--shadow-lg); transform:translateY(-2px); border-color:rgba(216,226,236,.3);}
.er-dcard.t-err{border-left-color:var(--err);}
.er-dcard.t-primary{border-left-color:var(--primary);}
.er-dcard.t-ok{border-left-color:var(--ok);}
.er-dcard.t-warn{border-left-color:var(--warn);}
.er-dhead, .er-arow{display:flex; justify-content:space-between; align-items:flex-start; gap:12px; flex-wrap:wrap;}
.er-dtitle{font-weight:700; font-size:1.02rem; color:var(--text); letter-spacing:-.01em;}
.er-dmeta{font-size:.82rem; color:var(--muted); margin-top:3px;}
.er-dbadges{display:flex; gap:8px; flex-wrap:wrap;}
.er-grid2{display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:20px; margin-top:16px;}
.er-lbl{font-size:.72rem; color:var(--muted); font-weight:600; margin-bottom:5px; text-transform:uppercase; letter-spacing:.05em;}
.er-val{font-size:.9rem; color:var(--text); line-height:1.55;}
.er-quote{
  font-size:.87rem; color:var(--text); line-height:1.55;
  background:rgba(240,244,248,.7); backdrop-filter:blur(4px); -webkit-backdrop-filter:blur(4px);
  border:1px solid var(--line); border-radius:12px; padding:12px 14px;
}
.er-reason{font-size:.9rem; color:var(--text); line-height:1.55; margin:12px 0 4px 0;}
.er-dcard details{margin-top:14px; border-top:1px solid var(--line); padding-top:12px;}
.er-dcard summary{cursor:pointer; font-size:.85rem; font-weight:700; color:var(--primary); transition:color .15s ease;}
.er-dcard summary:hover{color:var(--primary-light);}
.er-dcard details div{font-size:.88rem; line-height:1.55; margin-top:8px; color:var(--text);}
.er-foot{font-size:.78rem; color:var(--muted); margin-top:10px;}

/* ---------- review agent ---------- */
.er-flow{display:flex; align-items:stretch; gap:12px; flex-wrap:wrap; margin-bottom:8px;}
.er-flow-step{
  flex:1; min-width:180px; border:1px solid var(--line); border-radius:14px;
  padding:12px 16px; background:var(--glass); backdrop-filter:blur(8px); -webkit-backdrop-filter:blur(8px);
  transition:all .2s ease; animation:fadeInUp .3s ease both;
}
.er-flow-step:nth-child(1){animation-delay:0s;} .er-flow-step:nth-child(3){animation-delay:.1s;} .er-flow-step:nth-child(5){animation-delay:.2s;}
.er-flow-step b{display:block; font-size:.88rem; color:var(--text); font-weight:700;}
.er-flow-step span{font-size:.78rem; color:var(--muted); font-weight:400;}
.er-flow-step.review{
  border-color:rgba(13,148,136,.25);
  background:linear-gradient(135deg,rgba(13,148,136,.08),rgba(13,148,136,.03));
}
.er-flow-sep{align-self:center; color:var(--accent); font-size:1.2rem; font-weight:700;}
.er-issue{
  background:linear-gradient(135deg,rgba(217,119,6,.08),rgba(217,119,6,.03));
  border:1px solid rgba(217,119,6,.2); border-radius:12px;
  padding:12px 16px; font-size:.88rem; margin-bottom:8px; color:var(--text);
}
.er-risk{
  background:linear-gradient(135deg,rgba(220,38,38,.08),rgba(220,38,38,.03));
  border:1px solid rgba(220,38,38,.2); border-radius:12px;
  padding:12px 16px; font-size:.88rem; margin-bottom:8px; color:var(--text);
}
.er-note{
  background:linear-gradient(135deg,rgba(15,91,120,.07),rgba(15,91,120,.03));
  border:1px solid rgba(15,91,120,.15); border-radius:12px;
  padding:12px 16px; font-size:.86rem; color:var(--text); margin-top:12px;
}

/* ---------- lifecycle ---------- */
.er-step{display:flex; gap:16px; position:relative; padding-bottom:14px; animation:slideInLeft .3s ease both;}
.er-step:nth-child(1){animation-delay:0s;} .er-step:nth-child(2){animation-delay:.04s;}
.er-step:nth-child(3){animation-delay:.08s;} .er-step:nth-child(4){animation-delay:.12s;}
.er-step:nth-child(5){animation-delay:.16s;} .er-step:nth-child(6){animation-delay:.2s;}
.er-step:nth-child(7){animation-delay:.24s;} .er-step:nth-child(8){animation-delay:.28s;}
.er-step:nth-child(9){animation-delay:.32s;}
.er-step:last-child{padding-bottom:0;}
.er-step:not(:last-child)::before{
  content:""; position:absolute; left:17px; top:40px; bottom:-2px; width:2px;
  background:var(--line); transition:background .3s ease;
}
.er-step.done:not(:last-child)::before{background:linear-gradient(180deg,var(--ok),rgba(5,150,105,.4));}
.er-node{
  flex:0 0 36px; height:36px; border-radius:50%; display:flex; align-items:center; justify-content:center;
  font-weight:700; font-size:.85rem; border:2px solid var(--line); background:#FFFFFF; color:var(--muted); z-index:1;
  transition:all .3s ease;
}
.er-step.done .er-node{
  background:linear-gradient(135deg,var(--ok),#10B981); border-color:var(--ok); color:#FFFFFF;
  box-shadow:0 2px 8px rgba(5,150,105,.25);
}
.er-step.prog .er-node{
  border-color:var(--primary); color:var(--primary);
  background:linear-gradient(135deg,rgba(15,91,120,.1),rgba(15,91,120,.05));
  box-shadow:0 0 0 4px rgba(15,91,120,.1), 0 2px 8px rgba(15,91,120,.12);
}
.er-step.rev .er-node{border-color:var(--err); color:var(--err); background:rgba(220,38,38,.06); box-shadow:0 2px 8px rgba(220,38,38,.12);}
.er-step.na .er-node{border-style:dashed; opacity:.6;}
.er-step-body{
  flex:1; background:var(--glass); backdrop-filter:blur(8px); -webkit-backdrop-filter:blur(8px);
  border:1px solid rgba(216,226,236,.5); border-radius:14px; padding:14px 18px;
  display:flex; justify-content:space-between; align-items:center; gap:12px; flex-wrap:wrap;
  transition:all .2s ease; box-shadow:var(--shadow-sm);
}
.er-step:hover .er-step-body{box-shadow:var(--shadow); border-color:rgba(15,91,120,.1);}
.er-step-title{font-weight:700; font-size:.95rem; color:var(--text);}
.er-step-desc{font-size:.82rem; color:var(--muted); margin-top:2px;}
.er-mini{display:grid; grid-template-columns:repeat(auto-fit,minmax(118px,1fr)); gap:10px;}
.er-mini-item{
  background:var(--glass); backdrop-filter:blur(8px); -webkit-backdrop-filter:blur(8px);
  border:1px solid rgba(216,226,236,.5); border-top:3px solid var(--line);
  border-radius:14px; padding:12px 14px; transition:all .2s ease;
}
.er-mini-item:hover{box-shadow:var(--shadow); transform:translateY(-1px);}
.er-mini-item.done{border-top-color:var(--ok);}
.er-mini-item.prog{border-top-color:var(--primary);}
.er-mini-item.rev{border-top-color:var(--err);}
.er-mini-title{font-size:.8rem; font-weight:700; color:var(--text); min-height:2.2em;}
.er-mini-status{font-size:.74rem; color:var(--muted); margin-top:4px;}

/* ---------- cert preview card ---------- */
.er-cert-frame{
  background:linear-gradient(145deg, #FFFFFF 0%, #F8FAFC 100%);
  border:2px solid #CBD5E1; border-radius:20px; padding:32px 36px;
  box-shadow:0 12px 36px rgba(15,29,43,.08); position:relative; overflow:hidden;
  margin-bottom:24px;
}
.er-cert-frame::before{
  content:''; position:absolute; top:0; left:0; right:0; height:6px;
  background:linear-gradient(90deg, #0F5B78 0%, #0D9488 50%, #059669 100%);
}
.er-cert-header{display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:24px; border-bottom:1px solid #E2E8F0; padding-bottom:18px;}
.er-cert-title{font-size:1.35rem; font-weight:800; color:#0F1D2B; letter-spacing:-.02em;}
.er-cert-sub{font-size:.82rem; color:#64748B; margin-top:3px;}
.er-cert-badge{
  display:inline-flex; align-items:center; gap:6px; background:rgba(5,150,105,.1);
  color:#065F46; border:1px solid rgba(5,150,105,.25); border-radius:999px;
  padding:6px 14px; font-size:.76rem; font-weight:700; text-transform:uppercase; letter-spacing:.05em;
}
.er-cert-grid{display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:18px; margin-bottom:22px;}
.er-cert-cell b{display:block; font-size:.72rem; color:#64748B; text-transform:uppercase; letter-spacing:.05em; margin-bottom:4px;}
.er-cert-cell span{font-size:.95rem; font-weight:600; color:#0F1D2B;}
.er-cert-footer{
  display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:14px;
  margin-top:20px; padding-top:16px; border-top:1px dashed #CBD5E1; font-size:.8rem; color:#64748B;
}

/* ---------- quick fill chips ---------- */
.er-preset-chip{
  display:inline-flex; align-items:center; gap:6px; background:#FFFFFF;
  border:1px solid #D8E2EC; border-radius:999px; padding:6px 14px;
  font-size:.82rem; font-weight:600; color:#0F5B78; cursor:pointer;
  transition:all .2s ease; margin-right:8px; margin-bottom:8px;
}
.er-preset-chip:hover{background:#E8F3F7; border-color:#0F5B78; transform:translateY(-1px);}

/* ---------- confidence meter ---------- */
.er-conf-bar{display:flex; align-items:center; gap:10px; margin-top:8px;}
.er-conf-track{flex:1; height:6px; background:#E2E8F0; border-radius:999px; overflow:hidden;}
.er-conf-fill{height:100%; border-radius:999px; background:linear-gradient(90deg, #0D9488, #059669);}
.er-conf-text{font-size:.78rem; font-weight:700; color:#0F1D2B; min-width:45px;}

/* ---------- safeguards status pills ---------- */
.er-safeguard-card{
  display:flex; align-items:center; gap:14px; background:var(--glass);
  backdrop-filter:blur(10px); border:1px solid rgba(216,226,236,.6);
  border-radius:14px; padding:14px 18px; margin-bottom:12px;
}
.er-safeguard-dot{width:10px; height:10px; border-radius:50%; background:#059669; box-shadow:0 0 0 3px rgba(5,150,105,.2);}
.er-safeguard-title{font-size:.88rem; font-weight:700; color:var(--text);}
.er-safeguard-desc{font-size:.78rem; color:var(--muted); margin-top:1px;}

/* ---------- misc ---------- */
.er-empty{
  background:var(--glass); backdrop-filter:blur(12px); -webkit-backdrop-filter:blur(12px);
  border:2px dashed rgba(91,112,131,.2); border-radius:var(--radius-lg);
  padding:40px 28px; text-align:center; animation:fadeInUp .4s ease;
}
.er-empty b{display:block; font-size:1.05rem; color:var(--text); margin-bottom:6px; font-weight:700;}
.er-empty span{font-size:.9rem; color:var(--muted);}
.er-summary{display:flex; gap:32px; flex-wrap:wrap;}
.er-summary div b{display:block; font-size:.7rem; color:var(--muted); font-weight:600; text-transform:uppercase; letter-spacing:.05em;}
.er-summary div span{font-size:.95rem; font-weight:700; color:var(--text);}
.er-footer{
  margin-top:40px; padding-top:18px; border-top:1px solid var(--line);
  font-size:.78rem; color:var(--muted); line-height:1.6;
}
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
        '<defs><linearGradient id="lg1" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">'
        '<stop stop-color="#0F5B78"/><stop offset="1" stop-color="#0D9488"/></linearGradient>'
        '<linearGradient id="lg2" x1="15" y1="18" x2="25" y2="26" gradientUnits="userSpaceOnUse">'
        '<stop stop-color="#14B8A6"/><stop offset="1" stop-color="#06B6D4"/></linearGradient></defs>'
        '<rect width="40" height="40" rx="12" fill="url(#lg1)"/>'
        '<path d="M20 8.5 29 12v7.2c0 5.3-3.6 9.6-9 11.3-5.4-1.7-9-6-9-11.3V12l9-3.5z" '
        'fill="rgba(255,255,255,.95)" stroke="#FFFFFF" stroke-width="1.4" stroke-linejoin="round"/>'
        '<path d="m15.6 20.2 3.2 3.2 5.6-6.4" stroke="url(#lg2)" stroke-width="2.6" '
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
        f'<div class="er-topbar"><div class="er-brand">{logo(48)}'
        '<div><div class="er-name">EraseRight</div>'
        '<div class="er-tag">Intelligent Data Subject Request Fulfilment System</div></div></div>'
        '<div class="er-status"><span class="er-dot"></span>AI Protection Active</div></div>'
    )


def render_sidebar():
    ss = st.session_state

    with st.sidebar:

        md(
            f'<div class="er-side-brand">{logo(40)}<div><div class="er-side-name">EraseRight</div>'
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
        f'<div class="er-footer"><div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">'
        f'{logo(22)}<span style="font-weight:700;color:var(--text)">EraseRight</span></div>'
        'Intelligent Data Subject Request Fulfilment System.<br>'
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

    col_left, col_right = st.columns([3, 2])

    with col_left:
        with card("overview_intro"):
            md(
                '<div class="er-panel-title">Privacy request operations</div>'
                '<div class="er-section-sub" style="margin-top:6px;line-height:1.6">'
                'Submit an access or erasure request, discover matching records, '
                'review policy-grounded AI recommendations, and complete the process '
                'with human approval, verification and an auditable record.'
                '</div>'
            )
            st.write("")
            c1, c2 = st.columns(2)
            with c1:
                st.button(
                    "Start a privacy request", key="overview_start_request",
                    type="primary", use_container_width=True,
                    on_click=go_to, args=(P_SUBMIT,)
                )
            with c2:
                st.button(
                    "▶ Start guided demo", key="overview_start_demo",
                    use_container_width=True, on_click=start_guided_demo
                )

    with col_right:
        with card("overview_how"):
            md(
                '<div class="er-panel-title">How it works</div>'
                '<div class="er-steps-list">'
                '<div class="er-steps-item"><div class="er-steps-num">1</div><div class="er-steps-text">Submit request'
                '<span>Capture data subject identity and request type.</span></div></div>'
                '<div class="er-steps-item"><div class="er-steps-num">2</div><div class="er-steps-text">AI analysis'
                '<span>Policy-grounded proposals with independent review.</span></div></div>'
                '<div class="er-steps-item"><div class="er-steps-num">3</div><div class="er-steps-text">Human approval'
                '<span>Nothing executes without your explicit sign-off.</span></div></div>'
                '<div class="er-steps-item"><div class="er-steps-num">4</div><div class="er-steps-text">Execute &amp; verify'
                '<span>Auditable execution with post-action verification.</span></div></div>'
                '</div>'
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
        st.caption("Quick fill sample subject (1-click test):")
        pcol1, pcol2, pcol3 = st.columns(3)
        with pcol1:
            if st.button("👤 Aarav Sharma", key="preset_aarav", use_container_width=True):
                st.session_state["form_name"] = "Aarav Sharma"
                st.session_state["form_email"] = "aarav@example.com"
                st.session_state["form_customer_id"] = "C101"
                st.rerun()
        with pcol2:
            if st.button("👤 Priya Nair", key="preset_priya", use_container_width=True):
                st.session_state["form_name"] = "Priya Nair"
                st.session_state["form_email"] = "priya@example.com"
                st.session_state["form_customer_id"] = "C102"
                st.rerun()
        with pcol3:
            if st.button("👤 Rahul Kumar", key="preset_rahul", use_container_width=True):
                st.session_state["form_name"] = "Rahul Kumar"
                st.session_state["form_email"] = "rahul@example.com"
                st.session_state["form_customer_id"] = "C103"
                st.rerun()

        with st.form("privacy_request_form"):

            request_type = st.selectbox(
                "Request type",
                [ERASURE, ACCESS]
            )

            name = st.text_input(
                "Full name",
                value=st.session_state.get("form_name", ""),
                placeholder="Enter full name"
            )

            email = st.text_input(
                "Email address",
                value=st.session_state.get("form_email", ""),
                placeholder="Enter email address"
            )

            customer_id = st.text_input(
                "Customer ID",
                value=st.session_state.get("form_customer_id", ""),
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
    confidence_html = ""
    if isinstance(confidence, (int, float)):
        conf_pct = int(float(confidence) * 100)
        conf_color = "#059669" if conf_pct >= 85 else "#D97706" if conf_pct >= 70 else "#DC2626"
        confidence_html = (
            f'<div class="er-conf-bar">'
            f'<span class="er-lbl" style="margin:0;min-width:75px">Confidence:</span>'
            f'<div class="er-conf-track"><div class="er-conf-fill" style="width:{conf_pct}%;background:{conf_color}"></div></div>'
            f'<span class="er-conf-text" style="color:{conf_color}">{conf_pct}%</span>'
            f'</div>'
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
        f'<div class="er-dtitle">Record #{esc(decision.get("record_id"))} · <span style="font-weight:500;color:var(--muted)">{esc(decision.get("data_type", "Unknown type"))}</span></div>'
        f'<div class="er-dmeta">Source: <b>{esc(decision.get("source", "unknown source"))}</b></div></div>'
        f'<div class="er-dbadges">{action_badge(action)}'
        f'{status_badge(decision.get("approval_status", "PENDING"))}</div></div>'
        '<div class="er-grid2">'
        f'<div><div class="er-lbl">AI Reasoning &amp; Proposal</div><div class="er-val">{fmt_text(decision.get("reason"))}</div>{confidence_html}</div>'
        '<div><div class="er-lbl">Retrieved Policy Evidence</div>'
        f'<div class="er-quote">{fmt_text(decision.get("policy_evidence"), "No relevant policy passage retrieved. The safe outcome is review, not an assumed legal rule.")}</div>'
        f'{source_html}</div>'
        f'</div>{risk_html}{next_html}{analysis_html}{llm_html}</div>'
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
        md(
            f'<div class="er-cert-frame">'
            f'<div class="er-cert-header"><div>'
            f'<div class="er-cert-title">Sample Erasure Certificate Preview</div>'
            f'<div class="er-cert-sub">Demonstration of verifiable completion certificate</div></div>'
            f'<div class="er-cert-badge">{svg("verified", 14, 2.5)} PREVIEW MODE</div></div>'
            f'<div class="er-cert-grid">'
            f'<div class="er-cert-cell"><b>Certificate ID</b><span>DEMO-ER-2026-001</span></div>'
            f'<div class="er-cert-cell"><b>Data Subject</b><span>Alex Demo</span></div>'
            f'<div class="er-cert-cell"><b>Customer ID</b><span>DEMO-1001</span></div>'
            f'<div class="er-cert-cell"><b>Request Scope</b><span>Erasure Request</span></div>'
            f'<div class="er-cert-cell"><b>Destructive Actions</b><span>2 Proposed</span></div>'
            f'<div class="er-cert-cell"><b>Execution Status</b><span>Simulation (Read-Only)</span></div>'
            f'</div>'
            f'<div class="er-cert-footer"><span>Issued by EraseRight Privacy Engine · Standard GDPR Art. 17 Verification</span>'
            f'<span style="font-family:monospace;font-size:.74rem">PREVIEW ONLY · REAL PDF ISSUED POST-APPROVAL</span></div>'
            f'</div>'
        )
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

    md(
        f'<div class="er-cert-frame">'
        f'<div class="er-cert-header"><div>'
        f'<div class="er-cert-title">Data Subject Request Processing Certificate</div>'
        f'<div class="er-cert-sub">Cryptographically signed &amp; verified fulfilment record</div></div>'
        f'<div class="er-cert-badge">{svg("verified", 14, 2.5)} COMPLIANCE VERIFIED</div></div>'
        f'<div class="er-cert-grid">'
        f'<div class="er-cert-cell"><b>Certificate ID</b><span>{esc(ss["request_id"])}</span></div>'
        f'<div class="er-cert-cell"><b>Data Subject</b><span>{esc(details.get("name"))}</span></div>'
        f'<div class="er-cert-cell"><b>Customer ID</b><span>{esc(details.get("customer_id"))}</span></div>'
        f'<div class="er-cert-cell"><b>Request Scope</b><span>{esc(details.get("request_type"))}</span></div>'
        f'<div class="er-cert-cell"><b>Verification Status</b><span>{verified_n} of {len(results)} Verified</span></div>'
        f'<div class="er-cert-cell"><b>Audit Log Status</b><span>Immutable Ledger Stored</span></div>'
        f'</div>'
        f'<div class="er-cert-footer"><span>Issued by EraseRight Privacy Engine · Standard GDPR Art. 17 Verification</span>'
        f'<span style="font-family:monospace;font-size:.74rem">HASH: SHA256:{abs(hash(str(ss["request_id"]))) :016x}</span></div>'
        f'</div>'
    )

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