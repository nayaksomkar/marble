from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime


class ResearchSessionBase(BaseModel):
    user_query: str = Field(..., min_length=1, max_length=5000)


class ResearchSessionCreate(ResearchSessionBase):
    pass


class AgentStepCreate(BaseModel):
    session_id: int
    agent_name: str
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    extra_data: Optional[Dict[str, Any]] = None


class AgentStep(AgentStepCreate):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResearchSession(ResearchSessionBase):
    id: int
    is_complete: bool
    iteration_count: int
    final_output: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    agent_steps: List[AgentStep] = []

    model_config = ConfigDict(from_attributes=True)


class ResearchRequest(BaseModel):
    user_query: str = Field(..., min_length=1, max_length=5000)
    max_iterations: Optional[int] = Field(3, ge=0, le=10)
    critique_threshold: Optional[int] = Field(8, ge=0, le=10)


class ResearchResponse(BaseModel):
    session_id: int
    user_query: str
    final_output: str
    is_complete: bool
    iteration_count: int
    steps: List[AgentStep] = []
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class HealthCheck(BaseModel):
    status: str
    environment: str
    database_connected: bool
    version: str