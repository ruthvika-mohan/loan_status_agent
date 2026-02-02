"""
Desktop Voice Agent for Loan Status

This is the SIMPLEST way to test your agent with actual voice.
No infrastructure needed - just run locally!

Setup:
1. pip install SpeechRecognition pyttsx3 pyaudio requests
2. Make sure your FastAPI backend is running on localhost:8000
3. Run: python voice_agent_desktop.py

Note: On Mac, you might need: brew install portaudio
"""

import speech_recognition as sr
import pyttsx3
import requests
import uuid
import time

# Configuration
BACKEND_URL = "http://localhost:8000/chat"

class VoiceAgent:
    def __init__(self):
        # Initialize speech recognition
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 4000  # Adjust based on background noise
        self.recognizer.dynamic_energy_threshold = True
        
        # Initialize text-to-speech
        self.tts = pyttsx3.init()
        
        # Configure voice (choose female voice if available)
        voices = self.tts.getProperty('voices')
        for voice in voices:
            if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                self.tts.setProperty('voice', voice.id)
                break
        
        self.tts.setProperty('rate', 160)  # Speed (default is ~200)
        self.tts.setProperty('volume', 0.9)  # Volume (0.0 to 1.0)
        
        # Session management
        self.session_id = str(uuid.uuid4())
        
    def speak(self, text):
        """Convert text to speech and play"""
        # Clean up special markers
        text = text.replace("[Call ended]", "").strip()
        
        if not text:
            return
            
        print(f"\n🤖 Agent: {text}")
        self.tts.say(text)
        self.tts.runAndWait()
    
    def listen(self, timeout=5, phrase_limit=10):
        """Listen to user and convert speech to text"""
        with sr.Microphone() as source:
            print("\n🎤 Listening... (speak now)")
            
            # Adjust for ambient noise
            if not hasattr(self, 'calibrated'):
                print("🔧 Calibrating microphone...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                self.calibrated = True
            
            try:
                # Listen with timeout
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout,
                    phrase_time_limit=phrase_limit
                )
                
                print("🔄 Processing...")
                
                # Convert to text using Google Speech Recognition
                text = self.recognizer.recognize_google(audio)
                print(f"🧑 You said: {text}")
                return text
                
            except sr.WaitTimeoutError:
                print("⏱️  No speech detected (timeout)")
                return None
            except sr.UnknownValueError:
                print("❓ Could not understand audio")
                return ""
            except sr.RequestError as e:
                print(f"❌ Could not connect to speech service: {e}")
                return None
    
    def send_to_backend(self, user_input):
        """Send message to your existing backend"""
        try:
            response = requests.post(
                BACKEND_URL,
                json={
                    "session_id": self.session_id,
                    "message": user_input
                },
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()["response"]
            else:
                return "Sorry, I'm having trouble connecting to the system."
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Backend error: {e}")
            return "Sorry, I can't reach the system right now."
    
    def run(self):
        """Main conversation loop"""
        print("\n" + "="*60)
        print("🎤 VOICE LOAN STATUS AGENT")
        print("="*60)
        print("\n💡 Tips:")
        print("   - Speak clearly after you see 'Listening...'")
        print("   - Say 'yes', 'no', 'retry', or 'agent'")
        print("   - The agent will end the call when done")
        print("\n" + "="*60 + "\n")
        
        # Start call
        print("📞 Starting call...\n")
        time.sleep(0.5)
        
        # Get initial greeting
        greeting = self.send_to_backend("")
        self.speak(greeting)
        
        # Main conversation loop
        while True:
            # Listen to user
            user_speech = self.listen(timeout=10, phrase_limit=15)
            
            # Handle no input
            if user_speech is None:
                self.speak("Are you still there? Please speak.")
                continue
            
            if user_speech == "":
                self.speak("I didn't catch that. Could you repeat that?")
                continue
            
            # Send to backend
            response = self.send_to_backend(user_speech)
            
            # Speak response
            self.speak(response)
            
            # Check if call ended
            if "[Call ended]" in response or "ended" in response.lower():
                print("\n📴 Call ended.")
                break
            
            # Small pause before next listen
            time.sleep(0.5)
        
        print("\n" + "="*60)
        print("✅ Session complete!")
        print("="*60 + "\n")


def test_microphone():
    """Test if microphone is working"""
    print("\n🎤 Testing microphone...")
    recognizer = sr.Recognizer()
    
    with sr.Microphone() as source:
        print("Say something...")
        try:
            audio = recognizer.listen(source, timeout=3)
            text = recognizer.recognize_google(audio)
            print(f"✅ Heard: {text}")
            return True
        except Exception as e:
            print(f"❌ Microphone test failed: {e}")
            return False


def test_tts():
    """Test if text-to-speech is working"""
    print("\n🔊 Testing text-to-speech...")
    try:
        tts = pyttsx3.init()
        tts.say("Hello, this is a test.")
        tts.runAndWait()
        print("✅ Text-to-speech working")
        return True
    except Exception as e:
        print(f"❌ TTS test failed: {e}")
        return False


def test_backend():
    """Test if backend is running"""
    print("\n🌐 Testing backend connection...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        print("✅ Backend is running")
        return True
    except Exception as e:
        print(f"❌ Backend test failed: {e}")
        print("   Make sure your FastAPI server is running on port 8000")
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("VOICE AGENT - SYSTEM CHECK")
    print("="*60)
    
    # Run system checks
    mic_ok = test_microphone()
    tts_ok = test_tts()
    backend_ok = test_backend()
    
    print("\n" + "="*60)
    print("RESULTS:")
    print(f"  Microphone: {'✅' if mic_ok else '❌'}")
    print(f"  Text-to-Speech: {'✅' if tts_ok else '❌'}")
    print(f"  Backend: {'✅' if backend_ok else '❌'}")
    print("="*60)
    
    if mic_ok and tts_ok and backend_ok:
        print("\n✅ All systems ready!")
        input("\nPress ENTER to start the voice agent...")
        
        # Start the agent
        agent = VoiceAgent()
        agent.run()
    else:
        print("\n❌ Some systems are not ready. Please fix the issues above.")
        print("\nCommon fixes:")
        print("  - Microphone: Check system permissions")
        print("  - Backend: Run 'uvicorn main:app --reload' in another terminal")
        print("  - TTS: Try 'pip install --upgrade pyttsx3'")