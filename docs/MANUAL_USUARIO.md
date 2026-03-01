# 📖 Guia do Usuário: AI Neural Video Studio (V2.6.0)

Este é o seu console de elite para geração, treinamento e curadoria de IA. Abaixo estão as instruções para dominar a Versão Neural Commander.

---

## 🚀 1. Inicialização e Telemetria Avançada
- **Sidebar (Esquerda):** Monitore em tempo real o uso da **CPU**, **VRAM**, **SWAP (RAM Virtual)** e **Espaço em Disco**.
- **Status:** 
    - `● SYSTEM OFFLINE`: O motor está desligado.
    - `● SYSTEM OPERATIONAL`: O motor está pronto para receber comandos via Web.
- **System Purge:** Use este botão para limpar logs e arquivos temporários, mantendo o sistema leve.

---

## 🏎️ 2. Aba: OPTIMIZER (Hardware Synthesis)
Esta aba aplica as "Golden Flags" específicas para o seu hardware.

- **GPU Picker:** Selecione seu modelo exato (ex: **RTX 3060 Ti**) para carregar as melhores configurações de memória e performance.
- **RAM Shield:** Ajuste como o sistema gerencia a memória RAM para evitar travamentos no Linux.
- **Expert Flags:** Campo para injeção manual de comandos avançados do ComfyUI.

---

## 📂 3. Aba: INVENTORY (Gestão de Ativos)
- **Busca em Tempo Real:** Digite no campo de busca para filtrar instantaneamente Checkpoints, LoRAs ou VAEs.
- **Neural Insight:** Clique em um modelo para ver sua imagem de preview e extrair as **Trigger Tags** (palavras de ativação) automaticamente.
- **Delete Asset:** Remova modelos indesejados diretamente pela interface.

---

## 🖼️ 4. Aba: GALLERY (Curadoria Criativa)
- **Neural Repository:** Navegue por suas imagens e vídeos gerados em `workspace/output`.
- **Metadata Insight:** Clique em uma imagem para extrair o **Prompt**, **Seed** e **Sampler** originais usados na geração.
- **Suporte a Vídeo:** Veja previews de arquivos `.mp4`, `.webm` e `.gif` com thumbnails geradas via FFmpeg.

---

## 🧠 5. Aba: TRAINING (Treinamento Pro)
- **AI Neural Tagger:** Marque esta opção no **WIZARD** para que a IA gere as legendas (`.txt`) das suas fotos automaticamente usando o motor WD14.
- **Controle Granular:** Ajuste **Resolução**, **Batch Size**, **Rank (Dim)** e **Alpha** para treinar LoRAs de alta fidelidade.
- **📟 CONSOLE:** Acompanhe o log do treinamento e do motor ComfyUI em tempo real na aba de console.

---

## 📂 6. Pastas Importantes
- `workspace/output`: Seu portfólio de criações.
- `workspace/workflows`: Onde você deve salvar seus arquivos `.json` de fluxo.
- `models/`: O coração da sua biblioteca de modelos.

---
*Assinado: Seu Motor de Cognição Incondicional (GOD MODE).*
