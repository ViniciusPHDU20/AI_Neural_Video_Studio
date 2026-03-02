import os, sys, subprocess, ctypes, threading, json, socket, time, re, requests
from pathlib import Path
try: import psutil
except: psutil = None
from tkinter import messagebox
from PIL import Image
import customtkinter as ctk

# --- ENVIRONMENT & PATHS ---
FILE_PATH = Path(__file__).resolve()
BASE_DIR = FILE_PATH.parent.parent
VENV_PATH = BASE_DIR / ".venv"
VERSION = "4.0.5 (Enterprise Stabilized)"
ctk.set_appearance_mode("Dark"); ctk.set_default_color_theme("dark-blue")

ENGINE_DIR, MODELS_DIR = BASE_DIR / "engine", BASE_DIR / "models"
CONFIG_DIR, WORKSPACE_DIR, TOOLS_DIR = BASE_DIR / "config", BASE_DIR / "workspace", BASE_DIR / "tools"
CONFIG_FILE, VAULT_FILE = CONFIG_DIR / "user_config.json", CONFIG_DIR / "vault.json"
OUTPUT_DIR, WORKFLOWS_DIR = WORKSPACE_DIR / "output", WORKSPACE_DIR / "workflows"
ENGINE_LOG = ENGINE_DIR / "comfyui_stealth.log"

GPU_DATABASE = {
    "NVIDIA": {"RTX 3060 Ti / 4060 (8GB)": "--normalvram --use-split-cross-attention --fp8_e4m3fn-text-enc", "High-End (12GB+)": "--gpu-only --use-split-cross-attention"},
    "AMD": {"RX Series": "--directml --normalvram"}, "CPU": {"Basic": "--cpu"}
}
RAM_PROFILES = {"Max Performance": "", "Balanced (Standard)": "--normalvram", "Economy Saver": "--lowvram"}

PRESET_MODELS = {
    "● [VIDEO] Wan 2.1 T2V (GGUF)": {"repo": "city96/Wan2.1-T2V-14B-gguf", "file": "wan2.1-t2v-14b-Q4_K_M.gguf", "type": "checkpoints", "source": "hf"},
    "● [VIDEO] Wan 2.1 I2V (GGUF)": {"repo": "city96/Wan2.1-I2V-14B-720P-gguf", "file": "wan2.1-i2v-14b-720p-Q4_K_M.gguf", "type": "checkpoints", "source": "hf"},
    "● [CORE] T5 Encoder (GGUF)": {"repo": "city96/t5-v1_1-xxl-encoder-gguf", "file": "t5-v1_1-xxl-encoder-Q4_K_M.gguf", "type": "clip", "source": "hf"},
    "● [CORE] VAE Wan 2.1": {"repo": "Kijai/WanVideo_comfy", "file": "Wan2_1_VAE_fp32.safetensors", "type": "vae", "source": "hf"},
    "● [STYLE] MaouBig V1.2 (Anime)": {"id": "164827", "type": "checkpoints", "source": "civitai"},
    "● [BASE] Pony XL": {"id": "290640", "type": "checkpoints", "source": "civitai"}
}

class App(ctk.CTk):
    def __init__(self):
        super().__init__(); self.title(f"AI STUDIO | {VERSION}"); self.geometry("1450x920")
        self.process, self.saved_apis, self.console_active = None, [], True
        self.detected_vendor, self.active_profile, self.active_model_path = "CPU", "", None
        self.active_ram_profile, self.active_preset, self.active_wf_path = "Balanced (Standard)", {}, None
        
        self.grid_columnconfigure(1, weight=1); self.grid_rowconfigure(0, weight=1)
        self.sidebar = ctk.CTkFrame(self, width=250, fg_color="#0b0b0b"); self.sidebar.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(self.sidebar, text="NEURAL STUDIO", font=("Orbitron", 22, "bold"), text_color="#00a8ff").pack(pady=30)
        self.btn_studio = ctk.CTkButton(self.sidebar, text="LAUNCH STUDIO", command=self.start_studio, fg_color="#27ae60", font=("Roboto", 14, "bold")); self.btn_studio.pack(pady=10, padx=20, fill="x")
        self.btn_stop = ctk.CTkButton(self.sidebar, text="STOP ENGINE", command=self.stop_studio, fg_color="#c0392b"); self.btn_stop.pack(pady=5, padx=20, fill="x")
        self.status_indicator = ctk.CTkLabel(self.sidebar, text="● OFFLINE", font=("Consolas", 12), text_color="#ff4444"); self.status_indicator.pack(pady=10)
        
        self.setup_telemetry_ui()
        self.tabs = ctk.CTkTabview(self); self.tabs.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.tab_acq = self.tabs.add("ACQUISITION"); self.tab_blue = self.tabs.add("BLUEPRINTS"); self.tab_gal = self.tabs.add("GALLERY")
        self.tab_vault = self.tabs.add("VAULT"); self.tab_opt = self.tabs.add("OPTIMIZER"); self.tab_log = self.tabs.add("CONSOLE")
        
        self.setup_acq_tab(); self.setup_blueprints_tab(); self.setup_gal_tab(); self.setup_vault_tab(); self.setup_optimizer_tab(); self.setup_console_tab()
        self.load_vault(); self.load_config(); self.detect_hardware(); self.start_loops()
        self.after(1000, self.refresh_models_list); self.after(1500, self.refresh_gallery); self.after(2000, self.refresh_blueprints)

    def setup_telemetry_ui(self):
        f = ctk.CTkFrame(self.sidebar, fg_color="#151515", corner_radius=10); f.pack(padx=10, pady=10, fill="x", side="bottom")
        self.lbl_vram = ctk.CTkLabel(f, text="VRAM: -- MB", text_color="#00a8ff"); self.lbl_vram.pack()
        self.lbl_ram = ctk.CTkLabel(f, text="RAM: -- %", text_color="#e1b12c"); self.lbl_ram.pack()
        self.lbl_cpu = ctk.CTkLabel(f, text="CPU: -- %", text_color="#e1b12c"); self.lbl_cpu.pack()
        self.lbl_disk = ctk.CTkLabel(f, text="DISK: -- GB", text_color="#4cd137"); self.lbl_disk.pack()

    def setup_acq_tab(self):
        f = ctk.CTkFrame(self.tab_acq, fg_color="transparent"); f.pack(fill="both", expand=True, padx=20, pady=20)
        l = ctk.CTkFrame(f, fg_color="transparent"); l.pack(side="left", fill="both", expand=True, padx=(0, 10))
        ctk.CTkLabel(l, text="ACQUISITION CENTER", font=("Orbitron", 18, "bold"), text_color="#00a8ff").pack(anchor="w", pady=(0, 20))
        self.preset_menu = ctk.CTkOptionMenu(l, values=list(PRESET_MODELS.keys()), command=self.apply_preset, height=45); self.preset_menu.pack(pady=10, fill="x")
        self.entry_id = ctk.CTkEntry(l, placeholder_text="Model ID or Repo Path", height=45); self.entry_id.pack(pady=5, fill="x")
        self.option_type = ctk.CTkOptionMenu(l, values=["checkpoints", "loras", "vae", "clip", "unet"], height=45); self.option_type.pack(pady=5, fill="x")
        ctk.CTkButton(l, text="START DOWNLOAD", command=self.start_download, fg_color="#0097e6", height=55, font=("Roboto", 14, "bold")).pack(pady=20, fill="x")
        self.btn_deploy = ctk.CTkButton(l, text="INJECT BLUEPRINT", command=self.inject_active_workflow, fg_color="#8e44ad", height=55, state="disabled", font=("Roboto", 14, "bold")); self.btn_deploy.pack(pady=5, fill="x")
        
        r = ctk.CTkFrame(f, fg_color="#0f0f0f", corner_radius=15); r.pack(side="right", fill="both", expand=True)
        self.inv_scroll = ctk.CTkScrollableFrame(r, label_text="LOCAL ARSENAL", fg_color="transparent"); self.inv_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        self.txt_meta = ctk.CTkTextbox(r, height=120, font=("Consolas", 11), fg_color="#000", text_color="#3ae374"); self.txt_meta.pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(r, text="REMOVE ASSET", command=self.delete_model_action, fg_color="#c0392b").pack(pady=10, padx=10, fill="x")

    def setup_blueprints_tab(self):
        self.blue_scroll = ctk.CTkScrollableFrame(self.tab_blue, label_text="PRODUCTION BLUEPRINTS", fg_color="transparent")
        self.blue_scroll.pack(fill="both", expand=True, padx=20, pady=20)
        ctk.CTkButton(self.tab_blue, text="REFRESH BLUEPRINTS", command=self.refresh_blueprints).pack(pady=10)

    def setup_gal_tab(self):
        f = ctk.CTkFrame(self.tab_gal, fg_color="transparent"); f.pack(fill="both", expand=True)
        self.gal_list = ctk.CTkScrollableFrame(f, width=300, fg_color="#0f0f0f"); self.gal_list.pack(side="left", fill="y", padx=10, pady=10)
        pv = ctk.CTkFrame(f, fg_color="#000", corner_radius=15); pv.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        self.lbl_gal_img = ctk.CTkLabel(pv, text="PREVIEW VIEWPORT", text_color="#444", font=("Roboto", 16)); self.lbl_gal_img.pack(expand=True)
        ctk.CTkButton(self.gal_list, text="REFRESH GALLERY", command=self.refresh_gallery, fg_color="#2c3e50").pack(fill="x", pady=10, padx=10)

    def setup_vault_tab(self):
        f = ctk.CTkFrame(self.tab_vault, fg_color="transparent"); f.pack(padx=50, pady=50, fill="both", expand=True)
        ctk.CTkLabel(f, text="SECURE VAULT", font=("Orbitron", 22, "bold"), text_color="#e1b12c").pack(pady=30)
        self.api_provider = ctk.CTkOptionMenu(f, values=["Civitai (API Key)", "Hugging Face (Token)"], height=50, width=500); self.api_provider.pack(pady=10)
        self.entry_api = ctk.CTkEntry(f, placeholder_text="Insert Key/Token...", show="●", height=50, width=500); self.entry_api.pack(pady=10)
        ctk.CTkButton(f, text="LOCK TO VAULT", command=self.save_api_key, height=55, fg_color="#e1b12c", text_color="#000", font=("Roboto", 14, "bold")).pack(pady=30)
        self.api_list_frame = ctk.CTkScrollableFrame(f, label_text="ENCRYPTED KEYS", fg_color="#0f0f0f", width=500, height=300); self.api_list_frame.pack(pady=10)

    def setup_optimizer_tab(self):
        f = ctk.CTkFrame(self.tab_opt, fg_color="transparent"); f.pack(padx=50, pady=50, fill="both", expand=True)
        ctk.CTkLabel(f, text="ENGINE OPTIMIZER", font=("Orbitron", 22, "bold"), text_color="#9c88ff").pack(pady=30)
        self.gpu_picker = ctk.CTkOptionMenu(f, values=["Detecting..."], command=self.set_profile, height=55, width=600); self.gpu_picker.pack(pady=10)
        self.ram_menu = ctk.CTkOptionMenu(f, values=list(RAM_PROFILES.keys()), command=self.set_ram_profile, height=55, width=600); self.ram_menu.pack(pady=10)
        self.entry_expert = ctk.CTkEntry(f, placeholder_text="Expert Arguments (e.g. --xformers --fp16)", height=55, width=600); self.entry_expert.pack(pady=10)
        self.entry_expert.bind("<KeyRelease>", lambda e: self.update_expert_flags())

    def setup_console_tab(self):
        self.console_box = ctk.CTkTextbox(self.tab_log, font=("Consolas", 12), fg_color="#000", text_color="#3ae374"); self.console_box.pack(fill="both", expand=True, padx=15, pady=15)

    def load_vault(self):
        if VAULT_FILE.exists():
            try:
                with open(VAULT_FILE, 'r') as f: self.saved_apis = json.load(f); self.refresh_api_ui()
            except: self.saved_apis = []

    def persist_vault(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(VAULT_FILE, 'w') as f: json.dump(self.saved_apis, f, indent=4)

    def load_config(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    d = json.load(f); self.active_profile = d.get("hw_profile", ""); self.expert_flags = d.get("expert_flags", ""); self.active_ram_profile = d.get("ram_profile", "Balanced (Standard)")
                if self.expert_flags: self.entry_expert.delete(0, "end"); self.entry_expert.insert(0, self.expert_flags)
                self.ram_menu.set(self.active_ram_profile)
            except: pass

    def persist_config(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        d = {"hw_profile": self.active_profile, "hw_vendor": self.detected_vendor, "expert_flags": self.expert_flags, "ram_profile": self.active_ram_profile}
        with open(CONFIG_FILE, 'w') as f: json.dump(d, f, indent=4)

    def telemetry_loop(self):
        while True:
            try:
                if psutil: 
                    self.lbl_cpu.configure(text=f"CPU: {psutil.cpu_percent()}%"); self.lbl_ram.configure(text=f"RAM: {psutil.virtual_memory().percent}%")
                    self.lbl_disk.configure(text=f"DISK: {psutil.disk_usage(str(MODELS_DIR)).free // (1024**3)} GB FREE")
                vram = "VRAM: -- MB"
                if self.detected_vendor == "NVIDIA":
                    try: out = subprocess.check_output("nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits", shell=True, text=True, timeout=1).strip(); vram = f"VRAM: {out} MB"
                    except: pass
                self.lbl_vram.configure(text=vram)
            except: pass
            time.sleep(2)

    def status_loop(self):
        while True:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.settimeout(1); on = s.connect_ex(('127.0.0.1', 8188)) == 0; s.close()
                self.status_indicator.configure(text="● ONLINE" if on else "● OFFLINE", text_color="#4cd137" if on else "#ff4444")
            except: pass
            time.sleep(3)

    def console_loop(self):
        last_pos = 0
        while self.console_active:
            if ENGINE_LOG.exists():
                size = ENGINE_LOG.stat().st_size
                if size < last_pos: self.console_box.delete("1.0", "end"); last_pos = 0
                if size > last_pos:
                    with open(ENGINE_LOG, "r", encoding="utf-8", errors="ignore") as f:
                        f.seek(last_pos)
                        content = f.read()
                        if content: self.console_box.insert("end", content); self.console_box.see("end")
                        last_pos = f.tell()
            time.sleep(0.2)

    def start_loops(self):
        threading.Thread(target=self.telemetry_loop, daemon=True).start()
        threading.Thread(target=self.status_loop, daemon=True).start()
        threading.Thread(target=self.console_loop, daemon=True).start()

    def start_studio(self):
        if self.process: return
        self.kill_port(8188); time.sleep(1)
        gpu_f = GPU_DATABASE.get(self.detected_vendor, {}).get(self.active_profile, "").split()
        ram_f = RAM_PROFILES.get(self.active_ram_profile, "").split()
        py = str(VENV_PATH / "bin/python3" if os.name != "nt" else VENV_PATH / "Scripts/python.exe")
        args = [py, "-u", str(ENGINE_DIR / "main.py"), "--listen", "127.0.0.1", "--port", "8188", "--extra-model-paths-config", str(CONFIG_DIR / "extra_model_paths.yaml")] + gpu_f + ram_f
        try:
            env = os.environ.copy(); env["PYTHONUNBUFFERED"] = "1"
            self.process = subprocess.Popen(args, stdout=open(ENGINE_LOG, "w"), stderr=subprocess.STDOUT, cwd=str(ENGINE_DIR), env=env)
        except Exception as e: messagebox.showerror("Error", str(e))

    def stop_studio(self):
        self.kill_port(8188); 
        if self.process: self.process.terminate(); self.process = None

    def start_download(self):
        m_id = self.entry_id.get().strip()
        m_type = self.option_type.get()
        if not m_id: return
        threading.Thread(target=self.run_downloader, args=(m_id, m_type), daemon=True).start()

    def run_downloader(self, m_id, m_type):
        py = str(VENV_PATH / "bin/python3" if os.name != "nt" else VENV_PATH / "Scripts/python.exe")
        p = self.active_preset
        
        # Robust source detection
        src = "hf" # Default
        if p and p.get("source"):
            src = p["source"]
        elif "/" in m_id:
            src = "hf"
        else:
            src = "civitai"

        dl_script = TOOLS_DIR / ("hf_downloader.py" if src == "hf" else "downloader.py")
        
        # Build command based on source
        if src == "hf":
            repo = p.get("repo", m_id) if p else m_id
            filename = p.get("file", "") if p else ""
            cmd = [py, "-u", str(dl_script), repo, filename, m_type]
        else:
            model_id = p.get("id", m_id) if p else m_id
            cmd = [py, "-u", str(dl_script), model_id, m_type]

        env = os.environ.copy()
        env["PYTHONWARNINGS"] = "ignore:unsupported version:RequestsDependencyWarning"
        for item in self.saved_apis:
            if "Hugging" in item["provider"]: env["HUGGING_FACE_HUB_TOKEN"] = item["key"]
            if "Civitai" in item["provider"]: env["CIVITAI_API_KEY"] = item["key"]
            
        with open(ENGINE_LOG, "a") as f:
            f.write(f"\n[*] START DOWNLOAD: {m_id} via {src.upper()}\n"); f.flush()
            subprocess.Popen(cmd, env=env, stdout=f, stderr=f).wait()
        self.after(500, self.refresh_models_list)

    def refresh_models_list(self):
        for w in self.inv_scroll.winfo_children(): w.destroy()
        if MODELS_DIR.exists():
            for root, _, files in os.walk(MODELS_DIR):
                for f in sorted(files):
                    if f.endswith((".safetensors", ".ckpt", ".gguf")):
                        path = Path(root) / f
                        ctk.CTkButton(self.inv_scroll, text=f"📦 {f}", anchor="w", fg_color="transparent", 
                                     hover_color="#1e272e", command=lambda p=path: self.load_model_insight(p)).pack(fill="x")

    def refresh_gallery(self):
        for w in self.gal_list.winfo_children(): w.destroy()
        if OUTPUT_DIR.exists():
            for f in sorted(os.listdir(OUTPUT_DIR), reverse=True):
                if f.lower().endswith((".png", ".mp4", ".gif", ".jpg")):
                    path = OUTPUT_DIR / f
                    ctk.CTkButton(self.gal_list, text=f"🎬 {f}", anchor="w", fg_color="transparent", 
                                 hover_color="#1e272e", command=lambda p=path: self.load_gallery_item(p)).pack(fill="x")

    def refresh_blueprints(self):
        for w in self.blue_scroll.winfo_children(): w.destroy()
        if WORKFLOWS_DIR.exists():
            for f in sorted(os.listdir(WORKFLOWS_DIR)):
                if f.endswith(".json"):
                    path = WORKFLOWS_DIR / f
                    ctk.CTkButton(self.blue_scroll, text=f"⚡ DEPLOY: {f}", anchor="w", fg_color="#1e272e", 
                                 hover_color="#8e44ad", command=lambda p=path: self.manual_deploy(p)).pack(fill="x", pady=2)

    def manual_deploy(self, path):
        self.active_wf_path = path
        self.inject_active_workflow()

    def load_model_insight(self, path): 
        self.active_model_path = path; self.txt_meta.delete("1.0", "end")
        self.txt_meta.insert("end", f"ASSET: {path.name}\nTYPE: {path.parent.name}\nPATH: {path}")
        self.load_workflow_preset(path.name)

    def load_workflow_preset(self, model_name):
        wf_name = model_name.split(".")[0] + ".json"
        wf_path = WORKFLOWS_DIR / wf_name
        if wf_path.exists():
            self.active_wf_path = wf_path
            self.btn_deploy.configure(state="normal", text=f"ACTIVATE: {wf_name}", fg_color="#8e44ad")
            self.console_box.insert("end", f"\n[V] Linked Blueprint: {wf_name}\n")
        else:
            self.active_wf_path = None
            self.btn_deploy.configure(state="disabled", text="INJECT BLUEPRINT", fg_color="#333")

    def inject_active_workflow(self):
        if not self.active_wf_path: return
        try:
            with open(self.active_wf_path, "r") as f: wf = json.load(f)
            prompt_data = wf.get("prompt", wf)
            r = requests.post("http://127.0.0.1:8188/prompt", json={"prompt": prompt_data}, timeout=10)
            if r.status_code == 200:
                self.console_box.insert("end", f"\n[V] SUCCESS: Blueprint {self.active_wf_path.name} injected!\n")
                messagebox.showinfo("Neural Studio", "Blueprint Deployed!")
            else:
                self.console_box.insert("end", f"\n[X] Rejected: {r.status_code} - {r.text[:100]}\n")
        except Exception as e:
            self.console_box.insert("end", f"\n[X] Engine Offline: {e}\n")
            messagebox.showerror("Error", "Launch Engine First!")

    def load_gallery_item(self, path):
        try:
            if path.suffix.lower() in [".png", ".jpg"]:
                img = ctk.CTkImage(Image.open(path), size=(450, 450)); self.lbl_gal_img.configure(image=img, text="")
            else: self.lbl_gal_img.configure(image=None, text=f"PREVIEW: {path.name}\n(Video/GIF Support in ComfyUI)")
        except: pass

    def delete_model_action(self):
        if self.active_model_path and messagebox.askyesno("Delete", f"Remove {self.active_model_path.name}?"):
            try: os.remove(self.active_model_path); self.refresh_models_list()
            except Exception as e: messagebox.showerror("Error", str(e))

    def detect_hardware(self):
        try:
            out = subprocess.check_output(r"lspci | grep -i 'vga\|3d'", shell=True, text=True).upper()
            if "NVIDIA" in out: self.detected_vendor = "NVIDIA"
            elif "AMD" in out: self.detected_vendor = "AMD"
        except: pass
        self.refresh_optimizer_ui()

    def refresh_optimizer_ui(self):
        m = list(GPU_DATABASE.get(self.detected_vendor, {}).keys()); self.gpu_picker.configure(values=m)
        if m: self.gpu_picker.set(self.active_profile if self.active_profile in m else m[0]); self.active_profile = self.gpu_picker.get()

    def save_api_key(self):
        k, p = self.entry_api.get().strip(), self.api_provider.get()
        if len(k) > 10: self.saved_apis.append({"provider": p, "key": k}); self.persist_vault(); self.refresh_api_ui(); self.entry_api.delete(0, "end")

    def remove_api_key(self, item):
        if item in self.saved_apis: self.saved_apis.remove(item); self.persist_vault(); self.refresh_api_ui()

    def refresh_api_ui(self):
        for w in self.api_list_frame.winfo_children(): w.destroy()
        for i in self.saved_apis:
            f = ctk.CTkFrame(self.api_list_frame, fg_color="#1a1a1a"); f.pack(fill="x", pady=2)
            c = "#3498db" if "Hugging" in i["provider"] else "#e67e22"
            ctk.CTkLabel(f, text=f"[{i['provider'][:3].upper()}] {i['key'][:8]}...", text_color=c).pack(side="left", padx=10)
            ctk.CTkButton(f, text="DEL", width=40, fg_color="#c0392b", command=lambda item=i: self.remove_api_key(item)).pack(side="right")

    def set_profile(self, c): self.active_profile = c; self.persist_config()
    def set_ram_profile(self, c): self.active_ram_profile = c; self.persist_config()
    def update_expert_flags(self): self.expert_flags = self.entry_expert.get(); self.persist_config()
    def apply_preset(self, c):
        p = PRESET_MODELS.get(c); self.active_preset = p; self.entry_id.delete(0, "end")
        m_id = p.get("repo") if p.get("source") == "hf" else p.get("id", "")
        self.entry_id.insert(0, m_id); self.option_type.set(p["type"])
        m_filename = p.get("file") if p.get("source") == "hf" else f"{m_id}.safetensors"
        if (MODELS_DIR / p["type"] / m_filename).exists(): self.load_workflow_preset(m_filename)

    def kill_port(self, port):
        try:
            if os.name != "nt": subprocess.run(["fuser", "-k", f"{port}/tcp"], capture_output=True)
            else: subprocess.run(f"powershell -Command \"Stop-Process -Id (Get-NetTCPConnection -LocalPort {port}).OwningProcess -Force\"", shell=True, capture_output=True)
        except: pass

if __name__ == "__main__": App().mainloop()
