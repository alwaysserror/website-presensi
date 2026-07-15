from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user

from ..extensions import db
from ..helpers import ensure_session_owner, fill_session_from_form, get_session_or_404, role_required
from ..models import Attendance, PresenceSession, User


def register_teacher_routes(app):
    @app.route("/pengajar")
    @role_required("pengajar")
    def teacher_dashboard():
        sessions = (
            PresenceSession.query.filter_by(teacher_id=current_user.id)
            .order_by(PresenceSession.created_at.desc())
            .limit(6)
            .all()
        )
        total_attendance = (
            Attendance.query.join(PresenceSession)
            .filter(PresenceSession.teacher_id == current_user.id)
            .count()
        )
        return render_template(
            "teacher/dashboard.html",
            sessions=sessions,
            total_attendance=total_attendance,
        )

    @app.route("/pengajar/sesi")
    @role_required("pengajar")
    def teacher_sessions():
        sessions = (
            PresenceSession.query.filter_by(teacher_id=current_user.id)
            .order_by(PresenceSession.created_at.desc())
            .all()
        )
        return render_template("teacher/sessions.html", sessions=sessions)

    @app.route("/pengajar/sesi/buat", methods=["GET", "POST"])
    @role_required("pengajar")
    def teacher_session_create():
        if request.method == "POST":
            session = PresenceSession(teacher=current_user)
            fill_session_from_form(session)
            db.session.add(session)
            db.session.commit()
            flash("Sesi presensi berhasil dibuat.", "success")
            return redirect(url_for("teacher_sessions"))

        return render_template("teacher/session_form.html", session=None)

    @app.route("/pengajar/sesi/<int:session_id>")
    @role_required("pengajar")
    def teacher_session_detail(session_id):
        session = get_session_or_404(session_id)
        ensure_session_owner(session)
        attendances = (
            Attendance.query.filter_by(session_id=session.id)
            .join(User, Attendance.participant_id == User.id)
            .order_by(Attendance.check_in_at.desc())
            .all()
        )
        return render_template(
            "teacher/session_detail.html",
            session=session,
            attendances=attendances,
        )

    @app.route("/pengajar/sesi/<int:session_id>/edit", methods=["GET", "POST"])
    @role_required("pengajar")
    def teacher_session_edit(session_id):
        session = get_session_or_404(session_id)
        ensure_session_owner(session)
        if request.method == "POST":
            fill_session_from_form(session)
            db.session.commit()
            flash("Sesi presensi berhasil diperbarui.", "success")
            return redirect(url_for("teacher_session_detail", session_id=session.id))

        return render_template("teacher/session_form.html", session=session)

    @app.post("/pengajar/sesi/<int:session_id>/toggle")
    @role_required("pengajar")
    def teacher_session_toggle(session_id):
        session = get_session_or_404(session_id)
        ensure_session_owner(session)
        session.is_open = not session.is_open
        db.session.commit()
        flash("Status sesi diperbarui.", "success")
        return redirect(request.referrer or url_for("teacher_sessions"))

    @app.post("/pengajar/sesi/<int:session_id>/hapus")
    @role_required("pengajar")
    def teacher_session_delete(session_id):
        session = get_session_or_404(session_id)
        ensure_session_owner(session)
        db.session.delete(session)
        db.session.commit()
        flash("Sesi presensi dihapus.", "success")
        return redirect(url_for("teacher_sessions"))

    @app.route("/pengajar/rekap")
    @role_required("pengajar")
    def teacher_recap():
        sessions = (
            PresenceSession.query.filter_by(teacher_id=current_user.id)
            .order_by(PresenceSession.created_at.desc())
            .all()
        )
        return render_template("teacher/recap.html", sessions=sessions)
