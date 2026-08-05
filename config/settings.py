from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ==========================
    # Gemini
    # ==========================
    GEMINI_API_KEY: str
    GEMINI_MODEL: str

    # ==========================
    # Paths
    # ==========================
    RAW_DATA_PATH: str
    PROCESSED_DATA_PATH: str
    FAISS_INDEX_PATH: str
    BM25_INDEX_PATH: str

    # ==========================
    # Chunking
    # ==========================
    CHUNK_SIZE: int
    CHUNK_OVERLAP: int

    # ==========================
    # Retrieval
    # ==========================
    TOP_K_BM25: int
    TOP_K_VECTOR: int
    TOP_K_FINAL: int
    SIMILARITY_THRESHOLD: float

    # ==========================
    # Embeddings
    # ==========================
    EMBEDDING_MODEL: str

    # ==========================
    # API
    # ==========================
    HOST: str
    PORT: int

    # ==========================
    # Logging
    # ==========================
    LOG_LEVEL: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()