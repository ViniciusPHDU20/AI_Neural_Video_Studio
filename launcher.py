import os
import sys
import subprocess
import ctypes
from pathlib import Path
import tkinter as tk
import customtkinter as ctk
import threading
import json
import socket
import shutil
import time
import re
from tkinter import messagebox

# --- AUTO-CORREÇÃO DE AMBIENTE (GOD MODE) ---
BASE_DIR = Path(__file__).parent.absolute()

def get_short_path(path):
    if os.name != "nt": return str(path)
    try:
        output_buf = ctypes.create_unicode_buffer(1024)
        ctypes.windll.kernel32.GetShortPathNameW(str(path), output_buf, 1024)
        return output_buf.value
    except: return str(path)

BASE_DIR_PATH = Path(get_short_path(BASE_DIR))
VENV_PATH = BASE_DIR_PATH / ".venv"

def check_venv():
    if hasattr(sys, 'real_prefix') or (sys.base_prefix != sys.prefix): return
    venv_python = VENV_PATH / ("Scripts/python.exe" if os.name == "nt" else "bin/python3")
    if venv_python.exists():
        subprocess.Popen([str(venv_python)] + sys.argv)
        sys.exit(0)

check_venv()

# --- CONFIGURAÇÕES DE SISTEMA ---
VERSION = "1.6.0 (Optimizer Edition)"
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

SCRIPTS_DIR = BASE_DIR_PATH / "scripts"
TOOLS_DIR = BASE_DIR_PATH / "tools"
ENGINE_DIR = BASE_DIR_PATH / "engine"
MODELS_DIR = BASE_DIR_PATH / "models"
CONFIG_FILE = BASE_DIR_PATH / "config" / "user_config.json"

# --- PERFIS DE PERFORMANCE (HARDWARE PROFILES) ---
GPU_PROFILES = {
    "NVIDIA": {
        "POTATO (2-4GB VRAM)": "--lowvram --fp8_e4m3fn-text-enc --disable-xformers",
        "INDUSTRIAL (8GB - 3060 Ti)": "--medvram --xformers --fp8_e4m3fn-text-enc",
        "GOD MODE (16-24GB VRAM)": "--highvram --xformers --fp16-vae"
    },
    "AMD": {
        "RX BUDGET (4-6GB VRAM)": "--directml --lowvram --fp8_e4m3fn-text-enc",
        "RX POWER (12GB+ - 6750 XT)": "--directml --medvram --fp8_e4m3fn-text-enc"
    },
    "CPU": {
        "SLOW MODE (No GPU)": "--cpu"
    }
}

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"AI NEURAL VIDEO STUDIO | {VERSION}")
        self.geometry("1000x800")
        self.process = None
        self.saved_apis = []
        self.detected_vendor = "CPU"
        self.active_profile = ""

        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- SIDEBAR ---
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#111111")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="NEURAL CORE", font=ctk.CTkFont(size=22, weight="bold", family="Consolas")).pack(pady=30)
        
        self.status_indicator = ctk.CTkLabel(self.sidebar, text="● SYSTEM OFFLINE", text_color="#ff4444", font=ctk.CTkFont(size=12, weight="bold"))
        self.status_indicator.pack(pady=5)

        self.btn_start = ctk.CTkButton(self.sidebar, text="IGNITION", command=self.start_studio, fg_color="#2d5a27", height=40)
        self.btn_start.pack(padx=20, pady=10, fill="x")

        self.btn_stop = ctk.CTkButton(self.sidebar, text="TERMINATE", command=self.stop_studio, fg_color="#8b0000", height=40)
        self.btn_stop.pack(padx=20, pady=10, fill="x")

        # --- TABS ---
        self.tabs = ctk.CTkTabview(self, segmented_button_fg_color="#111111")
        self.tabs.grid(row=0, column=1, padx=20, pady=10, sticky="nsew")
        
        self.tab_dl = self.tabs.add("📦 ACQUISITION")
        self.tab_train = self.tabs.add("🧠 TRAINING")
        self.tab_opt = self.tabs.add("🚀 OPTIMIZER")
        self.tab_vault = self.tabs.add("⚙️ VAULT")

        self.setup_acquisition_tab()
        self.setup_training_tab()
        self.setup_optimizer_tab()
        self.setup_vault_tab()

        self.detect_hardware()
        self.load_config()
        self.check_status_loop()

    def detect_hardware(self):
        try:
            if os.name == "nt":
                cmd = 'powershell -ExecutionPolicy Bypass -Command "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name"'
            else:
                cmd = "lspci | grep -i 'vga\|3d'"
            
            output = subprocess.check_output(cmd, shell=True, text=True).upper()
            if "NVIDIA" in output: self.detected_vendor = "NVIDIA"
            elif "AMD" in output or "RADEON" in output: self.detected_vendor = "AMD"
            else: self.detected_vendor = "CPU"
        except: self.detected_vendor = "CPU"
        
        self.refresh_optimizer_ui()

    def setup_optimizer_tab(self):
        f = ctk.CTkFrame(self.tab_opt, fg_color="#1a1a1a", corner_radius=15, border_width=1, border_color="#333")
        f.pack(padx=40, pady=40, fill="both", expand=True)
        
        ctk.CTkLabel(f, text="HARDWARE ACCELERATION MANAGER", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=20)
        
        self.lbl_detected = ctk.CTkLabel(f, text=f"DETECTED GPU: ---", text_color="#3b8ed0", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_detected.pack(pady=10)

        ctk.CTkLabel(f, text="Selecione o perfil de potência baseado na sua VRAM:", text_color="gray").pack(pady=(20, 5))
        
        self.profile_menu = ctk.CTkOptionMenu(f, values=["Detectando..."], command=self.set_profile, width=300, height=40)
        self.profile_menu.pack(pady=10)

        self.lbl_flags = ctk.CTkLabel(f, text="Active Flags: None", font=("Consolas", 10), text_color="gray")
        self.lbl_flags.pack(pady=20)

    def refresh_optimizer_ui(self):
        self.lbl_detected.configure(text=f"DETECTED HARDWARE: {self.detected_vendor}")
        profiles = list(GPU_PROFILES[self.detected_vendor].keys())
        self.profile_menu.configure(values=profiles)
        if profiles:
            # Tentar carregar o que está no config, senão pega o primeiro
            default = self.active_profile if self.active_profile in profiles else profiles[0]
            self.profile_menu.set(default)
            self.set_profile(default)

    def set_profile(self, choice):
        self.active_profile = choice
        flags = GPU_PROFILES[self.detected_vendor][choice]
        self.lbl_flags.configure(text=f"ENGINE FLAGS: {flags}")
        self.persist_config()

    def setup_acquisition_tab(self):
        # Simplificado para foco em performance
        self.entry_id = ctk.CTkEntry(self.tab_dl, placeholder_text="CIVITAI MODEL ID", height=45)
        self.entry_id.pack(padx=20, pady=20, fill="x")
        self.btn_dl = ctk.CTkButton(self.tab_dl, text="DOWNLOAD TARGET", command=self.start_download, height=45, fg_color="#3b8ed0")
        self.btn_dl.pack(padx=20, pady=10, fill="x")
        self.log_acquisition = ctk.CTkTextbox(self.tab_dl, height=350, font=("Consolas", 12), fg_color="#050505")
        self.log_acquisition.pack(padx=20, pady=20, fill="both", expand=True)

    def setup_training_tab(self):
        ctk.CTkLabel(self.tab_train, text="LORA TRAINING HUB", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)
        self.entry_trigger = ctk.CTkEntry(self.tab_train, placeholder_text="TRIGGER WORD", height=40)
        self.entry_trigger.pack(padx=40, pady=10, fill="x")
        ctk.CTkButton(self.tab_train, text="OPEN DATASET WIZARD", command=self.dataset_wizard, fg_color="#4B0082", height=40).pack(padx=40, pady=10, fill="x")
        self.log_train = ctk.CTkTextbox(self.tab_train, height=300, font=("Consolas", 11), fg_color="#050505")
        self.log_train.pack(padx=20, pady=20, fill="both", expand=True)

    def setup_vault_tab(self):
        f = ctk.CTkFrame(self.tab_vault, fg_color="transparent")
        f.pack(padx=30, pady=30, fill="both", expand=True)
        
        self.entry_api = ctk.CTkEntry(f, placeholder_text="Paste Civitai API Key...", show="*", height=45)
        self.entry_api.pack(fill="x", pady=10)
        
        ctk.CTkButton(f, text="REGISTER IN VAULT", command=self.save_api_key, height=40).pack(fill="x", pady=10)
        
        self.api_list_frame = ctk.CTkScrollableFrame(f, label_text="AUTHORIZED CREDENTIALS", fg_color="#0d0d0d")
        self.api_list_frame.pack(fill="both", expand=True, pady=20)

    # --- LOGICA DE SEGURANÇA E PERFORMANCE ---

    def validate_api_key(self, key):
        # Civitai keys são geralmente strings hexadecimais de 32 caracteres
        if not re.match(r"^[a-f0-9]{32}$", key.lower()):
            return False
        return True

    def save_api_key(self):
        key = self.entry_api.get().strip()
        if not self.validate_api_key(key):
            messagebox.showerror("Invalid Format", "A chave inserida não é uma Civitai API Key válida.\nFormato esperado: 32 caracteres (letras e números).")
            return
        
        if key not in self.saved_apis:
            self.saved_apis.append(key)
            self.persist_config()
            self.refresh_api_ui()
            messagebox.showinfo("Vault", "Chave autenticada e salva!")
        self.entry_api.delete(0, "end")

    def refresh_api_ui(self):
        for w in self.api_list_frame.winfo_children(): w.destroy()
        for key in self.saved_apis:
            f = ctk.CTkFrame(self.api_list_frame, fg_color="#1a1a1a")
            f.pack(fill="x", pady=2, padx=5)
            ctk.CTkLabel(f, text=f"ID: {key[:6]}***{key[-4:]}", font=("Consolas", 12)).pack(side="left", padx=10)
            ctk.CTkButton(f, text="REVOKE", width=70, height=22, fg_color="#444", command=lambda k=key: self.remove_api_key(k)).pack(side="right", padx=5)

    def remove_api_key(self, key):
        if key in self.saved_apis:
            self.saved_apis.remove(key)
            self.persist_config(); self.refresh_api_ui()

    def persist_config(self):
        data = {
            "api_keys": self.saved_apis,
            "hw_profile": self.active_profile,
            "hw_vendor": self.detected_vendor
        }
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w') as f: json.dump(data, f, indent=4)

    def load_config(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    d = json.load(f)
                    self.saved_apis = d.get("api_keys", [])
                    self.active_profile = d.get("hw_profile", "")
                self.refresh_api_ui()
                self.refresh_optimizer_ui()
            except: pass

    def start_studio(self):
        if self.process is None:
            # 1. Kill zumbis
            port = 8188
            if os.name == "nt": subprocess.run(f"powershell -Command \"Stop-Process -Id (Get-NetTCPConnection -LocalPort {port}).OwningProcess -Force\"", shell=True, capture_output=True)
            else: subprocess.run(["fuser", "-k", f"{port}/tcp"], capture_output=True)
            time.sleep(1)

            # 2. Get Flags do Perfil
            flags = GPU_PROFILES[self.detected_vendor].get(self.active_profile, "--lowvram").split()
            
            py = get_short_path(VENV_PATH / ("Scripts/python.exe" if os.name == "nt" else "bin/python3"))
            main = ENGINE_DIR / "main.py"
            
            args = [str(py), str(main), "--listen", "127.0.0.1", "--port", "8188"] + flags
            
            try:
                if os.name == "nt":
                    # Hard-quoted para Windows
                    cmd = ' '.join([f'"{a}"' for a in args])
                    self.process = subprocess.Popen(f'start "AI ENGINE" cmd /k {cmd}', shell=True, cwd=str(BASE_DIR_PATH))
                else:
                    # Stealth Linux
                    log_f = open(ENGINE_DIR / "comfyui_stealth.log", "w")
                    self.process = subprocess.Popen(args, stdout=log_f, stderr=log_f, cwd=str(BASE_DIR_PATH))
                messagebox.showinfo("Success", f"Engine started with profile: {self.active_profile}")
            except Exception as e: messagebox.showerror("Critical", str(e))

    def stop_studio(self):
        if self.process:
            if os.name == "nt": subprocess.run(["taskkill", "/F", "/T", "/PID", str(self.process.pid)], capture_output=True)
            else: self.process.terminate()
            self.process = None
        self.status_indicator.configure(text="● SYSTEM OFFLINE", text_color="#ff4444")

    def check_status_loop(self):
        def check():
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.settimeout(1)
            online = s.connect_ex(('127.0.0.1', 8188)) == 0
            self.status_indicator.configure(text="● SYSTEM OPERATIONAL" if online else "● SYSTEM OFFLINE", 
                                            text_color="#44ff44" if online else "#ff4444")
            s.close(); self.after(5000, check)
        self.after(2000, check)

    def dataset_wizard(self):
        trigger = self.entry_trigger.get().strip()
        if not trigger: return
        src = ctk.filedialog.askdirectory()
        if not src: return
        dst = BASE_DIR_PATH / "workspace/training_data" / trigger / "img" / f"15_{trigger}"
        dst.mkdir(parents=True, exist_ok=True)
        import shutil
        for i, f in enumerate(os.listdir(src)):
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                ext = os.path.splitext(f)[1]; shutil.copy2(os.path.join(src, f), dst / f"{trigger}_{i:03d}{ext}")
                with open(dst / f"{trigger}_{i:03d}.txt", "w") as tf: tf.write(trigger)
        messagebox.showinfo("Wizard", "Dataset Created Successfully.")

    def start_download(self):
        m_id = self.entry_id.get().strip()
        if m_id: threading.Thread(target=self.run_downloader, args=(m_id,), daemon=True).start()

    def run_downloader(self, m_id):
        py = get_short_path(VENV_PATH / ("Scripts/python.exe" if os.name == "nt" else "bin/python3"))
        dl = get_short_path(TOOLS_DIR / "downloader.py")
        cmd = [str(py), str(dl), m_id, "checkpoints"]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout: self.log_acquisition.insert("end", f"[{time.strftime('%H:%M:%S')}] {line.strip()}\n"); self.log_acquisition.see("end")
        proc.wait()

if __name__ == "__main__":
    app = App(); app.mainloop()
