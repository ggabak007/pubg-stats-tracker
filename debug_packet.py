import requests
import json

# ================= 설정 구역 =================
API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJqdGkiOiJiZjBiMjBjMC00M2UwLTAxM2YtZjM4MC0yNjA4ZjgwMTViOTQiLCJpc3MiOiJnYW1lbG9ja2VyIiwiaWF0IjoxNzgwNzU1NjA4LCJwdWIiOiJibHVlaG9sZSIsInRpdGxlIjoicHViZyIsImFwcCI6Ii1iNmM3ZjBlMy04NjlmLTQ3MTEtYjMxNC0zMTJjNzAyYWIyOTcifQ.2f-XPWLbZ5nMRVbg_SR4frNpTkJ-YQxTOBmM6Bnj24o"
SEARCH_NAME = "ggabak007_" # 확인하고 싶은 닉네임 입력
# ============================================

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/vnd.api+json"
}

def inspect_pubg_packet(nickname):
    print(f"\n================ [ 1단계: {nickname} 유저 검색 패킷 확인 ] ================")
    player_url = f"https://api.pubg.com/shards/steam/players?filter[playerNames]={nickname}"
    res = requests.get(player_url, headers=HEADERS)
    
    print(f"📌 응답 상태 코드: {res.status_code}")
    
    if res.status_code != 200:
        print("❌ 유저 정보를 가져오지 못했습니다. 에러 패킷:")
        print(res.text)
        return

    player_json = res.json()
    # 1. 서버에서 받은 원본 유저 데이터 통째로 출력
    print("\n📦 [서버에서 수신한 원본 유저 패킷 (JSON 데이터)]:")
    print(json.dumps(player_json, indent=4, ensure_ascii=False))

    # 2. 매치 ID 리스트 추출 검증
    try:
        data = player_json['data'][0]
        account_id = data['id']
        official_name = data['attributes']['name']
        matches = data['relationships']['matches']['data']
        
        print(f"\n✅ 계정 확인 성공!")
        print(f" - 대소문자 정규 닉네임: {official_name}")
        print(f" - 고유 Account ID: {account_id}")
        print(f" - 최근 매치 패킷 개수: 총 {len(matches)}개")
        
        if matches:
            print("\n📌 가장 최근 매치 고유 ID 3개 예시:")
            for idx, m in enumerate(matches[:3]):
                print(f"   [{idx+1}] {m['id']}")
                
            # 3. 최신 매치 1개의 상세 정보 패킷도 까보기
            first_match_id = matches[0]['id']
            print(f"\n================ [ 2단계: 최신 매치 ({first_match_id}) 상세 패킷 확인 ] ================")
            match_url = f"https://api.pubg.com/shards/steam/matches/{first_match_id}"
            m_res = requests.get(match_url, headers=HEADERS)
            
            if m_res.status_code == 200:
                m_json = m_res.json()
                attrs = m_json['data']['attributes']
                print(f"🎮 게임 모드(gameMode): {attrs.get('gameMode')}")
                print(f"⚔️ 매치 타입(matchType): {attrs.get('matchType')}") # official, competitive, custom 등
                print(f"🗺️ 맵 이름(mapName): {attrs.get('mapName')}")
                print(f"⏱️ 경기 일시: {attrs.get('createdAt')}")
                print("\n👉 이 2단계 패킷 안에 참여한 100명의 유저 스탯이 들어가 있습니다!")
            else:
                print(f"❌ 매치 상세 패킷 조회 실패 코드: {m_res.status_code}")

    except Exception as e:
        print(f"\n❌ 패킷 파싱 중 구조 오류 발생: {e}")

if __name__ == "__main__":
    inspect_pubg_packet(SEARCH_NAME)