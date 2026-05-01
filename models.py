from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class ResearchSession(Base):
    __tablename__ = "research_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_query = Column(Text, nullable=False)
    final_output = Column(Text)
    is_complete = Column(Boolean, default=False)
    iteration_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    agent_steps = relationship(
        "AgentStep",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="AgentStep.created_at.asc()",
    )


class AgentStep(Base):
    __tablename__ = "agent_steps"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("research_sessions.id", ondelete="CASCADE"), nullable=False)
    agent_name = Column(String(50), nullable=False, index=True)
    step_type = Column(String(50), nullable=True)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    extra_data = Column(JSON, nullable=True)
    status = Column(String(20), default="completed")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    session = relationship("ResearchSession", back_populates="agent_steps")