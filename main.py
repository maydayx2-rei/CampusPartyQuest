"""
FastAPI 서버
실행: uvicorn main:app --reload
"""
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os

from services import PartyQuestService

app = FastAPI(title="Campus Party Quest", version="1.0")
service = PartyQuestService()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


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
    reward_type: str  # "XP" 또는 "POINT"
    amount: int


# ── 파티를 JSON으로 변환하는 헬퍼 ──
def party_to_dict(p):
    return {
        "party_id": p.party_id,
        "game_title": p.game_title,
        "required_members": p.required_members,
        "host": p.host.username,
        "status": p.status.value,
        "members": [
            {"user": m.user.username, "is_ready": m.is_ready}
            for m in p.members
        ],
    }


# ════════════ API ════════════

@app.get("/api")
def api_root():
    return {"message": "Campus Party Quest API 작동 중!"}


# 파티 생성
@app.post("/parties")
def create_party(req: CreatePartyRequest):
    party = service.create_party(req.host_id, req.game_title, req.required_members)
    return party_to_dict(party)


# 파티 목록
@app.get("/parties")
def list_parties():
    return [party_to_dict(p) for p in service.list_parties()]


# 파티 단건 조회
@app.get("/parties/{party_id}")
def get_party(party_id: str):
    party = service.get_party(party_id)
    if party is None:
        return {"error": "존재하지 않는 파티입니다."}
    return party_to_dict(party)


# 파티 참여
@app.post("/parties/{party_id}/join")
def join_party(party_id: str, req: JoinRequest):
    ok, msg = service.join_party(party_id, req.user_id)
    return {"success": ok, "message": msg}


# 레디 체크
@app.post("/parties/{party_id}/ready")
def set_ready(party_id: str, req: ReadyRequest):
    ok, msg = service.set_ready(party_id, req.user_id)
    return {"success": ok, "message": msg}


# 매칭 수락
@app.post("/parties/{party_id}/confirm")
def confirm_match(party_id: str, req: ConfirmRequest):
    ok, msg, match = service.confirm_match(party_id, req.requester_id)
    result = {"success": ok, "message": msg}
    if match:
        result["match_id"] = match.match_id
    return result


# 파티 취소
@app.post("/parties/{party_id}/cancel")
def cancel_party(party_id: str, req: ConfirmRequest):
    ok, msg = service.cancel_party(party_id, req.requester_id)
    return {"success": ok, "message": msg}


# 퀘스트 완료 + 보상
@app.post("/parties/{party_id}/complete")
def complete_quest(party_id: str, req: RewardRequest):
    ok, msg, results = service.complete_quest_and_reward(party_id, req.reward_type, req.amount)
    return {"success": ok, "message": msg, "rewards": results}


# ── 정적 화면 (index.html) ──
@app.get("/")
def serve_ui():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))