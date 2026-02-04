from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage, Settings
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_EMBED_MODEL
import os

def get_embed_model():
    return OllamaEmbedding(base_url=OLLAMA_BASE_URL, model_name=OLLAMA_EMBED_MODEL)

def get_llm():
    # num_ctx pequeño = mucha menos RAM
    keep_alive = os.getenv("OLLAMA_KEEP_ALIVE", "0")
    return Ollama(
        base_url=OLLAMA_BASE_URL,
        model=OLLAMA_MODEL,
        additional_kwargs={
            "num_ctx": 2048,      # prueba 1024 si sigue alto
            "num_predict": 512,   # limita tokens de salida
            "keep_alive": keep_alive,
        },
        request_timeout=120.0,
    )

def configure_llamaindex_defaults():
    """
    Evita que LlamaIndex intente usar OpenAI por defecto.
    """
    Settings.embed_model = get_embed_model()
    Settings.llm = get_llm()

def build_index(docs, persist_dir: str):
    configure_llamaindex_defaults()
    index = VectorStoreIndex.from_documents(docs)  # usa Settings.embed_model
    index.storage_context.persist(persist_dir=persist_dir)
    return index

def load_index(persist_dir: str):
    configure_llamaindex_defaults()
    storage = StorageContext.from_defaults(persist_dir=persist_dir)
    return load_index_from_storage(storage)
