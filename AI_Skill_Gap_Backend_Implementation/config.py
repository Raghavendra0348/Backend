import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-production")

    # Default to SQLite for zero-friction local development.
    # Set DATABASE_URL=mysql+pymysql://user:pass@host/skill_gap_db in .env for MySQL.
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///skill_gap.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "storage/uploads")
    MODEL_PATH = os.getenv("MODEL_PATH", "ml/models/skill_gap_model.joblib")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 5 * 1024 * 1024))

    # External dataset paths (resolved relative to this file's parent directory)
    _BASE = Path(__file__).parent.parent
    ESCO_DATA_DIR = os.getenv(
        "ESCO_DATA_DIR",
        str(_BASE / "ESCO dataset - v1.2.1 - classification - en - csv")
    )
    ONET_DATA_DIR = os.getenv("ONET_DATA_DIR", str(_BASE / "Dataset"))
    COURSERA_ZIP = os.getenv(
        "COURSERA_ZIP",
        str(_BASE / "Dataset" / "archive (1).zip")
    )
    STUDENT_DATASET_XLSX = os.getenv(
        "STUDENT_DATASET_XLSX",
        str(_BASE / "Dataset" / "Final_Updated_DMA_DATASET_Indian_Names (1).xlsx")
    )
