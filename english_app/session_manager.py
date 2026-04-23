import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

DATA_DIR = "english_app/data"
SESSIONS_DIR = os.path.join(DATA_DIR, "sessions")
AUDIO_DIR = os.path.join(DATA_DIR, "audio")
VIDEO_DIR = os.path.join(DATA_DIR, "videos")

class SessionManager:
    def __init__(self):
        self.ensure_directories()

    def ensure_directories(self):
        os.makedirs(SESSIONS_DIR, exist_ok=True)
        os.makedirs(AUDIO_DIR, exist_ok=True)
        os.makedirs(VIDEO_DIR, exist_ok=True)

    def create_new_session(self) -> Dict:
        """Initialize a new empty session structure."""
        return {
            "id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "created_at": datetime.now().isoformat(),
            "video_url": "",
            "video_title": "", # Added video title
            "phase1": {
                "notes": "",
                "missed_parts": ""
            },
            "phase2": {
                "vocab_issues": "",    # New: Vocabulary analysis text
                "grammar_issues": "",  # New: Grammar analysis text
                "linking_issues": "",  # New: Linking analysis text
                "vocab_list": [],      # List of {word: "", meaning: ""}
                "grammar_list": [],    # New: List of {sentence: "", point: "", note: ""}
                "notes": ""            # General analysis notes
            },
            "phase3": {
                "audio_file": None,
                "summary": ""
            }
        }

    def save_session(self, session_data: Dict):
        """Save the session data to a JSON file."""
        if not session_data.get("id"):
            session_data["id"] = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        file_path = os.path.join(SESSIONS_DIR, f"{session_data['id']}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)
        return file_path

    def load_session(self, session_id: str) -> Optional[Dict]:
        """Load a session by ID."""
        file_path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def list_sessions(self) -> List[Dict]:
        """List all available sessions sorted by date (newest first)."""
        sessions = []
        if not os.path.exists(SESSIONS_DIR):
            return []
            
        for filename in os.listdir(SESSIONS_DIR):
            if filename.endswith(".json"):
                file_path = os.path.join(SESSIONS_DIR, filename)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        sessions.append({
                            "id": data.get("id"),
                            "created_at": data.get("created_at"),
                            "video_url": data.get("video_url", "No Video"),
                            "video_title": data.get("video_title", ""), # Load title
                            "phase1": data.get("phase1", {}),
                            "phase2": data.get("phase2", {}),
                            "phase3": data.get("phase3", {})
                        })
                except Exception:
                    continue
        
        return sorted(sessions, key=lambda x: x["created_at"], reverse=True)

    def save_audio(self, session_id: str, audio_bytes: bytes) -> str:
        """Save audio recording and return the relative path."""
        filename = f"{session_id}_recording.wav"
        file_path = os.path.join(AUDIO_DIR, filename)
        with open(file_path, "wb") as f:
            f.write(audio_bytes)
        return filename

    def delete_session(self, session_id: str) -> bool:
        """Delete session JSON and associated audio/video files."""
        try:
            # 1. Delete JSON Session File
            json_path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
            if os.path.exists(json_path):
                os.remove(json_path)
            
            # 2. Delete Audio Recording
            audio_path = os.path.join(AUDIO_DIR, f"{session_id}_recording.wav")
            if os.path.exists(audio_path):
                os.remove(audio_path)
                
            # 3. Delete Video Files (if any exist from old version)
            video_base = os.path.join(VIDEO_DIR, session_id)
            for ext in ['.mp4', '.webm', '.mkv']:
                v_path = video_base + ext
                if os.path.exists(v_path):
                    os.remove(v_path)
            
            return True
        except Exception as e:
            logger.exception("Error deleting session %s: %s", session_id, e)
            return False
