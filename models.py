"""
도메인 모델

"""
from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum


class PartyStatus(Enum):
    OPEN = "OPEN"
    READY = "READY"
    MATCHED = "MATCHED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class QuestStatus(Enum):
    IN_PROGRESS = "IN_PROGRESS"
    CONFIRMING = "CONFIRMING"
    COMPLETED = "COMPLETED"
    ABORTED = "ABORTED"


class User:
    def __init__(self, user_id: str, username: str):
        self.user_id = user_id
        self.username = username
        self.trust_score: int = 100
        self.xp: int = 0
        self.point: int = 0

    def update_trust(self, delta: int) -> None:
        self.trust_score += delta

    def get_reward_total(self) -> int:
        return self.xp + self.point


class Party:
    def __init__(self, party_id: str, game_title: str, required_members: int, host: User):
        self.party_id = party_id
        self.game_title = game_title
        self.required_members = required_members
        self.host = host
        self.status: PartyStatus = PartyStatus.OPEN
        self.members: list[PartyMember] = []

    def change_status(self, new_status: PartyStatus) -> None:
        self.status = new_status

    def is_fully_ready(self) -> bool:
        # 멤버가 정원만큼 차고, 전원 레디인지 확인
        if len(self.members) < self.required_members:
            return False
        return all(m.is_ready for m in self.members)


class PartyMember:
    def __init__(self, user: User, party: Party):
        self.user = user
        self.party = party
        self.is_ready: bool = False

    def set_ready(self) -> None:
        self.is_ready = True

    def cancel_ready(self) -> None:
        self.is_ready = False


class Match:
    def __init__(self, match_id: str, party: Party):
        self.match_id = match_id
        self.party = party
        self.confirmed_at: datetime | None = None

    def confirm(self) -> None:
        self.confirmed_at = datetime.now()


class Quest:
    def __init__(self, quest_id: str, match: Match):
        self.quest_id = quest_id
        self.match = match
        self.status: QuestStatus = QuestStatus.IN_PROGRESS


class Reward(ABC):
    def __init__(self, reward_id: str, user: User, quest: Quest):
        self.reward_id = reward_id
        self.user = user
        self.quest = quest

    @abstractmethod
    def apply(self) -> None:
        ...

    @abstractmethod
    def get_amount(self) -> int:
        ...


class XPReward(Reward):
    def __init__(self, reward_id: str, user: User, quest: Quest, xp_amount: int):
        super().__init__(reward_id, user, quest)
        self.xp_amount = xp_amount

    def apply(self) -> None:
        self.user.xp += self.xp_amount

    def get_amount(self) -> int:
        return self.xp_amount


class PointReward(Reward):
    def __init__(self, reward_id: str, user: User, quest: Quest, point_amount: int):
        super().__init__(reward_id, user, quest)
        self.point_amount = point_amount

    def apply(self) -> None:
        self.user.point += self.point_amount

    def get_amount(self) -> int:
        return self.point_amount