from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .config import ROLE_LABELS
from .extensions import db, login_manager


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, index=True)
    phone = db.Column(db.String(40))
    is_active_user = db.Column(db.Boolean, nullable=False, default=True)
    reset_token = db.Column(db.String(128), index=True)
    reset_token_expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    face_profile = db.relationship(
        "FaceProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    attendances = db.relationship(
        "Attendance",
        back_populates="participant",
        cascade="all, delete-orphan",
        foreign_keys="Attendance.participant_id",
    )
    sessions = db.relationship(
        "PresenceSession",
        back_populates="teacher",
        foreign_keys="PresenceSession.teacher_id",
    )

    @property
    def is_active(self):
        return self.is_active_user

    @property
    def role_label(self):
        return ROLE_LABELS.get(self.role, self.role.title())

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class FaceProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, unique=True)
    model_xml = db.Column("descriptor_json", db.Text, nullable=False)
    samples_count = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now,
    )

    user = db.relationship("User", back_populates="face_profile")


class PresenceSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    class_name = db.Column(db.String(120))
    description = db.Column(db.Text)
    location = db.Column(db.String(160))
    teacher_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    is_open = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now,
    )

    teacher = db.relationship(
        "User",
        back_populates="sessions",
        foreign_keys=[teacher_id],
    )
    attendances = db.relationship(
        "Attendance",
        back_populates="session",
        cascade="all, delete-orphan",
    )

    def accepts_attendance(self):
        now = datetime.now()
        if not self.is_open:
            return False
        if self.start_time and now < self.start_time:
            return False
        if self.end_time and now > self.end_time:
            return False
        return True


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("presence_session.id"), nullable=False)
    participant_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    check_in_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    confidence = db.Column(db.Float, nullable=False, default=0.0)
    status = db.Column(db.String(30), nullable=False, default="hadir")
    note = db.Column(db.String(255))

    session = db.relationship("PresenceSession", back_populates="attendances")
    participant = db.relationship(
        "User",
        back_populates="attendances",
        foreign_keys=[participant_id],
    )

    __table_args__ = (
        db.UniqueConstraint("session_id", "participant_id", name="uq_attendance_once"),
    )


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
