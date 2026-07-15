import secrets
from datetime import datetime, timedelta

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user

from ..config import ROLE_LABELS
from ..extensions import db
from ..helpers import validate_role
from ..models import User


def register_auth_routes(app):
    @app.route("/login/<role>", methods=["GET", "POST"])
    @app.route("/masuk/<role>", methods=["GET", "POST"])
    def login(role):
        validate_role(role)
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            user = User.query.filter_by(email=email, role=role).first()

            if user and user.check_password(password) and user.is_active:
                login_user(user)
                flash(f"Selamat datang, {user.name}.", "success")
                return redirect(url_for("dashboard"))

            flash("Email, password, atau role tidak sesuai.", "error")

        return render_template("auth/login.html", role=role)

    @app.route("/register/<role>", methods=["GET", "POST"])
    @app.route("/daftar/<role>", methods=["GET", "POST"])
    def register(role):
        validate_role(role)
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            phone = request.form.get("phone", "").strip()
            password = request.form.get("password", "")
            confirm_password = request.form.get("confirm_password", "")
            invite_code = request.form.get("invite_code", "").strip()

            if not name or not email or not password:
                flash("Nama, email, dan password wajib diisi.", "error")
            elif password != confirm_password:
                flash("Konfirmasi password tidak sama.", "error")
            elif len(password) < 6:
                flash("Password minimal 6 karakter.", "error")
            elif role == "admin" and invite_code != app.config["ADMIN_INVITE_CODE"]:
                flash("Kode admin tidak valid.", "error")
            elif User.query.filter_by(email=email).first():
                flash("Email sudah terdaftar.", "error")
            else:
                user = User(name=name, email=email, phone=phone, role=role)
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                flash("Akun berhasil dibuat. Silakan login.", "success")
                return redirect(url_for("login", role=role))

        return render_template("auth/register.html", role=role)

    @app.route("/forgot/<role>", methods=["GET", "POST"])
    @app.route("/lupa-password/<role>", methods=["GET", "POST"])
    def forgot_password(role):
        validate_role(role)
        reset_link = None

        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            user = User.query.filter_by(email=email, role=role).first()
            if user:
                user.reset_token = secrets.token_urlsafe(32)
                user.reset_token_expires_at = datetime.now() + timedelta(minutes=30)
                db.session.commit()
                reset_link = url_for(
                    "reset_password",
                    role=role,
                    token=user.reset_token,
                    _external=True,
                )
            flash(
                "Jika email terdaftar, tautan reset disiapkan untuk mode lokal.",
                "success",
            )

        return render_template(
            "auth/forgot_password.html",
            role=role,
            reset_link=reset_link,
        )

    @app.route("/reset/<role>/<token>", methods=["GET", "POST"])
    def reset_password(role, token):
        validate_role(role)
        user = User.query.filter_by(role=role, reset_token=token).first_or_404()
        if not user.reset_token_expires_at or user.reset_token_expires_at < datetime.now():
            flash("Tautan reset sudah kedaluwarsa.", "error")
            return redirect(url_for("forgot_password", role=role))

        if request.method == "POST":
            password = request.form.get("password", "")
            confirm_password = request.form.get("confirm_password", "")
            if len(password) < 6:
                flash("Password minimal 6 karakter.", "error")
            elif password != confirm_password:
                flash("Konfirmasi password tidak sama.", "error")
            else:
                user.set_password(password)
                user.reset_token = None
                user.reset_token_expires_at = None
                db.session.commit()
                flash("Password berhasil diubah. Silakan login.", "success")
                return redirect(url_for("login", role=role))

        return render_template("auth/reset_password.html", role=role)
