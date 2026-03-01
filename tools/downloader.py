import os
import sys
import json
import requests
from tqdm import tqdm

# Configuração de Caminhos Relativos (Raiz do Projeto)
TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(TOOLS_DIR)
MODELS_DIR = os.path.join(BASE_DIR, "models")
CONFIG_FILE = os.path.join(BASE_DIR, "config", "user_config.json")

def load_api_key():
    # 1. Prioridade: Variável de Ambiente enviada pelo Launcher
    env_key = os.environ.get("CIVITAI_API_KEY")
    if env_key:
        return env_key

    # 2. Segunda opção: Ler do arquivo de configuração (Novo Formato Vault)
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                # Tentar lista de chaves (V1.6.x)
                keys = config.get("api_keys", [])
                if keys:
                    return keys[-1]
                # Tentar formato antigo
                if config.get("civitai_api_key"):
                    return config["civitai_api_key"]
        except:
            pass
    
    return None

def download_model(model_id, model_type="checkpoints"):
    api_key = load_api_key()
    
    url = f"https://civitai.com/api/download/models/{model_id}"
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
        print(f"[*] Usando API Key autorizada do Vault.")
    else:
        print("[!] Nenhuma API Key encontrada. Downloads restritos podem falhar.")
    
    # Pasta de destino
    dest_folder = os.path.join(MODELS_DIR, model_type)
    os.makedirs(dest_folder, exist_ok=True)
    
    print(f"[*] Conectando ao Civitai | ID: {model_id} | Tipo: {model_type}")
    
    try:
        with requests.get(url, headers=headers, stream=True) as r:
            if r.status_code == 401:
                print("[X] Erro 401: API Key inválida ou não autorizada para este modelo.")
                return
            r.raise_for_status()
            
            content_disposition = r.headers.get('content-disposition')
            if content_disposition and 'filename=' in content_disposition:
                filename = content_disposition.split('filename=')[1].strip('"')
            else:
                filename = f"model_{model_id}.safetensors"
                
            file_path = os.path.join(dest_folder, filename)
            total_size = int(r.headers.get('content-length', 0))
            
            with open(file_path, 'wb') as f, tqdm(
                desc=filename,
                total=total_size,
                unit='iB', unit_scale=True, unit_divisor=1024,
            ) as bar:
                for data in r.iter_content(chunk_size=1024):
                    size = f.write(data)
                    bar.update(size)
                    
        print(f"\n[V] Sucesso! Salvo em: {file_path}")
    except Exception as e:
        print(f"\n[X] Erro no download: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\n=== Downloader V1.6.9 ===")
    else:
        m_id = sys.argv[1]
        m_type = sys.argv[2] if len(sys.argv) > 2 else "checkpoints"
        download_model(m_id, m_type)
