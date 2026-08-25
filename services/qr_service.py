import qrcode
import os
import uuid
from config import CERTIFICATES_DIR, PUBLIC_BASE_URL


def generate_qr_image(certificate_number: str, base_url: str = None) -> str:
    if base_url is None:
        base_url = PUBLIC_BASE_URL
    verify_url = f"{base_url}/api/public/verify/{certificate_number}"
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(verify_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    os.makedirs(CERTIFICATES_DIR, exist_ok=True)
    filename = f"qr_{certificate_number}_{uuid.uuid4().hex[:8]}.png"
    filepath = os.path.join(CERTIFICATES_DIR, filename)
    img.save(filepath)
    return filepath


def get_verify_url(certificate_number: str, base_url: str = None) -> str:
    if base_url is None:
        base_url = PUBLIC_BASE_URL
    return f"{base_url}/api/public/verify/{certificate_number}"
