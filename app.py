import io
import os
from flask import Flask, request, jsonify, send_file
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle

app = Flask(__name__)

# ── Colours ──────────────────────────────────────────────────────────
WIDTH, HEIGHT = A4
BLACK     = colors.HexColor('#1F2937')
BODY_GREY = colors.HexColor('#4B5563')
MID_GREY  = colors.HexColor('#9CA3AF')
RULE_GREY = colors.HexColor('#D1D5DB')
MARGIN    = 44
COL_MID   = WIDTH / 2 + 10

# Logo lives next to app.py
LOGO = os.path.join(os.path.dirname(__file__), "enviroware_logo_clean.png")


def micro_label(c, x, y, text):
    c.setFillColor(MID_GREY)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(x, y, text)
    c.setStrokeColor(RULE_GREY)
    c.setLineWidth(0.5)
    c.line(x, y - 5, x + 200, y - 5)


def build_pdf(data: dict) -> bytes:
    """Render a packing slip and return raw PDF bytes."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)

    # ── Top rule ──────────────────────────────────────────────────────
    c.setStrokeColor(BLACK)
    c.setLineWidth(2)
    c.line(0, HEIGHT - 3, WIDTH, HEIGHT - 3)

    # ── Header ────────────────────────────────────────────────────────
    header_bot = HEIGHT - 78
    c.drawImage(LOGO, MARGIN, header_bot + 8,
                width=115, height=48,
                preserveAspectRatio=True, mask='auto')

    c.setFillColor(BLACK)
    c.setFont("Helvetica-Bold", 22)
    c.drawRightString(WIDTH - MARGIN, header_bot + 30, "PACKING SLIP")

    c.setStrokeColor(RULE_GREY)
    c.setLineWidth(0.8)
    c.line(MARGIN, header_bot, WIDTH - MARGIN, header_bot)

    # ── Two-column section ────────────────────────────────────────────
    section_top = header_bot - 22

    # LEFT — FROM + invoice details
    micro_label(c, MARGIN, section_top, "FROM")
    ly = section_top - 18
    c.setFillColor(BLACK)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(MARGIN, ly, "Enviroware")
    ly -= 14

    for line in [data['company_address1'], data['company_address2'],
                 data['company_phone'], data['company_email']]:
        c.setFillColor(BODY_GREY)
        c.setFont("Helvetica", 9)
        c.drawString(MARGIN, ly, line)
        ly -= 12

    ly -= 10
    micro_label(c, MARGIN, ly, "INVOICE DETAILS")
    ly -= 16
    for label, value in [("Invoice No.", data['invoice_no']), ("PO", data['po'])]:
        c.setFillColor(BODY_GREY)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(MARGIN, ly, label)
        c.setFillColor(BLACK)
        c.setFont("Helvetica", 9)
        c.drawString(MARGIN + 58, ly, value)
        ly -= 13

    # RIGHT — SHIP TO
    micro_label(c, COL_MID, section_top, "SHIP TO")
    ry = section_top - 28
    for i, line in enumerate(data['ship_to']):
        if not line:
            ry -= 6
            continue
        if i == 0:
            c.setFillColor(BLACK)
            c.setFont("Helvetica-Bold", 20)
            c.drawString(COL_MID, ry, line)
            ry -= 26
        else:
            c.setFillColor(BODY_GREY)
            c.setFont("Helvetica", 16)
            c.drawString(COL_MID, ry, line)
            ry -= 22

    # ── Table ─────────────────────────────────────────────────────────
    table_top_y = min(ly, ry) - 18
    c.setStrokeColor(RULE_GREY)
    c.setLineWidth(0.8)
    c.line(MARGIN, table_top_y + 8, WIDTH - MARGIN, table_top_y + 8)

    col_widths = [46, 80, 0, 82]
    col_widths[2] = WIDTH - (MARGIN * 2) - sum(w for w in col_widths if w)

    # Normalise line_items — accept either a list of lists or list of dicts
    raw_items = data['line_items']
    def normalise_item(item):
        if isinstance(item, dict):
            # Try common key names from DocuPipe / various sources
            qty   = str(item.get('qty') or item.get('quantity') or item.get('QTY') or '')
            sku   = str(item.get('sku') or item.get('SKU') or item.get('product_code') or '')
            desc  = str(item.get('description') or item.get('desc') or item.get('DESCRIPTION') or '')
            price = str(item.get('unit_price') or item.get('price') or item.get('UNIT PRICE') or '')
            return [qty, sku, desc, price]
        return list(item)
    normalised_items = [normalise_item(i) for i in raw_items]
    table_data = [['QTY', 'SKU', 'DESCRIPTION', 'UNIT PRICE']] + normalised_items
    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, 0), 8),
        ('TEXTCOLOR',     (0, 0), (-1, 0), BLACK),
        ('TOPPADDING',    (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('LINEBELOW',     (0, 0), (-1, 0), 1, BLACK),
        ('FONTNAME',      (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE',      (0, 1), (-1, -1), 9.5),
        ('TOPPADDING',    (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
        ('TEXTCOLOR',     (0, 1), (-1, -1), BLACK),
        ('LEFTPADDING',   (0, 0), (-1, -1), 10),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
        ('LINEBELOW',     (0, 1), (-1, -2), 0.4, RULE_GREY),
        ('LINEBELOW',     (0, -1), (-1, -1), 1, BLACK),
        ('ALIGN',  (0, 0), (0, -1), 'CENTER'),
        ('ALIGN',  (3, 0), (3, -1), 'RIGHT'),
        ('ALIGN',  (2, 0), (2, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    _, h = t.wrap(WIDTH - MARGIN * 2, 400)
    t.drawOn(c, MARGIN, table_top_y - h)

    # ── Footer ────────────────────────────────────────────────────────
    c.setStrokeColor(RULE_GREY)
    c.setLineWidth(0.5)
    c.line(MARGIN, 28, WIDTH - MARGIN, 28)
    c.setFillColor(MID_GREY)
    c.setFont("Helvetica", 7.5)
    c.drawString(MARGIN, 16,
                 "Enviroware  ·  orders@primetie.co.nz  ·  (07) 549-1716  ·  93 Tetley Road, Katikati")
    c.drawRightString(WIDTH - MARGIN, 16, "Page 1 of 1")

    c.save()
    buf.seek(0)
    return buf.read()


# ── Routes ────────────────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/packing-slip", methods=["POST"])
def packing_slip():
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"error": "Invalid or missing JSON body"}), 400

    required = ["invoice_no", "po", "ship_to", "company_email",
                "company_phone", "company_address1", "company_address2",
                "line_items"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    try:
        pdf_bytes = build_pdf(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    filename = f"PKS{data['invoice_no']}.pdf"
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
