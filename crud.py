from sqlalchemy.orm import Session
from typing import List
import models, schemas


def create_research_session(db: Session, session: schemas.ResearchSessionCreate) -> models.ResearchSession:
    db_session = models.ResearchSession(user_query=session.user_query)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


def get_research_session(db: Session, session_id: int) -> models.ResearchSession:
    return db.query(models.ResearchSession).filter(models.ResearchSession.id == session_id).first()


def get_research_sessions(db: Session, skip: int = 0, limit: int = 100) -> List[models.ResearchSession]:
    return db.query(models.ResearchSession).offset(skip).limit(limit).all()


def update_research_session(db: Session, session_id: int, final_output: str) -> models.ResearchSession:
    session = db.query(models.ResearchSession).filter(models.ResearchSession.id == session_id).first()
    if session:
        session.final_output = final_output
        session.is_complete = True
        session.completed_at = db.query(models.ResearchSession.updated_at).filter(
            models.ResearchSession.id == session_id
        ).scalar()
        db.commit()
        db.refresh(session)
    return session


def create_agent_step(db: Session, step: schemas.AgentStepCreate) -> models.AgentStep:
    db_step = models.AgentStep(
        session_id=step.session_id,
        agent_name=step.agent_name,
        input_data=step.input_data,
        output_data=step.output_data,
        extra_data=step.extra_data,
    )
    db.add(db_step)
    db.commit()
    db.refresh(db_step)
    return db_step


def get_agent_steps_by_session(db: Session, session_id: int) -> List[models.AgentStep]:
    return db.query(models.AgentStep).filter(
        models.AgentStep.session_id == session_id
    ).order_by(models.AgentStep.created_at.asc()).all()