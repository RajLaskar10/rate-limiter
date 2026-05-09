import time

import pandas as pd
import requests
import streamlit as st

try:
    API_URL = st.secrets["API_URL"]
except (KeyError, FileNotFoundError):
    API_URL = "http://localhost:8000"

st.set_page_config(page_title="Rate Limiter Dashboard", layout="wide")
st.title("Rate Limiter Dashboard")

# --- Sidebar Controls ---
st.sidebar.header("Controls")
identifier = st.sidebar.text_input("Identifier", value="user-1")
rule = st.sidebar.selectbox("Rule", ["default", "strict", "relaxed"])
rps = st.sidebar.slider("Requests per second", min_value=1, max_value=50, value=5)
running = st.sidebar.toggle("Send requests", value=False)

# --- Session State ---
if "allowed_count" not in st.session_state:
    st.session_state.allowed_count = 0
if "blocked_count" not in st.session_state:
    st.session_state.blocked_count = 0
if "token_history" not in st.session_state:
    st.session_state.token_history = []
if "result_history" not in st.session_state:
    st.session_state.result_history = []

# --- Metrics ---
col1, col2, col3 = st.columns(3)
col1.metric("Allowed", st.session_state.allowed_count)
col2.metric("Blocked", st.session_state.blocked_count)

# Fetch current token level
try:
    stats_resp = requests.get(f"{API_URL}/stats/{identifier}", params={"rule": rule}, timeout=2)
    if stats_resp.ok:
        stats_data = stats_resp.json()
        col3.metric("Tokens Remaining", stats_data["tokens"])
    else:
        col3.metric("Tokens Remaining", "N/A")
except requests.exceptions.ConnectionError:
    col3.metric("Tokens Remaining", "N/A")
    st.error(f"Could not connect to the API at {API_URL}")

# --- Charts ---
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("Token Level Over Time")
    if st.session_state.token_history:
        df_tokens = pd.DataFrame(st.session_state.token_history, columns=["time", "tokens"])
        st.line_chart(df_tokens.set_index("time"))
    else:
        st.info("No data yet. Toggle 'Send requests' to start.")

with chart_col2:
    st.subheader("Allowed vs Blocked")
    if st.session_state.result_history:
        df_results = pd.DataFrame(st.session_state.result_history, columns=["time", "result"])
        counts = df_results["result"].value_counts()
        st.bar_chart(counts)
    else:
        st.info("No data yet.")

# --- Request Loop ---
if running:
    delay = 1.0 / rps
    placeholder = st.empty()

    try:
        resp = requests.post(
            f"{API_URL}/check",
            json={"identifier": identifier, "rule": rule},
            timeout=2,
        )
        if resp.ok:
            data = resp.json()
            if data["allowed"]:
                st.session_state.allowed_count += 1
                st.session_state.result_history.append((time.time(), "allowed"))
            else:
                st.session_state.blocked_count += 1
                st.session_state.result_history.append((time.time(), "blocked"))

            st.session_state.token_history.append((time.time(), data["tokens_remaining"]))
            placeholder.json(data)
        else:
            placeholder.error(f"API error: {resp.status_code}")
    except requests.exceptions.ConnectionError:
        st.error(f"Could not connect to the API at {API_URL}")

    time.sleep(delay)
    st.rerun()

# --- Reset Button ---
if st.sidebar.button("Reset Counters"):
    st.session_state.allowed_count = 0
    st.session_state.blocked_count = 0
    st.session_state.token_history = []
    st.session_state.result_history = []
    st.rerun()
