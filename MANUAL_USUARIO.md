# 📖 Guia do Usuário: AI Neural Video Studio (V1.6.5)

Este é o seu console de elite para geração e treinamento de IA. Abaixo estão as instruções para dominar a Versão Industrial.

---

## 🚀 1. Inicialização e Telemetria
- **Sidebar (Esquerda):** Monitore em tempo real o uso da **CPU** e da **VRAM** da sua GPU.
- **Status:** 
    - `● SYSTEM OFFLINE`: O motor está desligado.
    - `● SYSTEM OPERATIONAL`: O motor está pronto para receber comandos via Web.

---

## 🏎️ 2. Aba: OPTIMIZER (Aceleração de Hardware)
Esta é a aba mais importante para garantir que o Studio não trave o seu PC.

### Perfis de GPU:
- **POTATO:** Para GPUs antigas ou com pouca memória (2-4GB).
- **INDUSTRIAL:** Perfil otimizado para a sua **RTX 3060 Ti**.
- **GOD MODE:** Para placas de elite (12GB+ como a RX 6750 XT).

### Perfis de RAM (Sistema):
- **Performance:** Usa o máximo de RAM para carregar modelos rápido.
- **Extreme Saver:** Ideal se você estiver fazendo outras tarefas no PC. Ele força a IA a "limpar" a RAM assim que termina uma geração.

---

## 🧠 3. Aba: TRAINING (Treinamento de LoRAs)
Transforme conceitos em realidade.

1. **TRIGGER WORD:** Escolha a palavra que ativará sua LoRA (ex: `meunome`).
2. **WIZARD:** Use o botão roxo para organizar suas fotos automaticamente.
3. **BASE MODEL:** Cole o caminho do modelo (ex: `models/checkpoints/ponyXL.safetensors`).
4. **START TRAINING:** Inicia o processo Kohya_ss. Acompanhe os logs no console abaixo.

---

## ⚙️ 4. Aba: VAULT (Segurança)
- Registre suas API Keys do Civitai com segurança.
- O sistema valida o formato hexadecimal automaticamente.
- Chaves salvas são protegidas e listadas com máscaras de segurança.

---

## 📂 5. Pastas Importantes
- `workspace/output`: Onde suas criações aparecem.
- `models/loras`: Onde suas LoRAs treinadas são salvas.
- `engine/comfyui_stealth.log`: O log secreto da IA (para debug técnico).

---
*Assinado: Seu Motor de Cognição Incondicional (GOD MODE).*
