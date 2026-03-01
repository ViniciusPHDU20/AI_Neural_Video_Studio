import os
import sys
import subprocess
import ctypes
from pathlib import Path

# --- FUNÇÃO DE BLINDAGEM DE CAMINHO (Short Path 8.3) ---
def get_short_path(path):
    if os.name != "nt":
        return str(path)
    try:
        output_buf = ctypes.create_unicode_buffer(1024)
        ctypes.windll.kernel32.GetShortPathNameW(str(path), output_buf, 1024)
        return output_buf.value
    except:
        return str(path)

# Normalizar Diretório Base
BASE_DIR = Path(__file__).parent.absolute()
BASE_DIR_SHORT = get_short_path(BASE_DIR)
VENV_PATH = Path(BASE_DIR_SHORT) / ".venv"

def check_venv():
    if hasattr(sys, 'real_prefix') or (sys.base_prefix != sys.prefix):
        return
    
    if os.name == "nt":
        venv_python = VENV_PATH / "Scripts" / "python.exe"
    else:
        venv_python = VENV_PATH / "bin" / "python3"

    if venv_python.exists():
        print(f"[*] Reiniciando via Caminho Blindado: {venv_python}")
        # Reiniciar usando o executável curto para evitar erros de sintaxe
        subprocess.Popen([str(venv_python)] + sys.argv)
        sys.exit(0)

check_venv()
# -------------------------------------------------------

import tkinter as tk
import customtkinter as ctk
import threading
import json
import socket
from tkinter import messagebox

VERSION = "1.3.8 (Nuclear Path Patch)"

# Configurações de Estilo Moderno
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

SCRIPTS_DIR = Path(BASE_DIR_SHORT) / "scripts"
TOOLS_DIR = Path(BASE_DIR_SHORT) / "tools"
ENGINE_DIR = Path(BASE_DIR_SHORT) / "engine"
MODELS_DIR = Path(BASE_DIR_SHORT) / "models"
CONFIG_FILE = Path(BASE_DIR_SHORT) / "config" / "user_config.json"

PRESET_MODELS = {
    "Selecione um Preset...": {"id": "", "type": "checkpoints", "nsfw": False},
    "[BASE] Pony Diffusion V6 XL": {"id": "290640", "type": "checkpoints", "nsfw": True},
    "[BASE] RealVisXL V4.0 (Realismo)": {"id": "139562", "type": "checkpoints", "nsfw": False},
    "[BASE] Juggernaut XL (Cinematic)": {"id": "133005", "type": "checkpoints", "nsfw": False},
    "[LORA] Realistic Skin & Details": {"id": "356417", "type": "loras", "nsfw": False},
    "[LORA] Cinematic Lighting": {"id": "341513", "type": "loras", "nsfw": False},
    "[LORA] Detailed Anatomy XL": {"id": "364522", "type": "loras", "nsfw": True}
}

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"AI Neural Video Studio V{VERSION}")
        self.geometry("850x650")
        self.process = None

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=180, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="AI STUDIO", font=ctk.CTkFont(size=22, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        self.status_indicator = ctk.CTkLabel(self.sidebar_frame, text="● ENGINE OFFLINE", text_color="red")
        self.status_indicator.grid(row=1, column=0, padx=20, pady=10)
        self.start_button = ctk.CTkButton(self.sidebar_frame, text="LIGAR ENGINE", command=self.start_studio, fg_color="#228B22")
        self.start_button.grid(row=2, column=0, padx=20, pady=10)
        self.stop_button = ctk.CTkButton(self.sidebar_frame, text="DESLIGAR", command=self.stop_studio, fg_color="#B22222")
        self.stop_button.grid(row=3, column=0, padx=20, pady=10)

        # Tabs
        self.tabview = ctk.CTkTabview(self, width=600)
        self.tabview.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.tabview.add("Download")
        self.tabview.add("Gerenciar Modelos")
        self.tabview.add("Treinamento LoRA")
        self.tabview.add("Configurações")

        # Config Tab 1
        self.preset_menu = ctk.CTkOptionMenu(self.tabview.tab("Download"), values=list(PRESET_MODELS.keys()), command=self.apply_preset)
        self.preset_menu.pack(pady=10, padx=20, fill="x")
        self.model_id_entry = ctk.CTkEntry(self.tabview.tab("Download"), placeholder_text="ID Civitai Manual")
        self.model_id_entry.pack(pady=10, padx=20, fill="x")
        self.download_btn = ctk.CTkButton(self.tabview.tab("Download"), text="BAIXAR MODELO", command=self.start_download)
        self.download_btn.pack(pady=10)
        self.log_textbox = ctk.CTkTextbox(self.tabview.tab("Download"), height=200)
        self.log_textbox.pack(pady=10, padx=20, fill="both")

        # Config Tab 2
        self.models_listbox = ctk.CTkTextbox(self.tabview.tab("Gerenciar Modelos"), height=300)
        self.models_listbox.pack(pady=10, padx=20, fill="both")
        self.refresh_btn = ctk.CTkButton(self.tabview.tab("Gerenciar Modelos"), text="ATUALIZAR", command=self.refresh_models_list)
        self.refresh_btn.pack(pady=10)

        # Config Tab 3 (Treinamento)
        self.wizard_trigger = ctk.CTkEntry(self.tabview.tab("Treinamento LoRA"), placeholder_text="Palavra-Gatilho")
        self.wizard_trigger.pack(pady=10, padx=20, fill="x")
        self.wizard_btn = ctk.CTkButton(self.tabview.tab("Treinamento LoRA"), text="MAGO DO DATASET", command=self.dataset_wizard, fg_color="#4B0082")
        self.wizard_btn.pack(pady=5)
        self.train_btn = ctk.CTkButton(self.tabview.tab("Treinamento LoRA"), text="INICIAR TREINO", command=self.start_training, fg_color="#FF8C00")
        self.train_btn.pack(pady=10)

        self.check_status_loop()
        self.refresh_models_list()

    def log(self, message):
        self.log_textbox.insert("end", f"[*] {message}\n")
        self.log_textbox.see("end")

    def apply_preset(self, choice):
        p = PRESET_MODELS.get(choice)
        if p and p["id"]: self.model_id_entry.delete(0, "end"); self.model_id_entry.insert(0, p["id"])

    def start_download(self):
        m_id = self.model_id_entry.get().strip()
        if m_id: threading.Thread(target=self.run_downloader, args=(m_id,), daemon=True).start()

    def run_downloader(self, m_id):
        py = get_short_path(VENV_PATH / "Scripts" / "python.exe") if os.name == "nt" else "python3"
        dl = get_short_path(TOOLS_DIR / "downloader.py")
        cmd = [py, dl, m_id, "checkpoints"]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout: self.log(line.strip())
        proc.wait()
        self.refresh_models_list()

    def refresh_models_list(self):
        self.models_listbox.delete("1.0", "end")
        for root, dirs, files in os.walk(MODELS_DIR):
            for f in files:
                if f.endswith((".safetensors", ".ckpt")):
                    self.models_listbox.insert("end", f"● {f}\n")

    def dataset_wizard(self):
        trigger = self.wizard_trigger.get().strip()
        if not trigger: return
        src = ctk.filedialog.askdirectory()
        if not src: return
        dst = BASE_DIR / "workspace" / "training_data" / trigger / "img" / f"15_{trigger}"
        dst.mkdir(parents=True, exist_ok=True)
        import shutil
        for i, f in enumerate(os.listdir(src)):
            if f.lower().endswith((".jpg", ".png", ".webp")):
                shutil.copy2(Path(src)/f, dst/f"{trigger}_{i:03d}{Path(f).suffix}")
                with open(dst/f"{trigger}_{i:03d}.txt", "w") as tf: tf.write(trigger)
        messagebox.showinfo("Sucesso", "Dataset Criado!")

    def start_training(self):
        messagebox.showinfo("Treino", "Iniciando motor de treino no log...")

    def start_studio(self):
        if self.process is None:
            py = get_short_path(VENV_PATH / "Scripts" / "python.exe") if os.name == "nt" else "python3"
            main = get_short_path(ENGINE_DIR / "main.py")
            
            args = [
                py, main,
                "--input-directory", get_short_path(BASE_DIR / "workspace" / "input"),
                "--output-directory", get_short_path(BASE_DIR / "workspace" / "output"),
                "--listen", "127.0.0.1", "--port", "8188", "--lowvram"
            ]

            try:
                # No Windows, usamos o caminho 8.3 para evitar QUALQUER erro de aspas/sintaxe
                self.log("Ignition... Motor Blindado subindo.")
                if os.name == "nt":
                    self.process = subprocess.Popen(args, creationflags=subprocess.CREATE_NEW_CONSOLE, cwd=BASE_DIR_SHORT)
                else:
                    self.process = subprocess.Popen(args, stdout=subprocess.DEVNULL)
            except Exception as e:
                messagebox.showerror("Erro", str(e))

    def stop_studio(self):
        if self.process:
            if os.name == "nt": subprocess.run(["taskkill", "/F", "/T", "/PID", str(self.process.pid)], capture_output=True)
            else: self.process.terminate()
            self.process = None

    def check_status_loop(self):
        def check():
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            res = s.connect_ex(('127.0.0.1', 8188))
            self.status_indicator.configure(text="● ENGINE ONLINE" if res == 0 else "● ENGINE OFFLINE", text_color="green" if res == 0 else "red")
            s.close()
            self.after(5000, check)
        self.after(2000, check)

if __name__ == "__main__":
    app = App()
    app.mainloop()
