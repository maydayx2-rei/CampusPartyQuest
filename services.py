"""
서비스 계층

"""
from __future__ import annotations

from models import (
    User, Party, PartyMember, Match, Quest,
    XPReward, PointReward,
    PartyStatus, QuestStatus,
)


class PartyQuestService:

    def __init__(self):
        self.users: dict[str, User] = {}
        self.parties: dict[str, Party] = {}
        self.matches: dict[str, Match] = {}
        self.quests: dict[str, Quest] = {}
        self._party_seq = 0
        self._match_seq = 0
        self._quest_seq = 0

    # ── 유저 (UC1/UC2 간소화: 없으면 생성) ──
    def get_or_create_user(self, user_id: str) -> User:
        if user_id not in self.users:
            self.users[user_id] = User(user_id, user_id)
        return self.users[user_id]

    # ── 파티 생성 ──
    def create_party(self, host_id: str, game_title: str, required_members: int) -> Party:
        host = self.get_or_create_user(host_id)
        self._party_seq += 1
        party_id = f"party_{self._party_seq}"
        party = Party(party_id, game_title, required_members, host)
        party.change_status(PartyStatus.OPEN)
        # 호스트도 멤버로 자동 참여
        host_member = PartyMember(host, party)
        party.members.append(host_member)
        self.parties[party_id] = party
        return party

    # ── 파티 목록 ──
    def list_parties(self) -> list[Party]:
        return list(self.parties.values())

    def get_party(self, party_id: str) -> Party | None:
        return self.parties.get(party_id)

    # ── 파티 참여 ──
    def join_party(self, party_id: str, user_id: str) -> tuple[bool, str]:
        party = self.parties.get(party_id)
        if party is None:
            return False, "존재하지 않는 파티입니다."
        if party.status != PartyStatus.OPEN:
            return False, "모집 중인 파티가 아닙니다."
        
        # 이미 참여했는지 확인
        if any(m.user.user_id == user_id for m in party.members):
            return False, "이미 참여한 파티입니다."
        if len(party.members) >= party.required_members:
            return False, "정원이 가득 찼습니다."

        user = self.get_or_create_user(user_id)
        party.members.append(PartyMember(user, party))

        # 정원이 차면 레디 체크 단계로
        if len(party.members) >= party.required_members:
            party.change_status(PartyStatus.READY)
            return True, "참여 완료. 정원이 찼습니다. 레디 체크를 시작하세요."
        return True, "참여 완료. 다른 멤버를 기다리는 중입니다."

    # ── 레디 체크 ──
    def set_ready(self, party_id: str, user_id: str) -> tuple[bool, str]:
        party = self.parties.get(party_id)
        if party is None:
            return False, "존재하지 않는 파티입니다."
        member = next((m for m in party.members if m.user.user_id == user_id), None)
        if member is None:
            return False, "파티 멤버가 아닙니다."
        member.set_ready()

        if party.is_fully_ready():
            return True, "레디 완료. 전원 준비됨 — 파티장이 매칭을 수락할 수 있습니다."
        return True, "레디 완료. 다른 멤버의 준비를 기다리는 중입니다."

    # ── 매칭 (파티장 수락) ──
    def confirm_match(self, party_id: str, requester_id: str) -> tuple[bool, str, Match | None]:
        party = self.parties.get(party_id)
        if party is None:
            return False, "존재하지 않는 파티입니다.", None
        if party.host.user_id != requester_id:
            return False, "파티장만 매칭을 수락할 수 있습니다.", None
        if not party.is_fully_ready():
            return False, "전원이 준비되지 않았습니다.", None

        self._match_seq += 1
        match_id = f"match_{self._match_seq}"
        match = Match(match_id, party)
        match.confirm()
        party.change_status(PartyStatus.MATCHED)
        self.matches[match_id] = match
        return True, "매칭 확정!", match

    # ── 파티 취소 ──
    def cancel_party(self, party_id: str, requester_id: str) -> tuple[bool, str]:
        party = self.parties.get(party_id)
        if party is None:
            return False, "존재하지 않는 파티입니다."
        if party.host.user_id != requester_id:
            return False, "파티장만 취소할 수 있습니다."
        party.change_status(PartyStatus.CANCELLED)
        return True, "파티가 취소되었습니다."

    # ── 퀘스트 완료 + 보상  ──
    def complete_quest_and_reward(self, party_id: str, reward_type: str, amount: int) -> tuple[bool, str, list[dict]]:
        party = self.parties.get(party_id)
        if party is None:
            return False, "존재하지 않는 파티입니다.", []
        if party.status != PartyStatus.MATCHED:
            return False, "매칭이 확정된 파티만 퀘스트를 완료할 수 있습니다.", []

        # 매칭/퀘스트 생성
        match = next((m for m in self.matches.values() if m.party.party_id == party_id), None)
        if match is None:
            return False, "매칭 정보가 없습니다.", []
        self._quest_seq += 1
        quest = Quest(f"quest_{self._quest_seq}", match)
        quest.status = QuestStatus.COMPLETED
        self.quests[quest.quest_id] = quest

        # 전원 보상 지급
        results = []
        for member in party.members:
            user = member.user
            if reward_type == "XP":
                reward = XPReward(f"rwd_{user.user_id}", user, quest, amount)
            else:
                reward = PointReward(f"rwd_{user.user_id}", user, quest, amount)
            reward.apply()                
            user.update_trust(+5)         # 완료 시 신뢰도 상승
            results.append({
                "user": user.username,
                "reward_type": reward_type,
                "amount": reward.get_amount(),
                "total_xp": user.xp,
                "total_point": user.point,
                "trust_score": user.trust_score,
            })
        return True, "퀘스트 완료 — 전원에게 보상이 지급되었습니다.", results