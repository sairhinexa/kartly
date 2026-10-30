








import os
import re
import html
import time
import base64
import urllib.parse
from xml.etree import ElementTree as ET

from flask import (Blueprint, request, render_template, redirect, url_for,
                   session, make_response, Response, abort)

from core import db, files

bp = Blueprint("market", __name__)

CATALOG_COLS = "id, name, price, description"
CATALOG_COLTYPES = ["num", "text", "num", "text"]


_login_attempts = {}





def current_user(con):
    uid = session.get("uid")
    if not uid:
        return None
    return con.execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone()


def nav_context(con):
    return dict(categories=db.CATEGORIES, user=current_user(con))


def _raw_cookie(name):

    raw = request.headers.get("Cookie", "")
    m = re.search(re.escape(name) + r"=([^;]*)", raw)
    return m.group(1) if m else None


def _read_file(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return Response(fh.read(), mimetype="text/plain")
    except (OSError, ValueError) as e:
        return Response(f"Error reading file: {e}", status=404, mimetype="text/plain")





@bp.route("/")
def home():
    con = db.get_db()
    tid = _raw_cookie("TrackingId")
    new_cookie = None
    welcome = False
    if not tid:
        import secrets
        tid = secrets.token_urlsafe(9)
        new_cookie = tid
        con.execute("INSERT INTO tracked_users VALUES(?)", (tid,))
        con.commit()
    else:

        sql = "SELECT * FROM tracked_users WHERE trackingId = '%s'" % tid
        rows, _err = db.vuln_query(con, sql)
        welcome = bool(rows)

    featured = con.execute("SELECT * FROM products WHERE released=1 ORDER BY id LIMIT 8").fetchall()
    html_body = render_template("home.html", featured=featured, welcome=welcome,
                                **nav_context(con))
    resp = make_response(html_body)
    if new_cookie:
        resp.set_cookie("TrackingId", new_cookie, samesite="Lax")
    return resp





@bp.route("/products")
def products():
    con = db.get_db()
    category = request.args.get("category")
    if category is None:
        rows = con.execute("SELECT * FROM products WHERE released=1 ORDER BY id").fetchall()
        return render_template("products.html", cards=rows, results=None,
                               selected=None, error=None, **nav_context(con))

    sql = "SELECT %s FROM products WHERE category = '%s' AND released = 1" % (CATALOG_COLS, category)
    rows, error = db.vuln_query(con, sql, col_types=CATALOG_COLTYPES)
    results = [dict(id=r[0], name=r[1], price=r[2], description=r[3]) for r in rows]
    return render_template("products.html", cards=None, results=results,
                           selected=category, error=error, **nav_context(con))





@bp.route("/search")
def search():
    con = db.get_db()
    q = request.args.get("q", "")


    q = re.sub(r"(?is)<\s*/?\s*script[^>]*>", "", q)
    rows = con.execute(
        "SELECT * FROM products WHERE released=1 "
        "AND (name LIKE ? OR description LIKE ?)",
        (f"%{q}%", f"%{q}%")).fetchall()

    return render_template("search.html", q=q, rows=rows, **nav_context(con))






@bp.route("/trending")
def trending():
    con = db.get_db()
    products = con.execute("SELECT * FROM products WHERE released=1 ORDER BY id LIMIT 10").fetchall()
    return render_template("trending.html", products=products, **nav_context(con))


@bp.route("/deals")
def deals():
    con = db.get_db()
    products = con.execute("SELECT * FROM products WHERE released=1 ORDER BY id DESC LIMIT 8").fetchall()
    return render_template("deals.html", products=products, **nav_context(con))





@bp.route("/product/<int:pid>")
def product(pid):
    con = db.get_db()
    p = con.execute("SELECT * FROM products WHERE id = ?", (pid,)).fetchone()
    if not p:
        abort(404)
    reviews = con.execute("SELECT * FROM reviews WHERE product_id = ? ORDER BY id DESC", (pid,)).fetchall()
    return render_template("product.html", p=p, reviews=reviews, **nav_context(con))


@bp.route("/product/<int:pid>/review", methods=["POST"])
def add_review(pid):
    con = db.get_db()
    author = request.form.get("author", "anonymous")
    rating = request.form.get("rating", "5")
    body = request.form.get("body", "")

    con.execute("INSERT INTO reviews(product_id,author,rating,body,created) "
                "VALUES(?,?,?,?,datetime('now'))", (pid, author, rating, body))
    con.commit()
    return redirect(url_for("market.product", pid=pid))





@bp.route("/login", methods=["GET", "POST"])
def login():
    con = db.get_db()
    error = None
    if request.method == "POST":

        client_ip = (request.headers.get("X-Forwarded-For") or request.remote_addr or "?").split(",")[0].strip()
        now = time.time()
        recent = [t for t in _login_attempts.get(client_ip, []) if now - t < 300]
        if len(recent) >= 5:
            return render_template("login.html",
                                   error="Too many failed attempts. Please wait a few minutes.",
                                   **nav_context(con))
        u = request.form.get("username", "")
        p = request.form.get("password", "")
        remember = request.form.get("remember")
        exists = con.execute("SELECT 1 FROM users WHERE username = ?", (u,)).fetchone()

        sql = "SELECT * FROM users WHERE username = '%s' AND password = '%s'" % (u, p)
        rows, _err = db.vuln_query(con, sql)
        if rows:
            session["uid"] = rows[0]["id"]
            resp = redirect(url_for("market.account"))
            if remember:

                from core import jwtmini
                token = jwtmini.encode({"uid": rows[0]["id"], "username": rows[0]["username"],
                                        "role": rows[0]["role"]})
                resp.set_cookie("kartly_remember", token, samesite="Lax", max_age=2592000)
            return resp
        recent.append(now)
        _login_attempts[client_ip] = recent

        error = "Invalid password." if exists else "No account with that username."
    return render_template("login.html", error=error, **nav_context(con))


@bp.route("/register", methods=["GET", "POST"])
def register():
    con = db.get_db()
    error = None
    if request.method == "POST":
        u = request.form.get("username", "").strip()
        p = request.form.get("password", "")
        email = request.form.get("email", "")
        if not u or not p:
            error = "Username and password required."
        elif con.execute("SELECT 1 FROM users WHERE username = ?", (u,)).fetchone():
            error = "That username is taken."
        else:
            import secrets
            con.execute("INSERT INTO users(username,password,email,role,full_name,address,api_token,is_premium)"
                        " VALUES(?,?,?,?,?,?,?,0)",
                        (u, p, email, "customer", u, "", secrets.token_hex(16)))
            con.commit()
            session["uid"] = con.execute("SELECT id FROM users WHERE username = ?", (u,)).fetchone()["id"]
            return redirect(url_for("market.account"))
    return render_template("register.html", error=error, **nav_context(con))


@bp.route("/logout")
def logout():
    session.pop("uid", None)
    return redirect(url_for("market.home"))


@bp.route("/account")
def account():
    con = db.get_db()
    user = current_user(con)
    if not user:
        return redirect(url_for("market.login"))
    orders = con.execute("SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC", (user["id"],)).fetchall()
    return render_template("account.html", orders=orders, **nav_context(con))





@bp.route("/media")
def media():

    f = request.args.get("file", "README.txt")
    return _read_file(os.path.join(files.MEDIA_DIR, f))


@bp.route("/theme")
def theme():

    f = request.args.get("file", "classic.css")
    clean = f.replace("../", "").replace("..\\", "")
    if f.startswith("/"):
        path = os.path.normpath(files.vroot() + f)
    else:
        path = os.path.join(files.THEME_DIR, clean)
    return _read_file(path)


@bp.route("/account/avatar")
def avatar():

    f = request.args.get("file", "default.txt")
    clean = f.replace("../", "").replace("..\\", "")
    return _read_file(os.path.join(files.AVATAR_DIR, clean))


@bp.route("/help")
def help_doc():

    f = request.args.get("file", "en/returns.txt")
    if "../" in f or "..\\" in f or f.startswith("/"):
        return Response("Blocked: illegal path", status=403, mimetype="text/plain")
    f2 = urllib.parse.unquote(f)
    return _read_file(os.path.join(files.HELP_DIR, f2))


@bp.route("/account/invoice")
def invoice():

    f = request.args.get("file", "/var/invoices/KTLY-2024-0007.txt")
    if not f.startswith("/var/invoices/"):
        return Response("Blocked: invoices must live under /var/invoices/", status=403, mimetype="text/plain")
    return _read_file(os.path.normpath(files.vroot() + f))


@bp.route("/product/<int:pid>/manual")
def manual(pid):

    f = request.args.get("file", "aurora-earbuds.png")
    if not f.endswith(".png"):
        return Response("Blocked: manuals are .png only", status=403, mimetype="text/plain")
    truncated = f.split("\x00")[0]
    return _read_file(os.path.join(files.MANUAL_DIR, truncated))





@bp.route("/seller/supplier-lookup")
def supplier_lookup():
    con = db.get_db()
    ref = request.args.get("ref")
    located = None
    if ref is not None:

        sql = "SELECT name FROM products WHERE id = %s" % ref
        rows, _err = db.vuln_query(con, sql)
        located = bool(rows)
    return render_template("supplier.html", ref=ref, located=located, **nav_context(con))





_WAF = re.compile(r"\b(union|select|from|where|or|and)\b|--|/\*", re.IGNORECASE)


@bp.route("/api/stock", methods=["POST"])
def api_stock():
    con = db.get_db()
    body = request.get_data(as_text=True) or ""


    if _WAF.search(body):
        return Response("Request blocked by WAF", status=403, mimetype="text/plain")
    try:
        product_id = (ET.fromstring(body).findtext(".//productId") or "").strip()
    except ET.ParseError:
        return Response("Malformed XML", status=400, mimetype="text/plain")

    sql = "SELECT stock FROM products WHERE id = %s" % product_id
    rows, error = db.vuln_query(con, sql)
    if error:
        return Response(error, mimetype="text/plain")
    out = " ".join(str(v) for r in rows for v in tuple(r)) if rows else "0"
    return Response(f"{out} units in stock", mimetype="text/plain")
