import subprocess
import sys
import os

def install_requirements():
    # exe로 실행 중이면 스킵
    if getattr(sys, 'frozen', False):
        return
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        pass

install_requirements()

import tkinter as tk
import tkinter.font as tkfont
import customtkinter as ctk
import threading
import requests
import time
import ctypes
import shutil

if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def _get_python():
    if getattr(sys, 'frozen', False):
        return shutil.which("python") or shutil.which("python3") or "python"
    return sys.executable

from PIL import Image, ImageTk
from customtkinter import CTkImage

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

try:
    from app.init_db import init_db
    init_db()
except Exception:
    pass

class GitReviewerGUI:
    def __init__(self, root):
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("GitReviewer")
        self.root = root
        self.root.title("GitReviewer")
        self.root.iconbitmap(os.path.join(BASE_DIR, "assets", "icon.ico"))
        self.root.geometry("240x360")
        self.root.resizable(False, False)

        self.processes = {}
        self.ngrok_url = None

        self._check_ngrok()
        self._build_ui()

    def _check_ngrok(self):
        """ngrok 설치 및 인증 토큰 확인"""
        if not shutil.which("ngrok"):
            tk.messagebox.showwarning("ngrok 미설치",
                "ngrok이 설치되어 있지 않습니다.\nhttps://ngrok.com 에서 설치해주세요.")
            return
        result = subprocess.run(["ngrok", "config", "check"],
                                capture_output=True, text=True)
        if result.returncode != 0:
            dialog = ctk.CTkInputDialog(
                text="ngrok 인증 토큰을 입력하세요:",
                title="ngrok 설정")
            token = dialog.get_input()
            if token and token.strip():
                subprocess.run(["ngrok", "config", "add-authtoken", token.strip()])

    def _start_redis(self):
        docker_check = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=5
        )
        
        if docker_check.returncode == 0:
            self.processes["Redis"] = subprocess.Popen(
                ["docker", "run", "--rm", "-p", "6379:6379", "redis:7-alpine"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return True

        # Docker 없으면 WSL 시도
        wsl_check = subprocess.run(["wsl", "--status"], capture_output=True)
        if wsl_check.returncode == 0:
            self.processes["Redis"] = subprocess.Popen(
                ["wsl", "sudo", "service", "redis-server", "start"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return True

        # 둘 다 없으면 경고
        self.root.after(0, lambda: tk.messagebox.showerror(
            "오류",
            "Redis를 실행할 수 없습니다.\nDocker Desktop 또는 WSL2를 설치해주세요."
        ))
        self.root.after(0, lambda: self.show_btn.configure(
            text="시작",
            fg_color="#0969da",
            hover_color="#0860ca"
        ))

        return False

    def _tint_icon(self, path, color=(128, 128, 128)):
        img = Image.open(path).convert("RGBA")
        r, g, b, a = img.split()
        colored = Image.new("RGBA", img.size, (*color, 255))
        colored.putalpha(a)
        return colored

    def _build_ui(self):
        # 타이틀
        ctk.CTkLabel(self.root, text="GitReviewer",
            font=("맑은 고딕", 22, "bold")).pack(pady=(20, 2))
        ctk.CTkLabel(self.root, text="v0.8.1",
            font=("맑은 고딕", 12), text_color="gray").pack()

        # 아이콘 로드
        img_normal = self._tint_icon(os.path.join(BASE_DIR, "assets", "settings.png"), color=(128, 128, 128))
        img_rotated = self._tint_icon(os.path.join(BASE_DIR, "assets", "settings.png"), color=(128, 128, 128))
        img_rotated = img_rotated.rotate(22.5, expand=False)

        icon = CTkImage(light_image=img_normal, size=(20, 20))
        icon_rotated = CTkImage(light_image=img_rotated, size=(20, 20))

        settings_btn = ctk.CTkButton(
            self.root, text="", image=icon, width=24, height=24,
            fg_color="transparent",
            hover_color=("#EBEBEB", "#242424"),
            command=self._open_settings
        )
        settings_btn.place(x=200, y=8)
        settings_btn.bind("<Enter>", lambda e: settings_btn.configure(image=icon_rotated))
        settings_btn.bind("<Leave>", lambda e: settings_btn.configure(image=icon))
    

        # 모드 토글
        self.mode_var = ctk.StringVar(value="dark")
        self.segment_btn = ctk.CTkSegmentedButton(
            self.root,
            values=["라이트", "다크"],
            variable=ctk.StringVar(value="라이트"),
            command=self._toggle_mode,
            width=160,
            font=("맑은 고딕", 12)
        )
        self.segment_btn.pack(pady=(8, 0))

        # 상태 프레임
        frame = ctk.CTkFrame(self.root, corner_radius=10)
        frame.pack(fill="x", padx=16, pady=12)   

        self.status_labels = {}
        services = ["Redis", "Uvicorn", "Worker", "ngrok"]
        for i, svc in enumerate(services):
            row = ctk.CTkFrame(frame, fg_color="transparent")
            if i == 0:
                row.pack(anchor="center", pady=(6, 1))
            elif i == len(services) - 1:
                row.pack(anchor="center", pady=(1, 6))
            else:
                row.pack(anchor="center", pady=1)
            ctk.CTkLabel(row, text=svc, width=60, anchor="w",
                        font=("맑은 고딕", 13, "bold")).pack(side="left")
            lbl = ctk.CTkLabel(row, text="● 중지", text_color="gray",
                            anchor="w",
                            font=("맑은 고딕", 13))
            lbl.pack(side="left", padx=(6, 0))
            self.status_labels[svc] = lbl

        # ngrok URL
        url_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        url_frame.pack(fill="x", padx=16)
        self.url_var = ctk.StringVar(value="ngrok URL 대기 중...")
        ctk.CTkEntry(url_frame, textvariable=self.url_var,
                    state="readonly",
                    font=("맑은 고딕", 12)).pack(side="left", fill="x", expand=True)
        self.copy_btn = ctk.CTkButton(url_frame, text="복사", width=50,
                                    font=("맑은 고딕", 12),
                                    command=self._copy_url)
        self.copy_btn.pack(side="left", padx=(6, 0))

        # 버튼
        btn_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        btn_frame.pack(fill="x", padx=54, pady=12)
        btn_frame.columnconfigure(0, weight=1)

        self.show_btn = ctk.CTkButton(btn_frame, text="실행", height=36,
                                    font=("맑은 고딕", 13),
                                    fg_color="#0969da", hover_color="#0860ca",
                                    command=self._toggle)
        self.show_btn.grid(row=0, column=0, sticky="ew")

    def _open_settings(self):
        if hasattr(self, '_settings_win') and self._settings_win.winfo_exists():
            self._settings_win.focus()
            return
            
        self._settings_win = ctk.CTkToplevel(self.root)
        self._settings_win.title("GitReviewer 설정")
        self._settings_win.iconbitmap(os.path.join(BASE_DIR, "assets", "icon.ico"))
        self._settings_win.geometry("300x360")
        self._settings_win.resizable(False, False)
        self._settings_win.attributes("-topmost", True)
        self.show_btns = []

        ctk.CTkLabel(self._settings_win, text="API 설정", font=("맑은 고딕", 14, "bold")).pack(pady=(16, 8))

        fields = [
            ("Anthropic API 키", "ANTHROPIC_API_KEY"),
            ("GitHub 개인 접근용 토큰", "GITHUB_TOKEN"),
            ("GitHub 리포지토리용 웹훅 시크릿", "WEBHOOK_SECRET"),
            ("API 요청 헤더용 토큰 (비밀번호)", "CONFIG_TOKEN"),
        ]

        from dotenv import dotenv_values
        env = dotenv_values(".env")

        entries = {}
        for label, key in fields:
            ctk.CTkLabel(self._settings_win, text=label, font=("맑은 고딕", 12), anchor="w").pack(fill="x", padx=20)
            row = ctk.CTkFrame(self._settings_win, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=(0, 8))
            entry = ctk.CTkEntry(row, width=220, show="*", font=("맑은 고딕", 12))
            entry.insert(0, env.get(key, ""))
            entry.pack(side="left")
            # 보기/숨기기 토글 버튼
            show_btn = ctk.CTkButton(row, text="보기", width=40, font=("맑은 고딕", 11),
                                    command=lambda e=entry: toggle_show(e))
            show_btn.pack(side="left", padx=(4, 0))
            self.show_btns.append(show_btn)
            def make_toggle(e=entry, b=show_btn):
                def toggle():
                    if e.cget("show") == "*":
                        e.configure(show="")
                        b.configure(text="숨김")
                    else:
                        e.configure(show="*")
                        b.configure(text="보기")
                return toggle
            show_btn.configure(command=make_toggle())
            show_btn.pack(side="left", padx=(6, 0))
            entries[key] = entry

        def save():
            from dotenv import dotenv_values
            env = dotenv_values(".env")
            env["REDIS_URL"] = "redis://localhost:6379"
            for key, entry in entries.items():
                env[key] = entry.get()
            with open(".env", "w") as f:
                for k, v in env.items():
                    f.write(f"{k}={v}\n")
            self._settings_win.destroy()

        self.save_btn = ctk.CTkButton(self._settings_win, text="저장", font=("맑은 고딕", 12),
                              command=save)
        self.save_btn.pack(pady=8)
        
    def _toggle_mode(self, value):
        if value == "라이트":
            ctk.set_appearance_mode("light")
            self.copy_btn.configure(fg_color="#0969da", hover_color="#0860ca")
            self.segment_btn.configure(selected_color="#0969da", selected_hover_color="#0860ca")
            # 현재 상태에 따라 토글 버튼 색 적용
            if not self.processes:
                self.show_btn.configure(fg_color="#0969da", hover_color="#0860ca")
            else:
                self.show_btn.configure(fg_color="gray", hover_color="#555555")
        else:
            ctk.set_appearance_mode("dark")
            self.copy_btn.configure(fg_color="#e85d04", hover_color="#dc4e00")
            self.segment_btn.configure(selected_color="#e85d04", selected_hover_color="#dc4e00")
            # 현재 상태에 따라 토글 버튼 색 적용
            if not self.processes:
                self.show_btn.configure(fg_color="#e85d04", hover_color="#dc4e00")
            else:
                self.show_btn.configure(fg_color="#555555", hover_color="#666666")

        if hasattr(self, 'show_btns'):
            for btn in self.show_btns:
                try:
                    if btn.winfo_exists():
                        if value == "라이트":
                            btn.configure(fg_color="#0969da", hover_color="#0860ca")
                        else:
                            btn.configure(fg_color="#e85d04", hover_color="#dc4e00")
                except:
                    pass

        if hasattr(self, 'save_btn'):
            try:
                if self.save_btn.winfo_exists():
                    if value == "라이트":
                        self.save_btn.configure(fg_color="#0969da", hover_color="#0860ca")
                    else:
                        self.save_btn.configure(fg_color="#e85d04", hover_color="#dc4e00")
            except:
                pass

    def _toggle(self):
        if not self.processes:
            # 시작
            self.show_btn.configure(text="종료", fg_color="gray", hover_color="#555555")
            threading.Thread(target=self._run_services, daemon=True).start()
        else:
            # 종료
            self._stop()
            self.show_btn.configure(text="시작", fg_color="#0969da", hover_color="#0860ca")
            
    def _set_status(self, svc, running):
        lbl = self.status_labels[svc]
        if running:
            lbl.configure(text="● 실행 중", text_color="#3fb950")
        else:
            lbl.configure(text="● 중지", text_color="gray")

    def _copy_url(self):
        if self.ngrok_url:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.ngrok_url + "/webhook")

    def _start(self):
        threading.Thread(target=self._run_services, daemon=True).start()

    def _run_services(self):
        # DB 초기화
        try:
            from app.init_db import init_db
            init_db()
        except Exception:
            pass

        # Redis
        if not self._start_redis():
            self.root.after(0, lambda: self.show_btn.configure(text="시작"))
            return
        time.sleep(2)
        self._set_status("Redis", True)

        # uvicorn
        self.processes["Uvicorn"] = subprocess.Popen(
            [_get_python(), "-m", "uvicorn", "app.main:app", "--port", "8000"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        time.sleep(2)
        self._set_status("Uvicorn", True)

        # worker
        self.processes["Worker"] = subprocess.Popen(
            [_get_python(), "worker.py"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        time.sleep(1)
        self._set_status("Worker", True)

        # ngrok
        self.processes["ngrok"] = subprocess.Popen(
            ["ngrok", "http", "8000"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        time.sleep(3)
        self._fetch_ngrok_url()

    def _fetch_ngrok_url(self):
        try:
            res = requests.get("http://127.0.0.1:4040/api/tunnels")
            tunnels = res.json().get("tunnels", [])
            for t in tunnels:
                if t.get("proto") == "https":
                    self.ngrok_url = t["public_url"]
                    self.url_var.set(self.ngrok_url + "/webhook")
                    self._set_status("ngrok", True)
                    return
        except:
            self.url_var.set("ngrok URL 가져오기 실패")

    def _stop(self):
        for svc, proc in self.processes.items():
            try:
                proc.terminate()
            except:
                pass
            self._set_status(svc, False)
        self.processes.clear()
        self.ngrok_url = None
        self.url_var.set("ngrok URL 대기 중...")

if __name__ == "__main__":
    root = ctk.CTk()
    app = GitReviewerGUI(root)
    root.mainloop()