










import os
import json
import datetime

from core import files

try:
    from reportlab.pdfgen import canvas as _rl_canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    _HAVE_RL = True
except Exception:
    _HAVE_RL = False

BRAND = (0.906, 0.4, 0.102)



def card_brand(number):
    n = (number or "").replace(" ", "")
    if n.startswith("4"):
        return "Visa"
    if n[:2] in ("34", "37"):
        return "Amex"
    if n[:1] == "5" or n[:2] in ("22", "23", "24", "25", "26", "27"):
        return "Mastercard"
    if n.startswith("6"):
        return "Discover"
    return "Card"


def _pay_line(o):
    brand = (o.get("pay_brand") or "Card")
    if brand.strip().lower() in ("cash on delivery", "cod", "cash"):
        return "Payment: Cash on delivery"
    return "Paid with: {} ****{}".format(brand, o.get("pay_last4") or "----")


def _money(v):
    try:
        return "${:,.2f}".format(float(v))
    except (TypeError, ValueError):
        return "$0.00"


def _items(o):
    its = o.get("items")
    if isinstance(its, str):
        try:
            its = json.loads(its)
        except Exception:
            its = []
    if not its:
        its = [{"name": "Order total", "qty": 1, "price": o.get("total", 0)}]
    norm = []
    for it in its:
        norm.append({
            "name": str(it.get("name", "Item")),
            "qty": int(it.get("qty", 1) or 1),
            "price": float(it.get("price", 0) or 0),
        })
    return norm


def _subtotal(items):
    return sum(i["price"] * i["qty"] for i in items)


def _addr_lines(o):
    out = [o.get("ship_name") or "Customer"]
    if o.get("ship_addr"):
        out.append(o["ship_addr"])
    city_zip = " ".join(x for x in (o.get("ship_city"), o.get("ship_zip")) if x)
    if city_zip.strip():
        out.append(city_zip.strip())
    return out



def render_txt(o):
    items = _items(o)
    sub = _subtotal(items)
    total = float(o.get("total", sub))
    lines = [
        "KARTLY INVOICE {}".format(o.get("reference", "")),
        "Date: {}".format((o.get("created") or "")[:10]),
        "Status: {}".format(o.get("status", "")),
        "",
        "Bill to:",
    ]
    lines += ["  " + l for l in _addr_lines(o)]
    lines += ["", "Items:"]
    for it in items:
        lines.append("  {} x{}  {}".format(it["name"], it["qty"], _money(it["price"] * it["qty"])))
    lines += [
        "",
        "Subtotal: {}".format(_money(sub)),
    ]
    if sub - total > 0.005:
        lines.append("Discount: -{}".format(_money(sub - total)))
    lines += [
        "Total: {}".format(_money(total)),
        _pay_line(o),
    ]

    if o.get("user_id") == 1:
        lines += ["",
                  "Internal note: VIP/staff account - confidential.",
                  "FLAG{br0k3n_0bj3ct_l3v3l_auth}"]
    return "\n".join(lines) + "\n"



def _pdf_reportlab(o):
    import io
    items = _items(o)
    sub = _subtotal(items)
    total = float(o.get("total", sub))
    buf = io.BytesIO()
    c = _rl_canvas.Canvas(buf, pagesize=A4)
    W, H = A4


    c.setFillColorRGB(*BRAND)
    c.rect(0, H - 32 * mm, W, 32 * mm, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 26)
    c.drawString(20 * mm, H - 20 * mm, "kartly")
    c.setFont("Helvetica", 11)
    c.drawRightString(W - 20 * mm, H - 15 * mm, "INVOICE")
    c.drawRightString(W - 20 * mm, H - 21 * mm, o.get("reference", ""))
    c.drawRightString(W - 20 * mm, H - 27 * mm, "Date: {}".format((o.get("created") or "")[:10]))


    y = H - 45 * mm
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(20 * mm, y, "BILL TO")
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica", 11)
    y -= 6 * mm
    for ln in _addr_lines(o):
        c.drawString(20 * mm, y, ln)
        y -= 5.5 * mm
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.setFont("Helvetica", 10)
    c.drawRightString(W - 20 * mm, H - 45 * mm, "Status: {}".format(o.get("status", "")))


    y -= 6 * mm
    c.setFillColorRGB(0.95, 0.95, 0.95)
    c.rect(20 * mm, y - 2 * mm, W - 40 * mm, 8 * mm, fill=1, stroke=0)
    c.setFillColorRGB(0.2, 0.2, 0.2)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(22 * mm, y, "Item")
    c.drawRightString(W - 60 * mm, y, "Qty")
    c.drawRightString(W - 40 * mm, y, "Unit")
    c.drawRightString(W - 22 * mm, y, "Amount")
    y -= 9 * mm
    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0, 0, 0)
    for it in items:
        c.drawString(22 * mm, y, it["name"][:48])
        c.drawRightString(W - 60 * mm, y, str(it["qty"]))
        c.drawRightString(W - 40 * mm, y, _money(it["price"]))
        c.drawRightString(W - 22 * mm, y, _money(it["price"] * it["qty"]))
        y -= 7 * mm


    y -= 4 * mm
    c.setStrokeColorRGB(0.8, 0.8, 0.8)
    c.line(W - 90 * mm, y, W - 20 * mm, y)
    y -= 7 * mm
    c.setFont("Helvetica", 10)
    c.drawRightString(W - 40 * mm, y, "Subtotal")
    c.drawRightString(W - 22 * mm, y, _money(sub))
    if sub - total > 0.005:
        y -= 6 * mm
        c.drawRightString(W - 40 * mm, y, "Discount")
        c.drawRightString(W - 22 * mm, y, "-" + _money(sub - total))
    y -= 8 * mm
    c.setFont("Helvetica-Bold", 13)
    c.setFillColorRGB(*BRAND)
    c.drawRightString(W - 40 * mm, y, "Total")
    c.drawRightString(W - 22 * mm, y, _money(total))


    c.setFillColorRGB(0.3, 0.3, 0.3)
    c.setFont("Helvetica", 10)
    y -= 12 * mm
    c.drawString(20 * mm, y, _pay_line(o))
    c.setFont("Helvetica-Oblique", 9)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawString(20 * mm, 18 * mm, "Thank you for shopping with Kartly.  Questions? support@kartly.lab")
    c.showPage()
    c.save()
    return buf.getvalue()


def _pdf_fallback(o):

    def esc(s):
        return s.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")

    text = "KARTLY  " + o.get("reference", "")
    body = render_txt(o).splitlines()
    parts = ["BT", "/F1 11 Tf", "15 TL", "1 0 0 1 56 780 Tm", "({}) Tj".format(esc(text)), "T* "]
    for ln in body:
        parts.append("T* ({}) Tj".format(esc(ln)))
    parts.append("ET")
    content = ("\n".join(parts)).encode("latin-1", "replace")

    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = b"%PDF-1.4\n"
    offsets = []
    for i, ob in enumerate(objs, 1):
        offsets.append(len(out))
        out += str(i).encode() + b" 0 obj\n" + ob + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 " + str(len(objs) + 1).encode() + b"\n0000000000 65535 f \n"
    for off in offsets:
        out += ("%010d 00000 n \n" % off).encode()
    out += (b"trailer\n<< /Size " + str(len(objs) + 1).encode() + b" /Root 1 0 R >>\n"
            b"startxref\n" + str(xref).encode() + b"\n%%EOF")
    return out


def render_pdf(o):
    if _HAVE_RL:
        try:
            return _pdf_reportlab(o)
        except Exception:
            pass
    return _pdf_fallback(o)



def write_invoice(o):

    ref = o.get("reference")
    if not ref:
        return
    os.makedirs(files.INVOICE_DIR, exist_ok=True)
    with open(os.path.join(files.INVOICE_DIR, ref + ".txt"), "w", encoding="utf-8") as fh:
        fh.write(render_txt(o))
    with open(os.path.join(files.INVOICE_DIR, ref + ".pdf"), "wb") as fh:
        fh.write(render_pdf(o))


_ORDER_COLS = ("user_id", "reference", "total", "status", "created",
               "ship_name", "ship_addr", "ship_city", "ship_zip",
               "pay_brand", "pay_last4", "items_json")


def order_dict(row):

    try:
        d = {k: row[k] for k in _ORDER_COLS}
    except (IndexError, KeyError, TypeError):
        d = dict(zip(_ORDER_COLS, row))
    d["items"] = d.pop("items_json", None)
    return d


def seed_all(con):

    cur = con.execute(
        "SELECT " + ",".join(_ORDER_COLS) + " FROM orders")
    for row in cur.fetchall():
        write_invoice(order_dict(dict(zip(_ORDER_COLS, row))))
