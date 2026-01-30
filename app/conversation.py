import json
from app.integrations.loan_system import get_loan_status
from app.llm_router import llm_route, llm_fallback


# ============================================================
# Load the conversation flow ONCE at startup
# FLOW is a dict: state_name -> state_definition
# ============================================================
with open("flows/loan_status_flow.json") as f:
    FLOW = json.load(f)


def render_prompt(node: dict, session: dict) -> str:
    """
    Renders a prompt for the user.

    Input:
    - node: current flow node
    - session: conversation session state

    Output:
    - string shown to user
    """
    prompt = node.get("prompt", "")
    
    # Replace template variables
    if "{{status}}" in prompt:
        prompt = prompt.replace("{{status}}", session.get("loan_status", "UNKNOWN"))
    
    return prompt


def handle_turn(user_input: str, session: dict):
    """
    Handles ONE conversational turn.

    Input:
    - user_input: text user just typed (string)
    - session: mutable dict holding conversation state

    Output:
    - (response_text, updated_session)
    """

    # --------------------------------------------------------
    # 0. TERMINAL GUARD
    # --------------------------------------------------------
    if session.get("ended"):
        # For calls, silence after handoff/goodbye is appropriate
        return (
            "[Call ended]",
            session
        )
    
    # --------------------------------------------------------
    # 0.5. INITIALIZE CALLER ID (simulates incoming call)
    # --------------------------------------------------------
    if "caller_id" not in session:
        import random
        # Generate random 10-digit phone number (simulating caller ID)
        session["caller_id"] = "".join([str(random.randint(0, 9)) for _ in range(10)])
        print(f"DEBUG | Incoming call from: {session['caller_id']}")

    # --------------------------------------------------------
    # 1. RESOLVE CURRENT STATE SAFELY
    # --------------------------------------------------------
    # Never allow None or invalid states
    state = session.get("state") or "start"
    if state not in FLOW:
        state = "start"

    session["state"] = state
    node = FLOW[state]

    # --------------------------------------------------------
    # 2. INITIAL GREETING (start state only)
    # --------------------------------------------------------
    # On first interaction, show greeting with caller ID confirmation
    if state == "start" and not session.get("greeted"):
        session["greeted"] = True
        caller_id = session["caller_id"]
        formatted_number = f"{caller_id[:3]}-{caller_id[3:6]}-{caller_id[6:]}"
        return (
            f"Hello! I can help you check your loan status. "
            f"I see you're calling from {formatted_number}. "
            f"Is this the number associated with your loan application?",
            session
        )

    # --------------------------------------------------------
    # 3. ACTION STATES (consume user input)
    # --------------------------------------------------------
    # These states CONSUME user input and do work
    # --------------------------------------------------------

    # -------- VERIFY PHONE NUMBER --------
    if node.get("action") == "verify_phone":
        # INPUT EXPECTED: phone number (digits)

        # If no input yet (transitioning from start), wait for input
        if not user_input.strip():
            return render_prompt(node, session), session

        # Validate phone number
        if not user_input.isdigit() or len(user_input) < 8:
            # Invalid input → intelligent LLM fallback
            return llm_fallback(user_input, session), session

        phone = user_input.strip()
        session["phone"] = phone

        status = get_loan_status(phone)
        print("DEBUG | loan lookup:", repr(phone), "→", status)

        if status == "NOT_FOUND":
            session["state"] = node["on_failure"]
        else:
            session["loan_status"] = status
            session["state"] = node["on_success"]

        print("DEBUG | transition after verify:", session["state"])

        # Continue to next state automatically
        return handle_turn("", session)
    
    # -------- VERIFY CALLER ID --------
    if node.get("action") == "verify_phone_from_caller_id":
        # Use the caller ID from session
        phone = session.get("caller_id")
        session["phone"] = phone

        status = get_loan_status(phone)
        print("DEBUG | caller ID lookup:", repr(phone), "→", status)

        if status == "NOT_FOUND":
            session["state"] = node["on_failure"]
        else:
            session["loan_status"] = status
            session["state"] = node["on_success"]

        # Continue to next state automatically
        return handle_turn("", session)
    
    # -------- TRANSFER TO AGENT --------
    if node.get("action") == "transfer_to_agent":
        # Simulate call transfer with hold music
        session["ended"] = True
        return (
            "[Transferring call... Hold music plays... Agent picks up]\n"
            "Agent: Hello, this is the loan department. How can I help you today?",
            session
        )
    
    # -------- GENERATE LLM GOODBYE --------
    if node.get("action") == "generate_goodbye":
        from app.llm_router import llm_generate_goodbye
        
        goodbye_message = llm_generate_goodbye(session)
        session["ended"] = True
        return goodbye_message, session
    
    # -------- GENERATE LLM GOODBYE AFTER SMS --------
    if node.get("action") == "llm_goodbye_after_sms":
        from app.llm_router import llm_generate_goodbye_after_sms
        
        goodbye_message = llm_generate_goodbye_after_sms(session)
        session["ended"] = True
        return goodbye_message, session

    # --------------------------------------------------------
    # 4. DECISION STATES (LLM-routed)
    # --------------------------------------------------------
    # These states expect free-text like:
    # "retry", "another number", "connect me to agent"
    #
    # INPUT: user_input
    # OUTPUT: next state OR clarification
    # --------------------------------------------------------
    if "allowed_actions" in node:
        # First time entering decision state → prompt user
        if session.get("last_prompted_state") != state:
            session["last_prompted_state"] = state
            return render_prompt(node, session), session

        # If no input, wait
        if not user_input.strip():
            return render_prompt(node, session), session

        # Now interpret user's choice
        action = llm_route(
            user_input,
            list(node["allowed_actions"].keys())
        )

        if action:
            session["state"] = node["allowed_actions"][action]
            session.pop("last_prompted_state", None)
            return handle_turn("", session)

        # User said something unclear - give helpful prompt with options
        options_text = " or ".join(f"'{opt}'" for opt in node["allowed_actions"].keys())
        return (
            f"I didn't quite understand that. Please say {options_text}.",
            session
        )

    # --------------------------------------------------------
    # 5. PROMPT-ONLY STATES
    # --------------------------------------------------------
    # These states ONLY speak, never consume input
    # --------------------------------------------------------
    if (
        "prompt" in node
        and "action" not in node
        and "allowed_actions" not in node
    ):
        if "next" in node:
            session["state"] = node["next"]
            return handle_turn("", session)
        
        return render_prompt(node, session), session

    # --------------------------------------------------------
    # 6. END STATE
    # --------------------------------------------------------
    if node.get("end"):
        session["ended"] = True
        return render_prompt(node, session), session

    # --------------------------------------------------------
    # 7. SAFETY FALLBACK (should never hit)
    # --------------------------------------------------------
    return (
        "I'm sorry, something went wrong. Please start a new conversation.",
        session
    )