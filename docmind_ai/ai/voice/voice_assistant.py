"""
DocMind AI - Voice Assistant
Text-to-Speech and Speech-to-Text for document analysis
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
import base64
import io


class VoiceAction(Enum):
    """Actions supported by voice assistant"""
    READ_SUMMARY = "read_summary"
    EXPLAIN_CHANGE = "explain_change"
    READ_RECOMMENDATIONS = "read_recommendations"
    READ_RISK = "read_risk"
    READ_FINDINGS = "read_findings"
    HELP = "help"
    STOP = "stop"


@dataclass
class VoiceCommand:
    """Parsed voice command"""
    action: VoiceAction
    parameters: Dict[str, Any]
    confidence: float
    transcript: str


@dataclass
class VoiceResponse:
    """Voice response data"""
    audio_data: Optional[bytes] = None
    text: str = ""
    action: Optional[VoiceAction] = None
    success: bool = True


class TextToSpeechEngine:
    """Text to Speech engine for reading summaries"""
    
    def __init__(self, engine: str = "gtts"):
        self.engine = engine
        self._init_engine()
    
    def _init_engine(self):
        """Initialize TTS engine"""
        if self.engine == "gtts":
            try:
                from gtts import gTTS
                self.gtts = gTTS
            except ImportError:
                self.gtts = None
        
        elif self.engine == "pyttsx3":
            try:
                import pyttsx3
                self.pyttsx3 = pyttsx3.init()
            except ImportError:
                self.pyttsx3 = None
    
    def speak(self, text: str, lang: str = "en") -> bytes:
        """Convert text to speech and return audio bytes"""
        if self.engine == "gtts" and self.gtts:
            return self._gtts_speak(text, lang)
        elif self.engine == "pyttsx3" and self.pyttsx3:
            return self._pyttsx3_speak(text)
        
        # Fallback - return empty bytes
        return b""
    
    def _gtts_speak(self, text: str, lang: str) -> bytes:
        """Use gTTS for TTS"""
        mp3_fp = io.BytesIO()
        self.gtts(text=text, lang=lang).write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        return mp3_fp.read()
    
    def _pyttsx3_speak(self, text: str) -> bytes:
        """Use pyttsx3 for TTS"""
        self.pyttsx3.save_to_file(text, 'temp_audio.wav')
        self.pyttsx3.runAndWait()
        
        # Read the file
        with open('temp_audio.wav', 'rb') as f:
            return f.read()
    
    def speak_to_file(self, text: str, filename: str, lang: str = "en"):
        """Save speech to file"""
        audio = self.speak(text, lang)
        if audio:
            with open(filename, 'wb') as f:
                f.write(audio)
            return True
        return False


class SpeechToTextEngine:
    """Speech to Text engine for voice commands"""
    
    def __init__(self, engine: str = "google"):
        self.engine = engine
        self._init_engine()
    
    def _init_engine(self):
        """Initialize STT engine"""
        if self.engine == "google":
            try:
                import speech_recognition as sr
                self.recognizer = sr.Recognizer()
                self.microphone = sr.Microphone()
            except ImportError:
                self.recognizer = None
    
    def listen(self, audio_data: bytes = None) -> Optional[str]:
        """Listen for speech and return transcript"""
        if self.engine == "google" and self.recognizer:
            return self._google_listen(audio_data)
        
        return None
    
    def _google_listen(self, audio_data: bytes = None) -> Optional[str]:
        """Use Google Speech Recognition"""
        try:
            import speech_recognition as sr
            
            recognizer = sr.Recognizer()
            
            if audio_data:
                # Process audio from bytes
                import io
                audio_fp = io.BytesIO(audio_data)
                with sr.AudioFile(audio_fp) as source:
                    audio = recognizer.record(source)
            else:
                # Use microphone
                with self.microphone as source:
                    recognizer.adjust_for_ambient_noise(source)
                    audio = recognizer.listen(source)
            
            # Google speech recognition
            text = recognizer.recognize_google(audio)
            return text
        
        except Exception as e:
            print(f"STT error: {e}")
            return None


class VoiceCommandParser:
    """Parse voice commands into actions"""
    
    def __init__(self):
        self.command_patterns = {
            VoiceAction.READ_SUMMARY: [
                "read summary", "summarize", "summary", "what's the summary",
                "tell me the summary", "give me the summary"
            ],
            VoiceAction.EXPLAIN_CHANGE: [
                "explain change", "explain", "what changed",
                "tell me about the change", "describe the change"
            ],
            VoiceAction.READ_RECOMMENDATIONS: [
                "recommendations", "what should i do", "suggestions",
                "next steps", "advice", "recommend"
            ],
            VoiceAction.READ_RISK: [
                "risk", "risks", "danger", "warning", "concern",
                "what are the risks"
            ],
            VoiceAction.READ_FINDINGS: [
                "findings", "critical", "important", "key points",
                "what did you find"
            ],
            VoiceAction.HELP: [
                "help", "commands", "what can you do", "available commands"
            ],
            VoiceAction.STOP: [
                "stop", "cancel", "quit", "exit", "never mind"
            ]
        }
    
    def parse(self, transcript: str) -> VoiceCommand:
        """Parse transcript into command"""
        transcript_lower = transcript.lower()
        
        # Find matching action
        best_match = None
        best_confidence = 0
        
        for action, patterns in self.command_patterns.items():
            for pattern in patterns:
                if pattern in transcript_lower:
                    confidence = len(pattern) / len(transcript_lower)
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = action
        
        if best_match:
            return VoiceCommand(
                action=best_match,
                parameters=self._extract_parameters(transcript),
                confidence=best_confidence,
                transcript=transcript
            )
        
        # Default to help
        return VoiceCommand(
            action=VoiceAction.HELP,
            parameters={},
            confidence=0.5,
            transcript=transcript
        )
    
    def _extract_parameters(self, transcript: str) -> Dict[str, Any]:
        """Extract parameters from transcript"""
        params = {}
        
        # Look for numbers (e.g., "explain change 3")
        import re
        numbers = re.findall(r'\d+', transcript)
        if numbers:
            params["change_index"] = int(numbers[0]) - 1  # Convert to 0-indexed
        
        # Look for severity keywords
        if "critical" in transcript.lower():
            params["severity"] = "critical"
        elif "high" in transcript.lower():
            params["severity"] = "high"
        
        return params


class VoiceAssistant:
    """Main voice assistant for document analysis"""
    
    def __init__(self, tts_engine: str = "gtts", stt_engine: str = "google"):
        self.tts = TextToSpeechEngine(tts_engine)
        self.stt = SpeechToTextEngine(stt_engine)
        self.command_parser = VoiceCommandParser()
        self.context: Dict[str, Any] = {}
        self.is_active = False
    
    def set_context(self, context: Dict[str, Any]):
        """Set analysis context for voice assistant"""
        self.context = context
    
    def speak_text(self, text: str, lang: str = "en") -> bytes:
        """Convert text to speech"""
        return self.tts.speak(text, lang)
    
    def listen_and_execute(self) -> VoiceResponse:
        """Listen for command, execute, and speak response"""
        # Listen for speech
        transcript = self.stt.listen()
        
        if not transcript:
            return VoiceResponse(
                text="I didn't hear anything. Please try again.",
                success=False
            )
        
        # Parse command
        command = self.command_parser.parse(transcript)
        
        # Execute command
        return self.execute_command(command)
    
    def execute_command(self, command: VoiceCommand) -> VoiceResponse:
        """Execute a voice command"""
        if command.action == VoiceAction.READ_SUMMARY:
            return self._read_summary(command)
        elif command.action == VoiceAction.EXPLAIN_CHANGE:
            return self._explain_change(command)
        elif command.action == VoiceAction.READ_RECOMMENDATIONS:
            return self._read_recommendations(command)
        elif command.action == VoiceAction.READ_RISK:
            return self._read_risk(command)
        elif command.action == VoiceAction.READ_FINDINGS:
            return self._read_findings(command)
        elif command.action == VoiceAction.HELP:
            return self._read_help()
        elif command.action == VoiceAction.STOP:
            self.is_active = False
            return VoiceResponse(
                text="Stopping voice assistant. Have a great day!",
                action=VoiceAction.STOP
            )
        
        return VoiceResponse(
            text="I didn't understand that command. Say 'help' for available commands.",
            success=False
        )
    
    def _read_summary(self, command: VoiceCommand) -> VoiceResponse:
        """Read executive summary"""
        summary = self.context.get("executive_summary", {})
        
        if not summary:
            return VoiceResponse(
                text="No summary available. Please run a document comparison first.",
                success=False
            )
        
        overview = summary.get("overview", "No overview available.")
        critical_findings = summary.get("critical_findings", [])
        recommendations = summary.get("recommendations", [])[:3]
        
        text = f"Executive Summary: {overview}"
        
        if critical_findings:
            text += " Key findings include: "
            for finding in critical_findings[:3]:
                text += f"{finding}. "
        
        if recommendations:
            text += " Recommendations: "
            for rec in recommendations:
                text += f"{rec}. "
        
        audio = self.speak_text(text)
        
        return VoiceResponse(
            audio_data=audio,
            text=text,
            action=VoiceAction.READ_SUMMARY
        )
    
    def _explain_change(self, command: VoiceCommand) -> VoiceResponse:
        """Explain a specific change"""
        changes = self.context.get("changes", [])
        
        if not changes:
            return VoiceResponse(
                text="No changes to explain. Please run a document comparison first.",
                success=False
            )
        
        change_idx = command.parameters.get("change_index", 0)
        
        if change_idx >= len(changes):
            change_idx = 0
        
        change = changes[change_idx]
        
        text = f"Change {change_idx + 1}: "
        text += f"Type: {change.get('change_type', 'unknown')}. "
        text += f"Severity: {change.get('severity', 'unknown')}. "
        
        original = change.get("original_content", "")
        modified = change.get("modified_content", "")
        
        if original:
            text += f"Original text was: {original[:100]}. "
        if modified:
            text += f"Modified to: {modified[:100]}."
        
        audio = self.speak_text(text)
        
        return VoiceResponse(
            audio_data=audio,
            text=text,
            action=VoiceAction.EXPLAIN_CHANGE
        )
    
    def _read_recommendations(self, command: VoiceCommand) -> VoiceResponse:
        """Read recommendations"""
        summary = self.context.get("executive_summary", {})
        
        recommendations = summary.get("recommendations", []) if summary else []
        risk_recs = self.context.get("risk_result", {}).get("recommendations", []) if self.context.get("risk_result") else []
        
        all_recs = (recommendations + risk_recs)[:5]
        
        if not all_recs:
            return VoiceResponse(
                text="No recommendations available.",
                success=False
            )
        
        text = "Here are the recommendations: "
        for i, rec in enumerate(all_recs, 1):
            text += f"{i}. {rec}. "
        
        audio = self.speak_text(text)
        
        return VoiceResponse(
            audio_data=audio,
            text=text,
            action=VoiceAction.READ_RECOMMENDATIONS
        )
    
    def _read_risk(self, command: VoiceCommand) -> VoiceResponse:
        """Read risk analysis"""
        risk_result = self.context.get("risk_result")
        
        if not risk_result:
            return VoiceResponse(
                text="No risk analysis available. Please run a document comparison first.",
                success=False
            )
        
        overall = risk_result.get("overall_risk_score", 0)
        level = risk_result.get("risk_level", "unknown")
        
        text = f"Risk Analysis: Overall risk score is {overall * 100:.0f} percent. "
        text += f"Risk level is {level}. "
        
        financial = risk_result.get("financial_risk", 0)
        legal = risk_result.get("legal_risk", 0)
        
        text += f"Financial risk: {financial * 100:.0f} percent. "
        text += f"Legal risk: {legal * 100:.0f} percent. "
        
        risk_factors = risk_result.get("risk_factors", [])[:3]
        if risk_factors:
            text += " Key risk factors include: "
            for factor in risk_factors:
                text += f"{factor}. "
        
        audio = self.speak_text(text)
        
        return VoiceResponse(
            audio_data=audio,
            text=text,
            action=VoiceAction.READ_RISK
        )
    
    def _read_findings(self, command: VoiceCommand) -> VoiceResponse:
        """Read critical findings"""
        summary = self.context.get("executive_summary", {})
        fraud_result = self.context.get("fraud_result")
        
        findings = []
        
        if summary and summary.get("critical_findings"):
            findings.extend(summary.get("critical_findings"))
        
        if fraud_result and fraud_result.get("critical_findings"):
            findings.extend([f"Fraud indicator: {f}" for f in fraud_result.get("critical_findings")])
        
        if not findings:
            return VoiceResponse(
                text="No critical findings at this time.",
                success=True
            )
        
        text = "Critical findings include: "
        for i, finding in enumerate(findings[:5], 1):
            text += f"{i}. {finding}. "
        
        audio = self.speak_text(text)
        
        return VoiceResponse(
            audio_data=audio,
            text=text,
            action=VoiceAction.READ_FINDINGS
        )
    
    def _read_help(self) -> VoiceResponse:
        """Read available commands"""
        text = """
        Available voice commands:
        1. Say 'read summary' to hear the executive summary.
        2. Say 'explain change' followed by a number to explain a specific change.
        3. Say 'recommendations' to hear suggested actions.
        4. Say 'risk' to hear the risk analysis.
        5. Say 'findings' to hear critical findings.
        6. Say 'stop' to exit.
        """
        
        audio = self.speak_text(text)
        
        return VoiceResponse(
            audio_data=audio,
            text=text,
            action=VoiceAction.HELP
        )


class VoiceController:
    """Controller for managing voice assistant sessions"""
    
    def __init__(self):
        self.assistant = VoiceAssistant()
        self.sessions: Dict[str, Dict] = {}
    
    def start_session(self, session_id: str, context: Dict[str, Any]):
        """Start a voice session"""
        self.assistant.set_context(context)
        self.assistant.is_active = True
        
        self.sessions[session_id] = {
            "active": True,
            "started_at": None,  # Would use datetime
            "command_count": 0
        }
    
    def end_session(self, session_id: str):
        """End a voice session"""
        if session_id in self.sessions:
            self.sessions[session_id]["active"] = False
            self.assistant.is_active = False
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get session status"""
        return self.sessions.get(session_id, {"active": False})


# WebSocket handler for real-time voice (optional feature)
class VoiceWebSocketHandler:
    """Handle WebSocket connections for voice streaming"""
    
    async def handle_connection(self, websocket):
        """Handle WebSocket voice connection"""
        await websocket.accept()
        
        try:
            while True:
                # Receive audio data
                audio_data = await websocket.receive_bytes()
                
                # Process with STT
                transcript = self.assistant.stt.listen(audio_data)
                
                if transcript:
                    # Parse command
                    command = self.assistant.command_parser.parse(transcript)
                    
                    # Execute
                    response = self.assistant.execute_command(command)
                    
                    # Send response
                    await websocket.send_json({
                        "transcript": transcript,
                        "response": response.text,
                        "action": response.action.value if response.action else None,
                        "success": response.success
                    })
                    
                    # Send audio if available
                    if response.audio_data:
                        await websocket.send_bytes(response.audio_data)
        
        except Exception as e:
            await websocket.close()