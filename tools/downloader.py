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
    env_key = os.environ.get("CIVITAI_API_KEY")
    if env_key: return env_key
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                keys = config.get("api_keys", [])
                if keys: return keys[-1]
                if config.get("civitai_api_key"): return config["civitai_api_key"]
        except: pass
    return None

def fetch_preview_image(version_id, dest_path):
    print(f"[*] Buscando imagem de preview para Versão: {version_id}...")
    try:
        # Primeiro, tentar obter o modelId a partir do modelVersionId
        url = f"https://civitai.com/api/v1/model-versions/{version_id}"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        
        image_url = None
        if 'images' in data and len(data['images']) > 0:
            image_url = data['images'][0]['url']
        
        if image_url:
            ir = requests.get(image_url, stream=True)
            ir.raise_for_status()
            with open(dest_path, 'wb') as f:
                for chunk in ir.iter_content(1024): f.write(chunk)
            print(f"[V] Preview salvo: {os.path.basename(dest_path)}")
    except Exception as e:
        print(f"[!] Não foi possível baixar o preview: {e}")

def download_model(version_id, model_type="checkpoints"):
    api_key = load_api_key()
    url = f"https://civitai.com/api/download/models/{version_id}"
    headers = {}
    if api_key:
        # Support both formats
        if api_key.startswith("Bearer "): headers["Authorization"] = api_key
        else: headers["Authorization"] = f"Bearer {api_key}"
        print(f"[*] Usando API Key autorizada do Vault.")
    
    dest_folder = os.path.join(MODELS_DIR, model_type)
    os.makedirs(dest_folder, exist_ok=True)
    
    print(f"[*] Conectando ao Civitai | Version ID: {version_id} | Tipo: {model_type}")
    
    try:
        with requests.get(url, headers=headers, stream=True, allow_redirects=True) as r:
            if r.status_code == 401:
                print("[X] Erro 401: API Key inválida ou não autorizada.")
                return
            if r.status_code == 404:
                print(f"[X] Erro 404: Modelo {version_id} não encontrado. Verifique se o ID é o da VERSÃO.")
                return
            r.raise_for_status()
            
            # Tentar extrair o nome do arquivo do header ou da URL final
            filename = None
            content_disposition = r.headers.get('content-disposition')
            if content_disposition and 'filename=' in content_disposition:
                filename = content_disposition.split('filename=')[1].strip('"')
            
            if not filename:
                filename = f"model_{version_id}.safetensors"
                
            file_path = os.path.join(dest_folder, filename)
            total_size = int(r.headers.get('content-length', 0))
            
            with open(file_path, 'wb') as f, tqdm(
                desc=filename, total=total_size, unit='iB', unit_scale=True, unit_divisor=1024,
            ) as bar:
                for data in r.iter_content(chunk_size=1024 * 1024): # 1MB chunks for speed
                    size = f.write(data); bar.update(size)
                    
        print(f"\n[V] Sucesso! Modelo salvo: {filename}")
        
        # Baixar Preview usando o ID da versão
        preview_path = os.path.splitext(file_path)[0] + ".preview.png"
        fetch_preview_image(version_id, preview_path)
        
    except Exception as e:
        print(f"\n[X] Erro no download: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\n=== Downloader V2.3.0 (Preview Edition) ===")
    else:
        m_id = sys.argv[1]
        m_type = sys.argv[2] if len(sys.argv) > 2 else "checkpoints"
        download_model(m_id, m_type)
