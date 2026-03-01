import os
import sys
from huggingface_hub import hf_hub_download
from pathlib import Path

# --- CONFIGURAÇÃO DE CAMINHOS ---
BASE_DIR = Path(__file__).parent.parent.absolute()
MODELS_DIR = BASE_DIR / "models"

def download_from_hf(repo_id, filename, model_type="checkpoints", subfolder=None):
    dest_folder = MODELS_DIR / model_type
    if subfolder: dest_folder = dest_folder / subfolder
    dest_folder.mkdir(parents=True, exist_ok=True)
    
    print(f"[*] Iniciando Download do Hugging Face:")
    print(f"[*] Repo: {repo_id}")
    print(f"[*] Arquivo: {filename}")
    print(f"[*] Destino: {dest_folder}")
    
    try:
        path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            local_dir=str(dest_folder),
            local_dir_use_symlinks=False
        )
        print(f"\n[V] Sucesso! Modelo salvo em: {path}")
        return path
    except Exception as e:
        print(f"\n[X] Erro no download do HF: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python hf_downloader.py <repo_id> <filename> [type] [subfolder]")
    else:
        rid = sys.argv[1]
        fname = sys.argv[2]
        mtype = sys.argv[3] if len(sys.argv) > 3 else "checkpoints"
        subf = sys.argv[4] if len(sys.argv) > 4 else None
        download_from_hf(rid, fname, mtype, subf)
