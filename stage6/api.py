"""Lesson 6.5: the multi-agent system from 6.4, served as a web API with FastAPI.

Run it:   python stage6/api.py
Chat:     http://127.0.0.1:8000        (the web page from lesson 6.6)
Docs:     http://127.0.0.1:8000/docs   (interactive, try the endpoints in your browser)
"""
import functools
import threading
import uuid
from datetime import datetime

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

import multi_agent
from hr_agent import search_handbook, check_vacation_balance, MODEL
from multiple_tools import request_time_off

# =====================================================================
# CONFIRMATION, WEB STYLE
# In the terminal (6.2) we paused with input(). A web server can't pause and
# wait for a keyboard. Instead, the action is SAVED as "pending" and the
# client must call POST /actions/{id}/confirm to approve or reject it.
# =====================================================================
PENDING = {}  # action_id -> details (in memory: lost on restart, fine for learning)


def needs_web_confirmation(func):
    @functools.wraps(func)
    def wrapper(**kwargs):
        action_id = uuid.uuid4().hex[:8]
        PENDING[action_id] = {"id": action_id, "tool": func.__name__, "args": kwargs,
                              "created": datetime.now().isoformat(timespec="seconds")}
        return {"status": "pending_confirmation", "action_id": action_id,
                "message": "Not done yet. Tell the user this needs their approval first."}
    return wrapper


ACTIONS = {"request_time_off": request_time_off}  # the real functions, run only after approval

# Give the HR specialist the web-confirmation version of the booking tool
multi_agent.SPECIALISTS["hr"]["tools"] = [
    search_handbook, check_vacation_balance, needs_web_confirmation(request_time_off),
]

# The local model handles one request at a time anyway, and our in-memory data
# isn't built for simultaneous edits, so we let one request run at a time.
agent_lock = threading.Lock()


# =====================================================================
# THE API
# Pydantic models define what JSON goes in and out. FastAPI checks
# incoming requests against them and builds the /docs page from them.
# =====================================================================
app = FastAPI(title="Nimbus HR Agent API", version="1.0")


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str
    pending_actions: list[dict]


class ConfirmRequest(BaseModel):
    approve: bool


@app.get("/", include_in_schema=False)
def home():
    """The chat web page (lesson 6.6). Open http://127.0.0.1:8000 in a browser."""
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.get("/health")
def health():
    """Is the server up? Which model is it using?"""
    return {"status": "ok", "model": MODEL, "specialists": list(multi_agent.SPECIALISTS)}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    """Ask the agent team a question."""
    question = req.question.strip()
    if not question:
        raise HTTPException(400, "question must not be empty")
    if len(question) > 1000:
        raise HTTPException(400, "question too long (max 1000 characters)")

    with agent_lock:
        before = set(PENDING)
        try:
            answer = multi_agent.handle(question)
        except Exception as e:  # never show a raw crash to the client
            raise HTTPException(503, f"The agent failed: {type(e).__name__}") from e
        new_actions = [PENDING[i] for i in PENDING if i not in before]
    return AskResponse(answer=answer, pending_actions=new_actions)


@app.get("/actions")
def list_actions():
    """All actions waiting for approval."""
    return list(PENDING.values())


@app.post("/actions/{action_id}/confirm")
def confirm(action_id: str, req: ConfirmRequest):
    """Approve or reject a pending action. Only approval actually runs it."""
    action = PENDING.pop(action_id, None)
    if action is None:
        raise HTTPException(404, f"No pending action '{action_id}'")
    if not req.approve:
        return {"status": "rejected", "action": action}
    with agent_lock:
        result = ACTIONS[action["tool"]](**action["args"])
    return {"status": "done", "action": action, "result": result}


if __name__ == "__main__":
    import uvicorn
    # 127.0.0.1 = only THIS computer can connect. There's no login yet, so
    # don't use 0.0.0.0 (which would let anyone on your network use the agent).
    uvicorn.run(app, host="127.0.0.1", port=8000)
