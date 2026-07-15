from flask import flash, redirect, render_template, url_for
from flask_login import current_user, login_required, logout_user


def register_main_routes(app):
    @app.route("/")
    def landing():
        return render_template("landing.html")

    @app.route("/dashboard")
    @login_required
    def dashboard():
        if current_user.role == "peserta":
            return redirect(url_for("participant_dashboard"))
        if current_user.role == "pengajar":
            return redirect(url_for("teacher_dashboard"))
        return redirect(url_for("admin_dashboard"))

    @app.route("/logout", methods=["POST"])
    @login_required
    def logout():
        logout_user()
        flash("Anda sudah keluar.", "success")
        return redirect(url_for("landing"))
