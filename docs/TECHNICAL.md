# TECHNICAL OVERVIEW: AI NEURAL VIDEO STUDIO

## Objective
The AI Neural Video Studio is designed to bridge the gap between complex node-based AI engines and a streamlined user experience. The primary goal is to provide a portable, zero-configuration environment for high-fidelity cinematic video synthesis and research-grade image generation.

## 🏗️ Architecture Detail

### 1. Engine Decoupling
The core generative engine (ComfyUI) is isolated within the `/engine` directory. This abstraction allows for independent updates of the base engine without affecting the user's workspace, blueprints, or models.

### 2. Portable Workspace Configuration
Paths are managed through a centralized relative mapping in `/config/extra_model_paths.yaml`. By using relative paths (`../models/`), the studio can be deployed on external drives or different operating systems without requiring path reconfiguration.

### 3. Integrated Command Center (`launcher.py`)
- **UI Logic:** Built on `CustomTkinter`, using a multi-threaded approach to prevent GUI blocking during heavy model downloads or engine startup.
- **Process Management:** Employs `subprocess.Popen` with OS-specific signaling (Bash for Linux/POSIX, Batch for NT) to manage engine lifecycles and clean shutdowns via port scanning (Port 8188).
- **Automated Retrieval:** `tools/downloader.py` integrates the Civitai API with Bearer token authentication, handling multi-part model streams and metadata extraction.

## 🧱 Implementation Stack
- **Languages:** Python 3.10+, Bash 5.0+, Batch (NT).
- **Backend:** ComfyUI Core (Stable Diffusion / SDXL).
- **Frontend:** CustomTkinter (Dark Mode UI).
- **Package Management:** Python Virtual Environments (venv) with targeted wheel installation for Torch/CUDA support.

## 🏁 Design Goal
A unified, single-entry point software that abstracts the complexities of Python environment management and AI model deployment, delivering a professional suite for photorealistic content production.
