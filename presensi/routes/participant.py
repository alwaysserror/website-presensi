from flask import jsonify, render_template, request
from flask_login import current_user

from ..extensions import db
from ..helpers import role_required
from ..models import Attendance, FaceProfile, PresenceSession
from ..services.face_utils import (
    extract_face_image,
    lbph_distance_to_confidence,
    predict_with_lbph_model,
    train_lbph_model,
)


def register_participant_routes(app):
    @app.route("/peserta")
    @role_required("peserta")
    def participant_dashboard():
        open_sessions = (
            PresenceSession.query.filter_by(is_open=True)
            .order_by(PresenceSession.start_time.desc(), PresenceSession.created_at.desc())
            .all()
        )
        available_sessions = [session for session in open_sessions if session.accepts_attendance()]
        attendance_count = Attendance.query.filter_by(participant_id=current_user.id).count()
        return render_template(
            "participant/dashboard.html",
            available_sessions=available_sessions,
            attendance_count=attendance_count,
        )

    @app.route("/peserta/wajah")
    @role_required("peserta")
    def participant_face():
        return render_template("participant/register_face.html")

    @app.post("/api/peserta/wajah")
    @role_required("peserta")
    def api_register_face():
        data = request.get_json(silent=True) or {}
        images = data.get("images") or []
        if len(images) < 3:
            return jsonify({"ok": False, "message": "Ambil minimal 3 sampel wajah."}), 400

        face_images = []
        errors = []
        for image in images[:8]:
            try:
                face_images.append(extract_face_image(image))
            except ValueError as exc:
                errors.append(str(exc))

        if len(face_images) < 3:
            message = errors[0] if errors else "Wajah belum terdeteksi jelas."
            return jsonify({"ok": False, "message": message}), 422

        model_xml = train_lbph_model(face_images, current_user.id)
        profile = current_user.face_profile or FaceProfile(user=current_user)
        profile.model_xml = model_xml
        profile.samples_count = len(face_images)
        db.session.add(profile)
        db.session.commit()

        return jsonify(
            {
                "ok": True,
                "message": f"Model LBPH wajah tersimpan dari {len(face_images)} sampel.",
            }
        )

    @app.route("/peserta/presensi")
    @role_required("peserta")
    def participant_attendance():
        sessions = (
            PresenceSession.query.filter_by(is_open=True)
            .order_by(PresenceSession.start_time.desc(), PresenceSession.created_at.desc())
            .all()
        )
        sessions = [session for session in sessions if session.accepts_attendance()]
        return render_template("participant/attendance.html", sessions=sessions)

    @app.post("/api/peserta/presensi")
    @role_required("peserta")
    def api_attendance_check_in():
        data = request.get_json(silent=True) or {}
        session_id = data.get("session_id")
        image = data.get("image")

        session = db.session.get(PresenceSession, session_id)
        if not session:
            return jsonify({"ok": False, "message": "Sesi tidak ditemukan."}), 404
        if not session.accepts_attendance():
            return jsonify({"ok": False, "message": "Sesi presensi belum dibuka atau sudah ditutup."}), 409
        if not current_user.face_profile:
            return jsonify({"ok": False, "message": "Daftarkan wajah terlebih dahulu."}), 409

        existing = Attendance.query.filter_by(
            session_id=session.id,
            participant_id=current_user.id,
        ).first()
        if existing:
            return jsonify(
                {
                    "ok": True,
                    "message": "Anda sudah presensi pada sesi ini.",
                    "confidence": existing.confidence,
                }
            )

        try:
            live_face = extract_face_image(image)
            threshold = app.config["LBPH_DISTANCE_THRESHOLD"]
            predicted_label, distance = predict_with_lbph_model(
                current_user.face_profile.model_xml,
                live_face,
                threshold,
            )
        except ValueError as exc:
            return jsonify({"ok": False, "message": str(exc)}), 422

        confidence = lbph_distance_to_confidence(distance, threshold)
        if predicted_label != current_user.id or distance > threshold:
            return jsonify(
                {
                    "ok": False,
                    "message": "Wajah tidak cocok dengan model LBPH akun.",
                    "confidence": confidence,
                    "distance": distance,
                    "threshold": threshold,
                }
            ), 403

        attendance = Attendance(
            session=session,
            participant=current_user,
            confidence=confidence,
            status="hadir",
        )
        db.session.add(attendance)
        db.session.commit()

        return jsonify(
            {
                "ok": True,
                "message": "Presensi berhasil dicatat.",
                "confidence": confidence,
                "distance": distance,
            }
        )

    @app.route("/peserta/riwayat")
    @role_required("peserta")
    def participant_history():
        attendances = (
            Attendance.query.filter_by(participant_id=current_user.id)
            .join(PresenceSession)
            .order_by(Attendance.check_in_at.desc())
            .all()
        )
        return render_template("participant/history.html", attendances=attendances)
