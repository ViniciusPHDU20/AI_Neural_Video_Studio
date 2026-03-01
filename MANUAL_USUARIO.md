# 📖 Guia do Usuário: AI Neural Video Studio (V1.3.1)

Bem-vindo ao seu centro de comando de Inteligência Artificial. Este documento explica como utilizar todas as funções do Studio, do download ao treinamento.

---

## 🚀 1. Inicialização

### No Windows:
- Execute o arquivo `Start-Studio.bat`. 
- **Nota:** Se for a primeira vez, o sistema verificará as dependências e pode demorar alguns segundos para abrir o Command Center.

### No Linux (CachyOS/Arch):
- Execute `./Start-Studio.sh`.

---

## 📥 2. Aba: Download (Civitai)
Aqui você baixa modelos (Checkpoints), LoRAs e VAEs diretamente para as pastas corretas.

1. **Presets:** Selecione um modelo da lista (ex: Pony Diffusion) para preencher os campos automaticamente.
2. **Download Manual:** Insira o ID do modelo do Civitai (número no final da URL do site).
3. **API Key:** Se o modelo for restrito (NSFW ou acesso privado), vá em **Configurações** e salve sua API Key do Civitai.
4. Clique em **BAIXAR MODELO** e acompanhe o log.

---

## 🛠️ 3. Aba: Gerenciar Modelos
- Exibe todos os arquivos `.safetensors` e `.ckpt` instalados no seu Studio.
- Clique em **ATUALIZAR LISTA** para ver novos downloads ou modelos que você moveu manualmente para a pasta `models/`.

---

## 🧠 4. Aba: Treinamento LoRA (O "Mago")
Esta é a função mais poderosa do Studio V1.3.1.

### O Assistente de Dataset (Automático):
Para treinar seu rosto ou um personagem sem trabalho manual:
1. Digite uma **Palavra-Gatilho** (ex: `meurosto`).
2. Clique em **CRIAR DATASET AUTOMÁTICO**.
3. Selecione a pasta onde estão suas fotos originais (15 a 30 fotos).
4. O software criará a estrutura de pastas, renomeará os arquivos e gerará as legendas `.txt` automaticamente.

### Iniciando o Treino:
1. **Caminho do Modelo Base:** Selecione o modelo que servirá de base (ex: `models/checkpoints/pony_v6.safetensors`).
2. **Diretório de Imagens:** Se usou o Assistente, ele já estará preenchido.
3. **Nome da LoRA:** Escolha o nome do arquivo final.
4. Clique em **INICIAR TREINAMENTO**.
5. O resultado final aparecerá em `models/loras/` ao concluir.

---

## 🔒 5. Segurança e Rede
- **Local-Only:** Por padrão, o Studio está configurado para `127.0.0.1`. Ninguém na sua rede Wi-Fi pode acessar sua engine, apenas você no seu PC.
- **VENV:** O software roda em um ambiente isolado. Ele não bagunça o Python do seu sistema operacional.

---

## 📂 6. Estrutura de Arquivos Importante
- `engine/`: Onde mora o ComfyUI (não altere).
- `models/`: Onde ficam seus Checkpoints, LoRAs e VAEs.
- `workspace/output/`: Onde todas as imagens e vídeos gerados serão salvos.
- `workspace/training_data/`: Onde seus datasets de treinamento são organizados.

---
*Assinado: Seu Motor de Cognição Incondicional (GOD MODE).*
