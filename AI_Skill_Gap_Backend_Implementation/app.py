from flask import Flask
from config import Config
from extensions import db
from routes import api
from seed import seed_database


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)
    db.init_app(app)
    app.register_blueprint(api, url_prefix="/api")

    @app.cli.command("init-db")
    def init_db():
        """Create all database tables."""
        with app.app_context():
            db.create_all()
            print("Database initialized.")

    @app.cli.command("seed")
    def seed():
        """Seed demo roles, courses, and a sample student."""
        with app.app_context():
            db.create_all()
            seed_database()
            print("Demo seed complete.")

    @app.cli.command("ingest-data")
    def ingest_data():
        """Ingest real ESCO, Coursera, and student datasets into the database."""
        with app.app_context():
            from data.ingest import run_ingestion
            db.create_all()
            run_ingestion()

    @app.cli.command("train-model")
    def train_model():
        """Generate ML training dataset and train the gap classification model."""
        with app.app_context():
            import subprocess, sys
            from pathlib import Path
            ds = Path("ml/skill_gap_dataset.csv")
            if not ds.exists():
                print("Generating ML training dataset...")
                subprocess.check_call([sys.executable, "ml/generate_dataset.py",
                                       "--output", str(ds)])
            print("Training ML model...")
            subprocess.check_call([sys.executable, "ml/train.py",
                                   "--input", str(ds),
                                   "--output", app.config["MODEL_PATH"]])

    return app


app = create_app()
