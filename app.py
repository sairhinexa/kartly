










import os
import re
import json
import time
import base64

from flask import Flask, request, session, Response, render_template
from flask_sock import Sock

from core import db, files
from market.views import bp as market_bp
import market.wave2
import market.pii

def _decode_session_jwt(token):



    try:
        header_seg = token.split(".")[0]
        header = json.loads(base64.urlsafe_b64decode(header_seg + "=" * (-len(header_seg) % 4)))
    except Exception:
        return None
    if str(header.get("alg", "")).lower() == "none":

        try:
            payload_seg = token.split(".")[1]
            return json.loads(base64.urlsafe_b64decode(payload_seg + "=" * (-len(payload_seg) % 4)))
        except Exception:
            return None
    from core import jwtmini
    return jwtmini.decode(token)


_WCD_EXT = re.compile(r"\.(js|css|png|jpe?g|gif|woff2?|ico|svg)$", re.I)
_WCD_CACHE = {}
_WCD_TTL = 60


def create_app():
    app = Flask(__name__)
    app.secret_key = "kartly-lab-insecure-fixed-key"
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024



    os.environ.setdefault("KARTLY_DB_PASSWORD", "Kt9a!prodDB-FLAG{0s_cmd_exec_env_leak}")

    db.reset_all()
    files.setup_files()

    app.register_blueprint(market_bp)
    app.teardown_appcontext(db.close_request_db)

    @app.errorhandler(404)
    def _not_found(_e):
        return render_template("404.html", categories=db.CATEGORIES, user=None), 404

    @app.errorhandler(500)
    def _server_error(_e):
        return render_template("500.html", categories=db.CATEGORIES, user=None), 500


    @app.before_request
    def _remember():
        if not session.get("uid"):
            rc = request.cookies.get("kartly_remember")
            if rc:
                try:
                    data = _decode_session_jwt(rc) or {}
                except Exception:
                    return
                uid = data.get("uid")
                if uid:
                    session["uid"] = uid


    @app.before_request
    def _wcd_get():
        if request.method == "GET" and _WCD_EXT.search(request.path):
            e = _WCD_CACHE.get(request.path)
            if e and time.time() - e[0] < _WCD_TTL:
                return Response(e[1], content_type=e[2])

    @app.after_request
    def _wcd_set(resp):
        if request.method == "GET" and resp.status_code == 200 and _WCD_EXT.search(request.path):
            try:
                _WCD_CACHE[request.path] = (time.time(), resp.get_data(), resp.content_type)
            except Exception:
                pass
        return resp


    sock = Sock(app)
    clients = set()

    @sock.route("/ws/support")
    def ws_support(ws):
        clients.add(ws)
        try:
            ws.send("<em>Support agent Mia joined the chat. How can we help?</em>")
            while True:
                msg = ws.receive()
                if msg is None:
                    break

                payload = "<strong>Visitor:</strong> " + msg
                for c in list(clients):
                    try:
                        c.send(payload)
                    except Exception:
                        clients.discard(c)
        finally:
            clients.discard(ws)

    return app


app = create_app()

if __name__ == "__main__":
    import os


    host = os.environ.get("KARTLY_HOST", "127.0.0.1")
    port = int(os.environ.get("KARTLY_PORT", "5000"))
    print("=" * 70)
    print(" Kartly marketplace -- security training target. Localhost use only.")
    print(f" Listening on {host}:{port}  ->  http://127.0.0.1:{port}/")
    if host not in ("127.0.0.1", "localhost"):
        print(" !! Bound to a non-loopback address. Do NOT run on a reachable network.")
    print("=" * 70)
    app.run(host=host, port=port, debug=False)
