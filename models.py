from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Boolean, func
from sqlalchemy.orm import relationship
from database import Base


class ResearchSession(Base):
    __tablename__ = "research_sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_query = Column(Text, nullable=False)
    final_output = Column(Text)
    is_complete = Column(Boolean, default=False)
    iteration_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime)


class AgentStep(Base):
    __tablename__ = "agent_steps"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("research_sessions.id", ondelete="CASCADE"), nullable=False)
    agent_name = Column(String(50), nullable=False)
    input_data = Column(JSON)
    output_data = Column(JSON)
    status = Column(String(20), default="completed")
    created_at = Column(DateTime, server_default=func.now())
    session = relationship("ResearchSession")