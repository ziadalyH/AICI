"""Conversation memory manager (simple implementation without LangChain).

This module provides conversation history management for multi-turn dialogues.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime


class Message:
    """Simple message class."""
    def __init__(self, role: str, content: str):
        self.role = role  # 'user' or 'assistant'
        self.content = content
        self.timestamp = datetime.now()


class ConversationManager:
    """
    Manages conversation history for multiple sessions.
    
    Each session maintains its own conversation history with a configurable
    window of recent exchanges.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the ConversationManager.
        
        Args:
            logger: Optional logger instance for logging operations
        """
        self.sessions: Dict[str, List[Message]] = {}
        self.logger = logger or logging.getLogger(__name__)
        
        self.logger.info("ConversationManager initialized")
    
    def add_exchange(self, session_id: str, question: str, answer: str) -> None:
        """
        Add a question-answer exchange to session history.
        
        Args:
            session_id: Unique session identifier
            question: User's question
            answer: AI's answer
        """
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        
        self.sessions[session_id].append(Message('user', question))
        self.sessions[session_id].append(Message('assistant', answer))
        
        total_messages = len(self.sessions[session_id])
        self.logger.info(
            f"Added exchange to session {session_id} "
            f"(total messages: {total_messages})"
        )
    
    def get_formatted_history(
        self,
        session_id: str,
        last_n: int = 3,
        max_answer_length: int = 200
    ) -> str:
        """
        Get formatted conversation history as a string for LLM context.
        
        Args:
            session_id: Unique session identifier
            last_n: Number of recent exchanges to include (default: 3)
            max_answer_length: Maximum length of AI answers to include (default: 200)
            
        Returns:
            Formatted conversation history string
        """
        if session_id not in self.sessions:
            return ""
        
        messages = self.sessions[session_id][-(last_n * 2):]
        
        if not messages:
            return ""
        
        formatted_lines = ["Previous conversation:"]
        
        for msg in messages:
            if msg.role == 'user':
                formatted_lines.append(f"User: {msg.content}")
            elif msg.role == 'assistant':
                # Truncate long answers
                content = msg.content
                if len(content) > max_answer_length:
                    content = content[:max_answer_length] + "..."
                formatted_lines.append(f"Assistant: {content}")
        
        return "\n".join(formatted_lines)
    
    def clear_session(self, session_id: str) -> bool:
        """
        Clear conversation history for a session.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            True if session was cleared, False if session didn't exist
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            self.logger.info(f"Cleared conversation history for session: {session_id}")
            return True
        
        self.logger.warning(f"Attempted to clear non-existent session: {session_id}")
        return False
    
    def get_session_count(self) -> int:
        """
        Get the number of active sessions.
        
        Returns:
            Number of active sessions
        """
        return len(self.sessions)
    
    def get_message_count(self, session_id: str) -> int:
        """
        Get the number of messages in a session.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Number of messages in the session (0 if session doesn't exist)
        """
        if session_id not in self.sessions:
            return 0
        
        return len(self.sessions[session_id])
