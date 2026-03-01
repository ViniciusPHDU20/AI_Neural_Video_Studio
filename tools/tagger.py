import os
import sys
import cv2
import numpy as np
import onnxruntime as ort
import pandas as pd
from PIL import Image
from pathlib import Path

# --- CONFIGURAÇÕES DO MOTOR DE TAGGING ---
MODEL_DIR = Path(__file__).parent / "tagger_models"
MODEL_PATH = MODEL_DIR / "model.onnx"
TAGS_PATH = MODEL_DIR / "selected_tags.csv"

def download_tagger_assets():
    if not MODEL_DIR.exists(): MODEL_DIR.mkdir(parents=True)
    import requests
    if not MODEL_PATH.exists():
        print("[*] Baixando Cérebro Neural (WD14 ONNX)...")
        url = "https://huggingface.co/SmilingWolf/wd-v1-4-vit-tagger-v2/resolve/main/model.onnx"
        r = requests.get(url); MODEL_PATH.write_bytes(r.content)
    if not TAGS_PATH.exists():
        print("[*] Baixando Dicionário de Tags...")
        url = "https://huggingface.co/SmilingWolf/wd-v1-4-vit-tagger-v2/resolve/main/selected_tags.csv"
        r = requests.get(url); TAGS_PATH.write_bytes(r.content)

def preprocess_image(image, size=448):
    image = image.convert("RGB")
    image = np.array(image)
    image = image[:, :, ::-1] # RGB to BGR
    
    # Padding para manter aspect ratio
    h, w = image.shape[:2]
    max_side = max(h, w)
    pad_h = (max_side - h) // 2
    pad_w = (max_side - w) // 2
    image = cv2.copyMakeBorder(image, pad_h, max_side - h - pad_h, pad_w, max_side - w - pad_w, cv2.BORDER_CONSTANT, value=[255, 255, 255])
    
    image = cv2.resize(image, (size, size), interpolation=cv2.INTER_AREA)
    image = image.astype(np.float32)
    return np.expand_dims(image, axis=0)

def run_tagger(image_folder, trigger_word="", threshold=0.35):
    download_tagger_assets()
    
    # Carregar Modelo e Tags
    tags_df = pd.read_csv(TAGS_PATH)
    tag_names = tags_df["name"].tolist()
    rating_indices = list(range(0, 4))
    character_indices = list(range(4, 1568))
    general_indices = list(range(1568, 9083))

    providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
    session = ort.InferenceSession(str(MODEL_PATH), providers=providers)
    input_name = session.get_inputs()[0].name

    print(f"[*] Iniciando Cognitive Tagging em: {image_folder}")
    
    files = [f for f in os.listdir(image_folder) if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))]
    
    for f in files:
        img_path = os.path.join(image_folder, f)
        txt_path = os.path.splitext(img_path)[0] + ".txt"
        
        try:
            with Image.open(img_path) as img:
                input_data = preprocess_image(img)
                preds = session.run(None, {input_name: input_data})[0][0]
                
                # Filtrar Tags Gerais
                general_tags = []
                for i in general_indices:
                    if preds[i] >= threshold:
                        general_tags.append(tag_names[i].replace("_", " "))
                
                # Construir Legenda: Trigger + Tags
                final_tags = [trigger_word] + general_tags if trigger_word else general_tags
                caption = ", ".join(final_tags)
                
                with open(txt_path, "w") as tf:
                    tf.write(caption)
                print(f"[V] Caption gerada: {f}")
        except Exception as e:
            print(f"[X] Erro ao processar {f}: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python tagger.py <folder> [trigger]")
    else:
        folder = sys.argv[1]
        trigger = sys.argv[2] if len(sys.argv) > 2 else ""
        run_tagger(folder, trigger)
