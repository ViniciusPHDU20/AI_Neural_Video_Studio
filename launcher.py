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
VERSION = "2.2.0 (Cognitive Intel)"
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

SCRIPTS_DIR = BASE_DIR_PATH / "scripts"
TOOLS_DIR = BASE_DIR_PATH / "tools"
ENGINE_DIR = BASE_DIR_PATH / "engine"
MODELS_DIR = BASE_DIR_PATH / "models"
CONFIG_FILE = BASE_DIR_PATH / "config" / "user_config.json"
WORKFLOWS_DIR = BASE_DIR_PATH / "workspace" / "workflows"

# --- MAPEAMENTO INDUSTRIAL DE HARDWARE ---
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
        self.geometry("1250x950")
        self.process = None
        self.saved_apis = []
        self.detected_vendor = "CPU"
        self.detected_vram = 0
        self.active_profile = ""
        self.active_ram_profile = "Balanced (Padrao)"
        self.expert_flags = ""

        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- SIDEBAR ---
        self.sidebar = ctk.CTkFrame(self, width=280, corner_radius=0, fg_color="#0a0a0a")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="NEURAL CORE 2.2", font=ctk.CTkFont(size=24, weight="bold", family="Consolas")).pack(pady=30)
        
        self.status_box = ctk.CTkFrame(self.sidebar, fg_color="#1a1a1a", corner_radius=10)
        self.status_box.pack(padx=15, pady=5, fill="x")
        self.status_indicator = ctk.CTkLabel(self.status_box, text="● SYSTEM OFFLINE", text_color="#ff4444", font=ctk.CTkFont(size=12, weight="bold"))
        self.status_indicator.pack(pady=10)

        # Telemetry Hub
        self.telemetry_box = ctk.CTkFrame(self.sidebar, fg_color="#1a1a1a", corner_radius=10)
        self.telemetry_box.pack(padx=15, pady=15, fill="x")
        ctk.CTkLabel(self.telemetry_box, text="COGNITIVE TELEMETRY", font=ctk.CTkFont(size=10, weight="bold"), text_color="#3b8ed0").pack(pady=(5,0))
        self.lbl_cpu = ctk.CTkLabel(self.telemetry_box, text="CPU: ---", font=("Consolas", 11)); self.lbl_cpu.pack(pady=2)
        self.lbl_swap = ctk.CTkLabel(self.telemetry_box, text="SWAP: ---", font=("Consolas", 11), text_color="#aaa"); self.lbl_swap.pack(pady=2)
        self.lbl_vram = ctk.CTkLabel(self.telemetry_box, text="VRAM: ---", font=("Consolas", 11)); self.lbl_vram.pack(pady=2)
        self.lbl_disk = ctk.CTkLabel(self.telemetry_box, text="DISK: ---", font=("Consolas", 11)); self.lbl_disk.pack(pady=2)

        self.btn_purge = ctk.CTkButton(self.sidebar, text="SYSTEM PURGE", command=lambda: self.system_purge(), fg_color="#333", height=35)
        self.btn_purge.pack(padx=20, pady=15, fill="x")

        self.btn_start = ctk.CTkButton(self.sidebar, text="ENGINE IGNITION", command=lambda: self.start_studio(), fg_color="#2d5a27", hover_color="#1e3d1a", height=50, font=ctk.CTkFont(size=14, weight="bold"))
        self.btn_start.pack(padx=20, pady=10, fill="x")
        self.btn_stop = ctk.CTkButton(self.sidebar, text="TERMINATE CORE", command=lambda: self.stop_studio(), fg_color="#8b0000", hover_color="#5a0000", height=50, font=ctk.CTkFont(size=14, weight="bold"))
        self.btn_stop.pack(padx=20, pady=10, fill="x")

        # --- TABS ---
        self.tabs = ctk.CTkTabview(self, segmented_button_fg_color="#0a0a0a", segmented_button_selected_color="#3b8ed0")
        self.tabs.grid(row=0, column=1, padx=20, pady=10, sticky="nsew")
        
        self.tab_dl = self.tabs.add("📦 ACQUISITION"); self.tab_inv = self.tabs.add("📂 INVENTORY")
        self.tab_canvas = self.tabs.add("🧠 NEURAL CANVAS"); self.tab_train = self.tabs.add("🚀 TRAINING")
        self.tab_opt = self.tabs.add("⚙️ OPTIMIZER"); self.tab_vault = self.tabs.add("🔒 VAULT")

        self.setup_acquisition_tab(); self.setup_inventory_tab(); self.setup_canvas_tab()
        self.setup_training_tab(); self.setup_optimizer_tab(); self.setup_vault_tab()

        self.detect_hardware(); self.load_config()
        self.check_status_loop(); self.start_telemetry_loop()

    # --- DATASET WIZARD (COGNITIVE UPGRADE) ---
    def dataset_wizard(self):
        trigger = self.entry_trigger.get().strip()
        if not trigger: messagebox.showwarning("Wizard", "Defina um TRIGGER WORD primeiro."); return
        src = ctk.filedialog.askdirectory()
        if not src: return
        
        dst = BASE_DIR_PATH / "workspace/training_data" / trigger / "img" / f"15_{trigger}"
        dst.mkdir(parents=True, exist_ok=True)
        res = int(self.train_res.get().strip()) if self.train_res.get().strip().isdigit() else 512
        
        def process():
            self.log_train.insert("end", "[*] Iniciando Dataset Wizard Neural...\n")
            for i, f in enumerate(os.listdir(src)):
                if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                    ext = os.path.splitext(f)[1]; path_src = os.path.join(src, f); path_dst = dst / f"{trigger}_{i:03d}{ext}"
                    # 1. Resize/Stabilize
                    if self.chk_resize.get():
                        with Image.open(path_src) as img:
                            img = img.convert("RGB"); img.thumbnail((res, res), Image.Resampling.LANCZOS)
                            new_img = Image.new("RGB", (res, res), (0, 0, 0))
                            new_img.paste(img, ((res - img.size[0]) // 2, (res - img.size[1]) // 2))
                            new_img.save(path_dst)
                    else: shutil.copy2(path_src, path_dst)
                    # 2. Captioning
                    with open(dst / f"{trigger}_{i:03d}.txt", "w") as tf: tf.write(trigger)
            
            # 3. AI Neural Tagger (WD14)
            if self.chk_tagger.get():
                self.log_train.insert("end", "[*] Invocando AI Neural Tagger (WD14)...\n")
                py = get_short_path(VENV_PATH / ("Scripts/python.exe" if os.name == "nt" else "bin/python3"))
                tagger_script = get_short_path(TOOLS_DIR / "tagger.py")
                cmd = [str(py), str(tagger_script), str(dst), trigger]
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                for line in proc.stdout: self.log_train.insert("end", f" > {line.strip()}\n"); self.log_train.see("end")
                proc.wait()
            
            messagebox.showinfo("Wizard", f"Dataset Neural Completo: {res}x{res} + Tags")
            self.log_train.insert("end", "[V] PROCESSO CONCLUÍDO COM SUCESSO!\n")

        threading.Thread(target=process, daemon=True).start()

    # --- SYSTEM METHODS ---
    def detect_hardware(self):
        try:
            if os.name == "nt":
                out = subprocess.check_output('powershell -Command "Get-CimInstance Win32_VideoController | Select-Object Name,AdapterRAM"', shell=True, text=True).upper()
                if "NVIDIA" in out: self.detected_vendor = "NVIDIA"
                elif "AMD" in out or "RADEON" in out: self.detected_vendor = "AMD"
            else:
                out = subprocess.check_output(r"lspci | grep -i 'vga\|3d'", shell=True, text=True).upper()
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

    def auto_suggest_profile(self):
        if self.detected_vram > 0 and not self.active_profile:
            models = list(GPU_DATABASE[self.detected_vendor].keys())
            if "NVIDIA" in self.detected_vendor:
                if self.detected_vram <= 6144: p = models[3]
                elif self.detected_vram <= 8192: p = models[0]
                elif self.detected_vram <= 16384: p = models[1]
                else: p = models[2]
            else: p = models[0]
            self.gpu_picker.set(p); self.set_profile(p)

    def setup_canvas_tab(self):
        self.canvas_list = ctk.CTkTextbox(self.tab_canvas, font=("Consolas", 12), fg_color="#050505")
        self.canvas_list.pack(padx=20, pady=20, fill="both", expand=True)
        f_controls = ctk.CTkFrame(self.tab_canvas, fg_color="transparent")
        f_controls.pack(pady=10)
        ctk.CTkButton(f_controls, text="REFRESH WORKFLOWS", command=lambda: self.refresh_canvas(), height=40).pack(side="left", padx=10)
        ctk.CTkButton(f_controls, text="OPEN FOLDER", command=lambda: os.system(f"xdg-open '{WORKFLOWS_DIR}'"), fg_color="#444", height=40).pack(side="left", padx=10)
        self.refresh_canvas()

    def refresh_canvas(self):
        self.canvas_list.delete("1.0", "end")
        WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)
        files = [f for f in os.listdir(WORKFLOWS_DIR) if f.endswith(".json")]
        if not files: self.canvas_list.insert("end", "Nenhum fluxo (.json) encontrado em workspace/workflows/")
        for f in sorted(files): self.canvas_list.insert("end", f"⚡ {f}\n")

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
                self.log_acquisition.insert("end", f"[V] Neural Engine Ignition: {self.active_profile}\n")
            except Exception as e: messagebox.showerror("Critical", str(e))

    def setup_acquisition_tab(self):
        self.preset_menu = ctk.CTkOptionMenu(self.tab_dl, values=list(PRESET_MODELS.keys()), command=lambda x: self.apply_preset(x), height=45); self.preset_menu.pack(padx=20, pady=20, fill="x")
        self.entry_id = ctk.CTkEntry(self.tab_dl, placeholder_text="CIVITAI ID", height=45); self.entry_id.pack(padx=20, pady=10, fill="x")
        self.option_type = ctk.CTkOptionMenu(self.tab_dl, values=["checkpoints", "loras", "vae", "controlnet"], height=45); self.option_type.pack(padx=20, pady=10, fill="x")
        self.btn_dl = ctk.CTkButton(self.tab_dl, text="DOWNLOAD TARGET", command=lambda: self.start_download(), height=55, font=ctk.CTkFont(weight="bold")); self.btn_dl.pack(padx=20, pady=10, fill="x")
        self.log_acquisition = ctk.CTkTextbox(self.tab_dl, height=350, font=("Consolas", 12), fg_color="#050505"); self.log_acquisition.pack(padx=20, pady=20, fill="both", expand=True)

    def setup_inventory_tab(self):
        self.inv_list = ctk.CTkTextbox(self.tab_inv, font=("Consolas", 12), fg_color="#050505"); self.inv_list.pack(padx=20, pady=20, fill="both", expand=True)
        self.lbl_inv_total = ctk.CTkLabel(self.tab_inv, text="Total Size: 0.00 GB", font=("Consolas", 12, "bold")); self.lbl_inv_total.pack(pady=5)
        ctk.CTkButton(self.tab_inv, text="REFRESH INVENTORY", command=lambda: self.refresh_models_list(), height=40).pack(pady=10)

    def setup_training_tab(self):
        f = ctk.CTkFrame(self.tab_train, fg_color="#1a1a1a", corner_radius=10); f.pack(padx=20, pady=10, fill="x")
        self.train_base_model = ctk.CTkEntry(f, placeholder_text="BASE MODEL PATH", height=35); self.train_base_model.pack(padx=20, pady=5, fill="x")
        self.train_lora_name = ctk.CTkEntry(f, placeholder_text="OUTPUT LORA NAME", height=35); self.train_lora_name.pack(padx=20, pady=5, fill="x")
        self.entry_trigger = ctk.CTkEntry(f, placeholder_text="TRIGGER WORD", height=35); self.entry_trigger.pack(padx=20, pady=5, fill="x")
        f_params = ctk.CTkFrame(self.tab_train, fg_color="transparent"); f_params.pack(padx=20, pady=10, fill="x"); f_params.grid_columnconfigure((0,1,2,3), weight=1)
        self.train_res = ctk.CTkEntry(f_params, placeholder_text="Res", height=35); self.train_res.grid(row=0, column=0, padx=5, sticky="ew"); self.train_res.insert(0, "512")
        self.train_batch = ctk.CTkEntry(f_params, placeholder_text="Batch", height=35); self.train_batch.grid(row=0, column=1, padx=5, sticky="ew"); self.train_batch.insert(0, "1")
        self.train_dim = ctk.CTkEntry(f_params, placeholder_text="Dim (Rank)", height=35); self.train_dim.grid(row=0, column=2, padx=5, sticky="ew"); self.train_dim.insert(0, "32")
        self.train_alpha = ctk.CTkEntry(f_params, placeholder_text="Alpha", height=35); self.train_alpha.grid(row=0, column=3, padx=5, sticky="ew"); self.train_alpha.insert(0, "16")
        f_params2 = ctk.CTkFrame(self.tab_train, fg_color="transparent"); f_params2.pack(padx=20, pady=5, fill="x"); f_params2.grid_columnconfigure((0,1), weight=1)
        self.train_steps = ctk.CTkEntry(f_params2, placeholder_text="Total Steps", height=35); self.train_steps.grid(row=0, column=0, padx=5, sticky="ew"); self.train_steps.insert(0, "1000")
        self.train_lr = ctk.CTkEntry(f_params2, placeholder_text="Learning Rate", height=35); self.train_lr.grid(row=0, column=1, padx=5, sticky="ew"); self.train_lr.insert(0, "1e-4")
        f_wizard = ctk.CTkFrame(self.tab_train, fg_color="transparent"); f_wizard.pack(pady=5)
        self.chk_resize = ctk.CTkCheckBox(f_wizard, text="Auto-Resize", font=("Consolas", 11)); self.chk_resize.pack(side="left", padx=10); self.chk_resize.select()
        self.chk_tagger = ctk.CTkCheckBox(f_wizard, text="AI Neural Tagger (WD14)", font=("Consolas", 11)); self.chk_tagger.pack(side="left", padx=10)
        ctk.CTkButton(f_wizard, text="DATASET WIZARD", command=lambda: self.dataset_wizard(), fg_color="#4B0082", height=40).pack(side="left", padx=10)
        self.btn_train = ctk.CTkButton(self.tab_train, text="START INDUSTRIAL TRAINING", command=lambda: self.start_training(), fg_color="#FF8C00", height=50, font=ctk.CTkFont(weight="bold")); self.btn_train.pack(padx=20, pady=10, fill="x")
        self.log_train = ctk.CTkTextbox(self.tab_train, height=200, font=("Consolas", 11), fg_color="#050505"); self.log_train.pack(padx=20, pady=10, fill="both", expand=True)

    def setup_vault_tab(self):
        f = ctk.CTkFrame(self.tab_vault, fg_color="transparent"); f.pack(padx=30, pady=30, fill="both", expand=True)
        self.entry_api = ctk.CTkEntry(f, placeholder_text="Paste API Key...", show="*", height=45); self.entry_api.pack(fill="x", pady=10)
        ctk.CTkButton(f, text="SAVE TO VAULT", command=lambda: self.save_api_key(), height=45).pack(fill="x", pady=10)
        self.api_list_frame = ctk.CTkScrollableFrame(f, label_text="AUTHORIZED KEYS", fg_color="#0d0d0d"); self.api_list_frame.pack(fill="both", expand=True, pady=20)

    def setup_optimizer_tab(self):
        f = ctk.CTkFrame(self.tab_opt, fg_color="#1a1a1a", corner_radius=15, border_width=1, border_color="#333")
        f.pack(padx=40, pady=20, fill="both", expand=True)
        ctk.CTkLabel(f, text="HARDWARE SYNTHESIS MANAGER", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)
        self.lbl_detected = ctk.CTkLabel(f, text="DETECTED GPU: ---", text_color="#3b8ed0", font=ctk.CTkFont(size=14, weight="bold")); self.lbl_detected.pack(pady=5)
        self.lbl_vram_total = ctk.CTkLabel(f, text="TOTAL VRAM: ---", text_color="white", font=("Consolas", 12)); self.lbl_vram_total.pack(pady=5)
        ctk.CTkLabel(f, text="SELECIONE SEU MODELO DE GPU (Manual Override):", text_color="#aaa").pack(pady=(15, 0))
        self.gpu_picker = ctk.CTkOptionMenu(f, values=["Detectando..."], command=lambda x: self.set_profile(x), width=450, height=45); self.gpu_picker.pack(pady=5)
        ctk.CTkLabel(f, text="Gerenciamento de RAM do Sistema:", text_color="gray").pack(pady=(15, 0))
        self.ram_menu = ctk.CTkOptionMenu(f, values=list(RAM_PROFILES.keys()), command=lambda x: self.set_ram_profile(x), width=400, height=40); self.ram_menu.pack(pady=5)
        ctk.CTkLabel(f, text="Expert Engine Flags (Manual Injection):", text_color="#FF8C00").pack(pady=(15, 0))
        self.entry_expert = ctk.CTkEntry(f, placeholder_text="Ex: --cuda-malloc", height=45, width=450); self.entry_expert.pack(pady=5)
        self.entry_expert.bind("<KeyRelease>", lambda e: self.update_expert_flags())
        self.lbl_flags = ctk.CTkLabel(f, text="Flags Active: ---", font=("Consolas", 10), text_color="#444", wraplength=600); self.lbl_flags.pack(pady=25)

    def load_config(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    d = json.load(f); self.saved_apis = d.get("api_keys", [])
                    self.active_profile = d.get("hw_profile", ""); self.active_ram_profile = d.get("ram_profile", "Balanced (Padrao)")
                    self.expert_flags = d.get("expert_flags", "")
                self.refresh_api_ui(); self.refresh_optimizer_ui()
                if self.expert_flags: self.entry_expert.insert(0, self.expert_flags)
            except: pass

    def persist_config(self):
        d = {"api_keys": self.saved_apis, "hw_profile": self.active_profile, "hw_vendor": self.detected_vendor, "ram_profile": self.active_ram_profile, "expert_flags": self.expert_flags}
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
        self.active_profile = choice; self.update_flags_preview(); self.persist_config()

    def set_ram_profile(self, choice):
        self.active_ram_profile = choice; self.update_flags_preview(); self.persist_config()

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
        categories = {"checkpoints": [], "loras": [], "vae": [], "controlnet": [], "other": []}
        total_size = 0
        if MODELS_DIR.exists():
            for root, dirs, files in os.walk(MODELS_DIR):
                for f in files:
                    if f.endswith((".safetensors", ".ckpt")):
                        path = Path(root) / f; f_size = os.path.getsize(path) / (1024**3); total_size += f_size
                        trigger = self.get_lora_trigger(str(path)) if "loras" in str(path).lower() else ""
                        item = f"● {f} ({f_size:.2f} GB) {trigger}"
                        found = False
                        for cat in categories.keys():
                            if cat in str(path).lower(): categories[cat].append(item); found = True; break
                        if not found: categories["other"].append(item)
            for cat, items in categories.items():
                if items:
                    self.inv_list.insert("end", f"\n--- {cat.upper()} ---\n")
                    for m in sorted(items): self.inv_list.insert("end", f"{m}\n")
        self.lbl_inv_total.configure(text=f"Total Inventory Size: {total_size:.2f} GB")

    def start_training(self):
        m = self.train_base_model.get().strip(); n = self.train_lora_name.get().strip(); t = self.entry_trigger.get().strip()
        res = self.train_res.get().strip(); batch = self.train_batch.get().strip()
        dim = self.train_dim.get().strip(); alpha = self.train_alpha.get().strip()
        steps = self.train_steps.get().strip(); lr = self.train_lr.get().strip()
        if not all([m, n, t, res, batch, dim, alpha, steps, lr]): messagebox.showwarning("Erro", "Preencha tudo!"); return
        threading.Thread(target=self.run_train, args=(m, n, t, res, batch, dim, alpha, steps, lr), daemon=True).start()

    def run_train(self, m, n, t, res, batch, dim, alpha, steps, lr):
        self.log_train.insert("end", f"[{time.strftime('%H:%M:%S')}] STARTING INDUSTRIAL TRAINING...\n")
        py = get_short_path(VENV_PATH / ("Scripts/python.exe" if os.name == "nt" else "bin/python3"))
        script = get_short_path(TOOLS_DIR / "sd-scripts" / "train_network.py")
        cmd = [str(py), str(script), "--pretrained_model_name_or_path", m, "--train_data_dir", str(BASE_DIR_PATH / "workspace/training_data" / t / "img"), "--output_dir", str(MODELS_DIR / "loras"), "--output_name", n, "--resolution", f"{res},{res}", "--train_batch_size", batch, "--network_dim", dim, "--network_alpha", alpha, "--max_train_steps", steps, "--learning_rate", lr, "--network_module", "networks.lora", "--xformers", "--mixed_precision", "fp16", "--gradient_checkpointing"]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout: self.log_train.insert("end", line); self.log_train.see("end")
        proc.wait()

if __name__ == "__main__":
    app = App(); app.mainloop()
