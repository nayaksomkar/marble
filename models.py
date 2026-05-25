"""
SQLAlchemy models: Document (stored text) and ResearchSession (LLM conversations).
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, func, ForeignKey
from database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    raw_text = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class ResearchSession(Base):
    __tablename__ = "research_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_query = Column(String(500), nullable=False)
    final_output = Column(Text, nullable=True)
    is_complete = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())


class AgentStep(Base):
    __tablename__ = "agent_steps"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("research_sessions.id"), nullable=False)
    agent_name = Column(String(100), nullable=False)
    input_data = Column(Text, nullable=True)
    output_data = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())