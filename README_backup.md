# 🎮 Campus Party Quest

캠퍼스 환경에서 게임 플레이어를 매칭하는 **퀘스트 기반 파티 매칭 시스템**입니다.

- **언어**: Python (FastAPI)
- **배포 URL**: ()

## 실행 방법

```bash
# 1. 가상환경 생성 및 활성화 (Windows PowerShell)
py -m venv venv
.\venv\Scripts\Activate.ps1

# 2. 패키지 설치
pip install -r requirements.txt

# 3. 서버 실행
uvicorn main:app --reload

# 4. 접속
#  - 웹 화면 : http://127.0.0.1:8000/
#  - API 문서: http://127.0.0.1:8000/docs
```

## 프로젝트 구조

| 파일 | 역할 | 대응 설계 산출물 |
|------|------|-----------------|
| `models.py` | 도메인 클래스 6개 + 다형성 Reward | 클래스 다이어그램 |
| `services.py` | 비즈니스 로직 (파티/매칭/보상 흐름) | 시퀀스 다이어그램 |
| `main.py` | FastAPI 서버 (REST API) | 구현 요구사항 |
| `index.html` | 웹 UI | UI 프로토타입 |

## 구현된 유즈케이스

- UC3 파티 생성 / UC4 목록 조회 / UC5 참여
- UC6 레디 체크 / UC7 파티 취소
- UC8 매칭 (파티장 수락) / UC11 퀘스트 완료 + 보상 지급

## 설계 반영 포인트

- **객체지향**: 6개 도메인 클래스를 설계 문서대로 구현
- **다형성**: `Reward` 추상 클래스를 `XPReward` / `PointReward`가 상속하여 `apply()`를 각자 구현
- **상태 관리**: `PartyStatus` (OPEN→READY→MATCHED) 상태 전이를 상태 머신 다이어그램대로 구현