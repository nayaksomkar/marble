from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class ResearchRequest(BaseModel):
    user_query: str = Field(..., min_length=1, max_length=5000)


class ResearchResponse(BaseModel):
    session_id: int
    user_query: str
    final_output: str = ""
    is_complete: bool = False
    iteration_count: int = 0
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    steps: List[Dict[str, Any]] = []


class AgentStepCreate(BaseModel):
    session_id: int
    agent_name: str
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    extra_data: Optional[Dict[str, Any]] = None


class HealthCheck(BaseModel):
    status: str
    environment: str
    database_connected: bool
    version: str