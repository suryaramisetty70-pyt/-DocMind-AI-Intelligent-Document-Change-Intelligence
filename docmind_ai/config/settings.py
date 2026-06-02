"""
DocMind AI - Intelligent Document Change Intelligence Platform
Configuration Management
"""

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
from pydantic_settings import BaseSettings

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
PROCESSED_DIR = DATA_DIR / "processed"
REPORTS_DIR = DATA_DIR / "reports"

# Create directories
for dir_path in [DATA_DIR, UPLOADS_DIR, PROCESSED_DIR, REPORTS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)


class DatabaseConfig(BaseModel):
    """Database configuration"""
    DATABASE_URL: str = "sqlite:///./docmind.db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "docmind"
    POSTGRES_PASSWORD: str = "docmind_password"
    POSTGRES_DB: str = "docmind_db"
    POOL_SIZE: int = 20
    MAX_OVERFLOW: int = 10


class OCRConfig(BaseModel):
    """OCR configuration"""
    OCR_ENGINE: str = "easyocr"  # easyocr, tesseract, pytesseract
    EASYOCR_LANGUAGES: list = ["en", "te", "hi", "ta"]
    TESSERACT_LANGUAGE: str = "eng+tam+hin+tel"
    OCR_CONFIDENCE_THRESHOLD: float = 0.6
    BATCH_SIZE: int = 16
    GPU_ENABLED: bool = True
    IMAGE_PREPROCESSING: bool = True


class AIConfig(BaseModel):
    """AI/ML configuration"""
    SENTENCE_TRANSFORMER_MODEL: str = "all-MiniLM-L6-v2"
    SEMANTIC_SIMILARITY_THRESHOLD: float = 0.75
    EMBEDDING_DIMENSION: int = 384
    FAISS_INDEX_TYPE: str = "IVF"  # IVF, Flat, HNSW
    FAISS_NLIST: int = 100
    LLM_MODEL: str = "gpt-3.5-turbo"
    LLM_TEMPERATURE: float = 0.3
    MAX_TOKENS: int = 2000


class DocumentConfig(BaseModel):
    """Document processing configuration"""
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    SUPPORTED_FORMATS: list = ["pdf", "docx", "xlsx", "xls", "txt", "csv"]
    MAX_PAGES: int = 1000
    TIMEOUT_SECONDS: int = 300
    CHUNK_SIZE: int = 1000
    PARALLEL_PROCESSING: bool = True


class SecurityConfig(BaseModel):
    """Security configuration"""
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    API_KEY_ENABLED: bool = True
    CORS_ORIGINS: list = ["*"]
    RATE_LIMIT_PER_MINUTE: int = 100


class StorageConfig(BaseModel):
    """Storage configuration"""
    STORAGE_TYPE: str = "local"  # local, s3, gcs
    S3_BUCKET: str = "docmind-documents"
    S3_REGION: str = "us-east-1"
    LOCAL_STORAGE_PATH: str = str(DATA_DIR)
    SIGNED_URL_EXPIRY: int = 3600


class MonitoringConfig(BaseModel):
    """Monitoring configuration"""
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: str = "docmind.log"
    METRICS_ENABLED: bool = True
    TRACE_ENABLED: bool = False


class Config(BaseSettings):
    """Main configuration class"""
    # Environment
    ENV: str = "development"
    DEBUG: bool = True
    
    # Sub-configurations
    database: DatabaseConfig = DatabaseConfig()
    ocr: OCRConfig = OCRConfig()
    ai: AIConfig = AIConfig()
    document: DocumentConfig = DocumentConfig()
    security: SecurityConfig = SecurityConfig()
    storage: StorageConfig = StorageConfig()
    monitoring: MonitoringConfig = MonitoringConfig()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global config instance
config = Config()


# Helper functions
def get_database_url() -> str:
    """Get database URL based on environment"""
    if config.ENV == "production":
        return f"postgresql://{config.database.POSTGRES_USER}:{config.database.POSTGRES_PASSWORD}@{config.database.POSTGRES_HOST}:{config.database.POSTGRES_PORT}/{config.database.POSTGRES_DB}"
    return config.database.DATABASE_URL


def get_storage_path(subfolder: str = "") -> Path:
    """Get storage path for a specific subfolder"""
    path = DATA_DIR / subfolder if subfolder else DATA_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def is_production() -> bool:
    """Check if running in production"""
    return config.ENV == "production"