from flask import Flask, render_template, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from extensions import db, migrate
from routes import api
from auth import auth_bp
from api import api_v1


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)
    db.init_app(app)
    migrate.init_app(app, db)
    JWTManager(app)
    # CORS: allow localhost in development; override CORS_ORIGINS env var in production
    import os
    allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:5000,http://127.0.0.1:5000").split(",")
    CORS(app, resources={r"/api/*": {"origins": allowed_origins}})
    app.register_blueprint(api,     url_prefix="/api")
    app.register_blueprint(api_v1,  url_prefix="/api/v1")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")

    # ───────────────────────────────────────────────────────────────────────────
    # Centralized error handlers (no raw exception messages to clients)
    # ───────────────────────────────────────────────────────────────────────────
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Bad request", "detail": str(e)}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({"error": "Authentication required"}), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({"error": "Access denied"}), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "Internal server error"}), 500

    @app.get("/")
    @app.get("/test")
    def test_bench():
        """Main home page — student setup, auth, role selection, job match scores."""
        return render_template("index.html")

    @app.get("/skills")
    def skills_page():
        """Skills, Resume Parser, Job Role Skills, and ML Gap Analysis page."""
        return render_template("skills.html")

    @app.get("/learning")
    def learning_page():
        """Learning Path, Recommendations, Progress, and Analytics page."""
        return render_template("learning.html")

    @app.get("/favicon.ico")
    def favicon():
        """Handle browser favicon request without 404."""
        return "", 204

    @app.cli.command("init-db")
    def init_db():
        """Create all database tables."""
        with app.app_context():
            db.create_all()
            print("Database initialized.")

    @app.cli.command("sync-roles")
    def sync_roles():
        """Synchronize the 15 IT Job Roles with exactly 15 core skills each."""
        with app.app_context():
            from data.ingest import sync_15_roles_and_skills
            db.create_all()
            res = sync_15_roles_and_skills()
            print(f"Role synchronization complete: {res}")

    @app.cli.command("seed-courses")
    def seed_courses():
        """Seed curated learning resources for all role skills."""
        with app.app_context():
            from data.seed_courses import seed_curated_courses
            db.create_all()
            res = seed_curated_courses()
            print(f"Course seeding complete: {res}")

    @app.cli.command("ingest-data")
    def ingest_data():
        """Ingest real ESCO, Coursera, and student datasets into the database."""
        with app.app_context():
            from data.ingest import run_ingestion
            db.create_all()
            run_ingestion()

    @app.cli.command("ingest-onet")
    def ingest_onet_cmd():
        """Ingest O*NET Knowledge and Work Activity competencies for the 6 IT roles."""
        with app.app_context():
            from data.ingest import ingest_onet
            db.create_all()
            cfg = app.config
            result = ingest_onet(
                knowledge_path=cfg["ONET_KNOWLEDGE_XLSX"],
                activities_path=cfg["ONET_ACTIVITIES_XLSX"],
                occupations_path=cfg["ONET_OCCUPATIONS_XLSX"],
            )
            print(f"\nO*NET ingestion complete: {result}")

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
