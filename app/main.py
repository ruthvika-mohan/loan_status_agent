from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.conversation import handle_turn

app = FastAPI()

# Add CORS middleware to allow browser requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions = {}

@app.post("/chat")
def chat(payload: dict):
    session_id = payload.get("session_id")
    message = payload.get("message", "")

    if session_id not in sessions:
        sessions[session_id] = {}

    try:
        response, updated_session = handle_turn(message, sessions[session_id])
        sessions[session_id] = updated_session

        return {
            "response": response,
            "ended": updated_session.get("ended", False)
        }

    except Exception as e:
        print(f"ERROR: {e}")
        return {
            "response": "Something went wrong. Please start a new conversation.",
            "ended": True
        }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "active_sessions": len(sessions)}


@app.post("/reset")
def reset_session(payload: dict):
    """Reset a specific session"""
    session_id = payload.get("session_id")
    if session_id in sessions:
        sessions[session_id] = {}
        return {"status": "reset"}
    return {"status": "not_found"}


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)