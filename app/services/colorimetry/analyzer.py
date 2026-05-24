import cv2
import numpy as np

NEUTRAL_LAB = 128.0

SKIN_REGIONS = {
    "mejilla_izq": (0.10, 0.48, 0.28, 0.22),
    "mejilla_der": (0.62, 0.48, 0.28, 0.22),
    "frente": (0.28, 0.20, 0.44, 0.18),
}

SKIN_YCRCB_LOWER = np.array([0, 120, 70], dtype=np.uint8)
SKIN_YCRCB_UPPER = np.array([255, 185, 155], dtype=np.uint8)


def gray_world_balance(bgr: np.ndarray) -> np.ndarray:
    """Corrige el tinte de la luz ambiental sobre la cara."""
    b, g, r = cv2.split(bgr.astype(np.float32))
    avg_b, avg_g, avg_r = b.mean(), g.mean(), r.mean()
    gray_avg = (avg_b + avg_g + avg_r) / 3.0

    scale = lambda channel, avg: np.clip(channel * (gray_avg / max(avg, 1.0)), 0, 255)
    return cv2.merge([
        scale(b, avg_b),
        scale(g, avg_g),
        scale(r, avg_r),
    ]).astype(np.uint8)


def detect_face(gray: np.ndarray):
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    faces = face_cascade.detectMultiScale(
        enhanced, scaleFactor=1.05, minNeighbors=6, minSize=(80, 80)
    )
    if len(faces) == 0:
        return None
    return max(faces, key=lambda f: f[2] * f[3])


def extract_skin_lab_pixels(bgr_roi: np.ndarray):
    ycrcb = cv2.cvtColor(bgr_roi, cv2.COLOR_BGR2YCrCb)
    skin_mask = cv2.inRange(ycrcb, SKIN_YCRCB_LOWER, SKIN_YCRCB_UPPER)

    lab = cv2.cvtColor(bgr_roi, cv2.COLOR_BGR2LAB)
    l_channel = lab[:, :, 0]
    valid = skin_mask & (l_channel >= 35) & (l_channel <= 225)

    if not np.any(valid):
        valid = (l_channel >= 35) & (l_channel <= 225)
    if not np.any(valid):
        return None

    ys, xs = np.where(valid)
    return lab[ys, xs]


def crop_region(image_bgr: np.ndarray, face, region):
    x, y, w, h = face
    rx, ry, rw, rh = region
    x1 = max(0, int(x + rx * w))
    y1 = max(0, int(y + ry * h))
    x2 = min(image_bgr.shape[1], int(x1 + rw * w))
    y2 = min(image_bgr.shape[0], int(y1 + rh * h))
    return image_bgr[y1:y2, x1:x2]


def classify_undertone(a_dev: float, b_dev: float) -> str:
    chroma = float(np.hypot(a_dev, b_dev))
    hue = float(np.degrees(np.arctan2(b_dev, a_dev)))

    if chroma < 4:
        return "Neutro"
    if b_dev <= -2:
        return "Frio"
    if a_dev >= 6 and b_dev <= 10 and a_dev > b_dev * 0.55:
        return "Frio"
    if b_dev >= 6 and hue >= 38:
        return "Calido"
    if abs(b_dev) <= 4 and abs(a_dev) <= 6:
        return "Neutro"
    if b_dev > 2:
        return "Calido"
    if b_dev < 0:
        return "Frio"
    return "Neutro"


def decode_image(contents: bytes) -> np.ndarray:
    image_bgr = cv2.imdecode(np.frombuffer(contents, np.uint8), cv2.IMREAD_COLOR)
    if image_bgr is None:
        raise ValueError("No se pudo leer la imagen")
    return image_bgr


def analyze_subtono(image_bgr: np.ndarray) -> str:
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    face = detect_face(gray)
    if face is None:
        raise ValueError("No se detectó ninguna cara")

    x, y, w, h = face
    face_bgr = gray_world_balance(image_bgr[y:y + h, x:x + w])

    all_skin_pixels = []
    for region in SKIN_REGIONS.values():
        roi = crop_region(face_bgr, (0, 0, w, h), region)
        if roi.size == 0:
            continue
        skin_pixels = extract_skin_lab_pixels(roi)
        if skin_pixels is not None:
            all_skin_pixels.append(skin_pixels)

    if not all_skin_pixels:
        raise ValueError("No se encontraron píxeles de piel válidos para analizar")

    skin_lab = np.vstack(all_skin_pixels)
    a_dev = float(np.median(skin_lab[:, 1]) - NEUTRAL_LAB)
    b_dev = float(np.median(skin_lab[:, 2]) - NEUTRAL_LAB)
    return classify_undertone(a_dev, b_dev)
