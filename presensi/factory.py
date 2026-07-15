import os
import secrets

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - fallback for minimal environments.
    def load_dotenv():
        return False
from flask import Flask

from .config import build_database_uri
from .extensions import db, login_manager
from .helpers import register_cli, register_template_helpers
from .routes.admin import register_admin_routes
from .routes.auth import register_auth_routes
from .routes.main import register_main_routes
from .routes.participant import register_participant_routes
from .routes.teacher import register_teacher_routes


load_dotenv()


def create_app():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, "templates"),
        static_folder=os.path.join(base_dir, "static"),
    )
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", secrets.token_hex(32))
    app.config["SQLALCHEMY_DATABASE_URI"] = build_database_uri()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["LBPH_DISTANCE_THRESHOLD"] = float(os.getenv("LBPH_DISTANCE_THRESHOLD", "75.0"))
    app.config["ADMIN_INVITE_CODE"] = os.getenv("ADMIN_INVITE_CODE", "admin123")
    app.config["SEED_ADMIN_EMAIL"] = os.getenv("SEED_ADMIN_EMAIL", "admin@presensi.local")
    app.config["SEED_ADMIN_PASSWORD"] = os.getenv("SEED_ADMIN_PASSWORD", "admin123")

    db.init_app(app)
    login_manager.init_app(app)

    register_template_helpers(app)
    register_cli(app)
    register_main_routes(app)
    register_auth_routes(app)
    register_participant_routes(app)
    register_teacher_routes(app)
    register_admin_routes(app)

    return app
