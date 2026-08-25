import qrcode

def generate_qr(certificate_number: str, output_path: str):
    url = f"/api/public/verify/{certificate_number}"
    img = qrcode.make(url)
    img.save(output_path)
    return output_path
