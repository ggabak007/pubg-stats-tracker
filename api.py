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
API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJqdGkiOiJiZjBiMjBjMC00M2UwLTAxM2YtZjM4MC0yNjA4ZjgwMTViOTQiLCJpc3MiOiJnYW1lbG9ja2VyIiwiaWF0IjoxNzgwNzU1NjA4LCJwdWIiOiJibHVlaG9sZSIsInRpdGxlIjoicHViZyIsImFwcCI6Ii1iNmM3ZjBlMy04NjlmLTQMTEtYjMxNC0zMTJjNzAyYWIyOTcifQ.2f-XPWLbZ5nMRVbg_SR4frNpTkJ-YQxTOBmM6Bnj24o"
ACCOUNT_ID = "account.25a46d05e1f8489d8709d29755d590d2"
PLAYER_NAME = "BP2_GGABAK" # 매치 리포트 서칭을 위한 고유 닉네임 상수 지정
# =======================================================

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/vnd.api+json"
}

class PUBGTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("배틀그라운드 경쟁전 마스터 트래커")
        self.root.geometry("750x680") # 하단 리스트 뷰를 포함한 최적화 규격
        self.root.resizable(False, False)
        
        self.seasons_dict = {}
        self.init_ui()
        self.load_seasons()

    def init_ui(self):
        # 1. 상단 컨트롤 바
        top_frame = tk.Frame(self.root)
        top_frame.pack(fill="x", padx=20, pady=15)
        
        tk.Label(top_frame, text="시즌 선택:", font=("맑은 고딕", 11)).pack(side="left")
        
        self.season_combo = ttk.Combobox(top_frame, state="readonly", width=22, font=("맑은 고딕", 10))
        self.season_combo.pack(side="left", padx=10)
        self.season_combo.bind("<<ComboboxSelected>>", self.on_season_selected)
        
        # 버튼 컨트롤러 배치
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
        
        # 2. 메인 전적 요약 대시보드
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

        # 3. 하단 최근 매치 기록 리스트 뷰
        self.list_title_frame = tk.LabelFrame(self.root, text=" 최근 게임 실시간 기록 (저장 안 됨) ", font=("맑은 고딕", 11, "bold"), padx=10, pady=10)
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
        selected_name = self.season_combo.get()
        season_id = self.get_season_id_by_name(selected_name)
        
        if os.path.exists("pubg_season_summary.xlsx"):
            try:
                df = pd.read_excel("pubg_season_summary.xlsx")
                row = df[df['시즌ID'] == season_id]
                if not row.empty:
                    r = row.iloc[0]
                    self.labels["현재 점수 (RP)"].config(text=f"{r['티어']} ({r['현재RP']} RP)")
                    self.labels["최고 점수 (RP)"].config(text=f"{r['최고RP']} RP")
                    self.labels["시즌 K/D/A"].config(text=str(r['KDA']))
                    self.labels["시즌 K/D"].config(text=str(r.get('KD', '-')))
                    self.labels["시즌 전체 판수"].config(text=f"{r.get('총판수', 0)}판")
                    self.labels["시즌 평균 딜량"].config(text=str(r['평균딜량']))
                    self.labels["1등(치킨) 횟수"].config(text=f"{r.get('치킨횟수', 0)}회")
                    self.labels["치킨 확률 (승률)"].config(text=f"{r.get('치킨확률', 0.0)}%")
                    self.labels["평균 순위"].config(text=f"#{r.get('평균순위', 0.0)}" if isinstance(r.get('평균순위'), (int, float)) else str(r.get('평균순위', '-')))
                    return
            except Exception:
                pass
        self.clear_summary_display()

    def clear_summary_display(self):
        for key in self.labels:
            self.labels[key].config(text="-")

    def refresh_season_stats(self):
        selected_name = self.season_combo.get()
        season_id = self.get_season_id_by_name(selected_name)
        if not season_id: return
        
        self.root.config(cursor="watch")
        url = f"https://api.pubg.com/shards/steam/players/{ACCOUNT_ID}/seasons/{season_id}/ranked"
        
        try:
            res = requests.get(url, headers=HEADERS)
            if res.status_code == 200:
                data = res.json()['data']['attributes']['rankedGameModeStats']
                mode = 'squad' if 'squad' in data else ('squad-fpp' if 'squad-fpp' in data else None)
                
                if mode and data[mode]['roundsPlayed'] > 0:
                    stats = data[mode]
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
                        if avg_rank == 0.0:
                            avg_rank = "데이터 없음"
                    
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
                    self.labels["평균 순위"].config(text=f"#{avg_rank}" if isinstance(avg_rank, (int, float)) else avg_rank)
                    
                    summary_file = "pubg_season_summary.xlsx"
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
                    messagebox.showinfo("성공", f"[{selected_name}] 전적 수집 및 엑셀 저장 완료!")
                else:
                    messagebox.showwarning("알림", "해당 시즌 경쟁전 기록이 없습니다.")
            elif res.status_code == 429:
                messagebox.showerror("제한", "API 요청 제한(1분 10회)에 걸렸습니다. 1분만 기다려주세요!")
            else:
                messagebox.showerror("오류", f"에러 발생 (코드: {res.status_code})")
        except Exception as e:
            messagebox.showerror("오류", traceback.format_exc())
        finally:
            self.root.config(cursor="")

    def start_recent_matches_thread(self):
        self.recent_btn.config(state="disabled", text="조회 중...")
        self.list_title_frame.config(text=" 최근 게임 조회 중... 최신 판부터 순서대로 표에 추가됩니다. ")
        
        t = threading.Thread(target=self.fetch_recent_matches_live)
        t.daemon = True
        t.start()

    def fetch_recent_matches_live(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        player_url = f"https://api.pubg.com/shards/steam/players/{ACCOUNT_ID}"
        
        try:
            res = requests.get(player_url, headers=HEADERS)
            if res.status_code != 200:
                if res.status_code == 429: messagebox.showerror("제한", "1분 제한에 걸렸습니다. 잠시 후 시도하세요.")
                else: messagebox.showerror("오류", f"플레이어 조회 실패: {res.status_code}")
                return
            
            relationships = res.json()['data']['relationships']
            matches_list = relationships.get('matches', {}).get('data', [])
            
            if not matches_list:
                messagebox.showinfo("알림", "최근 플레이한 매치 기록이 없습니다.")
                return
            
            match_ids = [m['id'] for m in matches_list]
            match_ids.reverse() # 실시간 리포트를 위해 최신 판 역순 정렬
            
            parsed_count = 0
            for m_id in match_ids:
                if parsed_count >= 10: # 분당 요청수 보호 제한장치
                    break
                    
                match_url = f"https://api.pubg.com/shards/steam/matches/{m_id}"
                m_res = requests.get(match_url, headers=HEADERS)
                
                if m_res.status_code == 200:
                    m_json = m_res.json()
                    included = m_json.get('included', [])
                    
                    m_time_raw = m_json['data']['attributes']['createdAt']
                    dt = datetime.strptime(m_time_raw, "%Y-%m-%dT%H:%M:%SZ")
                    m_time_str = dt.strftime("%Y-%m-%d %H:%M")
                    
                    player_stats = None
                    roster_id = None
                    
                    for item in included:
                        # 🎯 [KeyError 유발 원인 철저 방어] relationships 딕셔너리가 유실된 조각은 즉시 우회 차단합니다.
                        if 'relationships' not in item:
                            continue
                            
                        if item.get('type') == 'participant':
                            attrs = item.get('attributes', {})
                            p_name = attrs.get('stats', {}).get('name', '')
                            p_id = attrs.get('stats', {}).get('playerId', '')
                            
                            # 닉네임 유연 검색과 소문자 ID 검색을 결합하여 완벽하게 본인 스탯 세트를 조준 패칭합니다.
                            if p_name.lower() == PLAYER_NAME.lower() or p_id.lower() == ACCOUNT_ID.lower():
                                player_stats = attrs.get('stats', {})
                                rels = item.get('relationships', {})
                                roster_id = rels.get('roster', {}).get('data', {}).get('id')
                                break
                    
                    if player_stats and roster_id:
                        rank = 99
                        for item in included:
                            if item.get('type') == 'roster' and item.get('id') == roster_id:
                                rank = item.get('attributes', {}).get('stats', {}).get('rank', 99)
                                break
                        
                        # 표에 데이터 줄바꿈 및 순차 업데이트 출력
                        self.tree.insert("", "end", values=(
                            m_time_str, 
                            f"#{rank}", 
                            player_stats.get('kills', 0), 
                            player_stats.get('assists', 0), 
                            round(player_stats.get('damageDealt', 0)), 
                            m_id
                        ))
                        parsed_count += 1
                        time.sleep(0.05)
                elif m_res.status_code == 429:
                    break
            
            if parsed_count == 0:
                messagebox.showinfo("안내", "최근 플레이한 10경기의 데이터 팩 세트 매칭에 실패했습니다.\n닉네임 정보가 일치하는지 확인해 주세요.")
            
        except Exception:
            messagebox.showerror("오류", traceback.format_exc())
        finally:
            self.reset_recent_btn()

    def reset_recent_btn(self):
        self.recent_btn.config(state="normal", text="최근 게임 실시간 조회")
        self.list_title_frame.config(text=" 최근 게임 실시간 기록 (저장 안 됨) ")

if __name__ == "__main__":
    root = tk.Tk()
    app = PUBGTrackerApp(root)
    root.mainloop()