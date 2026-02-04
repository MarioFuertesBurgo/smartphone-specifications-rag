from __future__ import annotations

import os
import sys
import subprocess
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.rag_utils import load_index, get_llm
from llama_index.core.query_engine import RetrieverQueryEngine

ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=ENV_PATH)

PERSIST_DIR = PROJECT_ROOT / "index_store"

INTRO_TEXT = (
    "Hola. Soy un asistente RAG de especificaciones de moviles. "
    "Mi funcion es ayudarte a encontrar que movil es mejor para lo que buscas, "
    "usando una base de datos local de modelos y sus caracteristicas. "
    "Solo respondo preguntas sobre moviles."
)

SYSTEM_PROMPT = (
        "Eres un asistente especializado en smartphones. Responde siempre en espanol de Espana, "
    "tutea y usa un tono natural. Evita modismos latinoamericanos. "
    "No uses 'senor/senora' ni tratamientos formales. No mezcles ingles ni escribas etiquetas.\n\n"
    "Reglas de comportamiento:\n"
    "Tu objetivo es dar información sobre un modelo de smartphone o recomendar al usuario un smartphone segun la informacion que te proporcione"
    "Nunca des el precio exactamente, di que varia según la zona. Da una estimacion de si es caro o barato"

    "Además, se muy concreto de responder lo que te pregunta el usuario"

    "Si te preguntan algo que no está relacionado con telefonos moviles, rechaza amablemente la pregunta y di cual es tu función"
)


def build_prompt(q: str) -> str:
    return f"{SYSTEM_PROMPT}\n\nPregunta del usuario: {q}"


def run_pipeline() -> None:
    scripts = [
        "00_check_env.py",
        "01_setup_models.py",
        "02_load_neo4j.py",
        "03_build_rag.py",
    ]
    for script in scripts:
        script_path = PROJECT_ROOT / "scripts" / script
        subprocess.run([sys.executable, str(script_path)], check=True, cwd=str(PROJECT_ROOT))


def reset_ollama_model() -> None:
    model = os.getenv("OLLAMA_MODEL", "").strip()
    if not model:
        return
    try:
        subprocess.run(["ollama", "stop", model], check=False)
    except FileNotFoundError:
        pass


def create_query_engine():
    index = load_index(str(PERSIST_DIR))
    llm = get_llm()
    retriever = index.as_retriever(
        similarity_top_k=10,
        vector_store_query_mode="mmr",
        alpha=0.7,
    )
    return RetrieverQueryEngine.from_args(retriever, llm=llm)


app = Flask(__name__)
QUERY_ENGINE = None


@app.get("/")
def index():
    return render_template("index.html", intro_text=INTRO_TEXT)


@app.post("/api/chat")
def chat():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"reply": ""})

    prompt = build_prompt(message)
    resp = QUERY_ENGINE.query(prompt)
    return jsonify({"reply": str(resp)})


@app.get("/health")
def health():
    return {"ok": True}


def main() -> None:
    global QUERY_ENGINE
    if os.getenv("OLLAMA_RESET_ON_START", "0") == "1":
        reset_ollama_model()
    run_pipeline()
    QUERY_ENGINE = create_query_engine()
    port = int(os.getenv("WEB_APP_PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=False)


if __name__ == "__main__":
    main()
