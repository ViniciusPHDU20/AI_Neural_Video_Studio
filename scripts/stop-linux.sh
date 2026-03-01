#!/bin/bash

# --- Protocolo de Desligamento Seguro ---
echo "==================================================="
echo "    AI NEURAL VIDEO STUDIO - STOP SERVICE"
echo "==================================================="

# Tenta derrubar o processo pela porta padrão
PORT=8188
PID=$(lsof -t -i:$PORT)

if [ -z "$PID" ]; then
    echo "[!] Nenhum serviço detectado na porta $PORT."
else
    echo "[*] Finalizando processo Studio (PID: $PID)..."
    kill $PID
    sleep 2
    echo "[V] Estúdio desligado com sucesso."
fi

# Limpeza de memória GPU (opcional/agressivo)
# nvidia-smi --gpu-reset > /dev/null 2>&1

echo "==================================================="
