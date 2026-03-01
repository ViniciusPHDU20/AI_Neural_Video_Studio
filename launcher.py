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
VERSION = "1.5.3 (Final Polish)"
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

        self.title(f"AI NEURAL VIDEO STUDIO | {VERSION}")
        self.geometry("950x750")
        self.process = None
        self.saved_apis = []

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- SIDEBAR ---
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color="#1a1a1a")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.lbl_logo = ctk.CTkLabel(self.sidebar, text="NEURAL CORE", font=ctk.CTkFont(size=20, weight="bold", family="Consolas"))
        self.lbl_logo.pack(pady=30)
        self.status_box = ctk.CTkFrame(self.sidebar, fg_color="#252525", corner_radius=8)
        self.status_box.pack(padx=15, pady=10, fill="x")
        self.status_indicator = ctk.CTkLabel(self.status_box, text="● SYSTEM OFFLINE", text_color="#ff4444", font=ctk.CTkFont(size=12, weight="bold"))
        self.status_indicator.pack(pady=10)
        self.btn_start = ctk.CTkButton(self.sidebar, text="START ENGINE", command=self.start_studio, fg_color="#2d5a27")
        self.btn_start.pack(padx=20, pady=10, fill="x")
        self.btn_stop = ctk.CTkButton(self.sidebar, text="TERMINATE", command=self.stop_studio, fg_color="#8b0000")
        self.btn_stop.pack(padx=20, pady=10, fill="x")

        # --- TABS ---
        self.tabs = ctk.CTkTabview(self, segmented_button_fg_color="#1a1a1a")
        self.tabs.grid(row=0, column=1, padx=20, pady=10, sticky="nsew")
        self.tab_dl = self.tabs.add("📦 ACQUISITION")
        self.tab_models = self.tabs.add("📂 INVENTORY")
        self.tab_train = self.tabs.add("🧠 TRAINING")
        self.tab_settings = self.tabs.add("⚙️ VAULT")

        self.setup_acquisition_tab()
        self.setup_inventory_tab()
        self.setup_training_tab()
        self.setup_vault_tab()

        self.load_config()
        self.check_status_loop()
        self.refresh_models_list()

    def setup_acquisition_tab(self):
        self.preset_menu = ctk.CTkOptionMenu(self.tab_dl, values=list(PRESET_MODELS.keys()), command=self.apply_preset)
        self.preset_menu.pack(padx=20, pady=10, fill="x")
        f_man = ctk.CTkFrame(self.tab_dl, fg_color="#252525"); f_man.pack(padx=20, pady=10, fill="x")
        self.entry_id = ctk.CTkEntry(f_man, placeholder_text="MODEL ID", height=40); self.entry_id.pack(padx=10, side="left", expand=True, fill="x")
        self.option_type = ctk.CTkOptionMenu(f_man, values=["checkpoints", "loras", "vae"], width=120); self.option_type.pack(padx=10, side="left")
        self.btn_dl = ctk.CTkButton(self.tab_dl, text="DOWNLOAD TARGET", command=self.start_download, height=45); self.btn_dl.pack(padx=20, pady=10, fill="x")
        self.log_acquisition = ctk.CTkTextbox(self.tab_dl, height=250, font=("Consolas", 12), fg_color="#0d0d0d"); self.log_acquisition.pack(padx=20, pady=10, fill="both", expand=True)

    def setup_inventory_tab(self):
        self.inv_list = ctk.CTkTextbox(self.tab_models, font=("Consolas", 12), fg_color="#0d0d0d")
        self.inv_list.pack(padx=20, pady=20, fill="both", expand=True)
        ctk.CTkButton(self.tab_models, text="REFRESH INVENTORY", command=self.refresh_models_list).pack(pady=10)

    def setup_training_tab(self):
        f_config = ctk.CTkFrame(self.tab_train, fg_color="#252525", corner_radius=10)
        f_config.pack(padx=20, pady=10, fill="x")
        self.train_base_model = ctk.CTkEntry(f_config, placeholder_text="BASE MODEL PATH", height=35); self.train_base_model.pack(padx=20, pady=5, fill="x")
        self.train_lora_name = ctk.CTkEntry(f_config, placeholder_text="OUTPUT LORA NAME", height=35); self.train_lora_name.pack(padx=20, pady=5, fill="x")
        f_wizard = ctk.CTkFrame(self.tab_train, fg_color="#1a1a1a", border_width=1, border_color="#333")
        f_wizard.pack(padx=20, pady=10, fill="x")
        self.entry_trigger = ctk.CTkEntry(f_wizard, placeholder_text="TRIGGER WORD", height=35); self.entry_trigger.pack(padx=20, pady=10, side="left", expand=True, fill="x")
        ctk.CTkButton(f_wizard, text="MAGO DATASET", command=self.dataset_wizard, width=120, fg_color="#4B0082").pack(padx=10, side="left")
        self.btn_start_train = ctk.CTkButton(self.tab_train, text="🚀 START INDUSTRIAL TRAINING", command=self.start_training, height=45, fg_color="#FF8C00")
        self.btn_start_train.pack(padx=20, pady=10, fill="x")
        self.log_train = ctk.CTkTextbox(self.tab_train, height=200, font=("Consolas", 11), fg_color="#0d0d0d")
        self.log_train.pack(padx=20, pady=10, fill="both", expand=True)

    def setup_vault_tab(self):
        f_add = ctk.CTkFrame(self.tab_settings, fg_color="transparent")
        f_add.pack(padx=20, pady=20, fill="x")
        self.entry_api = ctk.CTkEntry(f_add, placeholder_text="Paste Civitai API Key...", show="*", height=40); self.entry_api.pack(pady=10, fill="x")
        ctk.CTkButton(f_add, text="ADD TO VAULT", command=self.save_api_key).pack(pady=5, fill="x")
        self.api_list_frame = ctk.CTkScrollableFrame(self.tab_settings, height=250, fg_color="#1a1a1a"); self.api_list_frame.pack(padx=20, pady=5, fill="both", expand=True)

    def apply_preset(self, choice):
        p = PRESET_MODELS.get(choice)
        if p and p["id"]: self.entry_id.delete(0, "end"); self.entry_id.insert(0, p["id"]); self.option_type.set(p["type"])

    def refresh_api_ui(self):
        for w in self.api_list_frame.winfo_children(): w.destroy()
        for key in self.saved_apis:
            f = ctk.CTkFrame(self.api_list_frame, fg_color="#252525"); f.pack(fill="x", pady=2)
            ctk.CTkLabel(f, text=f"🔑 {key[:8]}...{key[-4:]}", font=("Consolas", 12)).pack(side="left", padx=15, pady=5)
            ctk.CTkButton(f, text="REMOVE", width=60, height=24, fg_color="#444", command=lambda k=key: self.remove_api_key(k)).pack(side="right", padx=10, pady=5)

    def save_api_key(self):
        key = self.entry_api.get().strip()
        if not key: return
        if key not in self.saved_apis:
            self.saved_apis.append(key)
            self.persist_config(); self.refresh_api_ui()
            messagebox.showinfo("Vault", "Chave salva com sucesso!")
        self.entry_api.delete(0, "end")

    def remove_api_key(self, key):
        if key in self.saved_apis: self.saved_apis.remove(key); self.persist_config(); self.refresh_api_ui()

    def persist_config(self):
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w') as f: json.dump({"api_keys": self.saved_apis}, f, indent=4)

    def load_config(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    d = json.load(f)
                    self.saved_apis = d.get("api_keys", [])
                    old = d.get("civitai_api_key")
                    if old and old not in self.saved_apis: self.saved_apis.append(old)
                self.refresh_api_ui()
            except: pass

    def refresh_models_list(self):
        self.inv_list.delete("1.0", "end")
        u = set()
        if MODELS_DIR.exists():
            for root, dirs, files in os.walk(MODELS_DIR):
                for f in files:
                    if f.endswith((".safetensors", ".ckpt")): u.add(f)
            for m in sorted(list(u)): self.inv_list.insert("end", f"● {m}\n")
        if not u: self.inv_list.insert("end", "Inventory Empty.")

    def kill_port(self, port):
        try:
            if os.name == "nt": subprocess.run(f"powershell -Command \"Stop-Process -Id (Get-NetTCPConnection -LocalPort {port}).OwningProcess -Force\"", shell=True, capture_output=True)
            else: subprocess.run(["fuser", "-k", f"{port}/tcp"], capture_output=True)
        except: pass

    def start_studio(self):
        if self.process is None:
            self.kill_port(8188); time.sleep(1)
            main = ENGINE_DIR / "main.py"
            if not main.exists(): return
            py = get_short_path(VENV_PATH / ("Scripts/python.exe" if os.name == "nt" else "bin/python3"))
            args = [str(py), str(main), "--input-directory", str(BASE_DIR_PATH / "workspace/input"), "--output-directory", str(BASE_DIR_PATH / "workspace/output"), "--listen", "127.0.0.1", "--port", "8188", "--lowvram"]
            try:
                if os.name == "nt":
                    flat = ' '.join([f'"{a}"' for a in args])
                    self.process = subprocess.Popen(f'start "AI CORE" cmd /k {flat}', shell=True, cwd=str(BASE_DIR_PATH))
                else:
                    log_f = open(ENGINE_DIR / "comfyui_stealth.log", "w")
                    self.process = subprocess.Popen(args, stdout=log_f, stderr=log_f, cwd=str(BASE_DIR_PATH))
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
            on = s.connect_ex(('127.0.0.1', 8188)) == 0
            self.status_indicator.configure(text="● SYSTEM OPERATIONAL" if on else "● SYSTEM OFFLINE", text_color="#44ff44" if on else "#ff4444")
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
        messagebox.showinfo("Wizard", f"Dataset industrial criado!")

    def start_download(self):
        m_id = self.entry_id.get().strip(); m_type = self.option_type.get()
        if m_id: threading.Thread(target=self.run_downloader, args=(m_id, m_type), daemon=True).start()

    def run_downloader(self, m_id, m_type):
        py = get_short_path(VENV_PATH / ("Scripts/python.exe" if os.name == "nt" else "bin/python3"))
        dl = get_short_path(TOOLS_DIR / "downloader.py"); key = self.saved_apis[-1] if self.saved_apis else ""
        cmd = [str(py), str(dl), m_id, m_type]; env = os.environ.copy()
        if key: env["CIVITAI_API_KEY"] = key
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)
        for line in proc.stdout: self.log_acquisition.insert("end", f"[{time.strftime('%H:%M:%S')}] {line.strip()}\n"); self.log_acquisition.see("end")
        proc.wait(); self.after(500, self.refresh_models_list)

    def start_training(self):
        m_base = self.train_base_model.get().strip(); out_name = self.train_lora_name.get().strip(); trigger = self.entry_trigger.get().strip()
        if not all([m_base, out_name, trigger]): messagebox.showwarning("Erro", "Preencha tudo!"); return
        threading.Thread(target=self.run_training_process, args=(m_base, out_name, trigger), daemon=True).start()

    def run_training_process(self, m_base, out_name, trigger):
        self.log_train.insert("end", f"[{time.strftime('%H:%M:%S')}] AQUECENDO MOTOR DE TREINO...\n")
        py = get_short_path(VENV_PATH / ("Scripts/python.exe" if os.name == "nt" else "bin/python3"))
        script = get_short_path(TOOLS_DIR / "sd-scripts" / "train_network.py")
        data_dir = str(BASE_DIR_PATH / "workspace/training_data" / trigger / "img")
        output_dir = str(MODELS_DIR / "loras")
        cmd = [str(py), str(script), "--pretrained_model_name_or_path", str(m_base), "--train_data_dir", data_dir, "--output_dir", output_dir, "--output_name", out_name, "--resolution", "512,512", "--train_batch_size", "1", "--max_train_steps", "1000", "--learning_rate", "1e-4", "--network_module", "networks.lora", "--xformers", "--mixed_precision", "fp16", "--gradient_checkpointing"]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout: self.log_train.insert("end", line); self.log_train.see("end")
        proc.wait()
        if proc.returncode == 0: self.log_train.insert("end", f"\n[V] TREINO CONCLUÍDO!\n"); self.after(500, self.refresh_models_list)
        else: self.log_train.insert("end", "\n[X] FALHA NO TREINAMENTO.\n")

if __name__ == "__main__":
    app = App(); app.mainloop()
