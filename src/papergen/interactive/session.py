"""Session management for PaperGen interactive CLI."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import json
import uuid


@dataclass
class Message:
    """A single message in the conversation."""
    role: str  # "user", "assistant", "system", "tool"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    tool_calls: List[Dict] = field(default_factory=list)
    tool_results: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "tool_calls": self.tool_calls,
            "tool_results": self.tool_results
        }


class Session:
    """Manages conversation session state."""

    def __init__(self, session_id: Optional[str] = None):
        """Initialize session."""
        self.session_id = session_id or str(uuid.uuid4())[:8]
        self.messages: List[Message] = []
        self.created_at = datetime.now()
        self.working_dir = Path.cwd()
        self.context: Dict[str, Any] = {}

    def add_message(self, role: str, content: str, **kwargs) -> Message:
        """Add a message to the session."""
        msg = Message(role=role, content=content, **kwargs)
        self.messages.append(msg)
        return msg

    def get_messages_for_api(self) -> List[Dict]:
        """Get messages formatted for API call."""
        return [{"role": m.role, "content": m.content} for m in self.messages]

    def clear(self):
        """Clear conversation history."""
        self.messages = []

    def save(self, path: Path):
        """Save session to file."""
        data = {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "messages": [m.to_dict() for m in self.messages]
        }
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, path: Path) -> "Session":
        """Load session from file."""
        with open(path) as f:
            data = json.load(f)
        session = cls(data["session_id"])
        for m in data["messages"]:
            session.add_message(m["role"], m["content"])
        return session
