"""
FastAPI server — upload PDFs, extract text, store in SQLite, and answer
questions via LangGraph + Groq/Mistral LLMs.
"""
import json
from fastapi import FastAPI, UploadFile, File, HTTPException
import shutil
from pathlib import Path
from typing import Optional

import models
import crud
from database import get_db, get_db_session, init_db
from config import settings
from logging_config import logger
from extract import extract_text
from schemas import ResearchRequest, ResearchResponse
from workflow import run_workflow

app = FastAPI(title=settings.PROJECT_NAME, version="1.0.0")

UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


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
        db.execute(
            db.bind.dialect.statement_compiler(db.bind, db.bind.dialect).process([])
        )
        ok = True
    except Exception:
        ok = False
    try:
        db.close()
    except Exception:
        pass
    return {"status": "ok" if ok else "degraded", "database": ok}


# ── Upload / Documents ──────────────────────────────────────────────

@app.post("/upload")
def upload(file: UploadFile = File(...)):
    """Accept an uploaded file, save to uploads/, extract text, store in SQLite."""
    path = UPLOAD_DIR / file.filename
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    raw = extract_text(str(path))

    db = next(get_db())
    doc = crud.create_document(db, file.filename, raw)
    db.close()

    return {
        "id": doc.id,
        "filename": doc.filename,
        "size": len(raw),
        "preview": raw[:500],
    }


@app.get("/documents")
def list_docs():
    db = next(get_db())
    docs = crud.get_documents(db)
    db.close()
    return [
        {"id": d.id, "filename": d.filename, "size": len(d.raw_text or "")}
        for d in docs
    ]


@app.get("/documents/{did}")
def get_doc(did: int):
    db = next(get_db())
    doc = crud.get_document(db, did)
    db.close()
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    return {"id": doc.id, "filename": doc.filename, "text": doc.raw_text}


@app.delete("/documents/{did}")
def delete_doc(did: int):
    db = next(get_db())
    doc = crud.get_document(db, did)
    if not doc:
        db.close()
        raise HTTPException(status_code=404, detail="Not found")
    path = UPLOAD_DIR / doc.filename
    if path.exists():
        path.unlink()
    crud.delete_document(db, did)
    db.close()
    return {"deleted": did}


@app.post("/extract-existing")
def extract_existing():
    """Process only the files listed in test_data.json."""
    test_list = Path("./test_data.json")
    if not test_list.exists():
        return {"error": "test_data.json not found"}

    data = json.loads(test_list.read_text())
    filenames = data.get("files", [])
    results = []

    for fname in filenames:
        path = UPLOAD_DIR / fname
        if not path.exists():
            results.append({"file": fname, "error": "not found in uploads/"})
            continue
        raw = extract_text(str(path))
        db = next(get_db())
        doc = crud.create_document(db, fname, raw)
        db.close()
        results.append({"file": fname, "size": len(raw)})

    return {"processed": results}


# ── Research / Q&A ──────────────────────────────────────────────────

@app.post("/research")
def research(req: ResearchRequest):
    """
    Run a LangGraph workflow: retrieve document context, send to LLM,
    return the answer. Creates a session to track history.
    """
    db = get_db_session()
    try:
        result = run_workflow(
            query=req.query,
            provider=req.provider or "",
            model=req.model or "",
            temperature=req.temperature or 0.0,
        )

        answer = result.get("answer", "")
        provider_used = (req.provider or settings.LLM_PROVIDER).lower()
        model_used = req.model or settings.LLM_MODEL

        db_sess = crud.create_research_session(db, req.query)
        session_id = db_sess.id
        crud.update_research_session(db, session_id, answer)
        crud.create_agent_step(db, session_id, "retrieve_context",
                               input_data=req.query,
                               output_data=result.get("context", "")[:500])
        crud.create_agent_step(db, session_id, f"llm_{provider_used}",
                               input_data=req.query, output_data=answer)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Research error: {e}")
        raise
    finally:
        db.close()

    return {
        "session_id": session_id,
        "query": req.query,
        "output": answer,
        "provider": provider_used,
        "model": model_used,
    }


@app.get("/sessions")
def list_sessions():
    db = next(get_db())
    sessions = crud.get_research_sessions(db)
    db.close()
    return [{"id": s.id, "query": s.user_query, "complete": bool(s.is_complete)} for s in sessions]


@app.get("/sessions/{sid}")
def get_session(sid: int):
    db = next(get_db())
    s = crud.get_research_session(db, sid)
    if not s:
        db.close()
        raise HTTPException(status_code=404, detail="Session not found")
    steps = crud.get_agent_steps(db, sid)
    db.close()
    return {
        "id": s.id,
        "query": s.user_query,
        "output": s.final_output,
        "steps": [
            {"agent": st.agent_name, "input": st.input_data, "output": st.output_data}
            for st in steps
        ],
    }