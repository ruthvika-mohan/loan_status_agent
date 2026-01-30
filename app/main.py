from fastapi import FastAPI
from app.conversation import handle_turn

app = FastAPI()

# Session storage - resets when server restarts
sessions = {}

@app.post("/chat")
def chat(payload: dict):
    session_id = payload.get("session_id")
    message = payload.get("message", "")

    if session_id not in sessions:
        # Initialize new session
        sessions[session_id] = {}

    try:
        response, updated_session = handle_turn(message, sessions[session_id])
        sessions[session_id] = updated_session

        return {
            "response": response,
            "ended": updated_session.get("ended", False),
            "state": updated_session.get("state", "start")  # For debugging
        }

    except Exception as e:
        print(f"ERROR in chat handler: {e}")
        # Return graceful error response
        return {
            "response": "I apologize, something went wrong. Let's start fresh. Please share your phone number to check your loan status.",
            "ended": False
        }


@app.post("/reset")
def reset_session(payload: dict):
    """Endpoint to reset a specific session"""
    session_id = payload.get("session_id")
    if session_id in sessions:
        sessions[session_id] = {}
        return {"status": "reset", "message": "Session reset successfully"}
    return {"status": "not_found", "message": "Session not found"}


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "active_sessions": len(sessions)}