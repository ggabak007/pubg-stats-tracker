# 🎯 PUBG Ranked Tracker (배틀그라운드 경쟁전 전적 트래커)

Official PUBG API를 활용하여 스팀 배틀그라운드(PUBG) 플레이어의 경쟁전 시즌 전적 분석 및 최근 매치 기록을 실시간으로 추적하는 GUI 애플리케이션입니다.

---

## 🌟 주요 기능 (Key Features)

- **🔍 실시간 닉네임 검색:** 인게임 닉네임 검색을 통한 플레이어 고유 ID(Account ID) 자동 식별
- **📊 경쟁전 시즌 대시보드:**
  - 티어 및 현재 / 최고 RP 표시
  - KDA, K/D, 평균 딜량, 총 판수, 승률(치킨 확률), 평균 순위 종합 요약
- **📂 엑셀(Excel) 자동 저장:** 조회한 시즌 전적 데이터를 닉네임별 엑셀 파일(`pubg_{닉네임}_summary.xlsx`)로 자동 데이터 누적 저장
- **⚡ 최근 매치 실시간 리포트:** 
  - 최근 플레이한 경기(최대 20게임)의 매치 일시, 순위, 킬, 어시스트, 데미지 추적 및 표(Treeview) 출력
- **🧵 멀티 스레딩 기반 UI:** 데이터 로딩 중 프로그램이 먹통(응답 없음)이 되지 않도록 비동기 스레드 처리 적용

---

## 🛠️ 기술 스택 (Tech Stack)

- **Language:** Python 3.x
- **GUI Framework:** Tkinter, ttk
- **Data Handling:** Pandas, OpenPyXL
- **API & Networking:** Requests (PUBG Developer API)
- **Concurrency:** Threading

---

## 📂 프로젝트 구조 (Project Structure)

```text
├── pubg_tracker1.py      # 메인 멀티 닉네임 검색 트래커 (GUI 실행 파일)
├── api.py               # 단일 플레이어 전용 트래커 버전
├── name_code_check.py   # 닉네임 -> Account ID 변환 테스트 스크립트
├── requirements.txt     # 필요 라이브러리 목록
└── README.md            # 프로젝트 설명서
```

---

## 🚀 시작하기 (Getting Started)

### 1. 사전 준비 (Prerequisites)

이 프로그램을 실행하려면 **PUBG API Key**가 필요합니다.
1. [PUBG Developer Portal](https://developer.pubg.com/)에 접속하여 회원가입 및 로그인합니다.
2. 개인 **API Key**를 발급받습니다.

### 2. 라이브러리 설치

```bash
pip install requests pandas openpyxl
```

### 3. API 키 설정

`pubg_tracker1.py` 파일 상단의 `API_KEY` 변수에 본인의 발급받은 API 키를 입력합니다.

```python
# pubg_tracker1.py
API_KEY = "YOUR_PUBG_API_KEY_HERE"
```

### 4. 프로그램 실행

```bash
python pubg_tracker1.py
```

---

## 💡 사용 방법 (How to Use)

1. 프로그램 실행 후 상단 **"배그 인게임 닉네임"** 입력창에 검색할 유저의 정확한 닉네임을 입력합니다.
2. 원하는 **시즌**을 선택합니다.
3. **`시즌 전적 갱신`** 버튼 클릭:
   - 해당 시즌의 경쟁전 스탯을 불러오고 `pubg_{닉네임}_summary.xlsx`에 자동으로 기록됩니다.
4. **`최근 게임 실시간 조회`** 버튼 클릭:
   - 최근 진행한 매치들의 세부 결과(순위, KDA, 딜량)를 실시간으로 가져와 하단 표에 출력합니다.

---

## ⚠️ 주의사항 (Notes)

- **API Rate Limit (요청 제한):** PUBG Free Tier API는 **분당 10회**의 요청 제한이 있습니다. 연달아 조회 시 429 에러 메시지가 표시될 수 있으므로 잠시 후 다시 시도하세요.
- **보안 관련:** API 키가 포함된 코드를 GitHub Public 레포지토리에 올릴 경우, 키가 노출되어 무효화될 수 있으므로 커밋 전 API 키를 지우거나 환경변수(`.env`) 처리하는 것을 권장합니다.