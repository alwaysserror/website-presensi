import os


ROLE_LABELS = {
    "peserta": "Peserta",
    "pengajar": "Pengajar",
    "admin": "Admin",
}

ALLOWED_ROLES = tuple(ROLE_LABELS.keys())


def build_database_uri():
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url.replace("mysql://", "mysql+pymysql://", 1)

    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")
    host = os.getenv("DB_HOST", "127.0.0.1")
    port = os.getenv("DB_PORT", "3306")
    database = os.getenv("DB_NAME", "presensi_face")

    auth = user if not password else f"{user}:{password}"
    return f"mysql+pymysql://{auth}@{host}:{port}/{database}?charset=utf8mb4"
