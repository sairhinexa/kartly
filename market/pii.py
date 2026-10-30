










from flask import request, render_template, redirect, url_for, session, jsonify, abort

from core import db
from market.views import bp, current_user, nav_context
from market.wave2 import _cors





@bp.route("/dev/mail")
@bp.route("/dev/mail/")
def dev_mail():
    con = db.get_db()

    emails = con.execute("SELECT * FROM emails ORDER BY id DESC").fetchall()
    return render_template("mailbox.html", emails=emails, **nav_context(con))





@bp.route("/account/wallet")
def wallet():
    con = db.get_db()
    user = current_user(con)
    if not user:
        return redirect(url_for("market.login"))

    target = request.args.get("user_id", type=int) or user["id"]
    cards = con.execute("SELECT * FROM cards WHERE user_id = ?", (target,)).fetchall()
    owner = con.execute("SELECT username,full_name FROM users WHERE id = ?", (target,)).fetchone()
    return render_template("wallet.html", cards=cards, owner=owner, target=target,
                           me=user["id"], **nav_context(con))


@bp.route("/account/wallet/add", methods=["POST"])
def wallet_add():
    con = db.get_db()
    user = current_user(con)
    if not user:
        return redirect(url_for("market.login"))
    f = request.form

    con.execute("INSERT INTO cards(user_id,brand,number,expiry,cvv,cardholder) VALUES(?,?,?,?,?,?)",
                (user["id"], f.get("brand", "Visa"), f.get("number", ""), f.get("expiry", ""),
                 f.get("cvv", ""), f.get("cardholder", "")))
    con.commit()
    return redirect(url_for("market.wallet"))


@bp.route("/api/cards/<int:uid>")
def api_cards(uid):
    con = db.get_db()


    if not current_user(con):
        return _cors(jsonify({"error": "unauthorized"})), 401
    rows = con.execute("SELECT * FROM cards WHERE user_id = ?", (uid,)).fetchall()
    return _cors(jsonify({"user_id": uid, "cards": [{k: r[k] for k in r.keys()} for r in rows]}))
