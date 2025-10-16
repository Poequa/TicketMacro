import tkinter as tk
from tkinter import ttk
import threading, time, pyautogui, datetime, re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager


class NavyismClickerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Navyism Auto Clicker - Ticket Mode")
        self.root.geometry("440x520")
        self.root.resizable(False, False)
        self.root.configure(bg="#1E1E1E")

        font_main = ("굴림", 10)
        font_title = ("굴림", 13, "bold")

        # 타이틀
        tk.Label(root, text="🎫 네이비즘 초정밀 티켓팅 클릭기", font=font_title,
                 fg="white", bg="#1E1E1E").pack(pady=10)
        tk.Label(root, text="티켓 사이트를 선택하세요", font=font_main,
                 fg="#C0C0C0", bg="#1E1E1E").pack()

        # 도메인 맵
        self.domain_map = {
            "티켓링크": "www.ticketlink.co.kr",
            "인터파크": "ticket.interpark.com",
            "네이버": "naver.com",
            "멜론": "ticket.melon.com",
            "예스24": "ticket.yes24.com"
        }

        # 상단, 하단 버튼 구역
        frame_sites_top = tk.Frame(root, bg="#1E1E1E")
        frame_sites_bottom = tk.Frame(root, bg="#1E1E1E")
        frame_sites_top.pack(pady=(8, 3))
        frame_sites_bottom.pack(pady=(0, 8))

        # 상단 버튼 3개
        for name in ["티켓링크", "인터파크", "네이버"]:
            tk.Button(frame_sites_top, text=name, width=12, height=1,
                      command=lambda n=name: self.select_domain(n),
                      bg="#333333", fg="white", relief="flat",
                      font=("굴림", 10)).pack(side="left", padx=5)

        # 하단 버튼 2개
        for name in ["멜론", "예스24"]:
            tk.Button(frame_sites_bottom, text=name, width=12, height=1,
                      command=lambda n=name: self.select_domain(n),
                      bg="#333333", fg="white", relief="flat",
                      font=("굴림", 10)).pack(side="left", padx=5)

        # 선택 상태
        self.selected_label = tk.Label(root, text="선택된 사이트: 없음",
                                       fg="#AAAAAA", bg="#1E1E1E", font=("굴림", 11))
        self.selected_label.pack(pady=5)

        # 시간 선택
        frame_time = tk.Frame(root, bg="#1E1E1E")
        frame_time.pack(pady=5)
        hours = [f"{i:02d}" for i in range(24)]
        minutes = [f"{i:02d}" for i in range(60)]
        seconds = [f"{i:02d}" for i in range(60)]

        self.combo_h = ttk.Combobox(frame_time, values=hours, width=5, font=("굴림", 11),
                                    state="readonly", justify="center")
        self.combo_m = ttk.Combobox(frame_time, values=minutes, width=5, font=("굴림", 11),
                                    state="readonly", justify="center")
        self.combo_s = ttk.Combobox(frame_time, values=seconds, width=5, font=("굴림", 11),
                                    state="readonly", justify="center")

        self.combo_h.set("12"); self.combo_m.set("00"); self.combo_s.set("00")
        self.combo_h.grid(row=0, column=0, padx=5)
        tk.Label(frame_time, text="시", font=("굴림", 11), fg="white", bg="#1E1E1E").grid(row=0, column=1)
        self.combo_m.grid(row=0, column=2, padx=5)
        tk.Label(frame_time, text="분", font=("굴림", 11), fg="white", bg="#1E1E1E").grid(row=0, column=3)
        self.combo_s.grid(row=0, column=4, padx=5)
        tk.Label(frame_time, text="초", font=("굴림", 11), fg="white", bg="#1E1E1E").grid(row=0, column=5)

        # 실행 버튼
        btn_frame = tk.Frame(root, bg="#1E1E1E")
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="시작", command=self.start_clicker, width=10,
                  bg="#007ACC", fg="white", relief="flat", font=("굴림", 10)).grid(row=0, column=0, padx=8)
        tk.Button(btn_frame, text="종료", command=self.stop_clicker, width=10,
                  bg="#CC0000", fg="white", relief="flat", font=("굴림", 10)).grid(row=0, column=1, padx=8)

        # 3회 클릭 모드 버튼
        self.multi_click_mode = False
        self.multi_btn = tk.Button(root, text="3회 연속 클릭 모드 [OFF]",
                                   command=self.toggle_multi_click,
                                   width=25, bg="#444444", fg="white",
                                   relief="flat", font=("굴림", 10))
        self.multi_btn.pack(pady=(0, 10))

        # 티켓링크 전용 버튼 프레임
        self.coord_frame = tk.Frame(root, bg="#1E1E1E")

        # 서버시간 표시
        self.time_label = tk.Label(root, text="서버 시간: -", fg="#00FFFF",
                                   bg="#1E1E1E", font=("굴림", 11))
        self.time_label.pack(pady=5)

        # 상태 표시
        self.status_label = tk.Label(root, text="사이트 선택 후 서버시간 연동 중...",
                                     fg="#CCCCCC", bg="#1E1E1E", font=("굴림", 11))
        self.status_label.pack(pady=3)

        # 내부 상태
        self.running = False
        self.driver = None
        self.selected_domain = None
        self.selected_name = None
        self.coord1 = None
        self.coord2 = None

    # ───────────────────────────────
    def select_domain(self, name):
        self.selected_domain = self.domain_map[name]
        self.selected_name = name
        self.selected_label.config(text=f"선택된 사이트: {name} ({self.selected_domain})", fg="#00FFFF")

        # 티켓링크 전용 기능 추가
        for widget in self.coord_frame.winfo_children():
            widget.destroy()
        self.coord_frame.pack_forget()

        if name == "티켓링크":
            # 3회 클릭 모드 비활성화
            self.multi_btn.config(state="disabled", bg="#333333", fg="#777777")
            # 티켓링크 전용 버튼 추가
            self.coord_frame.pack(pady=5)
            tk.Button(self.coord_frame, text="좌표 1 설정", width=15, bg="#4444AA", fg="white",
                      relief="flat", font=("굴림", 10), command=self.set_coord1).pack(side="left", padx=10)
            tk.Button(self.coord_frame, text="좌표 2 설정", width=15, bg="#555555", fg="white",
                      relief="flat", font=("굴림", 10), command=self.set_coord2).pack(side="left", padx=10)
        else:
            # 다른 사이트일 경우 좌표 버튼 제거 & 3회 클릭 모드 복구
            self.multi_btn.config(state="normal", bg="#444444", fg="white")

        # 서버시간 연결
        self.status_label.config(text=f"{name} 서버시간 연동 중...")
        url = self.make_navyism_url(self.selected_domain)
        threading.Thread(target=self.show_server_time, args=(url,), daemon=True).start()

    # 좌표 설정 함수
    def set_coord1(self):
        self.status_label.config(text="📍 3초 후 마우스 위치 저장 (좌표 1)")
        threading.Thread(target=self.capture_coord, args=(1,), daemon=True).start()

    def set_coord2(self):
        self.status_label.config(text="📍 3초 후 마우스 위치 저장 (좌표 2)")
        threading.Thread(target=self.capture_coord, args=(2,), daemon=True).start()

    def capture_coord(self, num):
        time.sleep(3)
        x, y = pyautogui.position()
        if num == 1:
            self.coord1 = (x, y)
            self.status_label.config(text=f"✅ 좌표 1 저장 완료: {self.coord1}")
        else:
            self.coord2 = (x, y)
            self.status_label.config(text=f"✅ 좌표 2 저장 완료: {self.coord2}")

    def toggle_multi_click(self):
        if self.multi_btn['state'] == "disabled":
            return
        self.multi_click_mode = not self.multi_click_mode
        if self.multi_click_mode:
            self.multi_btn.config(text="3회 연속 클릭 모드 [ON]", bg="#00A86B")
            self.status_label.config(text="✅ 3회 연속 클릭 모드 활성화")
        else:
            self.multi_btn.config(text="3회 연속 클릭 모드 [OFF]", bg="#444444")
            self.status_label.config(text="⏹ 3회 연속 클릭 모드 비활성화")

    def make_navyism_url(self, domain):
        return f"https://time.navyism.com/?host={domain}"

    def show_server_time(self, url):
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--headless=new")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            driver.get(url)
            elem = None
            for _ in range(50):
                try:
                    elem = driver.find_element(By.ID, "time_area")
                    break
                except:
                    time.sleep(0.05)
            if elem:
                self.status_label.config(text="✅ 서버시간 연동 완료")
                while True:
                    text = elem.text.strip()
                    self.time_label.config(text=f"서버 시간: {text}")
                    time.sleep(0.2)
        except Exception as e:
            self.status_label.config(text=f"⚠ 서버시간 오류: {e}")

    # ───────────────────────────────
    def start_clicker(self):
        if self.running:
            return
        if not self.selected_domain:
            self.status_label.config(text="⚠ 먼저 사이트를 선택하세요.")
            return

        # 티켓링크 예외: 좌표 필수
        if self.selected_name == "티켓링크":
            if not self.coord1 or not self.coord2:
                self.status_label.config(text="⚠ 좌표 1, 2 모두 설정해주세요.")
                return

        self.running = True
        url = self.make_navyism_url(self.selected_domain)
        target_time = f"{int(self.combo_h.get())}시 {int(self.combo_m.get())}분 {int(self.combo_s.get())}초"
        self.status_label.config(text=f"{self.selected_name} 서버 감시 중...")
        threading.Thread(target=self.run_monitor, args=(url, target_time), daemon=True).start()

    # ───────────────────────────────
    def run_monitor(self, url, target_time):
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--headless=new")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            driver.get(url)
            elem = driver.find_element(By.ID, "time_area")

            target_sec = self.to_seconds(target_time)
            while self.running:
                text = elem.text.strip()
                self.time_label.config(text=f"서버 시간: {text}")
                now_sec = self.to_seconds(text)
                if now_sec >= target_sec and now_sec != 0:
                    # 티켓링크 전용 클릭
                    if self.selected_name == "티켓링크":
                        pyautogui.moveTo(self.coord1)
                        pyautogui.click()
                        time.sleep(0.05)
                        pyautogui.moveTo(self.coord2)
                        for _ in range(3):
                            pyautogui.click()
                            time.sleep(0.01)
                        self.status_label.config(text=f"⚡ 티켓링크 좌표 클릭 완료 ({target_time})")
                    else:
                        # 일반 모드
                        if self.multi_click_mode:
                            for _ in range(3):
                                pyautogui.click()
                                time.sleep(0.01)
                        else:
                            pyautogui.click()
                        self.status_label.config(text=f"✅ 클릭 완료 ({target_time})")
                    break
                time.sleep(0.005)
        except Exception as e:
            self.status_label.config(text=f"⚠ 오류: {e}")
        finally:
            self.running = False

    def stop_clicker(self):
        self.running = False
        self.status_label.config(text="⏹ 중지됨")

    def to_seconds(self, text):
        try:
            match = re.search(r"(\d{1,2})시\s*(\d{1,2})분\s*(\d{1,2})초", text)
            if not match:
                return 0
            h, m, s = map(int, match.groups())
            return h * 3600 + m * 60 + s
        except:
            return 0


# ───────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app = NavyismClickerApp(root)
    root.mainloop()
