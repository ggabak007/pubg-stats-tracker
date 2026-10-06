import requests

# 1. 여기에 본인의 정보 입력
API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJqdGkiOiJiZjBiMjBjMC00M2UwLTAxM2YtZjM4MC0yNjA4ZjgwMTViOTQiLCJpc3MiOiJnYW1lbG9ja2VyIiwiaWF0IjoxNzgwNzU1NjA4LCJwdWIiOiJibHVlaG9sZSIsInRpdGxlIjoicHViZyIsImFwcCI6Ii1iNmM3ZjBlMy04NjlmLTQ3MTEtYjMxNC0zMTJjNzAyYWIyOTcifQ.2f-XPWLbZ5nMRVbg_SR4frNpTkJ-YQxTOBmM6Bnj24o"
PLAYER_NAME = "BP2_GGABAK" 

# 2. PUBG API 요청 설정
url = f"https://api.pubg.com/shards/steam/players?filter[playerNames]={PLAYER_NAME}"
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/vnd.api+json"
}

# 3. 서버에 요청 및 결과 출력
response = requests.get(url, headers=headers)

if response.status_code == 200:
    player_data = response.json()
    account_id = player_data['data'][0]['id']
    print("\n" + "="*40)
    print(f"🎉 인증 성공! [{PLAYER_NAME}] 님의 고유 ID를 찾았습니다.")
    print(f"고유 ID: {account_id}")
    print("="*40 + "\n")
    print("이 고유 ID를 따로 복사해 두세요! 엑셀 저장 프로그램에 사용됩니다.")
else:
    print(f"❌ 에러 발생 (코드: {response.status_code})")
    print("API 키가 올바른지, 혹은 닉네임 대소문자가 맞는지 확인해 주세요.")
    print(response.text)