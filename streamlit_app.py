import streamlit as st
import requests
import uuid

BACKEND_URL = "http://127.0.0.1:8000/chat"

st.set_page_config(page_title="Loan Voice Agent", page_icon="📞")

st.title("📞 Loan Status Voice Agent")
st.caption("🎤 Simulating a voice call (using text as placeholder)")

# Session setup - generates new UUID each time Streamlit restarts
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.session_state.conversation_ended = False
    st.session_state.call_started = False

# Reset button
col1, col2 = st.columns([6, 1])
with col2:
    if st.button("🔄 New Call"):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.session_state.conversation_ended = False
        st.session_state.call_started = False
        st.rerun()

# Show call status
if not st.session_state.call_started and not st.session_state.messages:
    st.info("📞 Click 'Start Call' to begin")
    if st.button("📞 Start Call", type="primary"):
        st.session_state.call_started = True
        # Trigger initial greeting
        try:
            response = requests.post(
                BACKEND_URL,
                json={
                    "session_id": st.session_state.session_id,
                    "message": ""
                },
                timeout=10
            )
            if response.status_code == 200:
                result = response.json()
                agent_response = result.get("response", "")
                st.session_state.messages.append(("Agent", agent_response))
                st.rerun()
        except Exception as e:
            st.error("Could not connect to backend")
elif st.session_state.conversation_ended:
    st.success("✅ Call ended")
else:
    st.info("📞 Call in progress...")

# ---- CHAT HISTORY (TOP) ----
chat_container = st.container()
with chat_container:
    for sender, msg in st.session_state.messages:
        if sender == "Agent":
            st.markdown(f"**🤖 Agent:** {msg}")
        else:
            st.markdown(f"**🧑 You:** {msg}")

st.divider()

# ---- INPUT (BOTTOM) ----
# Disable input if conversation has ended or not started
input_disabled = st.session_state.conversation_ended or not st.session_state.call_started

with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_input(
        "What you say (simulating voice input):",
        disabled=input_disabled,
        placeholder="Say something..." if st.session_state.call_started else "Click 'Start Call' first"
    )
    submitted = st.form_submit_button("🎤 Speak", disabled=input_disabled)

if submitted and user_input.strip():
    try:
        # Call backend
        response = requests.post(
            BACKEND_URL,
            json={
                "session_id": st.session_state.session_id,
                "message": user_input
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            agent_response = result.get("response", "")
            
            # Add messages to history
            st.session_state.messages.append(("You", user_input))
            st.session_state.messages.append(("Agent", agent_response))
            
            # Check if conversation ended
            if result.get("ended", False) or "[Call ended]" in agent_response:
                st.session_state.conversation_ended = True
            
            st.rerun()
        else:
            st.error(f"Backend error: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        st.error(f"Could not connect to backend. Make sure the FastAPI server is running on port 8000.")
        st.exception(e)

# ---- SIDEBAR INFO ----
with st.sidebar:
    st.header("ℹ️ Call Simulation Info")
    st.write("**Session ID:**")
    st.code(st.session_state.session_id[:8] + "...")
    
    st.write("**Test Scenario:**")
    st.info("This simulates a voice call where:\n"
            "- Caller ID is auto-detected\n"
            "- Agent asks for confirmation\n"
            "- Text input = voice input\n"
            "- Agent responses = voice output")
    
    st.write("**Test Phone Numbers:**")
    st.code("9999999999 → UNDER_REVIEW")
    st.code("8888888888 → APPROVED")
    st.code("Any other → NOT_FOUND")
    
    st.write("**Voice Commands:**")
    st.markdown("""
    - "yes" / "no" → Confirm/decline
    - "retry" → Try different number
    - "agent" → Talk to human
    """)
    
    st.write("**Features:**")
    st.markdown("""
    - ✅ Caller ID detection
    - ✅ Phone number confirmation
    - ✅ Intelligent LLM fallback
    - ✅ Contextual goodbyes
    - ✅ Agent handoff simulation
    """)