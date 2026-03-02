# AI Neural Video Studio (Enterprise V4.0.5)

Uma suíte de produção de vídeo neural de alta performance, projetada para orquestrar fluxos de trabalho do ComfyUI com uma interface moderna e gestão automatizada de ativos.

![Status](https://img.shields.io/badge/Status-Stable-green) ![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows-blue)

## 🚀 Funcionalidades (God Mode)
*   **Command Center:** Interface unificada para iniciar Engine, monitorar hardware (VRAM/RAM) e gerenciar downloads.
*   **Smart Blueprints:** Injeção de workflows JSON complexos (Wan 2.1, Pony XL) com um único clique.
*   **Acquisition Automático:** Baixe modelos do Hugging Face e Civitai sem sair do app.
*   **Vault Seguro:** Gerenciamento criptografado de chaves de API.

## 🛠️ Instalação

### Linux (Arch/Debian/Ubuntu)
```bash
chmod +x Install-Linux.sh
./Install-Linux.sh
./Studio-Linux.sh
```

### Windows (10/11)
Execute `Install-Windows.bat` (Como Administrador recomendado para links simbólicos).
Execute `Studio-Windows.bat` para iniciar.

## 🎮 Como Usar

1.  **Inicie o Studio:** Clique em `LAUNCH STUDIO`. Aguarde o indicador ficar **ONLINE**.
2.  **Baixe Modelos:** Vá na aba **ACQUISITION**, escolha um preset (ex: `Wan 2.1 T2V`) e clique em `START DOWNLOAD`.
3.  **Ative o Fluxo:** 
    *   Vá na aba **BLUEPRINTS**.
    *   Clique em `⚡ DEPLOY: wan2.1...`.
    *   Acompanhe o processo no **CONSOLE** e na aba **GALLERY**.

## 📦 Modelos Suportados (Presets)
O sistema já vem configurado para baixar automaticamente:
*   **Wan 2.1 (14B GGUF):** Estado da arte em geração de vídeo (Text-to-Video e Image-to-Video).
*   **Pony XL:** Base robusta para geração de imagens estáticas.
*   **T5 Encoder & VAE:** Componentes essenciais pré-configurados.

## ⚖️ Licença
Distribuído sob licença MIT. Os modelos baixados possuem suas próprias licenças (CreativeML, Apache 2.0, etc.).
