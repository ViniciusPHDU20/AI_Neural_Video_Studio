# 🎬 AI_Neural_Video_Studio: Professional Command Center

**AI_Neural_Video_Studio** is a centralized command center for advanced AI Neural Video Generation. It provides a robust, professional-grade interface for managing **ComfyUI Core** operations, specializing in **Pony XL** support and high-fidelity video synthesis.

[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.x-yellow.svg)](https://www.python.org/)
[![ComfyUI](https://img.shields.io/badge/Engine-ComfyUI-brightgreen.svg)](https://github.com/comfyanonymous/ComfyUI)

## 🚀 Strategic Features

- **Centralized Launcher**: A unified entry point (`launcher.py`) for managing local AI models, nodes, and configurations.
- **Cross-Platform Installers**: Native deployment scripts for both Linux (`Install-Linux.sh`) and Windows (`Install-Windows.bat`).
- **High-Fidelity Support**: Specialized configurations for **Pony XL** and advanced video diffusion models.
- **Model Governance**: Automated model management and configuration tracking within the `.core` and `models` directory.
- **Interactive Manual**: Comprehensive user guidance provided via `MANUAL_USUARIO.md` for rapid onboarding.

## 🧰 Tech Stack

| Component | Technology |
| :--- | :--- |
| **Backend Architecture** | Python 3 (Launcher Core) |
| **Neural Engine** | ComfyUI / Stable Diffusion |
| **Model Support** | Pony XL, SDXL, AnimateDiff |
| **Platform Ops** | Bash / PowerShell / Batch |

## 🛠 Deployment & Installation

### Linux (Arch/Ubuntu)

1. Clone the studio:
   ```bash
   git clone https://github.com/ViniciusPHDU20/AI_Neural_Video_Studio.git
   cd AI_Neural_Video_Studio
   ```
2. Run the automated installer:
   ```bash
   chmod +x Install-Linux.sh
   ./Install-Linux.sh
   ```
3. Start the command center:
   ```bash
   ./Start-Studio.sh
   ```

### Windows (10/11)

1. Clone or download the repository.
2. Run `Install-Windows.bat` as administrator.
3. Start the studio via `Start-Studio.bat`.

## ⚙️ Project Structure

- `launcher.py`: The heart of the command center.
- `engine/`: Core AI logic and integration points.
- `models/`: Central repository for your neural weights.
- `TECHNICAL.md`: In-depth documentation for developers and power users.

---
*Developed by **ViniciusPHDU20***
