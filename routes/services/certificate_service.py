from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import os
from datetime import datetime

def generate_certificate_pdf(cert_data, output_path):
    c = canvas.Canvas(output_path, pagesize=A4)
    c.drawString(100, 800, f"Certificate Number: {cert_data['certificate_number']}")
    c.drawString(100, 780, f"Instrument ID: {cert_data['instrument_id']}")
    c.drawString(100, 760, f"Result: {cert_data['result']}")
    c.drawString(100, 740, f"Issue Date: {datetime.now().strftime('%Y-%m-%d')}")
    c.save()
    return output_path
