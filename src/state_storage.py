"""Persistent state storage for conversations."""

import json
import pickle
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional
from agent import ConversationState, Message, MessageRole, ToolCall, ToolStatus


class StateStorage(ABC):
    """Base class for state storage."""

    @abstractmethod
    def save(self, state: ConversationState) -> None:
        """Save conversation state."""
        pass

    @abstractmethod
    def load(self, session_id: str) -> Optional[ConversationState]:
        """Load conversation state."""
        pass


class FileStateStorage(StateStorage):
    """Store conversation state in files."""

    def __init__(self, storage_dir: str = "conversations"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)

    def save(self, state: ConversationState) -> None:
        """Save state to file."""
        filepath = self.storage_dir / f"{state.session_id}.pkl"
        with open(filepath, "wb") as f:
            pickle.dump(state, f)

    def load(self, session_id: str) -> Optional[ConversationState]:
        """Load state from file."""
        filepath = self.storage_dir / f"{session_id}.pkl"
        if filepath.exists():
            with open(filepath, "rb") as f:
                return pickle.load(f)
        return None


class JSONStateStorage(StateStorage):
    """Store conversation state in JSON."""

    def __init__(self, storage_dir: str = "conversations"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)

    def save(self, state: ConversationState) -> None:
        """Save state to JSON."""
        filepath = self.storage_dir / f"{state.session_id}.json"
        state_dict = state.to_dict()
        with open(filepath, "w") as f:
            json.dump(state_dict, f, indent=2, default=str)

    def load(self, session_id: str) -> Optional[ConversationState]:
        """Load state from JSON."""
        filepath = self.storage_dir / f"{session_id}.json"
        if filepath.exists():
            with open(filepath, "r") as f:
                data = json.load(f)
                # Reconstruct ConversationState from dict
                return ConversationState(
                    session_id=data["session_id"],
                    messages=data.get("messages", []),
                    context=data.get("context", {}),
                    metadata=data.get("metadata", {}),
                )
        return None
