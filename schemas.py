"""
Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel
from typing import Optional, List


class ResearchRequest(BaseModel):
    query: str
    provider: Optional[str] = None       # "groq" or "mistral"
    model: Optional[str] = None
    temperature: Optional[float] = None


class ResearchResponse(BaseModel):
    session_id: int
    query: str
    output: str
    provider: str
    model: str


class SessionSummary(BaseModel):
    id: int
    query: str
    complete: bool


class SessionDetail(BaseModel):
    id: int
    query: str
    output: Optional[str]
    steps: List[dict]


class UploadResponse(BaseModel):
    id: int
    filename: str
    size: int
    preview: str