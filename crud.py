"""
SQLAlchemy CRUD helpers for Document and ResearchSession models.
"""
from sqlalchemy.orm import Session
from typing import List, Optional
import models


# ── Document CRUD ──────────────────────────────────────────────────────

def create_document(db: Session, filename: str, text: str) -> models.Document:
    doc = models.Document(filename=filename, raw_text=text)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def get_document(db: Session, doc_id: int) -> Optional[models.Document]:
    return db.query(models.Document).filter(models.Document.id == doc_id).first()


def get_documents(db: Session, skip: int = 0, limit: int = 100) -> List[models.Document]:
    return db.query(models.Document).offset(skip).limit(limit).all()


def delete_document(db: Session, doc_id: int) -> None:
    db.query(models.Document).filter(models.Document.id == doc_id).delete()
    db.commit()


def get_all_document_texts(db: Session, max_chars: int = 3000) -> str:
    """Concatenate all extracted texts for use as LLM context (truncated)."""
    docs = db.query(models.Document).all()
    parts = []
    for d in docs:
        if d.raw_text:
            parts.append(f"--- {d.filename} ---\n{d.raw_text[:max_chars]}")
    return "\n\n".join(parts)


# ── ResearchSession CRUD ──────────────────────────────────────────────

def create_research_session(db: Session, query: str) -> models.ResearchSession:
    s = models.ResearchSession(user_query=query)
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def get_research_session(db: Session, sid: int) -> Optional[models.ResearchSession]:
    return db.query(models.ResearchSession).filter(models.ResearchSession.id == sid).first()


def get_research_sessions(db: Session) -> List[models.ResearchSession]:
    return db.query(models.ResearchSession).order_by(models.ResearchSession.created_at.desc()).all()


def update_research_session(db: Session, sid: int, output: str) -> None:
    s = db.query(models.ResearchSession).filter(models.ResearchSession.id == sid).first()
    if s:
        s.final_output = output
        s.is_complete = 1
        db.commit()


# ── AgentStep CRUD ────────────────────────────────────────────────────

def create_agent_step(db: Session, session_id: int, agent_name: str,
                      input_data: str = "", output_data: str = "") -> models.AgentStep:
    step = models.AgentStep(
        session_id=session_id, agent_name=agent_name,
        input_data=input_data, output_data=output_data,
    )
    db.add(step)
    db.commit()
    db.refresh(step)
    return step


def get_agent_steps(db: Session, session_id: int) -> List[models.AgentStep]:
    return db.query(models.AgentStep).filter(
        models.AgentStep.session_id == session_id
    ).order_by(models.AgentStep.id).all()