import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from app.rag_utils import load_index, get_llm
from llama_index.core.query_engine import RetrieverQueryEngine
from app.config import OLLAMA_MODEL, OLLAMA_EMBED_MODEL


print(f"Usando LLM: {OLLAMA_MODEL} | Embeddings: {OLLAMA_EMBED_MODEL}")


PERSIST_DIR = "index_store"
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
)


def build_prompt(q: str) -> str:
    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"Pregunta del usuario: {q}"
    )


def main():
    index = load_index(PERSIST_DIR)
    llm = get_llm()
    retriever = index.as_retriever(
        similarity_top_k=10,
        vector_store_query_mode="mmr",
        alpha=0.7,
    )
    query_engine = RetrieverQueryEngine.from_args(retriever, llm=llm)

    print(INTRO_TEXT)
    print("Chat RAG listo. Escribe 'exit' para salir.")
    while True:
        q = input("\n> ")
        if q.strip().lower() in ("exit", "quit"):
            break
        resp = query_engine.query(build_prompt(q))
        print("\n" + str(resp))

if __name__ == "__main__":
    main()
