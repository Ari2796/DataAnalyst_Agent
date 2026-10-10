"""Session and state management service with safe in-memory storage."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import pandas as pd
from app.schemas.dataset import DatasetProfile, SemanticMapping


@dataclass
class ConversationTurn:
    role: str  # "user" | "assistant" | "system"
    content: str
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionData:
    dataset_id: str
    filename: str
    df: pd.DataFrame
    file_size_bytes: int
    created_at: str
    profile: Optional[DatasetProfile] = None
    confirmed_mappings: Dict[str, str] = field(default_factory=dict)  # role -> col_name
    history: List[ConversationTurn] = field(default_factory=list)
    recent_entities: Dict[str, Any] = field(default_factory=dict)  # e.g., {'last_category': 'Electronics', 'last_metric': 'revenue'}


class SessionService:
    """Manages active dataset sessions and conversation memory."""

    def __init__(self):
        self._sessions: Dict[str, SessionData] = {}

    def create_session(
        self,
        dataset_id: str,
        filename: str,
        df: pd.DataFrame,
        file_size_bytes: int,
    ) -> SessionData:
        now_iso = datetime.now(timezone.utc).isoformat()
        session = SessionData(
            dataset_id=dataset_id,
            filename=filename,
            df=df,
            file_size_bytes=file_size_bytes,
            created_at=now_iso,
        )
        self._sessions[dataset_id] = session
        return session

    def get_session(self, dataset_id: str) -> Optional[SessionData]:
        return self._sessions.get(dataset_id)

    def delete_session(self, dataset_id: str) -> bool:
        if dataset_id in self._sessions:
            del self._sessions[dataset_id]
            return True
        return False

    def list_sessions(self) -> List[str]:
        return list(self._sessions.keys())

    def update_profile(self, dataset_id: str, profile: DatasetProfile) -> None:
        session = self.get_session(dataset_id)
        if session:
            session.profile = profile
            # Seed confirmed mappings from profile mappings
            for role, mapping in profile.semantic_mappings.items():
                if mapping.is_confirmed:
                    session.confirmed_mappings[mapping.mapped_role.value] = mapping.column_name

    def update_mappings(self, dataset_id: str, role_to_col: Dict[str, str]) -> None:
        session = self.get_session(dataset_id)
        if session:
            session.confirmed_mappings.update(role_to_col)
            if session.profile:
                for role_str, col_name in role_to_col.items():
                    if role_str in session.profile.semantic_mappings:
                        mapping = session.profile.semantic_mappings[role_str]
                        mapping.column_name = col_name
                        mapping.is_confirmed = True

    def add_message(
        self,
        dataset_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        session = self.get_session(dataset_id)
        if session:
            session.history.append(
                ConversationTurn(
                    role=role,
                    content=content,
                    metadata=metadata or {},
                )
            )

    def get_history(self, dataset_id: str, limit: int = 10) -> List[ConversationTurn]:
        session = self.get_session(dataset_id)
        if not session:
            return []
        return session.history[-limit:]

    def update_recent_entities(self, dataset_id: str, entities: Dict[str, Any]) -> None:
        session = self.get_session(dataset_id)
        if session:
            session.recent_entities.update(entities)

    def get_recent_entities(self, dataset_id: str) -> Dict[str, Any]:
        session = self.get_session(dataset_id)
        if not session:
            return {}
        return session.recent_entities.copy()


# Global session manager instance
session_service = SessionService()
