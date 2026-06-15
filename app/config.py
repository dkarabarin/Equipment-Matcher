import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Ollama settings
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
    USE_LLM = os.getenv("USE_LLM", "true").lower() == "true"
    
    # Catalog settings
    CATALOG_PATH = os.getenv("CATALOG_PATH", "data/КАТАЛОГ_ред_18.03.26.xlsx")
    
    # Directories
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
    OUTPUT_DIR = os.getenv("OUTPUT_DIR", "outputs")
    
    # Matching settings
    MAX_DEVIATION_PERCENT = float(os.getenv("MAX_DEVIATION_PERCENT", "20.0"))
    SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.7"))