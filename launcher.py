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
VERSION = "2.8.0 (Industrial Polish)"
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
        self.geometry("1400x950")
        self.process = None
        self.saved_apis = []
        self.env_profiles = {}
        self.detected_vendor = "CPU"
        self.detected_vram = 0
        self.active_profile = ""
        self.active_ram_profile = "Balanced (Padrao)"
        self.expert_flags = ""
        self.console_active = True

        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- SIDEBAR ---
        self.sidebar = ctk.CTkFrame(self, width=280, corner_radius=0, fg_color="#0a0a0a")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="NEURAL COMMANDER", font=ctk.CTkFont(size=20, weight="bold", family="Consolas")).pack(pady=30)
        
        self.status_box = ctk.CTkFrame(self.sidebar, fg_color="#1a1a1a", corner_radius=10)
        self.status_box.pack(padx=15, pady=5, fill="x")
        self.status_indicator = ctk.CTkLabel(self.status_box, text="● SYSTEM OFFLINE", text_color="#ff4444", font=ctk.CTkFont(size=12, weight="bold"))
        self.status_indicator.pack(pady=10)

        # Telemetry
        self.telemetry_box = ctk.CTkFrame(self.sidebar, fg_color="#1a1a1a", corner_radius=10)
        self.telemetry_box.pack(padx=15, pady=15, fill="x")
        self.lbl_cpu = ctk.CTkLabel(self.telemetry_box, text="CPU: ---", font=("Consolas", 11)); self.lbl_cpu.pack(pady=2)
        self.lbl_swap = ctk.CTkLabel(self.telemetry_box, text="SWAP: ---", font=("Consolas", 11), text_color="#aaa"); self.lbl_swap.pack(pady=2)
        self.lbl_vram = ctk.CTkLabel(self.telemetry_box, text="VRAM: ---", font=("Consolas", 11)); self.lbl_vram.pack(pady=2)
        self.lbl_disk = ctk.CTkLabel(self.telemetry_box, text="DISK: ---", font=("Consolas", 11)); self.lbl_disk.pack(pady=2)

        ctk.CTkButton(self.sidebar, text="SYSTEM PURGE", command=lambda: self.system_purge(), fg_color="#333", height=35).pack(padx=20, pady=15, fill="x")

        self.btn_start = ctk.CTkButton(self.sidebar, text="ENGINE IGNITION", command=lambda: self.start_studio(), fg_color="#2d5a27", hover_color="#1e3d1a", height=50, font=ctk.CTkFont(weight="bold"))
        self.btn_start.pack(padx=20, pady=10, fill="x")
        self.btn_stop = ctk.CTkButton(self.sidebar, text="TERMINATE CORE", command=lambda: self.stop_studio(), fg_color="#8b0000", hover_color="#5a0000", height=50, font=ctk.CTkFont(weight="bold"))
        self.btn_stop.pack(padx=20, pady=10, fill="x")

        # --- TABS ---
        self.tabs = ctk.CTkTabview(self, segmented_button_fg_color="#0a0a0a", segmented_button_selected_color="#3b8ed0")
        self.tabs.grid(row=0, column=1, padx=20, pady=10, sticky="nsew")
        
        self.tab_dl = self.tabs.add("📦 ACQUISITION"); self.tab_inv = self.tabs.add("📂 INVENTORY")
        self.tab_gal = self.tabs.add("🖼️ GALLERY"); self.tab_canvas = self.tabs.add("🧠 CANVAS")
        self.tab_train = self.tabs.add("🚀 TRAINING"); self.tab_log = self.tabs.add("📟 CONSOLE")
        self.tab_opt = self.tabs.add("⚙️ OPTIMIZER"); self.tab_vault = self.tabs.add("🔒 VAULT")

        self.setup_acquisition_tab(); self.setup_inventory_tab(); self.setup_gallery_tab(); self.setup_canvas_tab()
        self.setup_training_tab(); self.setup_console_tab(); self.setup_optimizer_tab(); self.setup_vault_tab()

        self.detect_hardware(); self.load_config()
        self.check_status_loop(); self.start_telemetry_loop(); self.start_console_stream()

    # --- GALLERY MODULE (POLISHED) ---
    def setup_gallery_tab(self):
        f_main = ctk.CTkFrame(self.tab_gal, fg_color="transparent"); f_main.pack(fill="both", expand=True)
        f_main.grid_columnconfigure(0, weight=1); f_main.grid_columnconfigure(1, weight=1)
        self.gal_list = ctk.CTkScrollableFrame(f_main, label_text="NEURAL REPOSITORY", fg_color="#050505")
        self.gal_list.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.f_gal_view = ctk.CTkFrame(f_main, fg_color="#111", corner_radius=15, border_width=1, border_color="#333")
        self.f_gal_view.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.lbl_gal_img = ctk.CTkLabel(self.f_gal_view, text="Select asset", width=500, height=500, fg_color="#050505", corner_radius=10); self.lbl_gal_img.pack(padx=20, pady=20)
        self.txt_gal_meta = ctk.CTkTextbox(self.f_gal_view, height=200, font=("Consolas", 11), fg_color="transparent"); self.txt_gal_meta.pack(padx=20, pady=10, fill="both", expand=True)
        self.btn_del_img = ctk.CTkButton(self.f_gal_view, text="DELETE ASSET", fg_color="#8b0000", hover_color="#5a0000", command=lambda: self.delete_gallery_item())
        self.btn_del_img.pack(side="bottom", pady=10, padx=20, fill="x")
        self.active_gallery_path = None
        ctk.CTkButton(self.tab_gal, text="REFRESH GALLERY", command=lambda: self.refresh_gallery(), height=40).pack(pady=10)

    def refresh_gallery(self):
        for w in self.gal_list.winfo_children(): w.destroy()
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        files = sorted([f for f in os.listdir(OUTPUT_DIR) if f.lower().endswith((".png", ".jpg", ".webp", ".mp4", ".webm", ".gif"))], reverse=True)
        for f in files:
            icon = "🎬" if f.lower().endswith((".mp4", ".webm", ".gif")) else "📷"
            p = OUTPUT_DIR / f
            btn = ctk.CTkButton(self.gal_list, text=f"{icon} {f}", anchor="w", fg_color="transparent", hover_color="#222", command=lambda path=p: self.load_gallery_item(path))
            btn.pack(fill="x", pady=1)

    def load_gallery_item(self, path):
        self.active_gallery_path = path
        try:
            img = None
            if path.suffix.lower() in [".mp4", ".webm", ".gif"]:
                thumb_path = TEMP_DIR / f"{path.stem}_thumb.png"
                TEMP_DIR.mkdir(parents=True, exist_ok=True)
                if not thumb_path.exists():
                    cmd = f'ffmpeg -y -i "{path}" -ss 00:00:01 -vframes 1 "{thumb_path}"'
                    subprocess.run(cmd, shell=True, capture_output=True)
                if thumb_path.exists(): img = Image.open(thumb_path)
                meta_text = f"--- MOTION ASSET ---\nNAME: {path.name}\nTYPE: {path.suffix}\nSIZE: {os.path.getsize(path)//1024} KB"
            else:
                img = Image.open(path); meta_text = "Metadata Not Found."
                if img.format == "PNG":
                    meta = img.info
                    if "prompt" in meta: meta_text = f"--- COGNITIVE PROMPT ---\n{meta['prompt']}"
            if img:
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(500, 500))
                self.lbl_gal_img.configure(image=ctk_img, text="")
            else: self.lbl_gal_img.configure(image=None, text="Preview Not Available")
            self.txt_gal_meta.delete("1.0", "end"); self.txt_gal_meta.insert("end", meta_text)
        except Exception as e: messagebox.showerror("Error", str(e))

    # --- INVENTORY HUB (POLISHED) ---
    def setup_inventory_tab(self):
        f_top = ctk.CTkFrame(self.tab_inv, fg_color="transparent"); f_top.pack(fill="x", padx=10, pady=5)
        self.entry_inv_search = ctk.CTkEntry(f_top, placeholder_text="🔍 Search Models...", height=35); self.entry_inv_search.pack(side="left", expand=True, fill="x", padx=5)
        self.entry_inv_search.bind("<KeyRelease>", lambda e: self.filter_inventory())
        ctk.CTkButton(f_top, text="REFRESH", command=lambda: self.refresh_models_list(), width=80).pack(side="left", padx=5)
        f_main = ctk.CTkFrame(self.tab_inv, fg_color="transparent"); f_main.pack(fill="both", expand=True)
        f_main.grid_columnconfigure(0, weight=1); f_main.grid_columnconfigure(1, weight=1)
        self.inv_scroll = ctk.CTkScrollableFrame(f_main, label_text="ASSET REPOSITORY", fg_color="#050505"); self.inv_scroll.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.f_insight = ctk.CTkFrame(f_main, fg_color="#111", corner_radius=15, border_width=1, border_color="#333"); self.f_insight.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.lbl_preview = ctk.CTkLabel(self.f_insight, text="Neural Insight", width=450, height=450, fg_color="#050505", corner_radius=10); self.lbl_preview.pack(padx=20, pady=20)
        self.txt_meta = ctk.CTkTextbox(self.f_insight, height=200, font=("Consolas", 11), fg_color="transparent"); self.txt_meta.pack(padx=20, pady=10, fill="both", expand=True)
        self.active_model_path = None
        self.lbl_inv_total = ctk.CTkLabel(self.tab_inv, text="Total Size: 0.00 GB", font=("Consolas", 12, "bold")); self.lbl_inv_total.pack(pady=5)

    def refresh_models_list(self):
        for w in self.inv_scroll.winfo_children(): w.destroy()
        categories = {"checkpoints": [], "loras": [], "vae": [], "controlnet": [], "other": []}
        total_size = 0
        if MODELS_DIR.exists():
            for root, dirs, files in os.walk(MODELS_DIR):
                for f in files:
                    if f.endswith((".safetensors", ".ckpt")):
                        path = Path(root) / f; f_size = os.path.getsize(path) / (1024**3); total_size += f_size
                        found = False
                        for cat in categories.keys():
                            if cat in str(path).lower(): categories[cat].append((f, path, f_size)); found = True; break
                        if not found: categories["other"].append((f, path, f_size))
            for cat, items in categories.items():
                if items:
                    ctk.CTkLabel(self.inv_scroll, text=f"--- {cat.upper()} ---", text_color="#3b8ed0", font=("Consolas", 12, "bold")).pack(fill="x", pady=(10, 2))
                    for name, path, size in sorted(items):
                        btn = ctk.CTkButton(self.inv_scroll, text=f"● {name} ({size:.2f} GB)", anchor="w", fg_color="transparent", hover_color="#222", command=lambda p=path, n=name, s=size: self.load_model_insight(p, n, s))
                        btn.pack(fill="x", pady=1)
        self.lbl_inv_total.configure(text=f"Total Inventory Size: {total_size:.2f} GB")

    def load_model_insight(self, path, name, size):
        self.active_model_path = path
        trigger = self.get_lora_trigger(str(path))
        info = f"NAME: {name}\nSIZE: {size:.2f} GB\nPATH: {path}\n\n{trigger}"
        self.txt_meta.delete("1.0", "end"); self.txt_meta.insert("end", info)
        prev_path = path.with_suffix(".preview.png")
        if prev_path.exists():
            img = Image.open(prev_path); ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(450, 450))
            self.lbl_preview.configure(image=ctk_img, text="")
        else: self.lbl_preview.configure(image=None, text="No Preview Found")

    # --- BASE CORE LOGIC ---
    def delete_gallery_item(self):
        if not self.active_gallery_path: return
        if messagebox.askyesno("Delete", "Deletar permanentemente?"):
            try: os.remove(self.active_gallery_path); self.refresh_gallery(); self.active_gallery_path = None
            except Exception as e: messagebox.showerror("Error", str(e))

    def setup_console_tab(self):
        self.console_box = ctk.CTkTextbox(self.tab_log, font=("Consolas", 11), fg_color="#050505", text_color="#44ff44")
        self.console_box.pack(padx=20, pady=20, fill="both", expand=True)

    def start_console_stream(self):
        def stream():
            while self.console_active:
                if ENGINE_LOG.exists():
                    with open(ENGINE_LOG, "r") as f:
                        f.seek(0, 2); 
                        while self.console_active:
                            line = f.readline()
                            if line: self.console_box.insert("end", line); self.console_box.see("end")
                            else: time.sleep(0.5)
                else: time.sleep(2)
        threading.Thread(target=stream, daemon=True).start()

    def detect_hardware(self):
        try:
            if os.name == "nt": out = subprocess.check_output('powershell -Command "Get-CimInstance Win32_VideoController | Select-Object Name,AdapterRAM"', shell=True, text=True).upper()
            else: out = subprocess.check_output(r"lspci | grep -i 'vga\|3d'", shell=True, text=True).upper()
            if "NVIDIA" in out: self.detected_vendor = "NVIDIA"
            elif "AMD" in out or "RADEON" in out: self.detected_vendor = "AMD"
            if self.detected_vendor == "NVIDIA":
                v_out = subprocess.check_output("nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits", shell=True, text=True).strip()
                self.detected_vram = int(v_out)
            elif self.detected_vendor == "AMD" and os.name == "nt":
                v_out = subprocess.check_output('powershell "(Get-CimInstance Win32_VideoController).AdapterRAM"', shell=True, text=True).strip()
                self.detected_vram = int(v_out) // 1048576
        except: pass
        self.refresh_optimizer_ui(); self.auto_suggest_profile()

    def start_telemetry_loop(self):
        def update():
            while True:
                try:
                    if psutil:
                        cpu = psutil.cpu_percent(); swap = psutil.swap_memory().percent
                        self.lbl_cpu.configure(text=f"CPU LOAD: {cpu}%"); self.lbl_swap.configure(text=f"SWAP USED: {swap}%")
                        usage = psutil.disk_usage(str(MODELS_DIR)); self.lbl_disk.configure(text=f"DISK FREE: {usage.free // (1024**3)} GB")
                    if self.detected_vendor == "NVIDIA":
                        v = subprocess.check_output("nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits", shell=True, text=True, timeout=1).strip()
                        self.lbl_vram.configure(text=f"VRAM USED: {v} MB")
                except: pass
                time.sleep(3)
        threading.Thread(target=update, daemon=True).start()

    def start_studio(self):
        if self.process is None:
            self.kill_port(8188); time.sleep(2)
            gpu_f = GPU_DATABASE[self.detected_vendor].get(self.active_profile, "").split()
            ram_f = RAM_PROFILES.get(self.active_ram_profile, "").split()
            exp_f = self.expert_flags.split()
            flags = list(set(gpu_f + ram_f + exp_f))
            py = get_short_path(VENV_PATH / ("Scripts/python.exe" if os.name == "nt" else "bin/python3"))
            main = str(ENGINE_DIR / "main.py")
            args = [str(py), main, "--input-directory", str(BASE_DIR_PATH / "workspace/input"), "--output-directory", str(BASE_DIR_PATH / "workspace/output"), "--extra-model-paths-config", str(BASE_DIR_PATH / "config/extra_model_paths.yaml"), "--listen", "127.0.0.1", "--port", "8188"] + flags
            try:
                if os.name == "nt":
                    cmd = ' '.join([f'"{a}"' for a in args]); self.process = subprocess.Popen(f'start "AI CORE" cmd /k {cmd}', shell=True, cwd=str(BASE_DIR_PATH))
                else:
                    log_f = open(ENGINE_LOG, "w"); self.process = subprocess.Popen(args, stdout=log_f, stderr=log_f, cwd=str(BASE_DIR_PATH))
                self.log_acquisition.insert("end", f"[V] Ignition: {self.active_profile}\n")
            except Exception as e: messagebox.showerror("Critical", str(e))

    def setup_acquisition_tab(self):
        self.preset_menu = ctk.CTkOptionMenu(self.tab_dl, values=list(PRESET_MODELS.keys()), command=lambda x: self.apply_preset(x), height=45); self.preset_menu.pack(padx=20, pady=20, fill="x")
        self.entry_id = ctk.CTkEntry(self.tab_dl, placeholder_text="CIVITAI ID", height=45); self.entry_id.pack(padx=20, pady=10, fill="x")
        self.option_type = ctk.CTkOptionMenu(self.tab_dl, values=["checkpoints", "loras", "vae", "controlnet"], height=45); self.option_type.pack(padx=20, pady=10, fill="x")
        self.btn_dl = ctk.CTkButton(self.tab_dl, text="DOWNLOAD TARGET", command=lambda: self.start_download(), height=55, font=ctk.CTkFont(weight="bold")); self.btn_dl.pack(padx=20, pady=10, fill="x")
        self.log_acquisition = ctk.CTkTextbox(self.tab_dl, height=350, font=("Consolas", 12), fg_color="#050505"); self.log_acquisition.pack(padx=20, pady=20, fill="both", expand=True)

    def setup_training_tab(self):
        f = ctk.CTkFrame(self.tab_train, fg_color="#1a1a1a", corner_radius=10); f.pack(padx=20, pady=10, fill="x")
        self.train_base_model = ctk.CTkEntry(f, placeholder_text="BASE MODEL PATH", height=35); self.train_base_model.pack(padx=20, pady=5, fill="x")
        self.train_lora_name = ctk.CTkEntry(f, placeholder_text="OUTPUT LORA NAME", height=35); self.train_lora_name.pack(padx=20, pady=5, fill="x")
        self.entry_trigger = ctk.CTkEntry(f, placeholder_text="TRIGGER WORD", height=35); self.entry_trigger.pack(padx=20, pady=5, fill="x")
        f_params = ctk.CTkFrame(self.tab_train, fg_color="transparent"); f_params.pack(padx=20, pady=10, fill="x"); f_params.grid_columnconfigure((0,1,2,3), weight=1)
        self.train_res = ctk.CTkEntry(f_params, placeholder_text="Res", height=35); self.train_res.grid(row=0, column=0, padx=5, sticky="ew"); self.train_res.insert(0, "512")
        self.train_batch = ctk.CTkEntry(f_params, placeholder_text="Batch", height=35); self.train_batch.grid(row=0, column=1, padx=5, sticky="ew"); self.train_batch.insert(0, "1")
        self.train_dim = ctk.CTkEntry(f_params, placeholder_text="Dim", height=35); self.train_dim.grid(row=0, column=2, padx=5, sticky="ew"); self.train_dim.insert(0, "32")
        self.train_alpha = ctk.CTkEntry(f_params, placeholder_text="Alpha", height=35); self.train_alpha.grid(row=0, column=3, padx=5, sticky="ew"); self.train_alpha.insert(0, "16")
        f_wizard = ctk.CTkFrame(self.tab_train, fg_color="transparent"); f_wizard.pack(pady=5)
        self.chk_resize = ctk.CTkCheckBox(f_wizard, text="Auto-Resize", font=("Consolas", 11)); self.chk_resize.pack(side="left", padx=10); self.chk_resize.select()
        self.chk_tagger = ctk.CTkCheckBox(f_wizard, text="AI Neural Tagger", font=("Consolas", 11)); self.chk_tagger.pack(side="left", padx=10)
        ctk.CTkButton(f_wizard, text="DATASET WIZARD", command=lambda: self.dataset_wizard(), fg_color="#4B0082", height=40).pack(side="left", padx=10)
        self.btn_train = ctk.CTkButton(self.tab_train, text="START INDUSTRIAL TRAINING", command=lambda: self.start_training(), fg_color="#FF8C00", height=50, font=ctk.CTkFont(weight="bold")); self.btn_train.pack(padx=20, pady=10, fill="x")
        self.log_train = ctk.CTkTextbox(self.tab_train, height=200, font=("Consolas", 11), fg_color="#050505"); self.log_train.pack(padx=20, pady=10, fill="both", expand=True)

    def setup_vault_tab(self):
        f = ctk.CTkFrame(self.tab_vault, fg_color="transparent"); f.pack(padx=30, pady=30, fill="both", expand=True)
        self.entry_api = ctk.CTkEntry(f, placeholder_text="Paste API Key...", show="*", height=45); self.entry_api.pack(fill="x", pady=10)
        ctk.CTkButton(f, text="SAVE TO VAULT", command=lambda: self.save_api_key(), height=45).pack(fill="x", pady=10)
        self.api_list_frame = ctk.CTkScrollableFrame(f, label_text="AUTHORIZED KEYS", fg_color="#0d0d0d"); self.api_list_frame.pack(fill="both", expand=True, pady=20)

    def load_config(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    d = json.load(f); self.saved_apis = d.get("api_keys", []); self.env_profiles = d.get("env_profiles", {})
                    self.active_profile = d.get("hw_profile", ""); self.active_ram_profile = d.get("ram_profile", "Balanced (Padrao)")
                    self.expert_flags = d.get("expert_flags", "")
                self.refresh_api_ui(); self.refresh_optimizer_ui()
                if self.expert_flags: self.entry_expert.insert(0, self.expert_flags)
            except: pass

    def persist_config(self):
        d = {"api_keys": self.saved_apis, "hw_profile": self.active_profile, "hw_vendor": self.detected_vendor, "ram_profile": self.active_ram_profile, "expert_flags": self.expert_flags, "env_profiles": self.env_profiles}
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        temp_file = CONFIG_FILE.with_suffix(".tmp")
        with open(temp_file, 'w') as f: json.dump(d, f, indent=4)
        os.replace(temp_file, CONFIG_FILE)

    def kill_port(self, port):
        try:
            if os.name != "nt":
                subprocess.run(["fuser", "-k", f"{port}/tcp"], capture_output=True, timeout=2)
                subprocess.run(f"lsof -ti:{port} | xargs kill -9", shell=True, capture_output=True, timeout=2)
            else: subprocess.run(f"powershell -Command \"Stop-Process -Id (Get-NetTCPConnection -LocalPort {port}).OwningProcess -Force\"", shell=True, capture_output=True, timeout=2)
        except: pass

    def setup_canvas_tab(self):
        f_main = ctk.CTkFrame(self.tab_canvas, fg_color="transparent"); f_main.pack(fill="both", expand=True)
        self.canvas_list = ctk.CTkTextbox(f_main, font=("Consolas", 12), fg_color="#050505", width=600); self.canvas_list.pack(side="left", padx=20, pady=20, fill="both", expand=True)
        f_controls = ctk.CTkFrame(self.tab_canvas, fg_color="transparent"); f_controls.pack(pady=10)
        ctk.CTkButton(f_controls, text="REFRESH WORKFLOWS", command=lambda: self.refresh_canvas(), height=40).pack(side="left", padx=10)
        self.refresh_canvas()

    def refresh_canvas(self):
        self.canvas_list.delete("1.0", "end")
        WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)
        files = [f for f in os.listdir(WORKFLOWS_DIR) if f.endswith(".json")]
        for f in sorted(files): self.canvas_list.insert("end", f"⚡ {f}\n")

    def refresh_api_ui(self):
        for w in self.api_list_frame.winfo_children(): w.destroy()
        for key in self.saved_apis:
            f = ctk.CTkFrame(self.api_list_frame, fg_color="#1a1a1a"); f.pack(fill="x", pady=2, padx=5)
            ctk.CTkLabel(f, text=f"ID: {key[:6]}***", font=("Consolas", 12)).pack(side="left", padx=10)
            ctk.CTkButton(f, text="X", width=40, height=22, command=lambda k=key: self.remove_api_key(k)).pack(side="right", padx=5)

    def remove_api_key(self, key):
        if key in self.saved_apis: self.saved_apis.remove(key); self.persist_config(); self.refresh_api_ui()

    def save_api_key(self):
        key = self.entry_api.get().strip()
        if len(key) >= 15 and " " not in key:
            if key not in self.saved_apis: self.saved_apis.append(key); self.persist_config(); self.refresh_api_ui()
        self.entry_api.delete(0, "end")

    def setup_optimizer_tab(self):
        f = ctk.CTkFrame(self.tab_opt, fg_color="#1a1a1a", corner_radius=15, border_width=1, border_color="#333"); f.pack(padx=40, pady=20, fill="both", expand=True)
        self.lbl_detected = ctk.CTkLabel(f, text="HARDWARE: ---", text_color="#3b8ed0", font=ctk.CTkFont(size=14, weight="bold")); self.lbl_detected.pack(pady=5)
        self.gpu_picker = ctk.CTkOptionMenu(f, values=["Detectando..."], command=lambda x: self.set_profile(x), width=450, height=40); self.gpu_picker.pack(pady=5)
        self.ram_menu = ctk.CTkOptionMenu(f, values=list(RAM_PROFILES.keys()), command=lambda x: self.set_ram_profile(x), width=450, height=40); self.ram_menu.pack(pady=5)
        self.entry_expert = ctk.CTkEntry(f, placeholder_text="Expert Flags...", height=45, width=450); self.entry_expert.pack(pady=5)
        self.entry_expert.bind("<KeyRelease>", lambda e: self.update_expert_flags())
        self.lbl_flags = ctk.CTkLabel(f, text="Flags Active: ---", font=("Consolas", 10), text_color="#444", wraplength=600); self.lbl_flags.pack(pady=25)

    def set_profile(self, choice): self.active_profile = choice; self.update_flags_preview(); self.persist_config()
    def set_ram_profile(self, choice): self.active_ram_profile = choice; self.set_profile(self.active_profile)
    def update_expert_flags(self): self.expert_flags = self.entry_expert.get().strip(); self.set_profile(self.active_profile)
    def update_flags_preview(self):
        gpu_f = GPU_DATABASE[self.detected_vendor].get(self.active_profile, ""); ram_f = RAM_PROFILES.get(self.active_ram_profile, "")
        self.lbl_flags.configure(text=f"FLAGS: {gpu_f} {ram_f} {self.expert_flags}")

    def filter_inventory(self):
        query = self.entry_inv_search.get().lower()
        for w in self.inv_scroll.winfo_children():
            if isinstance(w, ctk.CTkButton) and "●" in w.cget("text"):
                if query in w.cget("text").lower(): w.pack(fill="x", pady=1)
                else: w.pack_forget()

    def get_lora_trigger(self, file_path):
        try:
            with open(file_path, "rb") as f:
                header_size = struct.unpack("<Q", f.read(8))[0]; header_json = f.read(header_size).decode("utf-8"); header = json.loads(header_json)
                metadata = header.get("__metadata__", {}); tags = metadata.get("ss_tag_frequency", "")
                if tags:
                    tag_dict = json.loads(tags) if isinstance(tags, str) and tags.startswith("{") else {}
                    if tag_dict: return f"TAGS: {str(list(tag_dict.keys())[0])[:30]}"
                return ""
        except: return ""

    def dataset_wizard(self):
        trigger = self.entry_trigger.get().strip()
        if not trigger: messagebox.showwarning("Wizard", "Defina TRIGGER WORD"); return
        src = ctk.filedialog.askdirectory()
        if not src: return
        dst = BASE_DIR_PATH / "workspace/training_data" / trigger / "img" / f"15_{trigger}"
        dst.mkdir(parents=True, exist_ok=True)
        def process():
            self.log_train.insert("end", "[*] Wizard Neural...\n")
            for i, f in enumerate(os.listdir(src)):
                if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                    ext = os.path.splitext(f)[1]; path_src = os.path.join(src, f); path_dst = dst / f"{trigger}_{i:03d}{ext}"
                    shutil.copy2(path_src, path_dst)
                    with open(dst / f"{trigger}_{i:03d}.txt", "w") as tf: tf.write(trigger)
            if self.chk_tagger.get():
                py = get_short_path(VENV_PATH / ("bin/python3" if os.name != "nt" else "Scripts/python.exe"))
                tagger = get_short_path(TOOLS_DIR / "tagger.py")
                subprocess.run([str(py), str(tagger), str(dst), trigger])
            messagebox.showinfo("Wizard", "Dataset Criado!")
        threading.Thread(target=process, daemon=True).start()

    def auto_suggest_profile(self):
        if self.detected_vram > 0 and not self.active_profile:
            models = list(GPU_DATABASE[self.detected_vendor].keys())
            if "NVIDIA" in self.detected_vendor:
                if self.detected_vram <= 8192: p = models[0]
                else: p = models[1]
            else: p = models[0]
            self.gpu_picker.set(p); self.set_profile(p)

    def system_purge(self):
        if not messagebox.askyesno("Purge", "Limpeza profunda?"): return
        try:
            if ENGINE_LOG.exists(): ENGINE_LOG.write_text("")
            messagebox.showinfo("Purge", "Sistema limpo!")
        except: pass

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

    def apply_preset(self, choice):
        p = PRESET_MODELS.get(choice)
        if p and p["id"]: self.entry_id.delete(0, "end"); self.entry_id.insert(0, p["id"]); self.option_type.set(p["type"])

    def start_training(self):
        m = self.train_base_model.get().strip(); n = self.train_lora_name.get().strip(); t = self.entry_trigger.get().strip()
        res = self.train_res.get().strip(); batch = self.train_batch.get().strip(); dim = self.train_dim.get().strip(); alpha = self.train_alpha.get().strip()
        if not all([m, n, t, res, batch, dim, alpha]): messagebox.showwarning("Erro", "Preencha tudo!"); return
        threading.Thread(target=self.run_train, args=(m, n, t, res, batch, dim, alpha), daemon=True).start()

    def run_train(self, m, n, t, res, batch, dim, alpha):
        self.log_train.insert("end", f"[{time.strftime('%H:%M:%S')}] STARTING TRAINING...\n")
        py = get_short_path(VENV_PATH / ("Scripts/python.exe" if os.name == "nt" else "bin/python3"))
        script = get_short_path(TOOLS_DIR / "sd-scripts" / "train_network.py")
        cmd = [str(py), str(script), "--pretrained_model_name_or_path", m, "--train_data_dir", str(BASE_DIR_PATH / "workspace/training_data" / t / "img"), "--output_dir", str(MODELS_DIR / "loras"), "--output_name", n, "--resolution", f"{res},{res}", "--train_batch_size", batch, "--network_dim", dim, "--network_alpha", alpha, "--max_train_steps", "1000", "--learning_rate", "1e-4", "--network_module", "networks.lora", "--xformers", "--mixed_precision", "fp16", "--gradient_checkpointing"]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout: self.log_train.insert("end", line); self.log_train.see("end")
        proc.wait()

    def remove_api_key(self, key):
        if key in self.saved_apis: self.saved_apis.remove(key); self.persist_config(); self.refresh_api_ui()

    def save_api_key(self):
        key = self.entry_api.get().strip()
        if len(key) >= 15 and " " not in key:
            if key not in self.saved_apis: self.saved_apis.append(key); self.persist_config(); self.refresh_api_ui()
        self.entry_api.delete(0, "end")

if __name__ == "__main__":
    app = App(); app.mainloop()
