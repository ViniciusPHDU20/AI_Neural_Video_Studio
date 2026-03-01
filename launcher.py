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
import struct
try:
    import psutil
except ImportError:
    psutil = None
from tkinter import messagebox
from PIL import Image
import webbrowser

# --- AMBIENTE E CAMINHOS ---
BASE_DIR = Path(__file__).parent.absolute()

def get_short_path(path):
    if os.name == "nt":
        try:
            output_buf = ctypes.create_unicode_buffer(1024)
            ctypes.windll.kernel32.GetShortPathNameW(str(path), output_buf, 1024)
            return output_buf.value
        except: return str(path)
    return str(path)

BASE_DIR_PATH = Path(get_short_path(BASE_DIR))
VENV_PATH = BASE_DIR_PATH / ".venv"

def check_venv():
    if hasattr(sys, 'real_prefix') or (sys.base_prefix != sys.prefix): return
    venv_python = VENV_PATH / ("Scripts/python.exe" if os.name == "nt" else "bin/python3")
    if venv_python.exists():
        subprocess.Popen([str(venv_python)] + sys.argv)
        sys.exit(0)

check_venv()

# --- CONFIGURAÇÕES GLOBAIS ---
VERSION = "2.8.5 (STABLE ROLLBACK)"
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

SCRIPTS_DIR = BASE_DIR_PATH / "scripts"
TOOLS_DIR = BASE_DIR_PATH / "tools"
ENGINE_DIR = BASE_DIR_PATH / "engine"
MODELS_DIR = BASE_DIR_PATH / "models"
CONFIG_FILE = BASE_DIR_PATH / "config" / "user_config.json"
WORKFLOWS_DIR = BASE_DIR_PATH / "workspace" / "workflows"
OUTPUT_DIR = BASE_DIR_PATH / "workspace" / "output"
ENGINE_LOG = ENGINE_DIR / "comfyui_stealth.log"
TEMP_DIR = BASE_DIR_PATH / "workspace" / "temp"

GPU_DATABASE = {
    "NVIDIA": {
        "RTX 3060 Ti / 4060 (8GB)": "--normalvram --use-split-cross-attention --fp8_e4m3fn-text-enc",
        "RTX 3060 / 4060 Ti (12GB-16GB)": "--gpu-only --use-split-cross-attention --fp16-vae",
        "RTX 3090 / 4090 (24GB)": "--gpu-only --highvram --use-split-cross-attention --fp16-vae",
        "RTX 2060 / 3050 (4GB-6GB)": "--lowvram --fp8_e4m3fn-text-enc --disable-xformers",
        "GTX Series (Sem Tensor Cores)": "--lowvram --fp16-vae --disable-xformers"
    },
    "AMD": {
        "RX 6700 XT / 6750 XT (12GB)": "--directml --normalvram --fp8_e4m3fn-text-enc",
        "RX 7900 XT / XTX (20GB+)": "--directml --gpu-only --highvram --fp16-vae",
        "RX 580 / 6600 (4GB-8GB)": "--directml --lowvram --fp8_e4m3fn-text-enc"
    },
    "CPU / INTEGRATED": {"Integrated / Basic": "--cpu"}
}

RAM_PROFILES = {
    "Performance (Max RAM)": "",
    "Balanced (Padrao)": "--normalvram",
    "Extreme Saver": "--lowvram"
}

PRESET_MODELS = {
    "● [BASE] Pony Diffusion V6 XL": {"id": "290640", "type": "checkpoints", "source": "civitai"},
    "● [BASE] RealVisXL V4.0 (Photo)": {"id": "139562", "type": "checkpoints", "source": "civitai"},
    "● [VIDEO] Wan 2.2 T2V (14B GGUF)": {"repo": "city96/Wan2.1-T2V-14B-gguf", "file": "wan2.1-t2v-14b-q4_k_m.gguf", "type": "checkpoints", "source": "hf"},
    "● [VIDEO] LTX-Video (High Quality)": {"repo": "Lightricks/LTX-Video", "file": "ltx-video-2b-v0.9.safetensors", "type": "checkpoints", "source": "hf"},
    "● [LORA] Realistic Skin Details": {"id": "356417", "type": "loras", "source": "civitai"},
    "● [VAE] SDXL Official VAE": {"id": "290640", "type": "vae", "source": "civitai"}
}

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"AI NEURAL VIDEO STUDIO | {VERSION}")
        self.geometry("1400x950")
        
        # Atributos de Estado
        self.process = None
        self.saved_apis = []
        self.env_profiles = {}
        self.console_active = True
        self.detected_vendor = "CPU / INTEGRATED"
        self.active_profile = ""
        self.expert_flags = ""
        self.active_preset = {}
        self.active_ram_profile = "Balanced (Padrao)"
        self.active_model_path = None

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=280, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="AI STUDIO", font=("Orbitron", 24, "bold"), text_color="#3498db").pack(pady=30)
        
        self.btn_studio = ctk.CTkButton(self.sidebar, text="LAUNCH STUDIO", command=self.start_studio, height=45, fg_color="#27ae60", hover_color="#2ecc71").pack(pady=10, padx=20)
        self.btn_stop = ctk.CTkButton(self.sidebar, text="STOP SYSTEM", command=self.stop_studio, height=45, fg_color="#c0392b", hover_color="#e74c3c").pack(pady=5, padx=20)

        self.status_indicator = ctk.CTkLabel(self.sidebar, text="● SYSTEM OFFLINE", text_color="#ff4444", font=("Consolas", 12))
        self.status_indicator.pack(pady=20)

        # Telemetria UI
        tel_f = ctk.CTkFrame(self.sidebar, fg_color="#111", corner_radius=10)
        tel_f.pack(padx=20, pady=10, fill="x")
        self.lbl_vram = ctk.CTkLabel(tel_f, text="VRAM: -- MB", font=("Consolas", 11)); self.lbl_vram.pack(pady=2)
        self.lbl_cpu = ctk.CTkLabel(tel_f, text="CPU: -- %", font=("Consolas", 11)); self.lbl_cpu.pack(pady=2)
        self.lbl_swap = ctk.CTkLabel(tel_f, text="SWAP: -- %", font=("Consolas", 11)); self.lbl_swap.pack(pady=2)
        self.lbl_disk = ctk.CTkLabel(tel_f, text="DISK: -- GB", font=("Consolas", 11)); self.lbl_disk.pack(pady=2)

        # Tabs Setup
        self.tabs = ctk.CTkTabview(self, corner_radius=15, border_width=1, border_color="#333")
        self.tabs.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        self.tab_acq = self.tabs.add("ACQUISITION")
        self.tab_gal = self.tabs.add("GALLERY")
        self.tab_canvas = self.tabs.add("CANVAS")
        self.tab_train = self.tabs.add("TRAINING")
        self.tab_vault = self.tabs.add("VAULT")
        self.tab_opt = self.tabs.add("OPTIMIZER")
        self.tab_log = self.tabs.add("CONSOLE")

        self.setup_acq_tab()
        self.setup_gal_tab()
        self.setup_canvas_tab()
        self.setup_training_tab()
        self.setup_vault_tab()
        self.setup_optimizer_tab()
        self.setup_console_tab()

        self.detect_hardware()
        self.load_config()
        self.start_loops()

    def setup_acq_tab(self):
        f = ctk.CTkFrame(self.tab_acq, fg_color="transparent"); f.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Presets
        ctk.CTkLabel(f, text="PRESET MODELS", font=("Orbitron", 14, "bold")).grid(row=0, column=0, sticky="w", pady=10)
        self.preset_menu = ctk.CTkOptionMenu(f, values=list(PRESET_MODELS.keys()), command=self.apply_preset, width=400, height=35)
        self.preset_menu.grid(row=1, column=0, sticky="w", padx=5)

        # Manual Entry
        ctk.CTkLabel(f, text="MANUAL ACQUISITION (ID / REPO)", font=("Orbitron", 14, "bold")).grid(row=2, column=0, sticky="w", pady=20)
        self.entry_id = ctk.CTkEntry(f, placeholder_text="Civitai ID or HF Repo/File", width=400, height=35)
        self.entry_id.grid(row=3, column=0, sticky="w", padx=5)
        
        self.option_type = ctk.CTkOptionMenu(f, values=["checkpoints", "loras", "vae", "upscalers", "controlnet"], width=150, height=35)
        self.option_type.grid(row=3, column=1, padx=10)

        ctk.CTkButton(f, text="START DOWNLOAD", command=self.start_download, height=45, fg_color="#3498db").grid(row=4, column=0, columnspan=2, pady=30, sticky="ew")

        # Inventory
        ctk.CTkLabel(f, text="LOCAL INVENTORY", font=("Orbitron", 14, "bold")).grid(row=0, column=2, sticky="w", padx=40)
        self.inv_scroll = ctk.CTkScrollableFrame(f, width=500, height=500, fg_color="#050505"); self.inv_scroll.grid(row=1, column=2, rowspan=10, padx=40, sticky="nsew")
        self.lbl_inv_total = ctk.CTkLabel(f, text="Total: 0 GB", font=("Consolas", 12)); self.lbl_inv_total.grid(row=11, column=2, sticky="e", padx=40)
        
        self.txt_meta = ctk.CTkTextbox(f, height=150, width=400, font=("Consolas", 11), fg_color="#111"); self.txt_meta.grid(row=5, column=0, columnspan=2, pady=10, sticky="nsew")
        ctk.CTkButton(f, text="DELETE SELECTED MODEL", command=self.delete_model_action, height=40, fg_color="#c0392b", hover_color="#e74c3c").grid(row=6, column=0, columnspan=2, pady=5, sticky="ew")
        ctk.CTkButton(f, text="REFRESH LIST", command=self.refresh_models_list).grid(row=12, column=2, sticky="ew", padx=40, pady=10)

    def setup_gal_tab(self):
        f_main = ctk.CTkFrame(self.tab_gal, fg_color="transparent"); f_main.pack(fill="both", expand=True)
        self.gal_list = ctk.CTkScrollableFrame(f_main, width=300, fg_color="#050505"); self.gal_list.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.f_gal_view = ctk.CTkFrame(f_main, fg_color="#111", corner_radius=15, border_width=1, border_color="#333"); self.f_gal_view.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.lbl_gal_img = ctk.CTkLabel(self.f_gal_view, text="Select asset", width=500, height=500, fg_color="#050505"); self.lbl_gal_img.pack(padx=20, pady=20)
        self.txt_gal_meta = ctk.CTkTextbox(self.f_gal_view, height=200, font=("Consolas", 11), fg_color="transparent"); self.txt_gal_meta.pack(padx=20, pady=10, fill="both", expand=True)
        ctk.CTkButton(self.tab_gal, text="REFRESH GALLERY", command=self.refresh_gallery, height=40).pack(pady=10)

    def setup_canvas_tab(self):
        f_main = ctk.CTkFrame(self.tab_canvas, fg_color="transparent"); f_main.pack(fill="both", expand=True)
        self.canvas_list = ctk.CTkTextbox(f_main, font=("Consolas", 12), fg_color="#050505", width=600); self.canvas_list.pack(side="left", padx=20, pady=20, fill="both", expand=True)
        ctk.CTkButton(self.tab_canvas, text="REFRESH", command=self.refresh_canvas, height=40).pack(pady=10)

    def setup_training_tab(self):
        f = ctk.CTkFrame(self.tab_train, fg_color="#1a1a1a", corner_radius=10); f.pack(padx=20, pady=10, fill="x")
        self.train_base_model = ctk.CTkEntry(f, placeholder_text="BASE MODEL PATH", height=35); self.train_base_model.pack(padx=20, pady=5, fill="x")
        self.train_lora_name = ctk.CTkEntry(f, placeholder_text="OUTPUT LORA NAME", height=35); self.train_lora_name.pack(padx=20, pady=5, fill="x")
        self.entry_trigger = ctk.CTkEntry(f, placeholder_text="TRIGGER WORD", height=35); self.entry_trigger.pack(padx=20, pady=5, fill="x")
        ctk.CTkButton(self.tab_train, text="START TRAINING", command=self.start_training, fg_color="#FF8C00", height=50).pack(padx=20, pady=10, fill="x")
        self.log_train = ctk.CTkTextbox(self.tab_train, height=200, font=("Consolas", 11), fg_color="#050505"); self.log_train.pack(padx=20, pady=10, fill="both", expand=True)

    def setup_console_tab(self):
        self.console_box = ctk.CTkTextbox(self.tab_log, font=("Consolas", 11), fg_color="#050505", text_color="#44ff44"); self.console_box.pack(padx=20, pady=20, fill="both", expand=True)

    def setup_optimizer_tab(self):
        f = ctk.CTkFrame(self.tab_opt, fg_color="#1a1a1a", corner_radius=15, border_width=1, border_color="#333"); f.pack(padx=40, pady=20, fill="both", expand=True)
        self.gpu_picker = ctk.CTkOptionMenu(f, values=["Detectando..."], command=self.set_profile, width=450, height=40); self.gpu_picker.pack(pady=5)
        self.ram_menu = ctk.CTkOptionMenu(f, values=list(RAM_PROFILES.keys()), command=self.set_ram_profile, width=450, height=40); self.ram_menu.pack(pady=5)
        self.entry_expert = ctk.CTkEntry(f, placeholder_text="Expert Flags...", height=45, width=450); self.entry_expert.pack(pady=5)
        self.entry_expert.bind("<KeyRelease>", self.update_expert_flags)
        self.lbl_flags = ctk.CTkLabel(f, text="Flags Active: ---", font=("Consolas", 10), text_color="#444", wraplength=600); self.lbl_flags.pack(pady=25)

    def setup_vault_tab(self):
        f = ctk.CTkFrame(self.tab_vault, fg_color="transparent"); f.pack(padx=30, pady=30, fill="both", expand=True)
        self.api_provider = ctk.CTkOptionMenu(f, values=["Civitai (API Key)", "Hugging Face (Token)"], height=40)
        self.api_provider.pack(fill="x", pady=5)
        self.entry_api = ctk.CTkEntry(f, placeholder_text="Paste Key/Token here...", show="*", height=45); self.entry_api.pack(fill="x", pady=10)
        ctk.CTkButton(f, text="AUTHORIZE & SAVE", command=self.save_api_key, height=45, fg_color="#2c3e50", hover_color="#34495e").pack(fill="x", pady=10)
        self.api_list_frame = ctk.CTkScrollableFrame(f, label_text="AUTHORIZED VAULT", fg_color="#0d0d0d"); self.api_list_frame.pack(fill="both", expand=True, pady=20)

    # --- REFRESH LOGIC ---
    def refresh_optimizer_ui(self):
        if not hasattr(self, 'gpu_picker') or not self.gpu_picker: return
        models = list(GPU_DATABASE.get("NVIDIA").keys()) if self.detected_vendor == "NVIDIA" else list(GPU_DATABASE.get("AMD").keys())
        self.gpu_picker.configure(values=models)
        if models:
            d = self.active_profile if self.active_profile in models else models[0]
            self.gpu_picker.set(d); self.set_profile(d)

    def refresh_models_list(self):
        if not hasattr(self, 'inv_scroll') or not self.inv_scroll: return
        for w in self.inv_scroll.winfo_children(): w.destroy()
        total_size = 0
        if MODELS_DIR.exists():
            for root, dirs, files in os.walk(MODELS_DIR):
                for f in files:
                    if f.endswith((".safetensors", ".ckpt", ".gguf")):
                        path = Path(root) / f; f_size = os.path.getsize(path) / (1024**3); total_size += f_size
                        btn = ctk.CTkButton(self.inv_scroll, text=f"● {f} ({f_size:.2f} GB)", anchor="w", fg_color="transparent", hover_color="#222", command=lambda p=path, n=f, s=f_size: self.load_model_insight(p, n, s))
                        btn.pack(fill="x", pady=1)
        self.lbl_inv_total.configure(text=f"Total: {total_size:.2f} GB")

    def refresh_gallery(self):
        if not hasattr(self, 'gal_list') or not self.gal_list: return
        for w in self.gal_list.winfo_children(): w.destroy()
        if not OUTPUT_DIR.exists(): return
        files = sorted([f for f in os.listdir(OUTPUT_DIR) if f.lower().endswith((".png", ".jpg", ".webp", ".mp4", ".webm", ".gif"))], reverse=True)
        for f in files:
            path = OUTPUT_DIR / f
            btn = ctk.CTkButton(self.gal_list, text=f"📷 {f}", anchor="w", fg_color="transparent", hover_color="#222", command=lambda p=path: self.load_gallery_item(p))
            btn.pack(fill="x", pady=1)

    def refresh_canvas(self):
        if not hasattr(self, 'canvas_list') or not self.canvas_list: return
        self.canvas_list.delete("1.0", "end")
        if WORKFLOWS_DIR.exists():
            for f in sorted(os.listdir(WORKFLOWS_DIR)):
                if f.endswith(".json"): self.canvas_list.insert("end", f"⚡ {f}\n")

    def refresh_api_ui(self):
        if not hasattr(self, "api_list_frame") or not self.api_list_frame: return
        for w in self.api_list_frame.winfo_children(): w.destroy()
        if not self.saved_apis:
            ctk.CTkLabel(self.api_list_frame, text="No keys in vault.", text_color="#555").pack(pady=20)
        else:
            for item in self.saved_apis:
                provider = item.get("provider", "Civitai") if isinstance(item, dict) else "Civitai"
                key = item.get("key", item) if isinstance(item, dict) else item
                f = ctk.CTkFrame(self.api_list_frame, fg_color="#1a1a1a", height=45)
                f.pack(fill="x", pady=2, padx=5)
                color = "#3498db" if "Hugging" in provider else "#e67e22"
                ctk.CTkLabel(f, text=f"[{provider.upper()}]", font=("Consolas", 11, "bold"), text_color=color).pack(side="left", padx=10)
                ctk.CTkLabel(f, text=f"{key[:6]}...{key[-4:]}", font=("Consolas", 12)).pack(side="left", padx=5)
                ctk.CTkButton(f, text="REVOKE", width=60, height=24, fg_color="#c0392b", hover_color="#e74c3c", command=lambda k=item: self.remove_api_key(k)).pack(side="right", padx=10)
        self.api_list_frame.update()

    def save_api_key(self):
        key = self.entry_api.get().strip()
        provider = self.api_provider.get()
        if "Hugging" in provider and not key.startswith("hf_"):
            messagebox.showerror("Vault Error", "Hugging Face tokens must start with 'hf_'")
            return
        if len(key) < 20:
            messagebox.showerror("Vault Error", "Key seems too short to be valid.")
            return
        new_entry = {"provider": provider, "key": key}
        if new_entry not in self.saved_apis:
            self.saved_apis.append(new_entry)
            self.persist_config()
            self.refresh_api_ui()
        self.entry_api.delete(0, "end")

    def remove_api_key(self, key):
        if key in self.saved_apis: self.saved_apis.remove(key); self.persist_config(); self.refresh_api_ui()

    # --- CORE LÓGICA ---
    def detect_hardware(self):
        try:
            if os.name == "nt": out = subprocess.check_output('powershell -Command "Get-CimInstance Win32_VideoController | Select-Object Name"', shell=True, text=True).upper()
            else: out = subprocess.check_output(r"lspci | grep -i 'vga\|3d'", shell=True, text=True).upper()
            if "NVIDIA" in out: self.detected_vendor = "NVIDIA"
            elif "AMD" in out or "RADEON" in out: self.detected_vendor = "AMD"
        except: pass
        self.refresh_optimizer_ui()

    def load_config(self):
        if not CONFIG_FILE.exists(): return
        try:
            with open(CONFIG_FILE, 'r') as f:
                d = json.load(f); self.saved_apis = d.get("api_keys", []); self.active_profile = d.get("hw_profile", ""); self.expert_flags = d.get("expert_flags", "")
            self.refresh_api_ui(); self.refresh_optimizer_ui()
            if self.expert_flags: self.entry_expert.delete(0, "end"); self.entry_expert.insert(0, self.expert_flags)
        except: pass

    def persist_config(self):
        d = {"api_keys": self.saved_apis, "hw_profile": self.active_profile, "hw_vendor": self.detected_vendor, "expert_flags": self.expert_flags}
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        temp = CONFIG_FILE.with_suffix(".tmp")
        with open(temp, 'w') as f:
            json.dump(d, f, indent=4)
        os.replace(temp, CONFIG_FILE)

    def start_studio(self):
        if self.process: return
        self.kill_port(8188); time.sleep(2)
        gpu_f = GPU_DATABASE.get(self.detected_vendor, {}).get(self.active_profile, "").split()
        py = get_short_path(VENV_PATH / ("bin/python3" if os.name != "nt" else "bin/python.exe"))
        main = str(ENGINE_DIR / "main.py")
        args = [str(py), main, "--listen", "127.0.0.1", "--port", "8188", "--input-directory", str(BASE_DIR_PATH / "workspace/input"), "--output-directory", str(BASE_DIR_PATH / "workspace/output"), "--extra-model-paths-config", str(BASE_DIR_PATH / "config/extra_model_paths.yaml")] + gpu_f
        try:
            if os.name == "nt": self.process = subprocess.Popen(f'start "AI CORE" cmd /k {" ".join(args)}', shell=True, cwd=str(BASE_DIR_PATH))
            else: 
                log_f = open(ENGINE_LOG, "w"); self.process = subprocess.Popen(args, stdout=log_f, stderr=log_f, cwd=str(BASE_DIR_PATH))
        except Exception as e: messagebox.showerror("Error", str(e))

    def stop_studio(self):
        self.kill_port(8188)
        if self.process:
            try: self.process.terminate()
            except: pass
            self.process = None

    def kill_port(self, port):
        try:
            if os.name != "nt": subprocess.run(["fuser", "-k", f"{port}/tcp"], capture_output=True)
            else: subprocess.run(f"powershell -Command \"Stop-Process -Id (Get-NetTCPConnection -LocalPort {port}).OwningProcess -Force\"", shell=True, capture_output=True)
        except: pass

    def start_loops(self):
        threading.Thread(target=self.check_status_loop, daemon=True).start()
        threading.Thread(target=self.start_telemetry_loop, daemon=True).start()
        threading.Thread(target=self.start_console_stream, daemon=True).start()

    def check_status_loop(self):
        while True:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.settimeout(1)
                on = s.connect_ex(('127.0.0.1', 8188)) == 0; s.close()
                self.status_indicator.configure(text="● SYSTEM OPERATIONAL" if on else "● SYSTEM OFFLINE", text_color="#44ff44" if on else "#ff4444")
            except: pass
            time.sleep(5)

    def start_telemetry_loop(self):
        while True:
            try:
                if psutil:
                    self.lbl_cpu.configure(text=f"CPU: {psutil.cpu_percent()}%"); self.lbl_swap.configure(text=f"SWAP: {psutil.swap_memory().percent}%")
                    self.lbl_disk.configure(text=f"DISK: {psutil.disk_usage(str(MODELS_DIR)).free // (1024**3)} GB")
                if self.detected_vendor == "NVIDIA":
                    v = subprocess.check_output("nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits", shell=True, text=True, timeout=1).strip()
                    self.lbl_vram.configure(text=f"VRAM: {v} MB")
            except: pass
            time.sleep(3)

    def start_console_stream(self):
        while self.console_active:
            if ENGINE_LOG.exists():
                with open(ENGINE_LOG, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                    for line in lines[-100:]:
                        self.console_box.insert("end", line)
                    self.console_box.see("end")
                    while self.console_active:
                        line = f.readline()
                        if line:
                            self.console_box.insert("end", line)
                            self.console_box.see("end")
                        else:
                            time.sleep(0.2)
            else:
                time.sleep(1)

    def apply_preset(self, choice):
        p = PRESET_MODELS.get(choice)
        if p:
            self.active_preset = p
            if p.get("source") == "hf":
                self.entry_id.delete(0, "end")
                self.entry_id.insert(0, f"{p['repo']}/{p['file']}")
            else:
                self.entry_id.delete(0, "end")
                self.entry_id.insert(0, p.get("id", ""))
            self.option_type.set(p["type"])

    def start_download(self):
        m_id = self.entry_id.get().strip(); threading.Thread(target=self.run_downloader, args=(m_id, self.option_type.get()), daemon=True).start()

    def run_downloader(self, m_id, m_type):
        py = get_short_path(VENV_PATH / ("bin/python3" if os.name != "nt" else "bin/python.exe"))
        p = getattr(self, "active_preset", {})
        if p.get("source") == "hf":
            dl = get_short_path(TOOLS_DIR / "hf_downloader.py")
            cmd = [str(py), str(dl), p["repo"], p["file"], m_type]
        else:
            dl = get_short_path(TOOLS_DIR / "downloader.py")
            cmd = [str(py), str(dl), m_id, m_type]
        
        env = os.environ.copy()
        # Buscar chave correta no Vault
        for item in self.saved_apis:
            if isinstance(item, dict):
                if p.get("source") == "hf" and "Hugging" in item["provider"]:
                    env["HUGGING_FACE_HUB_TOKEN"] = item["key"]
                elif p.get("source") == "civitai" and "Civitai" in item["provider"]:
                    env["CIVITAI_API_KEY"] = item["key"]
        
        try:
            with open(ENGINE_LOG, "a") as f:
                f.write(f"\n[*] INICIANDO AQUISIÇÃO: {m_id} ({m_type})\n")
                f.flush()
                process = subprocess.Popen(cmd, env=env, stdout=f, stderr=f, bufsize=1, universal_newlines=True)
                process.wait()
                f.write(f"\n[V] PROCESSO DE AQUISIÇÃO FINALIZADO.\n")
        except Exception as e:
            with open(ENGINE_LOG, "a") as f:
                f.write(f"\n[X] ERRO CRÍTICO NO LAUNCHER: {str(e)}\n")
        self.after(500, self.refresh_models_list)

    def dataset_wizard(self): messagebox.showinfo("Wizard", "Pronto!")
    def start_training(self): pass
    def load_model_insight(self, path, name, size):
        self.active_model_path = path
        info = f"NAME: {name}\nSIZE: {size:.2f} GB\nPATH: {path}"
        self.txt_meta.delete("1.0", "end"); self.txt_meta.insert("end", info)
    def load_gallery_item(self, path):
        self.active_gallery_path = path
        self.txt_gal_meta.delete("1.0", "end"); self.txt_gal_meta.insert("end", f"FILE: {path.name}")
    def delete_model_action(self):
        if not hasattr(self, 'active_model_path') or not self.active_model_path:
            messagebox.showwarning("Warning", "Select a model first!")
            return
        if messagebox.askyesno("Confirm Delete", f"DANGER: Are you sure you want to permanently delete:\n{self.active_model_path.name}?"):
            try:
                os.remove(self.active_model_path)
                preview = self.active_model_path.with_suffix(".preview.png")
                if preview.exists(): os.remove(preview)
                messagebox.showinfo("Success", "Model deleted successfully!")
                self.active_model_path = None
                self.txt_meta.delete("1.0", "end")
                self.refresh_models_list()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete model: {e}")
    
    def set_profile(self, choice): self.active_profile = choice; self.persist_config()
    def set_ram_profile(self, choice): self.active_ram_profile = choice; self.persist_config()
    def update_expert_flags(self, event=None): self.expert_flags = self.entry_expert.get().strip(); self.persist_config()
    def delete_gallery_item(self): pass
    def filter_inventory(self): pass

if __name__ == "__main__":
    app = App(); app.mainloop()
