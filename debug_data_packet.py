import requests
import json

# ================= 설정 구역 =================
API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJqdGkiOiJiZjBiMjBjMC00M2UwLTAxM2YtZjM4MC0yNjA4ZjgwMTViOTQiLCJpc3MiOiJnYW1lbG9ja2VyIiwiaWF0IjoxNzgwNzU1NjA4LCJwdWIiOiJibHVlaG9sZSIsInRpdGxlIjoicHViZyIsImFwcCI6Ii1iNmM3ZjBlMy04NjlmLTQ3MTEtYjMxNC0zMTJjNzAyYWIyOTcifQ.2f-XPWLbZ5nMRVbg_SR4frNpTkJ-YQxTOBmM6Bnj24o"
TARGET_NAME = "ggabak007_"
ACCOUNT_ID = "account.25a46d05e1f8489d8709d29755d590d2"
# ============================================

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/vnd.api+json"
}

def get_recent_6_matches():
    # 1. 플레이어의 최근 매치 ID 목록 가져오기
    player_url = f"https://api.pubg.com/shards/steam/players/{ACCOUNT_ID}"
    res = requests.get(player_url, headers=HEADERS)
    
    if res.status_code != 200:
        print(f"❌ 유저 매치 목록 조회 실패: {res.status_code}")
        return

    matches = res.json()['data']['relationships']['matches']['data']
    match_ids = [m['id'] for m in matches] # 최근 매치 ID 추출
    
    print(f"📡 총 {len(match_ids)}개의 매치 중 최근 6경기를 분석합니다...\n", flush=True)

    # 🎯 10개 게임 결과를 담을 구조 (리스트 및 중복 확인용 set)
    games_collection = []
    unique_match_ids = set() # 중복 체크용 집합(set)

    # 2. for문을 돌면서 최근 10경기 추출
    for m_id in match_ids:
        if m_id in unique_match_ids:
            continue
        if len(games_collection) >= 10:
            break

        match_url = f"https://api.pubg.com/shards/steam/matches/{m_id}"
        m_res = requests.get(match_url, headers=HEADERS)
        
        if m_res.status_code == 200:
            m_json = m_res.json()
            included = m_json.get('included', [])
            
            # 경기 일시
            created_at = m_json['data']['attributes'].get('createdAt', '')
            
            p_stats = None
            roster_id = None
            
            # participant 내 내 닉네임 찾기
            for item in included:
                if item.get('type') == 'participant':
                    stats = item.get('attributes', {}).get('stats', {})
                    if stats.get('name', '').strip().lower() == TARGET_NAME.lower():
                        p_stats = stats
                        roster_id = item.get('relationships', {}).get('roster', {}).get('data', {}).get('id')
                        break
            
            # roster 내 팀 순위 찾기
            rank = "알수없음"
            if roster_id:
                for item in included:
                    if item.get('type') == 'roster' and item.get('id') == roster_id:
                        rank = item.get('attributes', {}).get('stats', {}).get('rank', '알수없음')
                        break
            
            if p_stats:
                # 🎯 1개 매치의 핵심 데이터를 딕셔너리로 묶어서 집합/리스트에 추가
                game_data = {
                    "매치ID": m_id,
                    "순위": f"#{rank}",
                    "킬": p_stats.get('kills', 0),
                    "어시스트": p_stats.get('assists', 0),
                    "딜량": round(p_stats.get('damageDealt', 0), 1),
                    "생존시간": f"{int(p_stats.get('timeSurvived', 0) // 60)}분",
                    "이동거리": f"{round(p_stats.get('walkDistance', 0) + p_stats.get('rideDistance', 0))}m"
                }
                
                games_collection.append(game_data)
                unique_match_ids.add(m_id) # set에 추가
                print(f"✅ [{len(games_collection)}/6] {m_id[:8]}... 매치 파싱 완료")

    # 3. 완성된 6게임 데이터 출력
    print("\n================ [ 최종 6게임 데이터 집합 ] ================")
    print(json.dumps(games_collection, indent=4, ensure_ascii=False))
    print("===========================================================")

if __name__ == "__main__":
    get_recent_6_matches()