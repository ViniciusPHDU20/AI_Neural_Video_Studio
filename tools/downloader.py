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

def load_or_ask_api_key():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            if config.get("civitai_api_key"):
                return config["civitai_api_key"]
    
    print("\n[!] Civitai API Key não encontrada.")
    print("Para baixar modelos restritos (Pony, NSFW), você precisa de uma API Key.")
    print("Crie uma em: https://civitai.com/user/settings (Lá embaixo em API Keys)")
    key = input("Cole sua API Key aqui (ou Enter para pular): ").strip()
    
    if key:
        with open(CONFIG_FILE, 'w') as f:
            json.dump({"civitai_api_key": key}, f, indent=4)
        print("[+] Chave salva com sucesso!")
        return key
    return None

def download_model(model_id, model_type="checkpoints"):
    api_key = load_or_ask_api_key()
    
    url = f"https://civitai.com/api/download/models/{model_id}"
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    # Pasta de destino
    dest_folder = os.path.join(MODELS_DIR, model_type)
    os.makedirs(dest_folder, exist_ok=True)
    
    print(f"[*] Iniciando conexão com Civitai para o Modelo ID: {model_id}...")
    
    try:
        with requests.get(url, headers=headers, stream=True) as r:
            r.raise_for_status()
            
            # Tentar pegar o nome do arquivo do header
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
                unit='iB',
                unit_scale=True,
                unit_divisor=1024,
            ) as bar:
                for data in r.iter_content(chunk_size=1024):
                    size = f.write(data)
                    bar.update(size)
                    
        print(f"\n[+] Sucesso! Arquivo salvo em: {file_path}")
    except Exception as e:
        print(f"\n[X] Erro no download: {e}")
        print("Verifique sua conexão ou se a API Key é válida.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\n=== AI Neural Video Studio Downloader ===")
        print("Uso: python downloader.py <MODEL_ID> [TYPE]")
        print("Tipos: checkpoints, loras, vae, controlnet")
        print("Exemplo: python downloader.py 290640 checkpoints")
    else:
        m_id = sys.argv[1]
        m_type = sys.argv[2] if len(sys.argv) > 2 else "checkpoints"
        download_model(m_id, m_type)
