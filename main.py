from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

import models, schemas, crud, workflow
from database import get_db, init_db
from logging_config import logger
from config import settings


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Multi-agent research assistant API",
)

origins = ["http://localhost:3000", "http://localhost:8080", "http://localhost:8000"]
if settings.ENVIRONMENT == "development":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.on_event("startup")
async def startup_event():
    init_db()
    logger.info("Application started")


@app.get("/")
def read_root():
    return {"message": "Marble Research Assistant", "status": "operational"}


@app.get("/health", response_model=schemas.HealthCheck)
def health_check():
    try:
        db_gen = get_db()
        db = next(db_gen)
        db.query(models.ResearchSession).limit(1).all()
        db_connected = True
        db.close()
    except Exception:
        db_connected = False
    return {
        "status": "healthy" if db_connected else "degraded",
        "environment": settings.ENVIRONMENT,
        "database_connected": db_connected,
        "version": "1.0.0",
    }


@app.post("/research/", response_model=schemas.ResearchResponse)
def start_research(request: schemas.ResearchRequest, db: Session = Depends(get_db)):
    session_data = schemas.ResearchSessionCreate(user_query=request.user_query)
    db_session = crud.create_research_session(db=db, session=session_data)

    workflow_state = {
        "max_iterations": request.max_iterations or settings.MAX_ITERATIONS,
        "critique_threshold": request.critique_threshold or settings.CRITIQUE_THRESHOLD,
    }

    initial_state = {
        "user_query": request.user_query,
        "research_data": "",
        "summary": "",
        "critique": "",
        "refined_output": "",
        "iteration": 0,
        "max_iterations": workflow_state["max_iterations"],
        "critique_score": 0,
    }
    final_state = orchestrator.graph.invoke(initial_state)

    steps = [
        {
            "agent_name": "researcher",
            "input_data": {"user_query": request.user_query},
            "output_data": {"research_data": final_state["research_data"]},
        },
        {
            "agent_name": "summarizer",
            "input_data": {"research_data": final_state["research_data"]},
            "output_data": {"summary": final_state["summary"]},
        },
        {
            "agent_name": "critic",
            "input_data": {"summary": final_state["summary"]},
            "output_data": {
                "critique": final_state["critique"],
                "critique_score": final_state.get("critique_score", 5),
            },
        },
    ]

    if final_state["refined_output"]:
        steps.append({
            "agent_name": "refiner",
            "input_data": {"summary": final_state["summary"], "critique": final_state["critique"]},
            "output_data": {"refined_output": final_state["refined_output"]},
        })

    for step_data in steps:
        step = schemas.AgentStepCreate(session_id=db_session.id, **step_data)
        crud.create_agent_step(db=db, step=step)

    final_output = final_state["refined_output"] if final_state["refined_output"] else final_state["summary"]
    crud.update_research_session(db=db, session_id=db_session.id, final_output=final_output)

    db_steps = crud.get_agent_steps_by_session(db=db, session_id=db_session.id)

    return schemas.ResearchResponse(
        session_id=db_session.id,
        user_query=db_session.user_query,
        final_output=final_output,
        is_complete=db_session.is_complete,
        iteration_count=db_session.iteration_count,
        created_at=db_session.created_at,
        completed_at=db_session.completed_at,
        steps=[schemas.AgentStep.model_validate(step) for step in db_steps],
    )


@app.get("/research/{session_id}", response_model=schemas.ResearchResponse)
def get_research(session_id: int, db: Session = Depends(get_db)):
    db_session = crud.get_research_session(db=db, session_id=session_id)
    if db_session is None:
        raise HTTPException(status_code=404, detail="Research session not found")
    db_steps = crud.get_agent_steps_by_session(db=db, session_id=session_id)
    return schemas.ResearchResponse(
        session_id=db_session.id,
        user_query=db_session.user_query,
        final_output=db_session.final_output or "",
        is_complete=db_session.is_complete,
        iteration_count=db_session.iteration_count,
        created_at=db_session.created_at,
        completed_at=db_session.completed_at,
        steps=[schemas.AgentStep.model_validate(step) for step in db_steps],
    )


@app.get("/research/", response_model=List[schemas.ResearchSession])
def list_research(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_research_sessions(db=db, skip=skip, limit=limit)