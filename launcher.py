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
try:
    import psutil
except ImportError:
    psutil = None
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
VERSION = "1.6.7 (Final Binding)"
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

SCRIPTS_DIR = BASE_DIR_PATH / "scripts"
TOOLS_DIR = BASE_DIR_PATH / "tools"
ENGINE_DIR = BASE_DIR_PATH / "engine"
MODELS_DIR = BASE_DIR_PATH / "models"
CONFIG_FILE = BASE_DIR_PATH / "config" / "user_config.json"

GPU_PROFILES = {
    "NVIDIA": {
        "POTATO (2-4GB VRAM)": "--lowvram --fp8_e4m3fn-text-enc",
        "INDUSTRIAL (8GB - 3060 Ti)": "--normalvram --use-split-cross-attention --fp8_e4m3fn-text-enc",
        "GOD MODE (16-24GB VRAM)": "--gpu-only --fp16-vae"
    },
    "AMD": {
        "RX BUDGET (4-6GB VRAM)": "--directml --lowvram --fp8_e4m3fn-text-enc",
        "RX POWER (12GB+ - 6750 XT)": "--directml --normalvram --fp8_e4m3fn-text-enc"
    },
    "CPU": {"SLOW MODE": "--cpu"}
}

RAM_PROFILES = {
    "Performance (Max RAM)": "",
    "Balanced (Padrao)": "--normalvram",
    "Extreme Saver": "--lowvram"
}

PRESET_MODELS = {
    "Selecione um Preset de Engenharia...": {"id": "", "type": "checkpoints"},
    "● [BASE] Pony Diffusion V6 XL": {"id": "290640", "type": "checkpoints"},
    "● [BASE] RealVisXL V4.0 (Photo)": {"id": "139562", "type": "checkpoints"},
    "● [BASE] Juggernaut XL (Cinema)": {"id": "133005", "type": "checkpoints"},
    "● [LORA] Realistic Skin Details": {"id": "356417", "type": "loras"},
    "● [LORA] Cinematic Lighting": {"id": "341513", "type": "loras"},
    "● [LORA] Detailed Anatomy XL": {"id": "364522", "type": "loras"},
    "● [VAE] SDXL Official VAE": {"id": "290640", "type": "vae"}
}

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"AI NEURAL VIDEO STUDIO | {VERSION}")
        self.geometry("1050x850")
        self.process = None
        self.saved_apis = []
        self.detected_vendor = "CPU"
        self.active_profile = ""
        self.active_ram_profile = "Balanced (Padrao)"

        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- SIDEBAR ---
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color="#0d0d0d")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="NEURAL CORE", font=ctk.CTkFont(size=22, weight="bold", family="Consolas")).pack(pady=25)
        
        self.status_box = ctk.CTkFrame(self.sidebar, fg_color="#1a1a1a", corner_radius=10)
        self.status_box.pack(padx=15, pady=5, fill="x")
        self.status_indicator = ctk.CTkLabel(self.status_box, text="● SYSTEM OFFLINE", text_color="#ff4444", font=ctk.CTkFont(size=12, weight="bold"))
        self.status_indicator.pack(pady=10)

        self.telemetry_box = ctk.CTkFrame(self.sidebar, fg_color="#1a1a1a", corner_radius=10)
        self.telemetry_box.pack(padx=15, pady=15, fill="x")
        ctk.CTkLabel(self.telemetry_box, text="SYSTEM TELEMETRY", font=ctk.CTkFont(size=10, weight="bold"), text_color="gray").pack(pady=(5,0))
        self.lbl_cpu = ctk.CTkLabel(self.telemetry_box, text="CPU: ---", font=("Consolas", 11)); self.lbl_cpu.pack(pady=2)
        self.lbl_vram = ctk.CTkLabel(self.telemetry_box, text="VRAM: ---", font=("Consolas", 11)); self.lbl_vram.pack(pady=2)

        self.btn_start = ctk.CTkButton(self.sidebar, text="IGNITION", command=lambda: self.start_studio(), fg_color="#2d5a27", hover_color="#1e3d1a", height=45, font=ctk.CTkFont(weight="bold"))
        self.btn_start.pack(padx=20, pady=10, fill="x")
        self.btn_stop = ctk.CTkButton(self.sidebar, text="TERMINATE", command=lambda: self.stop_studio(), fg_color="#8b0000", hover_color="#5a0000", height=45, font=ctk.CTkFont(weight="bold"))
        self.btn_stop.pack(padx=20, pady=10, fill="x")

        # --- TABS ---
        self.tabs = ctk.CTkTabview(self, segmented_button_fg_color="#0d0d0d", segmented_button_selected_color="#3b8ed0")
        self.tabs.grid(row=0, column=1, padx=20, pady=10, sticky="nsew")
        self.tab_dl = self.tabs.add("📦 ACQUISITION"); self.tab_train = self.tabs.add("🧠 TRAINING")
        self.tab_opt = self.tabs.add("🚀 OPTIMIZER"); self.tab_vault = self.tabs.add("⚙️ VAULT")

        self.setup_acquisition_tab()
        self.setup_training_tab()
        self.setup_optimizer_tab()
        self.setup_vault_tab()

        self.detect_hardware()
        self.load_config()
        self.check_status_loop()
        self.start_telemetry_loop()

    def setup_acquisition_tab(self):
        self.preset_menu = ctk.CTkOptionMenu(self.tab_dl, values=list(PRESET_MODELS.keys()), command=lambda x: self.apply_preset(x), height=45)
        self.preset_menu.pack(padx=20, pady=20, fill="x")
        self.entry_id = ctk.CTkEntry(self.tab_dl, placeholder_text="CIVITAI ID", height=45); self.entry_id.pack(padx=20, pady=10, fill="x")
        self.option_type = ctk.CTkOptionMenu(self.tab_dl, values=["checkpoints", "loras", "vae"], height=45); self.option_type.pack(padx=20, pady=10, fill="x")
        self.btn_dl = ctk.CTkButton(self.tab_dl, text="DOWNLOAD", command=lambda: self.start_download(), height=50); self.btn_dl.pack(padx=20, pady=10, fill="x")
        self.log_acquisition = ctk.CTkTextbox(self.tab_dl, height=350, font=("Consolas", 12), fg_color="#050505"); self.log_acquisition.pack(padx=20, pady=20, fill="both", expand=True)

    def setup_training_tab(self):
        f = ctk.CTkFrame(self.tab_train, fg_color="#1a1a1a", corner_radius=10); f.pack(padx=20, pady=20, fill="x")
        self.train_base_model = ctk.CTkEntry(f, placeholder_text="BASE MODEL PATH", height=40); self.train_base_model.pack(padx=20, pady=10, fill="x")
        self.train_lora_name = ctk.CTkEntry(f, placeholder_text="OUTPUT LORA NAME", height=40); self.train_lora_name.pack(padx=20, pady=10, fill="x")
        self.entry_trigger = ctk.CTkEntry(f, placeholder_text="TRIGGER WORD", height=40); self.entry_trigger.pack(padx=20, pady=10, fill="x")
        ctk.CTkButton(f, text="WIZARD", command=lambda: self.dataset_wizard(), fg_color="#4B0082").pack(pady=5)
        self.btn_train = ctk.CTkButton(self.tab_train, text="START TRAINING", command=lambda: self.start_training(), fg_color="#FF8C00", height=45); self.btn_train.pack(padx=20, pady=10, fill="x")
        self.log_train = ctk.CTkTextbox(self.tab_train, height=250, font=("Consolas", 11), fg_color="#050505"); self.log_train.pack(padx=20, pady=10, fill="both", expand=True)

    def setup_optimizer_tab(self):
        f = ctk.CTkFrame(self.tab_opt, fg_color="#1a1a1a", corner_radius=15, border_width=1, border_color="#333")
        f.pack(padx=40, pady=40, fill="both", expand=True)
        ctk.CTkLabel(f, text="ACCELERATION & RAM MANAGER", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=20)
        self.lbl_detected = ctk.CTkLabel(f, text="DETECTED GPU: ---", text_color="#3b8ed0", font=ctk.CTkFont(size=14, weight="bold")); self.lbl_detected.pack(pady=10)
        self.profile_menu = ctk.CTkOptionMenu(f, values=["Detectando..."], command=lambda x: self.set_profile(x), width=350, height=40); self.profile_menu.pack(pady=5)
        self.ram_menu = ctk.CTkOptionMenu(f, values=list(RAM_PROFILES.keys()), command=lambda x: self.set_ram_profile(x), width=350, height=40); self.ram_menu.pack(pady=10)
        self.lbl_flags = ctk.CTkLabel(f, text="Flags: ---", font=("Consolas", 10), text_color="gray", wraplength=400); self.lbl_flags.pack(pady=20)

    def setup_vault_tab(self):
        f = ctk.CTkFrame(self.tab_vault, fg_color="transparent"); f.pack(padx=30, pady=30, fill="both", expand=True)
        self.entry_api = ctk.CTkEntry(f, placeholder_text="Paste API Key...", show="*", height=45); self.entry_api.pack(fill="x", pady=10)
        ctk.CTkButton(f, text="SAVE", command=lambda: self.save_api_key(), height=45).pack(fill="x", pady=10)
        self.api_list_frame = ctk.CTkScrollableFrame(f, label_text="KEYS", fg_color="#0d0d0d"); self.api_list_frame.pack(fill="both", expand=True, pady=20)

    # --- LOGIC ---

    def detect_hardware(self):
        try:
            if os.name == "nt": cmd = 'powershell -ExecutionPolicy Bypass -Command "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name"'
            else: cmd = r"lspci | grep -i 'vga\|3d'"
            out = subprocess.check_output(cmd, shell=True, text=True, timeout=2).upper()
            if "NVIDIA" in out: self.detected_vendor = "NVIDIA"
            elif "AMD" in out or "RADEON" in out: self.detected_vendor = "AMD"
            else: self.detected_vendor = "CPU"
        except: self.detected_vendor = "CPU"
        self.refresh_optimizer_ui()

    def start_telemetry_loop(self):
        def update():
            while True:
                try:
                    if psutil: self.lbl_cpu.configure(text=f"CPU LOAD: {psutil.cpu_percent()}%")
                    if self.detected_vendor == "NVIDIA":
                        v = subprocess.check_output("nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits", shell=True, text=True, timeout=1).strip()
                        self.lbl_vram.configure(text=f"VRAM USED: {v} MB")
                except: pass
                time.sleep(3)
        threading.Thread(target=update, daemon=True).start()

    def save_api_key(self):
        key = self.entry_api.get().strip()
        if len(key) >= 15 and " " not in key:
            if key not in self.saved_apis: self.saved_apis.append(key); self.persist_config(); self.refresh_api_ui()
        self.entry_api.delete(0, "end")

    def refresh_api_ui(self):
        for w in self.api_list_frame.winfo_children(): w.destroy()
        for key in self.saved_apis:
            f = ctk.CTkFrame(self.api_list_frame, fg_color="#1a1a1a"); f.pack(fill="x", pady=2, padx=5)
            ctk.CTkLabel(f, text=f"ID: {key[:6]}***", font=("Consolas", 12)).pack(side="left", padx=10)
            ctk.CTkButton(f, text="X", width=40, height=22, command=lambda k=key: self.remove_api_key(k)).pack(side="right", padx=5)

    def remove_api_key(self, key):
        if key in self.saved_apis: self.saved_apis.remove(key); self.persist_config(); self.refresh_api_ui()

    def load_config(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    d = json.load(f); self.saved_apis = d.get("api_keys", [])
                    if not self.saved_apis and d.get("civitai_api_key"): self.saved_apis = [d.get("civitai_api_key")]
                    self.active_profile = d.get("hw_profile", ""); self.active_ram_profile = d.get("ram_profile", "Balanced (Padrao)")
                self.refresh_api_ui(); self.refresh_optimizer_ui(); self.ram_menu.set(self.active_ram_profile)
            except: pass

    def persist_config(self):
        d = {"api_keys": self.saved_apis, "hw_profile": self.active_profile, "hw_vendor": self.detected_vendor, "ram_profile": self.active_ram_profile}
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        # Escrita atômica para evitar perda de dados
        temp_file = CONFIG_FILE.with_suffix(".tmp")
        with open(temp_file, 'w') as f:
            json.dump(d, f, indent=4)
        os.replace(temp_file, CONFIG_FILE)

    def kill_port(self, port):
        try:
            if os.name != "nt":
                subprocess.run(["fuser", "-k", f"{port}/tcp"], capture_output=True, timeout=2)
                subprocess.run(f"lsof -ti:{port} | xargs kill -9", shell=True, capture_output=True, timeout=2)
            else: subprocess.run(f"powershell -Command \"Stop-Process -Id (Get-NetTCPConnection -LocalPort {port}).OwningProcess -Force\"", shell=True, capture_output=True, timeout=2)
        except: pass

    def start_studio(self):
        if self.process is None:
            self.kill_port(8188); time.sleep(2)
            gpu_f = GPU_PROFILES[self.detected_vendor].get(self.active_profile, "").split()
            ram_f = RAM_PROFILES.get(self.active_ram_profile, "").split()
            flags = list(set(gpu_f + ram_f))
            py = get_short_path(VENV_PATH / ("Scripts/python.exe" if os.name == "nt" else "bin/python3"))
            main = str(ENGINE_DIR / "main.py")
            args = [str(py), main, "--input-directory", str(BASE_DIR_PATH / "workspace/input"), 
                    "--output-directory", str(BASE_DIR_PATH / "workspace/output"),
                    "--extra-model-paths-config", str(BASE_DIR_PATH / "config/extra_model_paths.yaml"),
                    "--listen", "127.0.0.1", "--port", "8188"] + flags
            try:
                if os.name == "nt":
                    cmd = ' '.join([f'"{a}"' for a in args])
                    self.process = subprocess.Popen(f'start "AI CORE" cmd /k {cmd}', shell=True, cwd=str(BASE_DIR_PATH))
                else:
                    log_f = open(ENGINE_DIR / "comfyui_stealth.log", "w")
                    self.process = subprocess.Popen(args, stdout=log_f, stderr=log_f, cwd=str(BASE_DIR_PATH))
                self.log_acquisition.insert("end", f"[V] Ignition: {self.active_profile} | {self.active_ram_profile}\n")
            except Exception as e: messagebox.showerror("Error", str(e))

    def stop_studio(self):
        self.kill_port(8188)
        if self.process:
            try:
                if os.name == "nt": subprocess.run(["taskkill", "/F", "/T", "/PID", str(self.process.pid)], capture_output=True)
                else: self.process.terminate()
            except: pass
            self.process = None
        self.status_indicator.configure(text="● SYSTEM OFFLINE", text_color="#ff4444")

    def check_status_loop(self):
        def check():
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.settimeout(1)
            online = s.connect_ex(('127.0.0.1', 8188)) == 0
            self.status_indicator.configure(text="● SYSTEM OPERATIONAL" if online else "● SYSTEM OFFLINE", text_color="#44ff44" if online else "#ff4444")
            s.close(); self.after(5000, check)
        self.after(2000, check)

    def set_profile(self, choice):
        self.active_profile = choice; self.lbl_flags.configure(text=f"FLAGS: {GPU_PROFILES[self.detected_vendor][choice]} {RAM_PROFILES[self.active_ram_profile]}"); self.persist_config()

    def set_ram_profile(self, choice):
        self.active_ram_profile = choice; self.set_profile(self.active_profile)

    def refresh_optimizer_ui(self):
        self.lbl_detected.configure(text=f"HARDWARE: {self.detected_vendor}")
        p = list(GPU_PROFILES[self.detected_vendor].keys())
        self.profile_menu.configure(values=p)
        if p:
            d = self.active_profile if self.active_profile in p else p[0]
            self.profile_menu.set(d); self.set_profile(d)

    def apply_preset(self, choice):
        p = PRESET_MODELS.get(choice)
        if p and p["id"]: self.entry_id.delete(0, "end"); self.entry_id.insert(0, p["id"]); self.option_type.set(p["type"])

    def start_download(self):
        m_id = self.entry_id.get().strip()
        if m_id: threading.Thread(target=self.run_downloader, args=(m_id, self.option_type.get()), daemon=True).start()

    def run_downloader(self, m_id, m_type):
        py = get_short_path(VENV_PATH / ("Scripts/python.exe" if os.name == "nt" else "bin/python3"))
        dl = get_short_path(TOOLS_DIR / "downloader.py"); key = self.saved_apis[-1] if self.saved_apis else ""
        cmd = [str(py), str(dl), m_id, m_type]; env = os.environ.copy()
        if key: env["CIVITAI_API_KEY"] = key
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)
        for line in proc.stdout: self.log_acquisition.insert("end", f"[{time.strftime('%H:%M:%S')}] {line.strip()}\n"); self.log_acquisition.see("end")
        proc.wait(); self.after(500, self.refresh_models_list)

    def refresh_models_list(self):
        self.inv_list.delete("1.0", "end")
        u = set()
        if MODELS_DIR.exists():
            for root, dirs, files in os.walk(MODELS_DIR):
                for f in files:
                    if f.endswith((".safetensors", ".ckpt")): u.add(f)
            for m in sorted(list(u)): self.inv_list.insert("end", f"● {m}\n")

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
        messagebox.showinfo("Wizard", "Dataset Created.")

    def start_training(self):
        m = self.train_base_model.get().strip(); n = self.train_lora_name.get().strip(); t = self.entry_trigger.get().strip()
        if not all([m, n, t]): messagebox.showwarning("Erro", "Preencha tudo!"); return
        threading.Thread(target=self.run_train, args=(m, n, t), daemon=True).start()

    def run_train(self, m, n, t):
        self.log_train.insert("end", f"[{time.strftime('%H:%M:%S')}] STARTING TRAINING...\n")
        py = get_short_path(VENV_PATH / ("Scripts/python.exe" if os.name == "nt" else "bin/python3"))
        script = get_short_path(TOOLS_DIR / "sd-scripts" / "train_network.py")
        cmd = [str(py), str(script), "--pretrained_model_name_or_path", m, "--train_data_dir", str(BASE_DIR_PATH / "workspace/training_data" / t / "img"), "--output_dir", str(MODELS_DIR / "loras"), "--output_name", n, "--resolution", "512,512", "--train_batch_size", "1", "--max_train_steps", "1000", "--learning_rate", "1e-4", "--network_module", "networks.lora", "--xformers", "--mixed_precision", "fp16", "--gradient_checkpointing"]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout: self.log_train.insert("end", line); self.log_train.see("end")
        proc.wait()

if __name__ == "__main__":
    app = App(); app.mainloop()
