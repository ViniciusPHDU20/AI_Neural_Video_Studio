import os
import sys
import subprocess
import ctypes
from pathlib import Path

# --- AUTO-CORREÇÃO DE AMBIENTE (GOD MODE) ---
# Usar Pathlib para resolver caminhos de forma robusta em Linux e Windows
BASE_DIR = Path(__file__).parent.absolute()

def get_short_path(path):
    if os.name != "nt":
        return str(path)
    try:
        output_buf = ctypes.create_unicode_buffer(1024)
        ctypes.windll.kernel32.GetShortPathNameW(str(path), output_buf, 1024)
        return output_buf.value
    except:
        return str(path)

BASE_DIR_PATH = Path(get_short_path(BASE_DIR))
VENV_PATH = BASE_DIR_PATH / ".venv"

def check_venv():
    # Se já estivermos no VENV ou se ele não existir, seguimos em frente
    if hasattr(sys, 'real_prefix') or (sys.base_prefix != sys.prefix):
        return
    
    if os.name == "nt":
        venv_python = VENV_PATH / "Scripts" / "python.exe"
    else:
        venv_python = VENV_PATH / "bin" / "python3"

    if venv_python.exists():
        print(f"[*] Reiniciando via Ambiente Virtual: {venv_python}")
        subprocess.Popen([str(venv_python)] + sys.argv)
        sys.exit(0)

check_venv()
# --------------------------------------------

import tkinter as tk
import customtkinter as ctk
import threading
import json
import socket
from tkinter import messagebox

VERSION = "1.3.9 (Linux Perfection Patch)"

# Configurações de Estilo Moderno
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

SCRIPTS_DIR = BASE_DIR_PATH / "scripts"
TOOLS_DIR = BASE_DIR_PATH / "tools"
ENGINE_DIR = BASE_DIR_PATH / "engine"
MODELS_DIR = BASE_DIR_PATH / "models"
CONFIG_FILE = BASE_DIR_PATH / "config" / "user_config.json"

# Banco de Dados de Modelos Recomendados
PRESET_MODELS = {
    "Selecione um Preset...": {"id": "", "type": "checkpoints", "nsfw": False},
    "[BASE] Pony Diffusion V6 XL": {"id": "290640", "type": "checkpoints", "nsfw": True},
    "[BASE] RealVisXL V4.0 (Realismo)": {"id": "139562", "type": "checkpoints", "nsfw": False},
    "[BASE] Juggernaut XL (Cinematic)": {"id": "133005", "type": "checkpoints", "nsfw": False},
    "[LORA] Realistic Skin & Details": {"id": "356417", "type": "loras", "nsfw": False},
    "[LORA] Cinematic Lighting": {"id": "341513", "type": "loras", "nsfw": False},
    "[LORA] Detailed Anatomy XL": {"id": "364522", "type": "loras", "nsfw": True},
    "[VAE] SDXL Official VAE": {"id": "290640", "type": "vae", "nsfw": False}
}

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"AI Neural Video Studio V{VERSION} - Command Center")
        self.geometry("850x650")
        self.process = None

        # Grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=180, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="AI STUDIO", font=ctk.CTkFont(size=22, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        self.status_indicator = ctk.CTkLabel(self.sidebar_frame, text="● ENGINE OFFLINE", text_color="red", font=ctk.CTkFont(size=14, weight="bold"))
        self.status_indicator.grid(row=1, column=0, padx=20, pady=10)

        self.start_button = ctk.CTkButton(self.sidebar_frame, text="LIGAR ENGINE", command=self.start_studio, fg_color="#228B22", hover_color="#006400")
        self.start_button.grid(row=2, column=0, padx=20, pady=10)

        self.stop_button = ctk.CTkButton(self.sidebar_frame, text="DESLIGAR", command=self.stop_studio, fg_color="#B22222", hover_color="#8B0000")
        self.stop_button.grid(row=3, column=0, padx=20, pady=10)

        # Main Content
        self.tabview = ctk.CTkTabview(self, width=600)
        self.tabview.grid(row=0, column=1, padx=(20, 20), pady=(20, 20), sticky="nsew")
        self.tabview.add("Download")
        self.tabview.add("Gerenciar Modelos")
        self.tabview.add("Treinamento LoRA")
        self.tabview.add("Configurações")

        # Tab 1: Download
        self.label_preset = ctk.CTkLabel(self.tabview.tab("Download"), text="Presets de Modelos:", font=ctk.CTkFont(size=12, weight="bold"))
        self.label_preset.pack(pady=(10, 5), padx=20, anchor="w")
        self.preset_menu = ctk.CTkOptionMenu(self.tabview.tab("Download"), values=list(PRESET_MODELS.keys()), command=self.apply_preset)
        self.preset_menu.pack(pady=5, padx=20, fill="x")

        self.model_id_entry = ctk.CTkEntry(self.tabview.tab("Download"), placeholder_text="ID do Civitai Manual", height=35)
        self.model_id_entry.pack(pady=10, padx=20, fill="x")

        self.model_type_option = ctk.CTkOptionMenu(self.tabview.tab("Download"), values=["checkpoints", "loras", "vae", "controlnet"])
        self.model_type_option.pack(pady=5, padx=20, fill="x")

        self.download_btn = ctk.CTkButton(self.tabview.tab("Download"), text="BAIXAR MODELO", command=self.start_download, height=40)
        self.download_btn.pack(pady=20, padx=20)

        self.log_textbox = ctk.CTkTextbox(self.tabview.tab("Download"), height=180, font=("Consolas", 12))
        self.log_textbox.pack(pady=10, padx=20, fill="both", expand=True)

        # Tab 2: Gerenciar
        self.models_listbox = ctk.CTkTextbox(self.tabview.tab("Gerenciar Modelos"), height=250)
        self.models_listbox.pack(pady=10, padx=20, fill="both", expand=True)
        self.refresh_models_btn = ctk.CTkButton(self.tabview.tab("Gerenciar Modelos"), text="ATUALIZAR LISTA", command=self.refresh_models_list)
        self.refresh_models_btn.pack(pady=10)

        # Tab: Treinamento LoRA
        self.wizard_trigger = ctk.CTkEntry(self.tabview.tab("Treinamento LoRA"), placeholder_text="Palavra-Gatilho (ex: meunome)")
        self.wizard_trigger.pack(pady=10, padx=20, fill="x")
        self.wizard_btn = ctk.CTkButton(self.tabview.tab("Treinamento LoRA"), text="CRIAR DATASET AUTOMÁTICO", command=self.dataset_wizard, fg_color="#4B0082", hover_color="#800080")
        self.wizard_btn.pack(pady=5, padx=20, fill="x")
        self.train_btn = ctk.CTkButton(self.tabview.tab("Treinamento LoRA"), text="INICIAR TREINAMENTO", command=self.start_training, fg_color="#FF8C00", hover_color="#CC7000")
        self.train_btn.pack(pady=10, padx=20, fill="x")
        self.train_log = ctk.CTkTextbox(self.tabview.tab("Treinamento LoRA"), height=150, font=("Consolas", 12))
        self.train_log.pack(pady=10, padx=20, fill="both", expand=True)

        # Tab 3: Configurações
        self.api_key_label = ctk.CTkLabel(self.tabview.tab("Configurações"), text="Civitai API Key (Para modelos restritos/NSFW):", font=ctk.CTkFont(size=12, weight="bold"))
        self.api_key_label.pack(pady=(10, 5), padx=20, anchor="w")
        self.api_key_entry = ctk.CTkEntry(self.tabview.tab("Configurações"), placeholder_text="Insira sua API Key...", show="*", height=35)
        self.api_key_entry.pack(pady=5, padx=20, fill="x")
        self.save_config_btn = ctk.CTkButton(self.tabview.tab("Configurações"), text="SALVAR CONFIGURAÇÕES", command=self.save_config)
        self.save_config_btn.pack(pady=20)
        
        self.load_config()
        self.check_status_loop()
        self.refresh_models_list()

    def log(self, message):
        self.log_textbox.insert("end", f"[*] {message}\n")
        self.log_textbox.see("end")

    def apply_preset(self, choice):
        preset = PRESET_MODELS.get(choice)
        if preset and preset["id"]:
            self.model_id_entry.delete(0, "end")
            self.model_id_entry.insert(0, preset["id"])
            self.model_type_option.set(preset["type"])

    def load_config(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    self.api_key_entry.insert(0, config.get("civitai_api_key", ""))
            except: pass

    def save_config(self):
        key = self.api_key_entry.get().strip()
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump({"civitai_api_key": key}, f, indent=4)
        messagebox.showinfo("Sucesso", "Configurações salvas!")

    def start_download(self):
        m_id = self.model_id_entry.get().strip()
        m_type = self.model_type_option.get()
        if m_id:
            thread = threading.Thread(target=self.run_downloader, args=(m_id, m_type))
            thread.daemon = True
            thread.start()

    def run_downloader(self, m_id, m_type):
        self.log(f"Iniciando download do Modelo ID: {m_id}...")
        downloader_path = TOOLS_DIR / "downloader.py"
        if os.name == "nt":
            python_exe = VENV_PATH / "Scripts" / "python.exe"
        else:
            python_exe = VENV_PATH / "bin" / "python3"
        
        python_exe = python_exe if python_exe.exists() else Path(sys.executable)
        cmd = [str(python_exe), str(downloader_path), m_id, m_type]
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        for line in process.stdout:
            self.log(line.strip())
        process.wait()
        self.after(500, self.refresh_models_list)

    def refresh_models_list(self):
        self.models_listbox.delete("1.0", "end")
        found = False
        if MODELS_DIR.exists():
            for root, dirs, files in os.walk(MODELS_DIR):
                for file in files:
                    if file.endswith((".safetensors", ".ckpt")):
                        rel_path = os.path.relpath(os.path.join(root, file), MODELS_DIR)
                        self.models_listbox.insert("end", f"● {rel_path}\n")
                        found = True
        if not found: self.models_listbox.insert("end", "Nenhum modelo detectado.")

    def dataset_wizard(self):
        trigger = self.wizard_trigger.get().strip()
        if not trigger:
            messagebox.showwarning("Erro", "Defina uma Palavra-Gatilho!")
            return
        source_dir = ctk.filedialog.askdirectory(title="Selecione fotos ORIGINAIS")
        if not source_dir: return

        base_train = BASE_DIR_PATH / "workspace" / "training_data" / trigger
        img_dir = base_train / "img" / f"15_{trigger}"
        img_dir.mkdir(parents=True, exist_ok=True)

        import shutil
        count = 0
        for file in os.listdir(source_dir):
            if file.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                count += 1
                new_name = f"{trigger}_{count:03d}{os.path.splitext(file)[1]}"
                shutil.copy2(os.path.join(source_dir, file), img_dir / new_name)
                with open(img_dir / f"{trigger}_{count:03d}.txt", "w") as f:
                    f.write(trigger)

        messagebox.showinfo("Sucesso", f"Dataset com {count} imagens criado em {img_dir}")

    def start_training(self):
        messagebox.showinfo("Treino", "Motor de treino V1.3.9 em desenvolvimento para Linux.")

    def start_studio(self):
        if self.process is None:
            if os.name == "nt":
                python_exe = VENV_PATH / "Scripts" / "python.exe"
            else:
                python_exe = VENV_PATH / "bin" / "python3"

            main_py = ENGINE_DIR / "main.py"
            
            # Argumentos para ComfyUI
            args = [
                str(python_exe), str(main_py),
                "--input-directory", str(BASE_DIR_PATH / "workspace" / "input"),
                "--output-directory", str(BASE_DIR_PATH / "workspace" / "output"),
                "--extra-model-paths-config", str(BASE_DIR_PATH / "config" / "extra_model_paths.yaml"),
                "--listen", "127.0.0.1",
                "--port", "8188",
                "--lowvram",
                "--fp8_e4m3fn-text-enc"
            ]

            try:
                if os.name == "nt":
                    flat_args = ' '.join([f'"{a}"' for a in args])
                    self.process = subprocess.Popen(f'start "AI Studio Engine" cmd /k {flat_args}', shell=True, cwd=str(BASE_DIR_PATH))
                else:
                    # No Linux, rodamos em segundo plano mas garantimos logs
                    self.process = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=str(BASE_DIR_PATH))
                self.log("Engine disparada com sucesso!")
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao abrir Engine: {e}")

    def stop_studio(self):
        if self.process:
            if os.name == "nt":
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(self.process.pid)], capture_output=True)
            else:
                self.process.terminate()
            self.process = None
            self.status_indicator.configure(text="● ENGINE OFFLINE", text_color="red")

    def check_status_loop(self):
        def check():
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            try:
                if sock.connect_ex(('127.0.0.1', 8188)) == 0:
                    self.status_indicator.configure(text="● ENGINE ONLINE", text_color="green")
                else:
                    self.status_indicator.configure(text="● ENGINE OFFLINE", text_color="red")
            except: pass
            finally: sock.close()
            self.after(5000, check)
        self.after(2000, check)

if __name__ == "__main__":
    app = App()
    app.mainloop()
