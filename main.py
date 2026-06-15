"""
Campus Party Quest - FastAPI 서버
실행: uvicorn main:app --reload
문서: http://127.0.0.1:8000/docs
"""
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os

from services import PartyQuestService

app = FastAPI(title="Campus Party Quest", version="1.0")
service = PartyQuestService()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ── 요청 본문 ──
class RegisterRequest(BaseModel):
    user_id: str
    password: str
    username: str

class LoginRequest(BaseModel):
    user_id: str
    password: str

class CreatePartyRequest(BaseModel):
    host_id: str
    game_title: str
    required_members: int

class JoinRequest(BaseModel):
    user_id: str

class ReadyRequest(BaseModel):
    user_id: str

class ConfirmRequest(BaseModel):
    requester_id: str

class RewardRequest(BaseModel):
    reward_type: str
    amount: int


# ── 헬퍼 ──
def party_to_dict(p):
    return {
        "party_id": p.party_id,
        "game_title": p.game_title,
        "required_members": p.required_members,
        "host": p.host.username,
        "status": p.status.value,
        "members": [{"user": m.user.username, "is_ready": m.is_ready} for m in p.members],
    }


# ════════ 페이지 라우팅 ════════
@app.get("/")
def serve_login():
    return FileResponse(os.path.join(BASE_DIR, "templates", "login.html"))

@app.get("/list")
def serve_list():
    return FileResponse(os.path.join(BASE_DIR, "templates", "list.html"))

@app.get("/detail")
def serve_detail():
    return FileResponse(os.path.join(BASE_DIR, "templates", "detail.html"))

@app.get("/complete")
def serve_complete():
    return FileResponse(os.path.join(BASE_DIR, "templates", "complete.html"))


# ════════ AUTH API ════════
_passwords: dict = {}

@app.post("/api/register")
def register(req: RegisterRequest):
    if req.user_id in _passwords:
        return {"success": False, "message": "이미 사용 중인 아이디입니다."}
    _passwords[req.user_id] = req.password
    user = service.get_or_create_user(req.user_id)
    user.username = req.username
    return {"success": True, "user_id": user.user_id, "username": user.username, "trust_score": user.trust_score}

@app.post("/api/login")
def login(req: LoginRequest):
    if req.user_id not in _passwords:
        return {"success": False, "message": "존재하지 않는 아이디입니다."}
    if _passwords[req.user_id] != req.password:
        return {"success": False, "message": "비밀번호가 올바르지 않습니다."}
    user = service.get_or_create_user(req.user_id)
    return {"success": True, "user_id": user.user_id, "username": user.username, "trust_score": user.trust_score}


# ════════ PARTY API ════════
@app.get("/api")
def api_root():
    return {"message": "Campus Party Quest API 작동 중!"}

@app.post("/parties")
def create_party(req: CreatePartyRequest):
    party = service.create_party(req.host_id, req.game_title, req.required_members)
    return party_to_dict(party)

@app.get("/parties")
def list_parties():
    return [party_to_dict(p) for p in service.list_parties()]

@app.get("/parties/{party_id}")
def get_party(party_id: str):
    party = service.get_party(party_id)
    if party is None:
        return {"error": "존재하지 않는 파티입니다."}
    return party_to_dict(party)

@app.post("/parties/{party_id}/join")
def join_party(party_id: str, req: JoinRequest):
    ok, msg = service.join_party(party_id, req.user_id)
    return {"success": ok, "message": msg}

@app.post("/parties/{party_id}/ready")
def set_ready(party_id: str, req: ReadyRequest):
    ok, msg = service.set_ready(party_id, req.user_id)
    return {"success": ok, "message": msg}

@app.post("/parties/{party_id}/confirm")
def confirm_match(party_id: str, req: ConfirmRequest):
    ok, msg, match = service.confirm_match(party_id, req.requester_id)
    result = {"success": ok, "message": msg}
    if match:
        result["match_id"] = match.match_id
    return result

@app.post("/parties/{party_id}/cancel")
def cancel_party(party_id: str, req: ConfirmRequest):
    ok, msg = service.cancel_party(party_id, req.requester_id)
    return {"success": ok, "message": msg}

@app.post("/parties/{party_id}/complete")
def complete_quest(party_id: str, req: RewardRequest):
    ok, msg, results = service.complete_quest_and_reward(party_id, req.reward_type, req.amount)
    return {"success": ok, "message": msg, "rewards": results}