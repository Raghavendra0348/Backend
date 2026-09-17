import os
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# External dataset base paths (resolved relative to this file's parent directory)
_BASE = Path(__file__).resolve().parent.parent
_DATASET = _BASE / "Dataset"


def _resolve_path(primary: Path, fallback: Path) -> str:
    return str(primary if primary.exists() else fallback)


class Config:
    SECRET_KEY     = os.getenv("SECRET_KEY", "dev-secret-change-in-production")
    # JWT uses SECRET_KEY by default; override with JWT_SECRET_KEY for separation
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", os.getenv("SECRET_KEY",
                               "jwt-dev-secret-key-change-me-in-production-min-32chars"))
    JWT_ACCESS_TOKEN_EXPIRES  = timedelta(days=7)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

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

    # External dataset paths (organized with clean directory defaults & backward compatibility)
    ESCO_DATA_DIR = os.getenv(
        "ESCO_DATA_DIR",
        _resolve_path(
            _DATASET / "esco" / "classification_en_csv",
            _BASE / "ESCO dataset - v1.2.1 - classification - en - csv"
        )
    )
    ONET_DATA_DIR = os.getenv("ONET_DATA_DIR", str(_DATASET / "onet"))
    ONET_KNOWLEDGE_XLSX = os.getenv(
        "ONET_KNOWLEDGE_XLSX",
        _resolve_path(
            _DATASET / "onet" / "Knowledge.xlsx",
            _DATASET / "Knowledge (1).xlsx"
        )
    )
    ONET_ACTIVITIES_XLSX = os.getenv(
        "ONET_ACTIVITIES_XLSX",
        _resolve_path(
            _DATASET / "onet" / "Work_Activities.xlsx",
            _DATASET / "Work Activities (1).xlsx"
        )
    )
    ONET_OCCUPATIONS_XLSX = os.getenv(
        "ONET_OCCUPATIONS_XLSX",
        _resolve_path(
            _DATASET / "onet" / "Occupation_Data.xlsx",
            _DATASET / "Occupation Data (1).xlsx"
        )
    )
    COURSERA_CSV = os.getenv(
        "COURSERA_CSV",
        str(_DATASET / "coursera" / "Coursera.csv")
    )
    COURSERA_ZIP = os.getenv(
        "COURSERA_ZIP",
        str(_DATASET / "coursera" / "Coursera.csv")
    )
    STUDENT_DATASET_XLSX = os.getenv(
        "STUDENT_DATASET_XLSX",
        _resolve_path(
            _DATASET / "students" / "Student_Profiles_Indian_Names.xlsx",
            _DATASET / "Final_Updated_DMA_DATASET_Indian_Names (1).xlsx"
        )
    )
