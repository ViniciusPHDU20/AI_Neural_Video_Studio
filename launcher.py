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

# --- CONFIGURAÇÕES DE INTERFACE ---
VERSION = "1.5.1 (UI Logic Fix)"
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

SCRIPTS_DIR = BASE_DIR_PATH / "scripts"
TOOLS_DIR = BASE_DIR_PATH / "tools"
ENGINE_DIR = BASE_DIR_PATH / "engine"
MODELS_DIR = BASE_DIR_PATH / "models"
CONFIG_FILE = BASE_DIR_PATH / "config" / "user_config.json"

PRESET_MODELS = {
    "Selecione um Preset de Engenharia...": {"id": "", "type": "checkpoints"},
    "● [BASE] Pony Diffusion V6 XL": {"id": "290640", "type": "checkpoints"},
    "● [BASE] RealVisXL V4.0 (Photo)": {"id": "139562", "type": "checkpoints"},
    "● [BASE] Juggernaut XL (Cinema)": {"id": "133005", "type": "checkpoints"},
    "● [LORA] Realistic Skin Details": {"id": "356417", "type": "loras"},
    "● [LORA] Cinematic Lighting": {"id": "341513", "type": "loras"},
    "● [VAE] SDXL Official VAE": {"id": "290640", "type": "vae"}
}

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Setup Janela
        self.title(f"AI NEURAL VIDEO STUDIO | {VERSION}")
        self.geometry("950x700")
        self.process = None
        self.saved_apis = []

        # Layout Principal (Grid)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- SIDEBAR (CONTROLE DE SISTEMA) ---
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color="#1a1a1a")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.lbl_logo = ctk.CTkLabel(self.sidebar, text="NEURAL CORE", font=ctk.CTkFont(size=20, weight="bold", family="Consolas"))
        self.lbl_logo.pack(pady=30)

        self.status_box = ctk.CTkFrame(self.sidebar, fg_color="#252525", corner_radius=8)
        self.status_box.pack(padx=15, pady=10, fill="x")
        
        self.status_indicator = ctk.CTkLabel(self.status_box, text="● SYSTEM OFFLINE", text_color="#ff4444", font=ctk.CTkFont(size=12, weight="bold"))
        self.status_indicator.pack(pady=10)

        self.btn_start = ctk.CTkButton(self.sidebar, text="START ENGINE", command=self.start_studio, fg_color="#2d5a27", hover_color="#1e3d1a", font=ctk.CTkFont(weight="bold"))
        self.btn_start.pack(padx=20, pady=10, fill="x")

        self.btn_stop = ctk.CTkButton(self.sidebar, text="TERMINATE", command=self.stop_studio, fg_color="#8b0000", hover_color="#5a0000", font=ctk.CTkFont(weight="bold"))
        self.btn_stop.pack(padx=20, pady=10, fill="x")

        self.lbl_info = ctk.CTkLabel(self.sidebar, text=f"Station: ViniciusPHDU\nOS: {sys.platform.upper()}\nVersion: {VERSION}", justify="left", font=ctk.CTkFont(size=10), text_color="gray")
        self.lbl_info.pack(side="bottom", pady=20)

        # --- CONTEÚDO PRINCIPAL ---
        self.tabs = ctk.CTkTabview(self, segmented_button_fg_color="#1a1a1a", segmented_button_selected_color="#3b8ed0")
        self.tabs.grid(row=0, column=1, padx=20, pady=10, sticky="nsew")
        
        self.tab_dl = self.tabs.add("📦 ACQUISITION")
        self.tab_models = self.tabs.add("📂 INVENTORY")
        self.tab_train = self.tabs.add("🧠 TRAINING")
        self.tab_settings = self.tabs.add("⚙️ VAULT")

        self.setup_acquisition_tab()
        self.setup_inventory_tab()
        self.setup_training_tab()
        self.setup_vault_tab()

        # Iniciar Loops
        self.load_config()
        self.check_status_loop()
        self.refresh_models_list()

    def setup_acquisition_tab(self):
        f_presets = ctk.CTkFrame(self.tab_dl, fg_color="transparent")
        f_presets.pack(padx=20, pady=10, fill="x")
        ctk.CTkLabel(f_presets, text="INDUSTRIAL PRESETS", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
        self.preset_menu = ctk.CTkOptionMenu(f_presets, values=list(PRESET_MODELS.keys()), command=self.apply_preset, dynamic_resizing=False)
        self.preset_menu.pack(pady=5, fill="x")
        f_manual = ctk.CTkFrame(self.tab_dl, fg_color="#252525", corner_radius=10)
        f_manual.pack(padx=20, pady=10, fill="x")
        self.entry_id = ctk.CTkEntry(f_manual, placeholder_text="CIVITAI MODEL ID", height=40, border_width=1)
        self.entry_id.pack(padx=10, pady=15, side="left", expand=True, fill="x")
        self.option_type = ctk.CTkOptionMenu(f_manual, values=["checkpoints", "loras", "vae", "controlnet"], width=120)
        self.option_type.pack(padx=10, pady=15, side="left")
        self.btn_dl = ctk.CTkButton(self.tab_dl, text="DOWNLOAD TARGET", command=self.start_download, height=45, fg_color="#3b8ed0", font=ctk.CTkFont(weight="bold"))
        self.btn_dl.pack(padx=20, pady=15, fill="x")
        self.log_acquisition = ctk.CTkTextbox(self.tab_dl, height=250, font=("Consolas", 12), fg_color="#0d0d0d", border_width=1, border_color="#333")
        self.log_acquisition.pack(padx=20, pady=10, fill="both", expand=True)

    def setup_inventory_tab(self):
        self.inv_list = ctk.CTkTextbox(self.tab_models, font=("Consolas", 12), fg_color="#0d0d0d")
        self.inv_list.pack(padx=20, pady=20, fill="both", expand=True)
        ctk.CTkButton(self.tab_models, text="REFRESH INVENTORY", command=self.refresh_models_list).pack(pady=10)

    def setup_training_tab(self):
        f_wizard = ctk.CTkFrame(self.tab_train, fg_color="#252525", corner_radius=10)
        f_wizard.pack(padx=20, pady=20, fill="x")
        ctk.CTkLabel(f_wizard, text="DATASET WIZARD (AUTOMATED)", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        self.entry_trigger = ctk.CTkEntry(f_wizard, placeholder_text="TRIGGER WORD", height=35)
        self.entry_trigger.pack(padx=20, pady=5, fill="x")
        ctk.CTkButton(f_wizard, text="GENERATE DATASET STRUCTURE", command=self.dataset_wizard, fg_color="#4B0082").pack(pady=15)
        self.log_train = ctk.CTkTextbox(self.tab_train, height=200, font=("Consolas", 11), fg_color="#0d0d0d")
        self.log_train.pack(padx=20, pady=10, fill="both", expand=True)

    def setup_vault_tab(self):
        f_add = ctk.CTkFrame(self.tab_settings, fg_color="transparent")
        f_add.pack(padx=20, pady=20, fill="x")
        ctk.CTkLabel(f_add, text="REGISTER NEW API KEY", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w")
        self.entry_api = ctk.CTkEntry(f_add, placeholder_text="Paste your Civitai API Key here...", show="*", height=40)
        self.entry_api.pack(pady=10, fill="x")
        ctk.CTkButton(f_add, text="ADD TO VAULT", command=self.save_api_key, fg_color="#3b8ed0").pack(pady=5, fill="x")
        ctk.CTkLabel(self.tab_settings, text="SAVED CREDENTIALS", font=ctk.CTkFont(size=12, weight="bold"), text_color="gray").pack(padx=20, anchor="w", pady=(20,5))
        self.api_list_frame = ctk.CTkScrollableFrame(self.tab_settings, height=250, fg_color="#1a1a1a", border_width=1, border_color="#333")
        self.api_list_frame.pack(padx=20, pady=5, fill="both", expand=True)

    def apply_preset(self, choice):
        p = PRESET_MODELS.get(choice)
        if p and p["id"]:
            self.entry_id.delete(0, "end"); self.entry_id.insert(0, p["id"]); self.option_type.set(p["type"])

    def refresh_api_ui(self):
        for widget in self.api_list_frame.winfo_children(): widget.destroy()
        for idx, key in enumerate(self.saved_apis):
            f = ctk.CTkFrame(self.api_list_frame, fg_color="#252525", pady=5)
            f.pack(fill="x", pady=2)
            masked_key = f"{key[:8]}...{key[-4:]}"
            ctk.CTkLabel(f, text=f"🔑 Key {idx+1}: {masked_key}", font=("Consolas", 12)).pack(side="left", padx=15)
            ctk.CTkButton(f, text="REMOVE", width=60, height=24, fg_color="#444", hover_color="#8b0000", 
                          command=lambda k=key: self.remove_api_key(k)).pack(side="right", padx=10)

    def save_api_key(self):
        new_key = self.entry_api.get().strip()
        if new_key and new_key not in self.saved_apis:
            self.saved_apis.append(new_key)
            self.entry_api.delete(0, "end")
            self.persist_config()
            self.refresh_api_ui()
            messagebox.showinfo("Vault", "Chave salva com sucesso!")

    def remove_api_key(self, key):
        if key in self.saved_apis:
            self.saved_apis.remove(key)
            self.persist_config(); self.refresh_api_ui()

    def persist_config(self):
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w') as f: json.dump({"api_keys": self.saved_apis}, f, indent=4)

    def load_config(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    self.saved_apis = data.get("api_keys", [])
                    old_key = data.get("civitai_api_key")
                    if old_key and old_key not in self.saved_apis: self.saved_apis.append(old_key)
                self.refresh_api_ui()
            except: pass

    def refresh_models_list(self):
        self.inv_list.delete("1.0", "end")
        unique_models = set()
        if MODELS_DIR.exists():
            for root, dirs, files in os.walk(MODELS_DIR):
                for f in files:
                    if f.endswith((".safetensors", ".ckpt")):
                        unique_models.add(f)
            
            for model in sorted(list(unique_models)):
                self.inv_list.insert("end", f"● {model}\n")
        
        if not unique_models: self.inv_list.insert("end", "Inventory Empty.")

    def kill_port(self, port):
        try:
            if os.name == "nt":
                subprocess.run(f"powershell -Command \"Stop-Process -Id (Get-NetTCPConnection -LocalPort {port}).OwningProcess -Force\"", shell=True, capture_output=True)
            else:
                subprocess.run(["fuser", "-k", f"{port}/tcp"], capture_output=True)
        except: pass

    def start_studio(self):
        if self.process is None:
            self.kill_port(8188); time.sleep(1)
            main_py = ENGINE_DIR / "main.py"
            if not main_py.exists(): return
            py = get_short_path(VENV_PATH / ("Scripts/python.exe" if os.name == "nt" else "bin/python3"))
            args = [str(py), str(main_py), "--input-directory", str(BASE_DIR_PATH / "workspace/input"),
                    "--output-directory", str(BASE_DIR_PATH / "workspace/output"), "--listen", "127.0.0.1", "--port", "8188", "--lowvram"]
            try:
                if os.name == "nt":
                    flat_args = ' '.join([f'"{a}"' for a in args])
                    self.process = subprocess.Popen(f'start "AI CORE" cmd /k {flat_args}', shell=True, cwd=str(BASE_DIR_PATH))
                else:
                    log_f = open(ENGINE_DIR / "comfyui_stealth.log", "w")
                    self.process = subprocess.Popen(args, stdout=log_f, stderr=log_f, cwd=str(BASE_DIR_PATH))
            except Exception as e: messagebox.showerror("Critical", str(e))

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
            self.status_indicator.configure(text="● SYSTEM OPERATIONAL" if online else "● SYSTEM OFFLINE", 
                                            text_color="#44ff44" if online else "#ff4444")
            s.close(); self.after(5000, check)
        self.after(2000, check)

    def dataset_wizard(self):
        trigger = self.entry_trigger.get().strip()
        if not trigger: return
        src = ctk.filedialog.askdirectory(title="SELECT SOURCE IMAGES")
        if not src: return
        dst = BASE_DIR_PATH / "workspace/training_data" / trigger / "img" / f"15_{trigger}"
        dst.mkdir(parents=True, exist_ok=True)
        import shutil
        for i, f in enumerate(os.listdir(src)):
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                ext = os.path.splitext(f)[1]; shutil.copy2(os.path.join(src, f), dst / f"{trigger}_{i:03d}{ext}")
                with open(dst / f"{trigger}_{i:03d}.txt", "w") as tf: tf.write(trigger)
        messagebox.showinfo("Wizard", f"Dataset industrial criado em: {dst}")

    def start_download(self):
        m_id = self.entry_id.get().strip(); m_type = self.option_type.get()
        if m_id: threading.Thread(target=self.run_downloader, args=(m_id, m_type), daemon=True).start()

    def run_downloader(self, m_id, m_type):
        py = get_short_path(VENV_PATH / ("Scripts/python.exe" if os.name == "nt" else "bin/python3"))
        dl = get_short_path(TOOLS_DIR / "downloader.py"); api_key = self.saved_apis[-1] if self.saved_apis else ""
        cmd = [str(py), str(dl), m_id, m_type]; env = os.environ.copy()
        if api_key: env["CIVITAI_API_KEY"] = api_key
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)
        for line in proc.stdout: self.log_acquisition.insert("end", f"[{time.strftime('%H:%M:%S')}] {line.strip()}\n"); self.log_acquisition.see("end")
        proc.wait(); self.after(500, self.refresh_models_list)

if __name__ == "__main__":
    app = App(); app.mainloop()
