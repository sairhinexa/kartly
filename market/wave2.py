









import os
import re
import json
import base64
import subprocess
import urllib.request

from flask import (request, render_template, redirect, url_for, session,
                   jsonify, Response, abort, send_file)

from core import db, files, invoices
from market.views import bp, current_user, nav_context

ADMIN_PW = dict((u, p) for u, p, *_ in db.USERS).get("administrator", "s3cr3t")

FAKE_METADATA = json.dumps({
    "Code": "Success",
    "AccessKeyId": "ASIAKARTLY7PRODXMPL",
    "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYKARTLYKEY",
    "Token": "IQoJb3JpZ2luX2VjE...kartly-instance-role...",
    "Expiration": "2026-12-31T23:59:59Z",
    "_note": "FLAG{ssrf_t0_cl0ud_m3t4d4t4}",
}, indent=2)


ADMIN_MEMO = ("Reminder: Q4 board pack is staged in /secret. Rotate production "
              "credentials after the security audit. FLAG{4dm1n_c0ns0l3_r34ch3d}")





COD_MAX = 50.00


def _cart():
    return session.setdefault("cart", [])


def _totals():
    items = _cart()
    subtotal = sum(float(i["price"]) * int(i["qty"]) for i in items)
    discount = float(session.get("discount", 0))
    total = subtotal * (1 - discount)
    return items, subtotal, discount, total


@bp.route("/cart")
def cart():
    items, subtotal, discount, total = _totals()
    return render_template("cart.html", items=items, subtotal=subtotal,
                           discount=discount, total=total,
                           notice=session.pop("cart_notice", None), **nav_context(db.get_db()))


@bp.route("/cart/add", methods=["POST"])
def cart_add():
    con = db.get_db()
    pid = request.form.get("product_id", "0")
    p = con.execute("SELECT name FROM products WHERE id = ?", (pid,)).fetchone()
    name = p["name"] if p else f"Item {pid}"

    try:
        price = float(request.form.get("price", "0"))
        qty = int(request.form.get("qty", "1"))
    except ValueError:
        price, qty = 0.0, 1
    _cart().append({"product_id": pid, "name": name, "price": price, "qty": qty})
    session.modified = True
    session["cart_notice"] = f"Added {name} to your basket."
    return redirect(url_for("market.cart"))


@bp.route("/cart/update", methods=["POST"])
def cart_update():
    items = _cart()
    try:
        idx = int(request.form.get("idx"))
        items[idx]["qty"] = int(request.form.get("qty"))
        session.modified = True
    except (ValueError, IndexError, TypeError):
        pass
    return redirect(url_for("market.cart"))


@bp.route("/cart/remove/<int:idx>")
def cart_remove(idx):
    items = _cart()
    if 0 <= idx < len(items):
        items.pop(idx)
        session.modified = True
    return redirect(url_for("market.cart"))


@bp.route("/cart/coupon", methods=["POST"])
def cart_coupon():
    code = request.form.get("code", "").strip().upper()

    if code in ("SAVE10", "WELCOME10"):
        session["discount"] = float(session.get("discount", 0)) + 0.10
    elif code == "SAVE25":
        session["discount"] = float(session.get("discount", 0)) + 0.25
    return redirect(url_for("market.cart"))


@bp.route("/checkout", methods=["GET", "POST"])
def checkout():
    con = db.get_db()
    items, subtotal, discount, total = _totals()
    user = current_user(con)
    if request.method == "POST":
        if not items:
            return redirect(url_for("market.cart"))
        uid = user["id"] if user else None
        f = request.form


        ship_name = (f.get("ship_name") or (user["full_name"] if user else "") or "").strip()
        ship_addr = (f.get("ship_addr") or (user["address"] if user else "") or "").strip()
        ship_city = (f.get("ship_city") or "").strip()
        ship_zip = (f.get("ship_zip") or "").strip()
        pay_method = (f.get("pay_method") or "card").lower()
        if pay_method == "cod":



            card_num, brand, last4 = "", "Cash on Delivery", ""
        else:
            card_num = re.sub(r"\s+", "", f.get("card_number", ""))
            brand = invoices.card_brand(card_num) if card_num else "Card"
            last4 = card_num[-4:] if len(card_num) >= 4 else "----"
        import secrets
        ref = "KTLY-2026-" + secrets.token_hex(3).upper()


        con.execute(
            "INSERT INTO orders(user_id,reference,total,status,created,"
            "ship_name,ship_addr,ship_city,ship_zip,pay_brand,pay_last4,items_json) "
            "VALUES(?,?,?,?,datetime('now'),?,?,?,?,?,?,?)",
            (uid, ref, total, "Processing", ship_name, ship_addr, ship_city, ship_zip,
             brand, last4, json.dumps(items)))

        if f.get("save_card") and card_num and uid:
            con.execute("INSERT INTO cards(user_id,brand,number,expiry,cvv,cardholder) "
                        "VALUES(?,?,?,?,?,?)",
                        (uid, brand, card_num, f.get("card_expiry", ""),
                         f.get("card_cvv", ""), ship_name))
        con.commit()

        row = con.execute(
            "SELECT " + ",".join(invoices._ORDER_COLS) + " FROM orders WHERE reference = ?",
            (ref,)).fetchone()
        if row:
            invoices.write_invoice(invoices.order_dict(dict(zip(invoices._ORDER_COLS, row))))
        session["cart"] = []
        session["discount"] = 0
        return render_template("checkout.html", placed=True, reference=ref, total=total,
                               **nav_context(con))
    return render_template("checkout.html", placed=False, items=items, subtotal=subtotal,
                           discount=discount, total=total,
                           cod_max=COD_MAX, cod_available=(total <= COD_MAX),
                           **nav_context(con))


@bp.route("/account/invoice/view")
def invoice_view():

    con = db.get_db()
    ref = request.args.get("ref", "")
    if not re.fullmatch(r"[A-Za-z0-9\-]{1,40}", ref or ""):
        return Response("Invalid invoice reference", status=400, mimetype="text/plain")
    row = con.execute(
        "SELECT " + ",".join(invoices._ORDER_COLS) + " FROM orders WHERE reference = ?",
        (ref,)).fetchone()
    if not row:
        return Response("Invoice not found", status=404, mimetype="text/plain")
    o = invoices.order_dict(dict(zip(invoices._ORDER_COLS, row)))
    items = invoices._items(o)
    subtotal = invoices._subtotal(items)
    total = float(o.get("total") or subtotal)
    return render_template("invoice_view.html", o=o, items=items, subtotal=subtotal,
                           total=total, discount=subtotal - total,
                           pay_line=invoices._pay_line(o), ref=ref, **nav_context(con))


@bp.route("/account/invoice.pdf")
def invoice_pdf():

    con = db.get_db()
    ref = request.args.get("ref", "")
    if not re.fullmatch(r"[A-Za-z0-9\-]{1,40}", ref or ""):
        return Response("Invalid invoice reference", status=400, mimetype="text/plain")
    path = os.path.join(files.INVOICE_DIR, ref + ".pdf")
    if not os.path.exists(path):

        row = con.execute(
            "SELECT " + ",".join(invoices._ORDER_COLS) + " FROM orders WHERE reference = ?",
            (ref,)).fetchone()
        if row:
            invoices.write_invoice(invoices.order_dict(dict(zip(invoices._ORDER_COLS, row))))
    if not os.path.exists(path):
        return Response("Invoice not found", status=404, mimetype="text/plain")
    return send_file(path, mimetype="application/pdf",
                     as_attachment=True, download_name=ref + ".pdf")





@bp.route("/account/avatar/upload", methods=["POST"])
def avatar_upload():
    f = request.files.get("avatar")
    if not f:
        return redirect(url_for("market.account"))

    dest = os.path.join(files.AVATAR_DIR, f.filename)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    f.save(dest)
    session["cart_notice"] = f"Uploaded {f.filename}"
    return redirect(url_for("market.avatar_view", file=f.filename))


@bp.route("/account/avatar/view")
def avatar_view():

    f = request.args.get("file", "default.txt")
    clean = f.replace("../", "").replace("..\\", "")
    path = os.path.join(files.AVATAR_DIR, clean)
    try:
        data = open(path, "rb").read()
    except OSError as e:
        return Response(f"Not found: {e}", status=404)
    ctype = "text/html" if f.lower().endswith((".html", ".htm", ".svg")) else "application/octet-stream"
    if f.lower().endswith(".svg"):
        ctype = "image/svg+xml"
    return Response(data, mimetype=ctype)





@bp.route("/account/email", methods=["GET", "POST"])
def account_email():
    con = db.get_db()
    user = current_user(con)
    if not user:
        return redirect(url_for("market.login"))
    updated = False
    if request.method == "POST":

        new = request.form.get("email", "")
        con.execute("UPDATE users SET email = ? WHERE id = ?", (new, user["id"]))
        con.commit()
        updated = True
        user = current_user(con)
    return render_template("account_email.html", user=user, updated=updated, **nav_context(con))





def _require_admin(con):
    user = current_user(con)
    if not user or user["role"] != "admin":
        abort(403)
    return user


@bp.route("/admin")
def admin():
    con = db.get_db()
    _require_admin(con)
    users = con.execute("SELECT id,username,email,role FROM users ORDER BY id").fetchall()
    return render_template("admin.html", users=users, notice=session.pop("admin_notice", None),
                           output=None, host=None, memo=ADMIN_MEMO, **nav_context(con))


@bp.route("/admin/delete")
def admin_delete():
    con = db.get_db()
    _require_admin(con)
    username = request.args.get("username", "")
    con.execute("DELETE FROM users WHERE username = ?", (username,))
    con.commit()
    session["admin_notice"] = f"Deleted user '{username}'."
    return redirect(url_for("market.admin"))


@bp.route("/admin/diagnostics", methods=["POST"])
def admin_diag():
    con = db.get_db()
    _require_admin(con)
    host = request.form.get("host", "127.0.0.1")

    cmd = f"ping -n 1 {host}"
    try:
        out = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
        output = (out.stdout or "") + (out.stderr or "")
    except subprocess.TimeoutExpired:
        output = "Command timed out."
    users = con.execute("SELECT id,username,email,role FROM users ORDER BY id").fetchall()
    return render_template("admin.html", users=users, notice=None, output=output, host=host,
                           memo=ADMIN_MEMO, **nav_context(con))


@bp.route("/admin/export")
def admin_export():
    con = db.get_db()
    user = current_user(con)


    if not user or user["role"] != "admin":
        return jsonify({"error": "forbidden: admin role required"}), 403
    rows = con.execute("SELECT id,username,password,email,role,api_token FROM users").fetchall()
    return jsonify({
        "export": "all_users",
        "flag": "FLAG{pr1v_3sc_t0_4dm1n_data_export}",
        "users": [{k: r[k] for k in r.keys()} for r in rows],
    })







@bp.route("/account/profile", methods=["GET", "POST"])
def profile():
    con = db.get_db()
    user = current_user(con)
    if not user:
        return redirect(url_for("market.login"))
    saved = False
    if request.method == "POST":

        con.execute("UPDATE users SET city = ? WHERE id = ?",
                    (request.form.get("city", ""), user["id"]))
        con.commit()
        saved = True
    return render_template("profile.html", saved=saved, **nav_context(con))


@bp.route("/nearby")
def nearby():
    con = db.get_db()
    user = current_user(con)
    if not user:
        return redirect(url_for("market.login"))
    city = user["city"] or ""

    sql = "SELECT username, city FROM users WHERE city = '%s'" % city
    rows, error = db.vuln_query(con, sql)
    results = [[("" if v is None else str(v)) for v in tuple(r)] for r in rows] if rows else []
    return render_template("nearby.html", results=results, error=error, city=city, **nav_context(con))







@bp.route("/contact", methods=["GET", "POST"])
def contact():
    con = db.get_db()
    sent = False
    if request.method == "POST":
        con.execute("INSERT INTO messages(name,email,body,created) VALUES(?,?,?,datetime('now'))",
                    (request.form.get("name", ""), request.form.get("email", ""),
                     request.form.get("body", "")))
        con.commit()
        sent = True
    return render_template("contact.html", sent=sent, **nav_context(con))


@bp.route("/admin/messages")
def admin_messages():
    con = db.get_db()
    _require_admin(con)
    msgs = con.execute("SELECT * FROM messages ORDER BY id DESC").fetchall()
    return render_template("admin_messages.html", msgs=msgs, **nav_context(con))





@bp.route("/seller/import")
def seller_import():
    con = db.get_db()
    url = request.args.get("url")
    fetched = None
    if url:
        fetched = _ssrf_fetch(url)
    return render_template("seller_import.html", url=url, fetched=fetched, **nav_context(con))


def _ssrf_fetch(url):

    if "169.254.169.254" in url:
        return FAKE_METADATA
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "KartlyImageBot/1.0"})
        with urllib.request.urlopen(req, timeout=4) as r:
            body = r.read(6000)
        try:
            return body.decode("utf-8", "replace")
        except Exception:
            return f"<{len(body)} bytes of binary content fetched>"
    except Exception as e:
        return f"Fetch error: {e}"





def _cors(resp):

    origin = request.headers.get("Origin")
    if origin:
        resp.headers["Access-Control-Allow-Origin"] = origin
        resp.headers["Access-Control-Allow-Credentials"] = "true"
    return resp


@bp.route("/api/account")
def api_account():
    con = db.get_db()
    user = current_user(con)
    if not user:
        return _cors(jsonify({"error": "not authenticated"})), 401

    return _cors(jsonify({k: user[k] for k in user.keys()}))


@bp.route("/api/users/<int:uid>")
def api_user(uid):
    con = db.get_db()

    row = con.execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone()
    if not row:
        return jsonify({"error": "not found"}), 404
    return _cors(jsonify({k: row[k] for k in row.keys()}))


@bp.route("/api/orders/<int:oid>")
def api_order(oid):
    con = db.get_db()

    row = con.execute("SELECT * FROM orders WHERE id = ?", (oid,)).fetchone()
    if not row:
        return jsonify({"error": "not found"}), 404
    return _cors(jsonify({k: row[k] for k in row.keys()}))


@bp.route("/api/account/update", methods=["POST"])
def api_update():
    con = db.get_db()
    user = current_user(con)
    if not user:
        return jsonify({"error": "not authenticated"}), 401
    data = request.get_json(silent=True) or {}
    cols = {r[1] for r in con.execute("PRAGMA table_info('users')").fetchall()}


    applied = {}
    for k, v in data.items():
        if k in cols and k != "id":
            con.execute(f"UPDATE users SET {k} = ? WHERE id = ?", (v, user["id"]))
            applied[k] = v
    con.commit()
    return jsonify({"updated": applied})



def _docstore():
    con = db.get_db()
    return [{"username": r["username"], "password": r["password"], "role": r["role"]}
            for r in con.execute("SELECT username,password,role FROM users").fetchall()]


def _nosql_match(doc, query):
    for key, cond in query.items():
        val = doc.get(key)
        if isinstance(cond, dict):
            for op, operand in cond.items():
                if op == "$ne" and not (val != operand):
                    return False
                if op == "$eq" and not (val == operand):
                    return False
                if op == "$gt" and not (val is not None and val > operand):
                    return False
                if op == "$regex":
                    if val is None or re.search(str(operand), str(val)) is None:
                        return False
                if op == "$in" and val not in operand:
                    return False
        else:
            if val != cond:
                return False
    return True


@bp.route("/api/login", methods=["POST"])
def api_login():

    query = request.get_json(silent=True) or {}
    query = {k: v for k, v in query.items() if k in ("username", "password")}
    for doc in _docstore():
        if _nosql_match(doc, query):
            return _cors(jsonify({"authenticated": True, "username": doc["username"],
                                  "role": doc["role"]}))
    return _cors(jsonify({"authenticated": False})), 401





@bp.route("/robots.txt")
def robots():


    return Response("User-agent: *\nDisallow: /cart\nDisallow: /checkout\n"
                    "Disallow: /account\n", mimetype="text/plain")


@bp.route("/backup/kartly.sql.bak")
def backup():
    users = db.get_db().execute("SELECT id,username,password,email,role FROM users").fetchall()
    dump = ["-- Kartly database backup (DO NOT COMMIT)", "-- generated by nightly cron",
            "", "INSERT INTO users (id,username,password,email,role) VALUES"]
    rows = [f"  ({u['id']},'{u['username']}','{u['password']}','{u['email']}','{u['role']}')"
            for u in users]
    dump.append(",\n".join(rows) + ";")
    return Response("\n".join(dump), mimetype="text/plain")





@bp.route("/sitemap.xml")
def sitemap():
    con = db.get_db()
    urls = [url_for("market.home", _external=True),
            url_for("market.products", _external=True),
            url_for("market.deals", _external=True),
            url_for("market.trending", _external=True)]
    urls += [url_for("market.products", category=c, _external=True) for c in db.CATEGORIES]
    body = ['<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    body += [f"  <url><loc>{u}</loc></url>" for u in urls]
    body.append("</urlset>")
    return Response("\n".join(body), mimetype="application/xml")


@bp.route("/.well-known/security.txt")
def security_txt():
    return Response(
        "Contact: mailto:security@kartly.example\n"
        "Expires: 2027-01-01T00:00:00Z\n"
        "Preferred-Languages: en\n"
        "Policy: https://kartly.example/security-policy\n",
        mimetype="text/plain")


@bp.route("/api")
@bp.route("/api/")
def api_index():

    return _cors(jsonify({
        "name": "Kartly API",
        "version": "1.0",
        "endpoints": {
            "account": "/api/account",
            "user": "/api/users/{id}",
            "order": "/api/orders/{id}",
            "login": "/api/login",
            "account_update": "/api/account/update",
            "stock": "/api/stock",
        },
    }))


@bp.route("/status")
@bp.route("/healthz")
def status():
    return jsonify({"status": "ok", "service": "kartly-web", "version": "3.4.1",
                    "database": "connected", "cache": "enabled"})





@bp.route("/support")
def support():
    return render_template("support.html", **nav_context(db.get_db()))






_WCD_EXT = re.compile(r"\.(js|css|png|jpe?g|gif|woff2?|ico|svg)$", re.I)


@bp.route("/account/<path:sub>")
def account_static(sub):
    if not _WCD_EXT.search(sub):
        abort(404)
    con = db.get_db()
    user = current_user(con)
    if not user:
        return redirect(url_for("market.login"))
    orders = con.execute("SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC",
                         (user["id"],)).fetchall()
    return render_template("account.html", orders=orders, **nav_context(con))
