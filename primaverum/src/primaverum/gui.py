import streamlit as st
import sys
import os
import time
from datetime import datetime
from io import StringIO
from dotenv import load_dotenv

# Load environment variables (API Keys)
load_dotenv()

# Add the src directory to the path so we can import the crew
sys.path.append(os.path.join(os.getcwd(), "src"))

from primaverum.crew import Primaverum

st.set_page_config(page_title="Agent Interface: LogicModel Evolution", page_icon="🏛️", layout="wide")

st.title("🏛️ agentLogicTrainingSession")
st.markdown("---")

# Persistent Evolution Log
LOG_FILE = "LogicModel_Evolution_Log.md"

def load_log():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            return f.read()
    return "No formal logic integrated in LogicModel yet."

# Sidebar for History & Stats
with st.sidebar:
    st.header("⚙️ Session Status")
    
    # Cumulative Log Sidebar
    st.markdown("### 📚 LogicModel History")
    full_log = load_log()
    st.markdown(full_log)
    
    if st.button("📖 View Full Evolution Log", use_container_width=True):
        st.session_state.show_history = True

    st.divider()
    st.markdown("### 🧬 Hardware Nodes")
    st.info("K11 NUC: Control Plane (You are here)\nTrainer: don1 (Voice Router / Bridge)\nLogicAgent: don2 (LogicModel — Tabula Rasa)")
    
    if st.button("🗑️ Reset All Sessions", use_container_width=True):
        st.session_state.messages = []
        st.session_state.current_proposal = None
        st.session_state.run_integration = False
        st.rerun()

# Main History Modal
if st.session_state.get("show_history", False):
    st.header("📚 Full LogicModel Evolution Log")
    st.markdown(full_log)
    if st.button("✖️ Close History"):
        st.session_state.show_history = False
    st.divider()

# Chat interface init
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_proposal" not in st.session_state:
    st.session_state.current_proposal = None

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Action Buttons Area (Only visible when needed)
if st.session_state.current_proposal and not st.session_state.get("run_integration", False):
    st.info("⚠️ **Action Required**: agentLogicTrainingSession_proposal generated.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Approve Integration", use_container_width=True):
            st.session_state.run_integration = True
            st.rerun()
    with col2:
        if st.button("❌ Reject Proposal", use_container_width=True):
            st.session_state.current_proposal = None
            st.rerun()

# --- TRAINING PHASES ---

# PHASE 1: Generate Proposal (Trainer)
if st.button("🚀 Start agentLogicTrainingSession", disabled=st.session_state.current_proposal is not None):
    with st.chat_message("assistant"):
        with st.status("🧠 Trainer (don1): Performing SystemAudit & LogicRequirement...", expanded=True) as status:
            try:
                primaverum = Primaverum()
                trainer = primaverum.Trainer()
                
                # Execute the proposal task
                result = trainer.kickoff("Audit system stability and derive the next logical string required for the LogicModel.")
                
                proposal_text = f"### 📄 **agentLogicTrainingSession_proposal**\n\n{result.raw}"
                st.session_state.current_proposal = result.raw
                st.session_state.messages.append({"role": "assistant", "content": proposal_text})
                st.markdown(proposal_text)
                status.update(label="Proposal Generated!", state="complete")
            except Exception as e:
                st.error(f"Trainer failed: {e}")
    st.rerun()

# PHASE 2: Integration (LogicAgent)
if st.session_state.get("run_integration", False):
    st.session_state.run_integration = False
    proposal = st.session_state.current_proposal
    st.session_state.current_proposal = None 
    
    with st.chat_message("assistant"):
        with st.status("🧬 LogicAgent (don2): Integrating Proofs into LogicModel...", expanded=True) as status:
            try:
                primaverum = Primaverum()
                logic_agent = primaverum.LogicAgent()
                
                # LogicAgent processes the approved proposal
                result = logic_agent.kickoff(f"Integrate this approved LogicRequirement: {proposal}.")
                
                integration_text = f"### 🧬 **LogicModel Integration Complete**\n\n{result.raw}"
                st.session_state.messages.append({"role": "assistant", "content": integration_text})
                st.markdown(integration_text)
                
                # PHASE 3: Update Log (Trainer)
                st.write("Trainer: Distilling results and updating Evolution Log...")
                trainer = primaverum.Trainer()
                log_update = trainer.kickoff(f"Update LogicModel_Evolution_Log.md with this integration results: {result.raw}")
                
                st.success("✅ Log updated. agentLogicTrainingSession finalized.")
                status.update(label="Session complete!", state="complete")
            except Exception as e:
                st.error(f"LogicAgent failed: {e}")
    st.rerun()

# Chat input for conversation (Direct to Trainer)
if prompt := st.chat_input("Talk to Trainer (don1)..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Trainer is distilling intent..."):
            try:
                # We must use the instance from Primaverum to get the configured LLM
                primaverum_instance = Primaverum()
                trainer_agent = primaverum_instance.Trainer()
                
                result = trainer_agent.kickoff(prompt)
                response = result.raw
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"Error: {e}")
