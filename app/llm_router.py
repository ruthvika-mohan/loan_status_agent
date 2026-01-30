import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv('Tesco_Azure.env')

# -----------------------------------
# Azure OpenAI client configuration
# -----------------------------------
client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION")
)

CHAT_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")


def llm_route(user_input: str, allowed_actions: list[str]):
    """
    Maps free-text user input to ONE allowed action using Azure OpenAI.
    Returns the action string or None.
    """

    response = client.chat.completions.create(
        model=CHAT_DEPLOYMENT_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a banking assistant routing user intent. "
                    "Map the user's input to ONE allowed action. "
                    "Be flexible with variations.\n\n"
                    "Examples:\n"
                    "- 'give another number' → retry\n"
                    "- 'try again' → retry\n"
                    "- 'different number' → retry\n"
                    "- 'retry with another number' → retry\n"
                    "- 'talk to agent' → agent\n"
                    "- 'speak to human' → agent\n"
                    "- 'agent please' → agent\n"
                    "- 'handoff' → agent\n"
                    "- 'connect me to someone' → agent\n"
                    "- 'yes' → yes\n"
                    "- 'yeah' → yes\n"
                    "- 'sure' → yes\n"
                    "- 'ok' → yes\n"
                    "- 'yes please' → yes\n"
                    "- 'no' → no\n"
                    "- 'nah' → no\n"
                    "- 'no thanks' → no\n"
                    "- 'I don't know' → none (unclear intent)\n"
                    "- 'not sure' → none (unclear intent)\n\n"
                    "Respond ONLY with the action name (lowercase) or 'none'."
                )
            },
            {
                "role": "user",
                "content": f"""
User input: {user_input}
Allowed actions: {allowed_actions}
"""
            }
        ],
        temperature=0
    )

    action = response.choices[0].message.content.strip().lower()
    return action if action in allowed_actions else None


def llm_fallback(user_input: str, session: dict):
    """
    Intelligent fallback using LLM to handle off-topic or invalid inputs.
    Redirects user back to the loan status flow gracefully.
    
    Input:
    - user_input: what the user said
    - session: current session state
    
    Output:
    - A helpful response that redirects to phone number collection
    """
    
    # Get current state context
    current_state = session.get("state", "start")
    
    response = client.chat.completions.create(
        model=CHAT_DEPLOYMENT_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful banking assistant for loan status inquiries. "
                    "The user has said something that doesn't match what you asked for. "
                    "Your job is to:\n"
                    "1. Politely acknowledge what they said (if it makes sense)\n"
                    "2. Redirect them back to providing their phone number\n"
                    "3. Keep it brief (1-2 sentences max)\n"
                    "4. Be warm and helpful\n\n"
                    "Examples:\n"
                    "User: 'What's the weather?'\n"
                    "Response: 'I can't help with weather information, but I can check your loan status if you share your registered phone number.'\n\n"
                    "User: 'hello'\n"
                    "Response: 'Hello! I can help you check your loan status. Please share your registered phone number to continue.'\n\n"
                    "User: 'abc123'\n"
                    "Response: 'That doesn't look like a valid phone number. Please enter your registered phone number (digits only).'"
                )
            },
            {
                "role": "user",
                "content": f"""
User said: {user_input}
Current context: Asking for phone number to check loan status

Generate a brief, helpful redirect message.
"""
            }
        ],
        temperature=0.7,
        max_tokens=100
    )

    return response.choices[0].message.content.strip()


def llm_generate_goodbye(session: dict):
    """
    Generate a personalized goodbye message when user declines SMS.
    
    Input:
    - session: current session with loan status info
    
    Output:
    - A warm, brief goodbye message
    """
    
    loan_status = session.get("loan_status", "")
    
    response = client.chat.completions.create(
        model=CHAT_DEPLOYMENT_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful banking assistant. "
                    "The user just checked their loan status and declined an SMS update. "
                    "Generate a brief, warm goodbye message (1-2 sentences). "
                    "Be professional but friendly.\n\n"
                    "Examples:\n"
                    "- 'Thank you for checking your loan status. If you have any questions, feel free to reach out anytime!'\n"
                    "- 'Alright! Your application is progressing well. Have a great day!'\n"
                    "- 'Perfect! We'll keep you updated. Take care!'"
                )
            },
            {
                "role": "user",
                "content": f"""
Context: User's loan is {loan_status}. They declined SMS.

Generate a brief goodbye message.
"""
            }
        ],
        temperature=0.8,
        max_tokens=80
    )

    return response.choices[0].message.content.strip()


def llm_generate_goodbye_after_sms(session: dict):
    """
    Generate a personalized goodbye after sending SMS asking if they need anything else.
    If user says no or goodbye, end the conversation warmly.
    
    Input:
    - session: current session with loan status info
    
    Output:
    - A message asking if they need help with anything else
    """
    
    response = client.chat.completions.create(
        model=CHAT_DEPLOYMENT_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful banking assistant. "
                    "You just sent an SMS with the user's loan status. "
                    "Generate a brief, friendly closing message (1-2 sentences). "
                    "Thank them and wish them well.\n\n"
                    "Examples:\n"
                    "- 'Perfect! I've sent the details to your phone. Have a wonderful day!'\n"
                    "- 'All set! You should receive the SMS shortly. Thanks for using our service!'\n"
                    "- 'Done! Check your phone for the update. Take care!'"
                )
            },
            {
                "role": "user",
                "content": "Generate a brief goodbye after sending SMS."
            }
        ],
        temperature=0.8,
        max_tokens=80
    )

    return response.choices[0].message.content.strip()