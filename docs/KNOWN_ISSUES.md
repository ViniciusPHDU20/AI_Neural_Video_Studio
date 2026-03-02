# Relatório de Estabilidade e Problemas Conhecidos (V4.0.5)

**Data:** 02/03/2026
**Status:** ESTÁVEL (God Mode Active)

## ✅ Funcionalidades Estabilizadas
1.  **Orquestração de Engine:** O `launcher.py` inicia e gerencia o processo do ComfyUI com flags otimizadas para RTX 3060 Ti.
2.  **Sistema de Download Híbrido:** Suporte total para Hugging Face e Civitai (com correção de IDs de versão).
3.  **Injeção de Blueprints:** Envio limpo de JSON para a API do ComfyUI, ignorando metadados de UI que causavam travamentos.
4.  **Monitoramento:** Telemetria de VRAM/RAM via `nvidia-smi` integrada na interface.

## ⚠️ Limitações Conhecidas
1.  **Dependência da Engine Online:** O botão "INJECT BLUEPRINT" só funciona se o indicador estiver "● ONLINE". Se a Engine estiver carregando modelos pesados (como Wan 2.1 14B), a injeção pode dar timeout ou falhar silenciosamente até que o carregamento termine.
    *   *Solução:* Aguarde o Console mostrar "ComfyUI startup time" antes de injetar.
2.  **Modelos Pesados (GGUF):** Modelos acima de 10GB (Wan 2.1) podem levar tempo para baixar. O console pode parecer travado durante a alocação de espaço em disco.
3.  **Preview do Civitai:** Algumas imagens de preview podem falhar se a API do Civitai estiver sobrecarregada (Erro 524 ou 429). Isso não afeta o funcionamento do modelo.

## 📝 Notas para Desenvolvedores
*   O arquivo `launcher.py` foi reescrito para usar caminhos absolutos baseados em `Path(__file__)`.
*   A pasta `models/` é ignorada no Git. Use o **Acquisition Center** do App para repovoar os modelos.
