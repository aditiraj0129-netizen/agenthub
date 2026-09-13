"""
This is the front door of the whole system.
Every request from the frontend hits THIS file first.
It does 3 things before letting anything through:
  1. Checks an API key (so randoms can't hit your server)
  2. Rate-limits (so one user can't flood it)
  3. Logs the request (for your evaluation dashboard later)
"""
import time
import uuid
from fastapi import FastAPI, Request, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

import os
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("API_KEY", "dev-secret-key-change-me")

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="AgentHub Gateway")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tighten this in production
    allow_methods=["*"],
    allow_headers=["*"],
)

REQUEST_LOG = []   # in-memory for now; step 6 will wire this to the eval dashboard


def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True


@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    start = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start) * 1000, 2)
    REQUEST_LOG.append({
        "id": request_id,
        "path": request.url.path,
        "status": response.status_code,
        "duration_ms": duration_ms,
    })
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/logs", dependencies=[Depends(verify_api_key)])
def get_logs():
    """This powers your dashboard's live-logs panel later."""
    return REQUEST_LOG[-50:]


# --- Step 2 addition: the actual chat endpoint ---
from pydantic import BaseModel
from app.orchestrator.graph import compiled_graph


class ChatRequest(BaseModel):
    message: str


@app.post("/chat", dependencies=[Depends(verify_api_key)])
@limiter.limit("10/minute")
async def chat(request: Request, body: ChatRequest):
    result = compiled_graph.invoke({
        "user_input": body.message,
        "request_id": "",
        "input_safe": True,
        "input_block_reason": None,
        "intent": None,
        "agent_response": None,
        "final_output": None,
        "error": None,
    })
    return {
        "intent": result["intent"],
        "response": result["final_output"],
        "was_blocked": not result["input_safe"],
    }


# --- Step 3.5 addition: register + list competitor sites ---
from app.agents.competitor.registry import add_site, list_sites


class SiteRegistration(BaseModel):
    site_id: str
    url: str


@app.post("/competitor/sites", dependencies=[Depends(verify_api_key)])
def register_site(site: SiteRegistration):
    saved = add_site(site.site_id, site.url)
    return {"message": f"Registered {site.site_id}", "site": saved}


@app.get("/competitor/sites", dependencies=[Depends(verify_api_key)])
def get_sites():
    return list_sites()


# --- Step 3.5 addition: start the background scheduler ---
from app.agents.competitor.scheduler import start_scheduler

from app.db.database import init_db

@app.on_event("startup")
def on_startup():
    init_db()
    start_scheduler(interval_minutes=60)   # competitor watcher; checks every hour
    start_receptionist_scheduler()          # releases busy employees every minute


# --- Step 4 addition: MCP tool approval endpoints ---
from app.agents.mcp.approval import approve_call, reject_call, get_audit_log, get_pending


class ApprovalRequest(BaseModel):
    password: str


@app.post("/mcp/approve/{approval_id}", dependencies=[Depends(verify_api_key)])
def mcp_approve(approval_id: str, body: ApprovalRequest):
    return approve_call(approval_id, body.password)


@app.post("/mcp/reject/{approval_id}", dependencies=[Depends(verify_api_key)])
def mcp_reject(approval_id: str):
    return reject_call(approval_id)


@app.get("/mcp/pending", dependencies=[Depends(verify_api_key)])
def mcp_pending():
    return get_pending()


@app.get("/mcp/audit-log", dependencies=[Depends(verify_api_key)])
def mcp_audit_log():
    return get_audit_log()


# --- Step 5 addition: evaluation metrics endpoint ---
from app.evaluation.metrics import get_summary


@app.get("/metrics", dependencies=[Depends(verify_api_key)])
def metrics():
    return get_summary()


# --- Step 9 addition: pipeline trace endpoints ---
from app.db.database import get_db


@app.get("/trace/latest", dependencies=[Depends(verify_api_key)])
def trace_latest():
    with get_db() as conn:
        row = conn.execute("SELECT request_id FROM pipeline_trace ORDER BY id DESC LIMIT 1").fetchone()
        if not row:
            return {"request_id": None, "stages": []}
        request_id = row["request_id"]
        stages = conn.execute(
            "SELECT stage, detail, created_at FROM pipeline_trace WHERE request_id = ? ORDER BY id ASC",
            (request_id,),
        ).fetchall()
        return {"request_id": request_id, "stages": [dict(s) for s in stages]}


@app.get("/trace/{request_id}", dependencies=[Depends(verify_api_key)])
def trace_by_id(request_id: str):
    with get_db() as conn:
        stages = conn.execute(
            "SELECT stage, detail, created_at FROM pipeline_trace WHERE request_id = ? ORDER BY id ASC",
            (request_id,),
        ).fetchall()
        return {"request_id": request_id, "stages": [dict(s) for s in stages]}


# --- Step 10 addition: employees & tasks endpoints ---
from app.agents.receptionist.scheduler import start_receptionist_scheduler


@app.get("/employees", dependencies=[Depends(verify_api_key)])
def get_employees():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM employees").fetchall()
        return [dict(r) for r in rows]


@app.get("/tasks", dependencies=[Depends(verify_api_key)])
def get_tasks():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM tasks ORDER BY id DESC LIMIT 50").fetchall()
        return [dict(r) for r in rows]
