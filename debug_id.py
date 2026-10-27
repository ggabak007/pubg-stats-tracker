import requests
import json

# ================= 설정 구역 =================
API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJqdGkiOiJiZjBiMjBjMC00M2UwLTAxM2YtZjM4MC0yNjA4ZjgwMTViOTQiLCJpc3MiOiJnYW1lbG9ja2VyIiwiaWF0IjoxNzgwNzU1NjA4LCJwdWIiOiJibHVlaG9sZSIsInRpdGxlIjoicHViZyIsImFwcCI6Ii1iNmM3ZjBlMy04NjlmLTQ3MTEtYjMxNC0zMTJjNzAyYWIyOTcifQ.2f-XPWLbZ5nMRVbg_SR4frNpTkJ-YQxTOBmM6Bnj24o"
MATCH_ID = "fded196d-f443-41a3-8125-0a060dcb0fcf" # 요청하신 매치 ID
TARGET_NAME = "ggabak007_"
TARGET_ACCOUNT_ID = "account.25a46d05e1f8489d8709d29755d590d2"
# ============================================

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/vnd.api+json"
}

def test_match():
    url = f"https://api.pubg.com/shards/steam/matches/{MATCH_ID}"
    print(f"📡 매치 ID ({MATCH_ID}) 패킷을 서버에 요청 중...")
    res = requests.get(url, headers=HEADERS)
    
    print(f"📌 응답 상태 코드: {res.status_code}")
    if res.status_code != 200:
        print(f"❌ 매치 데이터를 가져오지 못했습니다: {res.text}")
        return

    m_json = res.json()
    included = m_json.get('included', [])
    print(f"📦 패킷 내 총 included 조각 개수: {len(included)}개\n")

    found_participant = None
    roster_id = None

    # 1. participant 조각에서 Target 검색
    for item in included:
        if item.get('type') == 'participant':
            stats = item.get('attributes', {}).get('stats', {})
            p_name = stats.get('name', '')
            p_id = stats.get('playerId', '')
            
            # 대소문자 무시 검색
            if (p_name and p_name.strip().lower() == TARGET_NAME.lower()) or (p_id and p_id == TARGET_ACCOUNT_ID):
                found_participant = item
                roster_id = item.get('relationships', {}).get('roster', {}).get('data', {}).get('id')
                break

    if not found_participant:
        print(f"❌ [{TARGET_NAME}] 유저를 participant 패킷에서 찾지 못했습니다!")
        print("💡 participant 에 들어있는 대표 유저 닉네임 예시 5개:")
        count = 0
        for item in included:
            if item.get('type') == 'participant':
                name = item.get('attributes', {}).get('stats', {})