from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

import models, schemas, crud, workflow
from database import get_db, init_db
from config import settings
from logging_config import logger

app = FastAPI(title=settings.PROJECT_NAME, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()
    logger.info("App started")


@app.get("/")
def root():
    return {"app": settings.PROJECT_NAME, "version": "1.0.0"}


@app.get("/health")
def health():
    try:
        db = next(get_db())
        db.execute(db.bind.dialect.statement_compiler(db.bind, db.bind.dialect).process([]))
        ok = True
    except Exception as e:
        ok = False
    return {"status": "ok" if ok else "degraded", "database": ok}


@app.post("/research/")
def research(req: schemas.ResearchRequest):
    db = next(get_db())
    session = crud.create_research_session(db, req.user_query)

    w = workflow.Workflow()
    result = w.run(req.user_query)

    steps = [
        schemas.AgentStepCreate(session_id=session.id, agent_name="researcher", output_data={"data": result["research_data"][:200]}),
        schemas.AgentStepCreate(session_id=session.id, agent_name="summarizer", output_data={"summary": result["summary"][:200]}),
        schemas.AgentStepCreate(session_id=session.id, agent_name="critic", output_data={"score": result["critique_score"]}),
    ]
    for s in steps:
        crud.create_agent_step(db, s)

    output = result.get("refined_output") or result["summary"]
    crud.update_research_session(db, session.id, output)
    db.close()

    return {"session_id": session.id, "output": output, "score": result["critique_score"]}


@app.get("/research/")
def list_sessions():
    db = next(get_db())
    sessions = crud.get_research_sessions(db)
    db.close()
    return [{"id": s.id, "query": s.user_query, "complete": s.is_complete} for s in sessions]


@app.get("/research/{sid}")
def get_session(sid: int):
    db = next(get_db())
    s = crud.get_research_session(db, sid)
    if not s:
        db.close()
        raise HTTPException(status_code=404, detail="Not found")
    steps = crud.get_agent_steps(db, sid)
    db.close()
    return {
        "id": s.id, "query": s.user_query, "output": s.final_output,
        "complete": s.is_complete, "steps": [
            {"agent": st.agent_name, "output": st.output_data} for st in steps
        ]
    }