from datetime import datetime

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from ..extensions import db
from ..helpers import get_session_or_404, role_required
from ..models import Attendance, PresenceSession, User


def register_admin_routes(app):
    @app.route("/admin")
    @role_required("admin")
    def admin_dashboard():
        total_users = User.query.count()
        total_sessions = PresenceSession.query.count()
        total_attendance = Attendance.query.count()
        today = datetime.now().date()
        attendance_today = Attendance.query.filter(
            db.func.date(Attendance.check_in_at) == today
        ).count()
        return render_template(
            "admin/dashboard.html",
            total_users=total_users,
            total_sessions=total_sessions,
            total_attendance=total_attendance,
            attendance_today=attendance_today,
        )

    @app.route("/admin/pengguna")
    @role_required("admin")
    def admin_users():
        role = request.args.get("role", "")
        query = User.query.order_by(User.created_at.desc())
        if role in ("peserta", "pengajar", "admin"):
            query = query.filter_by(role=role)
        users = query.all()
        return render_template("admin/users.html", users=users, selected_role=role)

    @app.post("/admin/pengguna/<int:user_id>/toggle")
    @role_required("admin")
    def admin_user_toggle(user_id):
        user = db.session.get(User, user_id) or abort(404)
        if user.id == current_user.id:
            flash("Akun admin yang sedang dipakai tidak bisa dinonaktifkan.", "error")
        else:
            user.is_active_user = not user.is_active_user
            db.session.commit()
            flash("Status pengguna diperbarui.", "success")
        return redirect(request.referrer or url_for("admin_users"))

    @app.post("/admin/pengguna/<int:user_id>/hapus")
    @role_required("admin")
    def admin_user_delete(user_id):
        user = db.session.get(User, user_id) or abort(404)
        if user.id == current_user.id:
            flash("Akun admin yang sedang dipakai tidak bisa dihapus.", "error")
        elif user.sessions or user.attendances:
            flash("Pengguna memiliki data sesi/presensi. Nonaktifkan akun sebagai arsip.", "error")
        else:
            db.session.delete(user)
            db.session.commit()
            flash("Pengguna dihapus.", "success")
        return redirect(request.referrer or url_for("admin_users"))

    @app.route("/admin/sesi")
    @role_required("admin")
    def admin_sessions():
        sessions = PresenceSession.query.order_by(PresenceSession.created_at.desc()).all()
        return render_template("admin/sessions.html", sessions=sessions)

    @app.post("/admin/sesi/<int:session_id>/toggle")
    @role_required("admin")
    def admin_session_toggle(session_id):
        session = get_session_or_404(session_id)
        session.is_open = not session.is_open
        db.session.commit()
        flash("Status sesi diperbarui.", "success")
        return redirect(request.referrer or url_for("admin_sessions"))

    @app.post("/admin/sesi/<int:session_id>/hapus")
    @role_required("admin")
    def admin_session_delete(session_id):
        session = get_session_or_404(session_id)
        db.session.delete(session)
        db.session.commit()
        flash("Sesi dihapus oleh admin.", "success")
        return redirect(url_for("admin_sessions"))

    @app.route("/admin/rekap")
    @role_required("admin")
    def admin_recap():
        attendances = (
            Attendance.query.join(PresenceSession)
            .join(User, Attendance.participant_id == User.id)
            .order_by(Attendance.check_in_at.desc())
            .all()
        )
        return render_template("admin/recap.html", attendances=attendances)
