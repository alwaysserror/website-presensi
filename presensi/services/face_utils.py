import base64
import os
import tempfile

try:
    import cv2
    import numpy as np
except ImportError:  # pragma: no cover - handled at runtime with a clear message.
    cv2 = None
    np = None


_FACE_CASCADE = None


def require_face_dependencies():
    if cv2 is None or np is None:
        raise ValueError(
            "Paket OpenCV dan NumPy belum terpasang. Jalankan: pip install -r requirements.txt"
        )
    if not hasattr(cv2, "face") or not hasattr(cv2.face, "LBPHFaceRecognizer_create"):
        raise ValueError(
            "LBPH resmi OpenCV belum tersedia. Install ulang dependency dengan: pip install -r requirements.txt"
        )


def get_face_cascade():
    global _FACE_CASCADE
    require_face_dependencies()
    if _FACE_CASCADE is None:
        cascade_path = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
        _FACE_CASCADE = cv2.CascadeClassifier(cascade_path)
        if _FACE_CASCADE.empty():
            raise ValueError("Model deteksi wajah OpenCV tidak ditemukan.")
    return _FACE_CASCADE


def decode_data_url(data_url):
    require_face_dependencies()
    if not isinstance(data_url, str) or len(data_url) < 100:
        raise ValueError("Gambar kamera tidak valid.")

    encoded = data_url.split(",", 1)[1] if "," in data_url else data_url
    try:
        raw = base64.b64decode(encoded)
    except ValueError as exc:
        raise ValueError("Format gambar kamera tidak valid.") from exc

    buffer = np.frombuffer(raw, dtype=np.uint8)
    image = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Gambar kamera gagal dibaca.")
    return image


def extract_face_image(data_url):
    image = decode_data_url(data_url)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    cascade = get_face_cascade()
    faces = cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(80, 80),
    )
    if len(faces) == 0:
        raise ValueError("Wajah belum terdeteksi. Hadapkan wajah ke kamera dengan cahaya cukup.")

    x, y, w, h = max(faces, key=lambda face: face[2] * face[3])
    margin_x = int(w * 0.18)
    margin_y = int(h * 0.22)
    x1 = max(x - margin_x, 0)
    y1 = max(y - margin_y, 0)
    x2 = min(x + w + margin_x, gray.shape[1])
    y2 = min(y + h + margin_y, gray.shape[0])
    face = gray[y1:y2, x1:x2]
    if face.size == 0:
        raise ValueError("Area wajah gagal diproses.")

    face = cv2.resize(face, (160, 160), interpolation=cv2.INTER_AREA)
    face = cv2.equalizeHist(face)
    return face


def create_lbph_recognizer(threshold=None):
    require_face_dependencies()
    if threshold is None:
        return cv2.face.LBPHFaceRecognizer_create(1, 8, 8, 8)
    return cv2.face.LBPHFaceRecognizer_create(1, 8, 8, 8, float(threshold))


def train_lbph_model(face_images, user_id):
    training_images = []
    for face in face_images:
        training_images.append(face)
        training_images.append(cv2.flip(face, 1))

    labels = np.full((len(training_images),), int(user_id), dtype=np.int32)
    recognizer = create_lbph_recognizer()
    recognizer.train(training_images, labels)
    return write_lbph_model(recognizer)


def predict_with_lbph_model(model_xml, face_image, threshold):
    recognizer = load_lbph_model(model_xml, threshold)
    label, distance = recognizer.predict(face_image)
    return int(label), float(distance)


def lbph_distance_to_confidence(distance, threshold):
    if not np.isfinite(distance) or distance < 0:
        return 0.0
    return max(0.0, min(1.0, threshold / (threshold + distance)))


def write_lbph_model(recognizer):
    path = temporary_xml_path()
    try:
        recognizer.write(path)
        with open(path, "r", encoding="utf-8") as file:
            return file.read()
    finally:
        remove_file_silently(path)


def load_lbph_model(model_xml, threshold):
    if not model_xml or "opencv_lbphfaces" not in model_xml:
        raise ValueError("Data wajah lama tidak memakai LBPH resmi. Daftarkan ulang wajah peserta.")

    path = temporary_xml_path()
    try:
        with open(path, "w", encoding="utf-8") as file:
            file.write(model_xml)
        recognizer = create_lbph_recognizer(threshold)
        recognizer.read(path)
        return recognizer
    finally:
        remove_file_silently(path)


def temporary_xml_path():
    handle = tempfile.NamedTemporaryFile(suffix=".xml", delete=False)
    path = handle.name
    handle.close()
    return path


def remove_file_silently(path):
    try:
        os.remove(path)
    except OSError:
        pass
