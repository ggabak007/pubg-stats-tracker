import tkinter as tk
from tkinter import ttk, messagebox
import requests
import pandas as pd
from datetime import datetime
import os
import traceback
import time
import threading

# ================= [ 사용자 설정 정보 ] =================
API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJqdGkiOiJiZjBiMjBjMC00M2UwLTAxM2YtZjM4MC0yNjA4ZjgwMTViOTQiLCJpc3MiOiJnYW1lbG9ja2VyIiwiaWF0IjoxNzgwNzU1NjA4LCJwdWIiOiJibHVlaG9sZSIsInRpdGxlIjoicHViZyIsImFwcCI6Ii1iNmM3ZjBlMy04NjlmLTQ3MTEtYjMxNC0zMTJjNzAyYWIyOTcifQ.2f-XPWLbZ5nMRVbg_SR4frNpTkJ-YQxTOBmM6Bnj24o"
# =======================================================

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/vnd.api+json"
}

class PUBGTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("배틀그라운드 경쟁전 멀티 닉네임 검색 트래커")
        self.root.geometry("750x720")
        self.root.resizable(False, False)
        
        self.seasons_dict = {}
        self.current_account_id = None
        self.current_player_name = None
        
        self.init_ui()
        self.load_seasons()

    def init_ui(self):
        # 1. 최상단 닉네임 검색 바
        search_frame = tk.Frame(self.root)
        search_frame.pack(fill="x", padx=20, pady=12)
        
        tk.Label(search_frame, text="배그 인게임 닉네임:", font=("맑은 고딕", 11, "bold"), fg="#2c3e50").pack(side="left")
        self.name_entry = tk.Entry(search_frame, font=("맑은 고딕", 11), width=20)
        self.name_entry.pack(side="left", padx=10)
        self.name_entry.insert(0, "ggabak007_") # 디버깅에서 확인된 실제 정확한 닉네임 세팅
        
        # 2. 시즌 선택 및 컨트롤 바
        top_frame = tk.Frame(self.root)
        top_frame.pack(fill="x", padx=20, pady=5)
        
        tk.Label(top_frame, text="시즌 선택:", font=("맑은 고딕", 11)).pack(side="left")
        
        self.season_combo = ttk.Combobox(top_frame, state="readonly", width=22, font=("맑은 고딕", 10))
        self.season_combo.pack(side="left", padx=10)
        self.season_combo.bind("<<ComboboxSelected>>", self.on_season_selected)
        
        btn_frame = tk.Frame(top_frame)
        btn_frame.pack(side="right")
        
        self.refresh_btn = tk.Button(btn_frame, text="시즌 전적 갱신", bg="#2ecc71", fg="white", 
                                font=("맑은 고딕", 10, "bold"), command=self.refresh_season_stats, padx=8)
        self.refresh_btn.pack(side="left", padx=5)
        
        self.recent_btn = tk.Button(btn_frame, text="최근 게임 실시간 조회", bg="#3498db", fg="white", 
                                font=("맑은 고딕", 10, "bold"), command=self.start_recent_matches_thread, padx=8)
        self.recent_btn.pack(side="left", padx=5)
        
        # 구분선
        lbl_line = tk.Label(self.root, text="-"*110, fg="gray")
        lbl_line.pack()
        
        # 3. 메인 전적 요약 대시보드
        self.main_frame = tk.LabelFrame(self.root, text=" 시즌 경쟁전 대시보드 (엑셀 자동저장) ", font=("맑은 고딕", 12, "bold"), padx=15, pady=15)
        self.main_frame.pack(fill="x", padx=20, pady=10)
        
        self.labels = {}
        stats_items = [
            ("현재 점수 (RP)", 0, 0), ("최고 점수 (RP)", 0, 2),
            ("시즌 K/D/A", 1, 0), ("시즌 K/D", 1, 2),
            ("시즌 전체 판수", 2, 0), ("시즌 평균 딜량", 2, 2),
            ("1등(치킨) 횟수", 3, 0), ("치킨 확률 (승률)", 3, 2),
            ("평균 순위", 4, 0)
        ]
        
        for key, row, col in stats_items:
            tk.Label(self.main_frame, text=key, font=("맑은 고딕", 10, "bold"), fg="#34495e").grid(row=row, column=col, sticky="w", padx=15, pady=6)
            lbl_val = tk.Label(self.main_frame, text="-", font=("맑은 고딕", 11, "bold"), fg="#2c3e50")
            lbl_val.grid(row=row, column=col+1, sticky="w", padx=15, pady=6)
            self.labels[key] = lbl_val

        # 4. 하단 최근 매치 기록 리스트 뷰
        self.list_title_frame = tk.LabelFrame(self.root, text=" 최근 경쟁전 실시간 기록 ", font=("맑은 고딕", 11, "bold"), padx=10, pady=10)
        self.list_title_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        columns = ("매치일시", "순위", "킬", "어시스트", "데미지", "매치ID")
        self.tree = ttk.Treeview(self.list_title_frame, columns=columns, show="headings", height=10)
        self.tree.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(self.list_title_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        widths = {"매치일시": 130, "순위": 60, "킬": 50, "어시스트": 60, "데미지": 70, "매치ID": 250}
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=widths[col], anchor="center")

    def get_account_id_by_name(self, player_name):
        url = f"https://api.pubg.com/shards/steam/players?filter[playerNames]={player_name.strip()}"
        try:
            res = requests.get(url, headers=HEADERS)
            if res.status_code == 200:
                data = res.json().get('data', [])
                if data:
                    self.current_account_id = data[0]['id']
                    self.current_player_name = data[0]['attributes']['name']
                    return True
            elif res.status_code == 404:
                messagebox.showerror("검색 실패", "해당 닉네임의 유저를 찾을 수 없습니다.\n대소문자를 확인해 주세요.")
                return False
        except Exception as e:
            messagebox.showerror("오류", f"유저 조회 실패: {e}")
        return False

    def load_seasons(self):
        url = "https://api.pubg.com/shards/steam/seasons"
        try:
            res = requests.get(url, headers=HEADERS)
            if res.status_code == 200:
                seasons_data = res.json().get('data', [])
                self.seasons_dict = {}
                for s in seasons_data:
                    attrs = s.get('attributes', {})
                    s_id = s.get('id', '')
                    if s_id and "pc-" in s_id and not attrs.get('isOffseason', False):
                        season_num = s_id.split('-')[-1]
                        self.seasons_dict[s_id] = f"시즌 {season_num}"
                
                sorted_seasons = sorted(list(self.seasons_dict.items()), 
                                        key=lambda x: int(x[1].split(' ')[1]) if x[1].split(' ')[1].isdigit() else 0, 
                                        reverse=True)
                self.season_combo['values'] = [v for k, v in sorted_seasons]
                self.season_combo.current(0)
                self.on_season_selected(None)
        except Exception as e:
            messagebox.showerror("오류", f"시즌 로드 실패:\n{e}")

    def get_season_id_by_name(self, name):
        for k, v in self.seasons_dict.items():
            if v == name: return k
        return None

    def on_season_selected(self, event):
        self.clear_summary_display()

    def clear_summary_display(self):
        for key in self.labels:
            self.labels[key].config(text="-")

    def refresh_season_stats(self):
        input_name = self.name_entry.get().strip()
        if not input_name:
            messagebox.showwarning("경고", "검색할 유저의 닉네임을 입력해 주세요.")
            return

        selected_name = self.season_combo.get()
        season_id = self.get_season_id_by_name(selected_name)
        if not season_id: return
        
        self.root.config(cursor="watch")
        
        if not self.get_account_id_by_name(input_name):
            self.root.config(cursor="")
            return
            
        url = f"https://api.pubg.com/shards/steam/players/{self.current_account_id}/seasons/{season_id}/ranked"
        
        try:
            res = requests.get(url, headers=HEADERS)
            if res.status_code == 200:
                data = res.json().get('data', {}).get('attributes', {}).get('rankedGameModeStats', {})
                
                # 가장 판수가 많은 경쟁전 모드 선택
                target_mode = None
                max_rounds = 0
                for mode_key, mode_data in data.items():
                    rounds = mode_data.get('roundsPlayed', 0)
                    if rounds > max_rounds:
                        max_rounds = rounds
                        target_mode = mode_key
                
                if target_mode and max_rounds > 0:
                    stats = data[target_mode]
                    games = stats['roundsPlayed']
                    deaths = stats['deaths'] if stats['deaths'] > 0 else 1
                    
                    kda = round((stats['kills'] + stats['assists']) / deaths, 2)
                    kd = round(stats['kills'] / deaths, 2)
                    avg_dmg = round(stats['damageDealt'] / games, 1)
                    wins = stats.get('wins', 0)
                    win_ratio = round((wins / games) * 100, 1)
                    
                    if 'rankSum' in stats and stats['rankSum'] > 0:
                        avg_rank = round(stats['rankSum'] / games, 1)
                    else:
                        avg_rank = round(stats.get('avgRank', 0.0), 1)
                    
                    ct = stats.get('currentTier', {})
                    tier_str = f"{ct.get('tier', 'Unranked')} {ct.get('subTier', '')}".strip()
                    current_rp = stats.get('currentRankPoint', 0)
                    best_rp = stats.get('bestRankPoint', 0)
                    
                    self.labels["현재 점수 (RP)"].config(text=f"{tier_str} ({current_rp} RP)")
                    self.labels["최고 점수 (RP)"].config(text=f"{best_rp} RP")
                    self.labels["시즌 K/D/A"].config(text=str(kda))
                    self.labels["시즌 K/D"].config(text=str(kd))
                    self.labels["시즌 전체 판수"].config(text=f"{games}판")
                    self.labels["시즌 평균 딜량"].config(text=str(avg_dmg))
                    self.labels["1등(치킨) 횟수"].config(text=f"{wins}회")
                    self.labels["치킨 확률 (승률)"].config(text=f"{win_ratio}%")
                    self.labels["평균 순위"].config(text=f"#{avg_rank}")
                    
                    summary_file = f"pubg_{self.current_player_name}_summary.xlsx"
                    new_sum = {
                        "시즌": selected_name, "시즌ID": season_id, "티어": tier_str, 
                        "현재RP": current_rp, "최고RP": best_rp, "KDA": kda, "KD": kd, 
                        "총판수": games, "평균딜량": avg_dmg, "치킨횟수": wins, "치킨확률": win_ratio, "평균순위": avg_rank
                    }
                    
                    if os.path.exists(summary_file):
                        try:
                            df = pd.read_excel(summary_file)
                            df = df[df['시즌ID'] != season_id]
                            df = pd.concat([df, pd.DataFrame([new_sum])], ignore_index=True)
                        except Exception:
                            df = pd.DataFrame([new_sum])
                    else:
                        df = pd.DataFrame([new_sum])
                        
                    df.to_excel(summary_file, index=False)
                    messagebox.showinfo("성공", f"[{self.current_player_name}] 님의 전적 수집 및 엑셀 저장 완료!")
                else:
                    messagebox.showwarning("알림", "선택한 시즌에 경쟁전 플레이 기록이 없습니다.")
            elif res.status_code == 429:
                messagebox.showerror("제한", "API 요청 제한(1분 10회)에 걸렸습니다.")
            else:
                messagebox.showerror("오류", f"에러 발생 (코드: {res.status_code})")
        except Exception as e:
            messagebox.showerror("오류", traceback.format_exc())
        finally:
            self.root.config(cursor="")

    def start_recent_matches_thread(self):
        input_name = self.name_entry.get().strip()
        if not input_name:
            messagebox.showwarning("경고", "검색할 유저의 닉네임을 입력해 주세요.")
            return
            
        self.recent_btn.config(state="disabled", text="조회 중...⏳")
        self.list_title_frame.config(text=f" [{input_name}] 님의 최근 경쟁전 매치 탐색 중... ")
        
        t = threading.Thread(target=self.fetch_recent_matches_live, args=(input_name,))
        t.daemon = True
        t.start()

    def fetch_recent_matches_live(self, player_name):
        # 1. 기존 표 내용 초기화
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # 닉네임 기반 고유 ID 동적 조회
        if not self.get_account_id_by_name(player_name):
            self.reset_recent_btn()
            return
            
        player_url = f"https://api.pubg.com/shards/steam/players/{self.current_account_id}"
        
        try:
            res = requests.get(player_url, headers=HEADERS)
            if res.status_code != 200:
                if res.status_code == 429: messagebox.showerror("제한", "1분 API 제한에 걸렸습니다. 잠시 후 다시 시도하세요.")
                else: messagebox.showerror("오류", f"플레이어 매치 목록 조회 실패: {res.status_code}")
                return
            
            relationships = res.json()['data']['relationships']
            matches_list = relationships.get('matches', {}).get('data', [])
            
            if not matches_list:
                messagebox.showinfo("알림", "최근 플레이한 매치 기록이 전혀 없습니다.")
                return
            
            match_ids = [m['id'] for m in matches_list]
            
            parsed_count = 0
            # 🎯 최근 매치 중 6경기를 타겟으로 가져옵니다.
            for m_id in match_ids: 
                if parsed_count >= 6:
                    break
                    
                match_url = f"https://api.pubg.com/shards/steam/matches/{m_id}"
                m_res = requests.get(match_url, headers=HEADERS)
                
                # API 연타(429) 예외 처리 및 대기
                if m_res.status_code == 429:
                    time.sleep(2)
                    m_res = requests.get(match_url, headers=HEADERS)
                
                if m_res.status_code == 200:
                    m_json = m_res.json()
                    included = m_json.get('included', [])
                    
                    # 경기 생성 일시 파싱
                    m_time_raw = m_json['data']['attributes']['createdAt']
                    dt = datetime.strptime(m_time_raw, "%Y-%m-%dT%H:%M:%SZ")
                    m_time_str = dt.strftime("%Y-%m-%d %H:%M")
                    
                    player_stats = None
                    roster_id = None
                    
                    # 🎯 participant 패킷에서 내 닉네임(or Account ID) 매칭
                    for item in included:
                        if item.get('type') == 'participant':
                            attrs = item.get('attributes', {})
                            p_stats = attrs.get('stats', {})
                            p_name = p_stats.get('name', '')
                            p_id = p_stats.get('playerId', '')
                            
                            if (p_name and p_name.strip().lower() == self.current_player_name.strip().lower()) or \
                               (p_id and p_id == self.current_account_id):
                                player_stats = p_stats
                                rels = item.get('relationships', {})
                                roster_id = rels.get('roster', {}).get('data', {}).get('id')
                                break
                    
                    # 🎯 roster 패킷에서 팀 최종 순위 매칭
                    if player_stats and roster_id:
                        rank = 99
                        for item in included:
                            if item.get('type') == 'roster' and item.get('id') == roster_id:
                                rank = item.get('attributes', {}).get('stats', {}).get('rank', 99)
                                break
                        
                        # Tkinter 하단 Treeview 표에 실시간 한 줄씩 데이터 삽입!
                        self.tree.insert("", "end", values=(
                            m_time_str, 
                            f"#{rank}", 
                            player_stats.get('kills', 0), 
                            player_stats.get('assists', 0), 
                            round(player_stats.get('damageDealt', 0), 1), 
                            m_id
                        ))
                        parsed_count += 1
                        
                    time.sleep(0.15) # API 요청 안정화 딜레이
                elif m_res.status_code == 429:
                    break
            
            if parsed_count == 0:
                messagebox.showinfo("안내", "최근 매치 데이터를 가져오지 못했습니다.")
                
        except Exception:
            messagebox.showerror("오류", traceback.format_exc())
        finally:
            self.reset_recent_btn()

    def reset_recent_btn(self):
        self.recent_btn.config(state="normal", text="최근 게임 실시간 조회")
        self.list_title_frame.config(text=" 최근 경쟁전 실시간 기록 ")

if __name__ == "__main__":
    root = tk.Tk()
    app = PUBGTrackerApp(root)
    root.mainloop()