"""
KentaurOSPS Dashboard v3.4.0 — Live monitoring for the immortal Kentaur.
"""
import os
import sys
import time

# Ensure project root is on path
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import streamlit as st
from datetime import datetime
from kentaur_osps import KentaurMind, KentaurMemory

st.set_page_config(page_title="KentaurOSPS Dashboard", layout="wide", page_icon="🐴")
st.title("🐴 KentaurOSPS — Live Monitoring")

# --- Initialize ---
if "mind" not in st.session_state:
    st.session_state.mind = KentaurMind(initial_profile="integrator")
    st.session_state.memory = KentaurMemory()
    st.session_state.history = []
    st.session_state.profile_history = []

mind = st.session_state.mind
memory = st.session_state.memory

# --- Sidebar ---
st.sidebar.header("⚙️ Controls")
auto_refresh = st.sidebar.checkbox("Auto-refresh every 5s", value=True)
refresh_rate = st.sidebar.slider("Refresh rate (seconds)", 3, 30, 5)
st.sidebar.divider()
st.sidebar.caption(f"KentaurOSPS v3.4.0")
st.sidebar.caption(f"Session started: {datetime.now():%H:%M:%S}")

# --- Heartbeat ---
current_vector = {"AcOr": 0.5, "IP": 0.5, "InEx": 0.0}
verdict = mind.process(
    current_vector,
    {"temperature": 0.7, "available_tools": [], "system_prompt": "Dashboard heartbeat"}
)

# --- Main layout ---
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("🧠 Current State")
    st.metric("Archetype", verdict.current_profile.upper())
    st.metric("Tension", f"{verdict.report.tension:.3f}")
    st.metric("Risk", verdict.report.risk.upper())

with col2:
    st.subheader("⚡ OSPS Metrics")
    st.metric("Phi_OSPS", f"{verdict.report.phi_osps:.3f}")
    st.metric("K_res", f"{verdict.report.k_res:.3f}")
    st.metric("Fuse Conflicts", verdict.report.fuse_conflicts)

with col3:
    st.subheader("🔄 Attractors")
    st.metric("ATTR_0 (Source)", f"{verdict.report.attr_0:.3f}")
    st.metric("ATTR_T (Spirit)", f"{verdict.report.attr_t:.3f}")
    st.metric("K_flow", f"{verdict.report.k_flow:.3f}")

# --- Recent Reflexes ---
st.subheader("🧬 Recent Reflexes")
reflexes = memory.recall(current_vector, top_k=5)
if reflexes:
    for r in reflexes:
        st.write(f"**{r.outcome.upper()}** ({r.similarity:.0%} match) — {r.lesson[:80]}...")
else:
    st.info("No reflexes yet. Memory is empty.")

# --- History chart ---
st.subheader("📈 Phi_OSPS History")

# Auto-record heartbeat to history
if "last_phi" not in st.session_state or st.session_state.last_phi != verdict.report.phi_osps:
    st.session_state.history.append(verdict.report.phi_osps)
    st.session_state.profile_history.append(verdict.current_profile)
    st.session_state.last_phi = verdict.report.phi_osps

if st.session_state.history:
    st.line_chart(st.session_state.history[-50:])
    st.caption(f"Last {min(len(st.session_state.history), 50)} heartbeats")
else:
    st.info("No data yet. Click 'Simulate heartbeat' or enable auto-refresh.")

# --- Directive log ---
st.subheader("📋 Last Directive")
directive = verdict.directives_for_prompt
if directive and directive != "No directives.":
    with st.expander("View directive"):
        st.code(directive)
else:
    st.caption("No active directives.")

# --- Auto-refresh ---
if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()

st.caption("🐴 KentaurOSPS v3.4.0 — Live Dashboard | Immortal since v3.3.0")
