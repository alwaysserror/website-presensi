from datetime import datetime
from functools import wraps

import click
from flask import abort, flash, redirect, request, url_for
from flask_login import current_user

from .config import ALLOWED_ROLES, ROLE_LABELS
from .extensions import db
from .models import PresenceSession, User


def register_template_helpers(app):
    @app.context_processor
    def inject_helpers():
        return {
            "ROLE_LABELS": ROLE_LABELS,
            "role_label": lambda role: ROLE_LABELS.get(role, role.title()),
        }

    @app.template_filter("datetime_id")
    def datetime_id(value):
        if not value:
            return "-"
        return value.strftime("%d/%m/%Y %H:%M")

    @app.template_filter("datetime_input")
    def datetime_input(value):
        if not value:
            return ""
        return value.strftime("%Y-%m-%dT%H:%M")

    @app.template_filter("percent")
    def percent(value):
        return f"{float(value or 0) * 100:.1f}%"


def register_cli(app):
    @app.cli.command("init-db")
    def init_db_command():
        """Create tables and a default admin account."""
        db.create_all()
        email = app.config.get("SEED_ADMIN_EMAIL", "admin@presensi.local")
        password = app.config.get("SEED_ADMIN_PASSWORD", "admin123")
        existing = User.query.filter_by(email=email).first()
        if not existing:
            admin = User(name="Administrator", email=email, role="admin")
            admin.set_password(password)
            db.session.add(admin)
            db.session.commit()
            click.echo(f"Admin dibuat: {email} / {password}")
        else:
            click.echo(f"Admin sudah ada: {email}")
        click.echo("Database siap dipakai.")


def validate_role(role):
    if role not in ALLOWED_ROLES:
        abort(404)


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("landing"))
            if current_user.role not in roles:
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator


def parse_datetime(value):
    if not value:
        return None
    return datetime.fromisoformat(value)


def get_session_or_404(session_id):
    session = db.session.get(PresenceSession, session_id)
    if not session:
        abort(404)
    return session


def fill_session_from_form(session):
    session.title = request.form.get("title", "").strip()
    session.class_name = request.form.get("class_name", "").strip()
    session.location = request.form.get("location", "").strip()
    session.description = request.form.get("description", "").strip()
    session.start_time = parse_datetime(request.form.get("start_time"))
    session.end_time = parse_datetime(request.form.get("end_time"))
    session.is_open = request.form.get("is_open") == "on"
    if not session.title:
        flash("Nama sesi wajib diisi.", "error")
        abort(400)


def ensure_session_owner(session):
    if session.teacher_id != current_user.id:
        abort(403)
