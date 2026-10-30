







import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEBROOT = os.path.join(BASE_DIR, "webroot")




MEDIA_DIR = os.path.join(BASE_DIR, "var", "www", "media")
AVATAR_DIR = os.path.join(BASE_DIR, "var", "www", "avatars")
HELP_DIR = os.path.join(BASE_DIR, "var", "www", "help")
THEME_DIR = os.path.join(BASE_DIR, "var", "www", "themes")
MANUAL_DIR = os.path.join(BASE_DIR, "var", "www", "manuals")
INVOICE_DIR = os.path.join(BASE_DIR, "var", "invoices")


ETC_DIR = os.path.join(BASE_DIR, "etc")
SECRET_DIR = os.path.join(BASE_DIR, "secret")


def vroot():

    return BASE_DIR

FAKE_PASSWD = """root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin
kartly:x:1000:1000:Kartly Application Service:/home/kartly:/bin/bash
postgres:x:1001:1001:PostgreSQL:/var/lib/postgresql:/bin/bash
"""


FLAG = (
    "# kartly production secrets - DO NOT COMMIT\n"
    "DATABASE_URL=postgres://kartly:Kt9a!prodDB@db.internal:5432/kartly\n"
    "SECRET_KEY=8f3c9a2e8b1d4f60b7c1a0e5d2f93a17\n"
    "FLAG=FLAG{f1l3syst3m_r34d_via_tr4v3rs4l}\n"
)


def _write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def setup_files():
    for d in (MEDIA_DIR, AVATAR_DIR, INVOICE_DIR, HELP_DIR, THEME_DIR, MANUAL_DIR, ETC_DIR, SECRET_DIR):
        os.makedirs(d, exist_ok=True)

    _write(os.path.join(MEDIA_DIR, "aurora-earbuds.txt"), "Product media asset: Aurora Wireless Earbuds hero image.")
    _write(os.path.join(MEDIA_DIR, "README.txt"), "Kartly media CDN. Public product imagery only.")
    _write(os.path.join(AVATAR_DIR, "default.txt"), "Default avatar placeholder.")
    _write(os.path.join(HELP_DIR, "en", "returns.txt"), "Kartly help: how to return an item within 30 days.")
    _write(os.path.join(THEME_DIR, "classic.css"), "/* Kartly classic theme */ body{--brand:#e8661a;}")
    _write(os.path.join(MANUAL_DIR, "aurora-earbuds.png"),
           "(binary-ish) Aurora Earbuds quick-start manual page 1.")



    _write(os.path.join(ETC_DIR, "passwd"), FAKE_PASSWD)
    _write(os.path.join(SECRET_DIR, "flag.txt"), FLAG)
