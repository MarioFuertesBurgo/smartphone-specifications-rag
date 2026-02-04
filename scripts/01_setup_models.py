import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Permite ejecutar desde cualquier sitio
sys.path.append(str(Path(__file__).resolve().parents[1]))

load_dotenv()

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL")

if not OLLAMA_MODEL or not OLLAMA_EMBED_MODEL:
    print("ERROR: OLLAMA_MODEL y OLLAMA_EMBED_MODEL deben estar definidos en el .env")
    sys.exit(1)

MODELS = [OLLAMA_MODEL, OLLAMA_EMBED_MODEL]

def main():
    for m in MODELS:
        print(f"Pulling model: {m}")
        try:
            subprocess.run(["ollama", "pull", m], check=True)
        except FileNotFoundError:
            print("ERROR: No encuentro 'ollama' en PATH. ¿Está instalado?")
            sys.exit(1)
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Falló 'ollama pull {m}'. Detalle: {e}")
            sys.exit(1)

    print("OK. Modelos listos.")

if __name__ == "__main__":
    main()
