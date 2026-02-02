"""
Desktop Voice Agent for Loan Status (Mac Optimized)

This version has better microphone handling for macOS.

Setup:
1. pip install SpeechRecognition pyttsx3 pyaudio requests
2. Grant microphone permissions in System Settings
3. Make sure your FastAPI backend is running on localhost:8000
4. Run: python voice_agent_desktop_mac.py
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
        
        # Mac-friendly settings (lower threshold, longer timeout)
        self.recognizer.energy_threshold = 300  # Lower for Mac mics
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8  # How long to wait for pause
        
        # Initialize text-to-speech
        self.tts = pyttsx3.init()
        
        # Configure voice
        voices = self.tts.getProperty('voices')
        # Mac has good built-in voices
        for voice in voices:
            if 'samantha' in voice.name.lower() or 'female' in voice.name.lower():
                self.tts.setProperty('voice', voice.id)
                break
        
        self.tts.setProperty('rate', 160)  # Speed
        self.tts.setProperty('volume', 0.9)  # Volume
        
        # Session management
        self.session_id = str(uuid.uuid4())
        self.last_agent_response = ""  # Track last response for context
        
    def speak(self, text):
        """Convert text to speech and play"""
        # Clean up special markers
        text = text.replace("[Call ended]", "").strip()
        
        if not text:
            return
            
        print(f"\n🤖 Agent: {text}")
        self.tts.say(text)
        self.tts.runAndWait()
        
        # CRITICAL: Wait for TTS to completely finish before continuing
        # This prevents beep from playing during speech
        time.sleep(0.5)
        print("⏸️  [Agent finished]")
    
    def listen(self, is_keypad_input=False):
        """Listen to user and convert speech to text (Mac optimized)"""
        with sr.Microphone() as source:
            # Calibrate for ambient noise (important on Mac)
            if not hasattr(self, 'calibrated'):
                print("\n🔧 Calibrating microphone...")
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
                self.calibrated = True
                print(f"✅ Mic calibrated (threshold: {self.recognizer.energy_threshold})")
            
            # Wait for agent to finish speaking completely
            time.sleep(1.5)
            
            # BEEP to indicate ready to listen
            print("\n🔔 *BEEP*")
            # Play a beep sound
            try:
                import os
                os.system('afplay /System/Library/Sounds/Tink.aiff &')
            except:
                pass
            
            # For keypad input, give MUCH more time
            if is_keypad_input:
                print("⌨️  [Enter 10 digits on keypad... You have 30 seconds]")
                timeout = 20
                phrase_limit = 30
            else:
                print("🎤 [Speak now...]")
                timeout = 8
                phrase_limit = 5
            
            try:
                # Listen
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout,
                    phrase_time_limit=phrase_limit
                )
                
                print("⏹️  [Stopped recording]")
                time.sleep(0.2)
                
                print("🔄 Processing speech...")
                
                # Convert to text using Google Speech Recognition
                text = self.recognizer.recognize_google(audio)
                print(f"✅ You said: '{text}'")
                return text
                
            except sr.WaitTimeoutError:
                print("⏱️  Timeout - No speech detected. Try speaking louder or closer to mic.")
                return None
            except sr.UnknownValueError:
                print("❓ Couldn't understand. Please speak more clearly.")
                return ""
            except sr.RequestError as e:
                print(f"❌ Speech service error: {e}")
                print("💡 Tip: Make sure you have internet connection")
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
        print("🎤 VOICE LOAN STATUS AGENT (Mac)")
        print("="*60)
        print("\n💡 Mac Tips:")
        print("   - Make sure you granted microphone permission")
        print("   - Speak clearly and wait for 'Recording...'")
        print("   - You have 10 seconds to start speaking")
        print("   - The agent will show what it heard")
        print("\n" + "="*60 + "\n")
        
        # Start call
        print("📞 Starting call...\n")
        time.sleep(0.5)
        
        # Get initial greeting
        greeting = self.send_to_backend("")
        self.speak(greeting)
        
        # Main conversation loop
        # Main conversation loop
        while True:
            # Detect if agent asked for keypad input
            # Check the last agent response for keypad keywords
            last_response = getattr(self, 'last_agent_response', '')
            is_keypad = 'keypad' in last_response.lower() or 'pound key' in last_response.lower()
            
            # Listen to user
            user_speech = self.listen(is_keypad_input=is_keypad)
            
            # Handle no input
            if user_speech is None:
                self.speak("I didn't hear anything. Let me try again.")
                continue
            
            if user_speech == "":
                self.speak("I didn't catch that. Could you repeat?")
                continue
            
            # Send to backend
            response = self.send_to_backend(user_speech)
            
            # Store for next iteration
            self.last_agent_response = response
            
            # Speak response
            self.speak(response)
            
            # Check if call ended
            if "[Call ended]" in response or "ended" in response.lower():
                print("\n📴 Call ended.")
                break
            
            # Small pause before next interaction
            time.sleep(0.3)
        
        print("\n" + "="*60)
        print("✅ Session complete!")
        print("="*60 + "\n")


def test_microphone():
    """Test if microphone is working (Mac optimized)"""
    print("\n🎤 Testing microphone (Mac version)...")
    print("💡 Speak within 5 seconds: Say 'testing one two three'")
    
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300  # Lower for Mac
    
    with sr.Microphone() as source:
        try:
            # Adjust for ambient noise
            print("🔧 Adjusting for background noise...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print(f"✅ Energy threshold: {recognizer.energy_threshold}")
            
            print("👂 Listening now... SPEAK!")
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            print("🔄 Processing...")
            text = recognizer.recognize_google(audio)
            print(f"✅ SUCCESS! Heard: '{text}'")
            return True
            
        except sr.WaitTimeoutError:
            print("❌ Timeout - didn't detect speech within 5 seconds")
            print("💡 Troubleshooting:")
            print("   1. Check System Settings → Privacy → Microphone")
            print("   2. Make sure Terminal has microphone permission")
            print("   3. Try speaking louder")
            print("   4. Check if your mic is muted")
            return False
        except sr.UnknownValueError:
            print("❌ Detected sound but couldn't understand it")
            print("💡 Try speaking more clearly")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False


def test_tts():
    """Test if text-to-speech is working"""
    print("\n🔊 Testing text-to-speech...")
    try:
        tts = pyttsx3.init()
        voices = tts.getProperty('voices')
        print(f"✅ Found {len(voices)} voices")
        
        # Use Samantha on Mac if available
        for voice in voices:
            if 'samantha' in voice.name.lower():
                tts.setProperty('voice', voice.id)
                print(f"✅ Using voice: {voice.name}")
                break
        
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
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend")
        print("💡 Run this in another terminal:")
        print("   uvicorn app.main:app --reload --port 8000")
        return False
    except Exception as e:
        print(f"❌ Backend test failed: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("VOICE AGENT - SYSTEM CHECK (Mac)")
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
        print("\n❌ Some systems are not ready.")
        
        if not mic_ok:
            print("\n🎤 MICROPHONE FIX:")
            print("   1. Open System Settings → Privacy & Security → Microphone")
            print("   2. Enable Terminal (or iTerm)")
            print("   3. Close and reopen Terminal")
            print("   4. Run this script again")
        
        if not backend_ok:
            print("\n🌐 BACKEND FIX:")
            print("   In another terminal, run:")
            print("   uvicorn app.main:app --reload --port 8000")