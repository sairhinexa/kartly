












import os
import re
import sqlite3
import time
import socket
import secrets
import threading
import urllib.request

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, ".dbs")
DB_PATH = os.path.join(DB_DIR, "market.db")




CATEGORIES = ["Electronics", "Home & Kitchen", "Toys & Games", "Pet Supplies",
              "Gifts", "Lifestyle", "Accessories"]


PRODUCTS = [
    ("Aurora Wireless Earbuds",    "Electronics",   59.99, 1, 42, "Noise-cancelling earbuds with 30h battery life."),
    ("Nimbus Smart Speaker",       "Electronics",   79.00, 1, 18, "Room-filling sound with built-in voice assistant."),
    ("Pixel-Perfect 4K Webcam",     "Electronics",   64.50, 1, 27, "Crystal-clear video for calls and streaming."),
    ("EverBrew Coffee Maker",       "Home & Kitchen",89.99, 1, 12, "Barista-grade coffee at the touch of a button."),
    ("ChopEasy Knife Set",          "Home & Kitchen",45.00, 1, 33, "Six precision-forged kitchen knives."),
    ("Cuddlebug Plush Dinosaur",    "Toys & Games",  22.00, 1, 55, "The softest dino a child could wish for."),
    ("BrainBender Puzzle Cube",     "Toys & Games",  14.99, 1, 80, "Classic twisty puzzle, speed-cube ready."),
    ("PawPalace Cat Tree",          "Pet Supplies",  74.99, 1, 9,  "Multi-level climbing tower for happy cats."),
    ("WoofWear Raincoat",           "Pet Supplies",  26.50, 1, 40, "Keep your dog dry on soggy walks."),
    ("Conversation-Starting Lamp",  "Gifts",         31.00, 1, 21, "A lamp that sparks talk at every dinner."),
    ("Everyday Canvas Backpack",    "Lifestyle",     48.00, 1, 36, "Durable, water-resistant, laptop-ready."),
    ("Minimalist Leather Wallet",   "Accessories",   29.99, 1, 60, "Slim RFID-blocking cardholder."),
    ("Summit Stainless Flask",      "Lifestyle",     19.99, 1, 48, "Keeps drinks hot 12h / cold 24h."),

    ("Prototype AR Glasses",        "Electronics",  499.00, 0, 3,  "UNRELEASED internal prototype. Staff only."),
    ("Unannounced Holiday Bundle",  "Gifts",         64.00, 0, 5,  "UNRELEASED seasonal bundle, embargoed."),

    ("QuietComfort Over-Ear Headphones","Electronics",129.00, 1, 24, "Adaptive noise cancellation and 40-hour playback."),
    ("StreamCast 4K Media Stick",    "Electronics",   39.99, 1, 61, "Stream every service in 4K HDR from any TV."),
    ("PowerPod 20000mAh Power Bank", "Electronics",   34.50, 1, 88, "Fast-charge two devices at once, airline-safe."),
    ("LumiGlow Smart Bulbs (4-pack)","Electronics",   27.99, 1, 52, "16 million colours, voice and app control."),
    ("TrailMate GPS Running Watch",  "Electronics",  149.00, 1, 17, "Multi-band GPS, heart-rate and 7-day battery."),
    ("ChefSteel Cast-Iron Skillet",  "Home & Kitchen",42.00, 1, 29, "Pre-seasoned 12-inch skillet, oven to table."),
    ("AromaLeaf Tea Infuser Set",    "Home & Kitchen",24.99, 1, 44, "Double-wall glass pot with stainless infuser."),
    ("FreshSeal Storage Set (10pc)", "Home & Kitchen",31.50, 1, 37, "Airtight, stackable, leak-proof containers."),
    ("CloudRest Memory Foam Pillow", "Home & Kitchen",38.00, 1, 26, "Cooling gel-infused contour support."),
    ("BrightWash Dish Rack",         "Home & Kitchen",22.75, 1, 40, "Rust-proof rack with swivel drainage spout."),
    ("GalaxyBlocks 500-Piece Set",   "Toys & Games",  33.99, 1, 48, "Compatible building bricks with a storage tub."),
    ("SpeedTrack RC Rally Car",      "Toys & Games",  44.00, 1, 21, "2.4GHz, 25 km/h, all-terrain grip tyres."),
    ("StoryTime Night Projector",    "Toys & Games",  26.50, 1, 33, "Starry ceiling projector with soothing sounds."),
    ("PuppyChew Dental Toy",         "Pet Supplies",  12.99, 1, 95, "Vet-recommended teeth-cleaning chew."),
    ("WhiskerWell Water Fountain",   "Pet Supplies",  29.99, 1, 30, "Ultra-quiet 2L fountain with carbon filter."),
    ("CosyDen Orthopaedic Dog Bed",  "Pet Supplies",  54.00, 1, 15, "Memory-foam base with washable cover."),
    ("Everscent Soy Candle Trio",    "Gifts",         28.00, 1, 50, "Hand-poured, 120-hour burn across three scents."),
    ("PocketPlanner 2026 Diary",     "Gifts",         16.99, 1, 70, "Week-to-view planner with vegan-leather cover."),
    ("Starlight String Lights 20m",  "Gifts",         18.50, 1, 64, "Warm-white LEDs with eight lighting modes."),
    ("ZenFlow Yoga Mat",             "Lifestyle",     34.00, 1, 42, "6mm non-slip eco mat with carry strap."),
    ("DayPack Commuter Bag",         "Lifestyle",     52.00, 1, 28, "Water-resistant, USB pass-through, 20L."),
    ("PureMist Ultrasonic Humidifier","Lifestyle",    39.50, 1, 23, "Whisper-quiet with auto shut-off and timer."),
    ("Horizon Polarised Sunglasses", "Accessories",   45.00, 1, 55, "UV400 polarised lenses, lightweight frame."),
    ("Heritage Leather Belt",        "Accessories",   33.00, 1, 47, "Full-grain leather with brushed-steel buckle."),
    ("UrbanKnit Ribbed Beanie",      "Accessories",   17.99, 1, 72, "Soft merino-blend, one size, six colours."),
]


USERS = [

    ("administrator", "s3cr3t",     "admin@kartly.lab",      "admin",   "Site Administrator", "1 Market St"),
    ("wiener",        "peter",      "wiener@kartly.lab",     "customer","Peter Wiener",       "42 Baker Ave"),
    ("carlos",        "montoya",    "carlos@kartly.lab",     "customer","Carlos Montoya",     "9 Elm Road"),
    ("seller_amy",    "sellPass99", "amy@soundgear.example", "seller",  "Amy Okafor (SoundGear Ltd)","Unit 7, Trade Park"),

    ("j.santos",      "Summer2025!",  "julia.santos@gmail.example",   "customer","Julia Santos",      "14 Rosewood Lane, Leeds"),
    ("dmitri.k",      "Hockey#88",    "dmitri.kozlov@outlook.example","customer","Dmitri Kozlov",     "203 Hillcrest Rd, Bristol"),
    ("aaliyah.b",     "Marig0ld",     "aaliyah.bello@yahoo.example",  "customer","Aaliyah Bello",     "8 Canal St, Manchester"),
    ("tom.whitfield", "Redwood2024",  "t.whitfield@proton.example",   "customer","Tom Whitfield",     "51 Oakfield Ave, Reading"),
    ("mei.lin",       "Lantern$7",    "mei.lin@gmail.example",        "customer","Mei Lin",           "27 Harbour View, Cardiff"),
    ("samira.n",      "Desert_rose1", "samira.nouri@gmail.example",   "customer","Samira Nouri",      "3 Birch Close, Oxford"),
    ("gcampbell",     "Thistle!99",   "g.campbell@btinternet.example","customer","Grace Campbell",    "66 Kelvin St, Glasgow"),
    ("ravi.menon",    "Chennai#12",   "ravi.menon@gmail.example",     "customer","Ravi Menon",        "18 Maple Drive, Leicester"),
    ("l.fischer",     "Edelweiss22",  "lena.fischer@gmx.example",     "customer","Lena Fischer",      "9 Garden Terrace, York"),
    ("noah.pt",       "Benfica2025",  "noah.pereira@gmail.example",   "customer","Noah Pereira",      "40 Sea Road, Brighton"),
    ("hkhan",         "Peshawar!7",   "hassan.khan@outlook.example",  "customer","Hassan Khan",       "12 Mill Lane, Luton"),
    ("eva.novak",     "Prague_88",    "eva.novak@seznam.example",     "customer","Eva Novak",         "77 Castle St, Durham"),
    ("marco.ricci",   "Vespa1960",    "marco.ricci@gmail.example",    "customer","Marco Ricci",       "5 Vine St, Bath"),
    ("priya.s",       "Jasmine#4",    "priya.sharma@gmail.example",   "customer","Priya Sharma",      "31 Fern Rd, Nottingham"),
    ("seller_tex",    "T3xW0rks!",    "sales@texworks.example",       "seller",  "TexWorks Trading",  "Dock 4, Felixstowe"),
    ("on.leave",      "Welcome1",     "liam.murphy@gmail.example",    "customer","Liam Murphy",       "22 Abbey Gate, Chester"),
]


ORDERS = [
    (2,  "KTLY-2024-0007", 82.49,  "Delivered",  200),
    (3,  "KTLY-2024-0011", 139.98, "Shipped",    120),
    (5,  "KTLY-2025-0241", 64.49,  "Delivered",  58),
    (6,  "KTLY-2025-0318", 149.00, "Delivered",  41),
    (7,  "KTLY-2025-0402", 27.99,  "Delivered",  33),
    (3,  "KTLY-2025-0455", 92.00,  "Delivered",  27),
    (8,  "KTLY-2025-0509", 215.49, "Shipped",    19),
    (9,  "KTLY-2025-0533", 34.00,  "Delivered",  15),
    (2,  "KTLY-2025-0547", 54.00,  "Shipped",    12),
    (10, "KTLY-2025-0561", 128.98, "Processing", 9),
    (11, "KTLY-2025-0574", 18.50,  "Delivered",  7),
    (12, "KTLY-2025-0588", 76.49,  "Shipped",    5),
    (1,  "KTLY-2025-0590", 499.00, "Processing", 4),
    (13, "KTLY-2025-0601", 45.00,  "Processing", 2),
    (5,  "KTLY-2025-0609", 39.50,  "Processing", 1),
]



CARDS = [
    (2, "Visa",       "4242424242424242", "08/27", "311",  "Peter Wiener"),
    (3, "Mastercard", "5555555555554444", "02/26", "804",  "Carlos Montoya"),
    (1, "Amex",       "378282246310005",  "11/28", "2731", "A Administrator  FLAG{cardh0ld3r_data_l34k}"),
    (5, "Visa",       "4000056655665556", "05/27", "190",  "Julia Santos"),
    (8, "Visa",       "4111111111111111", "09/26", "455",  "Tom Whitfield"),
    (6, "Mastercard", "5105105105105100", "12/26", "622",  "Dmitri Kozlov"),
]



EMAILS = [
    ("wiener@kartly.lab", "Welcome to Kartly",
     "Hi Peter, your Kartly account is ready. Happy shopping!"),
    ("carlos@kartly.lab", "Your order KTLY-2024-0011 has shipped",
     "Hi Carlos, your order is on its way to 9 Elm Road."),
    ("admin@kartly.lab", "Password reset requested",
     "A password reset was requested for administrator.\n"
     "Reset link: https://kartly.example/reset?token=adm-reset-9f3c2a\n"
     "If this wasn't you, ignore this email. FLAG{expos3d_dev_mailbox_pii}"),
]

_REVIEW_AUTHORS = ["jen_d", "marco99", "coffee_lover", "puzzler", "techfan22", "mum_of_three",
                   "gadget_greg", "home_hannah", "petlover_pam", "runner_raj", "minimalist_mia",
                   "verified_buyer", "weekend_warrior", "deal_hunter", "first_timer"]
_REVIEW_SNIPPETS = [
    (5, "Exactly as described, arrived a day early. Really pleased."),
    (5, "Been using it daily for a month now and it's held up perfectly."),
    (4, "Great value for the price. Lost a star for the flimsy packaging."),
    (4, "Does the job well. Would've liked more colour options."),
    (5, "Bought one for myself and ended up buying two more as gifts."),
    (3, "It's fine. Nothing special but nothing wrong with it either."),
    (5, "Customer service sorted a small issue instantly. Will buy again."),
    (4, "Better than the more expensive one I had before."),
    (2, "Looked smaller in person than I expected. Still usable."),
    (5, "Can't fault it. Exactly what I needed."),
    (4, "Solid quality. Setup took five minutes."),
    (5, "My kids love it. Keeps them busy for hours."),
]

VERSION_BANNERS = {
    "oracle":   "Oracle Database 11g Express Edition Release 11.2.0.2.0 - 64bit Production",
    "mysql":    "8.0.37-MySQL Community Server - GPL",
    "postgres": "PostgreSQL 15.4 on x86_64-pc-linux-gnu, compiled by gcc 12.2.0, 64-bit",
}

_lock = threading.Lock()
_ready = False


def reset_all():
    global _ready
    with _lock:
        _ready = False
        os.makedirs(DB_DIR, exist_ok=True)
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        _seed()
        _ready = True


def _seed():
    con = sqlite3.connect(DB_PATH)
    c = con.cursor()
    c.executescript("""
        CREATE TABLE users(
            id INTEGER PRIMARY KEY, username TEXT, password TEXT, email TEXT,
            role TEXT, full_name TEXT, address TEXT, api_token TEXT, is_premium INTEGER DEFAULT 0,
            city TEXT);
        CREATE TABLE emails(
            id INTEGER PRIMARY KEY, to_addr TEXT, subject TEXT, body TEXT, created TEXT);
        CREATE TABLE cards(
            id INTEGER PRIMARY KEY, user_id INTEGER, brand TEXT, number TEXT,
            expiry TEXT, cvv TEXT, cardholder TEXT);
        CREATE TABLE messages(
            id INTEGER PRIMARY KEY, name TEXT, email TEXT, body TEXT, created TEXT);
        CREATE TABLE products(
            id INTEGER PRIMARY KEY, name TEXT, category TEXT, price REAL,
            released INTEGER, stock INTEGER, description TEXT);
        CREATE TABLE reviews(
            id INTEGER PRIMARY KEY, product_id INTEGER, author TEXT, rating INTEGER,
            body TEXT, created TEXT);
        CREATE TABLE orders(
            id INTEGER PRIMARY KEY, user_id INTEGER, reference TEXT, total REAL,
            status TEXT, created TEXT,
            ship_name TEXT, ship_addr TEXT, ship_city TEXT, ship_zip TEXT,
            pay_brand TEXT, pay_last4 TEXT, items_json TEXT);
        CREATE TABLE tracked_users(trackingId TEXT);
        CREATE TABLE _versions(dbms TEXT, banner TEXT);
        CREATE TABLE all_tables(table_name TEXT, owner TEXT);
        CREATE TABLE all_tab_columns(table_name TEXT, column_name TEXT);
        CREATE VIEW dual AS SELECT 'X' AS dummy;
    """)
    for i, (n, cat, pr, rel, st, desc) in enumerate(PRODUCTS, 1):
        c.execute("INSERT INTO products VALUES(?,?,?,?,?,?,?)", (i, n, cat, pr, rel, st, desc))
    for i, (u, p, e, role, fn, addr) in enumerate(USERS, 1):
        c.execute("INSERT INTO users(id,username,password,email,role,full_name,address,api_token,is_premium)"
                  " VALUES(?,?,?,?,?,?,?,?,?)",
                  (i, u, p, e, role, fn, addr, secrets.token_hex(16), 1 if u == "administrator" else 0))

    import random as _rnd
    rng = _rnd.Random(1337)
    for pid in range(1, len(PRODUCTS) + 1):
        if pid in (14, 15):
            continue
        for _ in range(rng.randint(0, 4)):
            rating, body = rng.choice(_REVIEW_SNIPPETS)
            c.execute("INSERT INTO reviews(product_id,author,rating,body,created) "
                      "VALUES(?,?,?,?,datetime('now',?))",
                      (pid, rng.choice(_REVIEW_AUTHORS), rating, body, f"-{rng.randint(1,180)} days"))

    import json as _json
    from core import invoices as _inv
    _card_by_uid = {}
    for cu, cbrand, cnum, *_rest in CARDS:
        _card_by_uid.setdefault(cu, (cbrand, cnum))
    _zips = ["LS1 4DY", "M1 2WD", "BS1 5TR", "CF10 3AT", "OX1 2JD", "G2 8QE",
             "LE1 6RH", "YO1 7HH", "BN1 1AE", "LU1 2NP", "DH1 3RW", "BA1 1LZ"]
    for _oi, (uid, ref, total, status, days) in enumerate(ORDERS):
        u = USERS[uid - 1]
        full_name, addr = u[4], u[5]
        if "," in addr:
            street, city = addr.rsplit(",", 1)
            street, city = street.strip(), city.strip()
        else:
            street, city = addr.strip(), ""
        brand, num = _card_by_uid.get(uid, ("Visa", "4242424242424242"))
        last4 = num[-4:]
        prod = PRODUCTS[(uid * 7 + _oi) % len(PRODUCTS)][0]
        items = _json.dumps([{"name": prod, "qty": 1, "price": total}])
        c.execute("INSERT INTO orders(user_id,reference,total,status,created,"
                  "ship_name,ship_addr,ship_city,ship_zip,pay_brand,pay_last4,items_json) "
                  "VALUES(?,?,?,?,datetime('now',?),?,?,?,?,?,?,?)",
                  (uid, ref, total, status, f"-{days} days",
                   full_name, street, city, _zips[_oi % len(_zips)], brand, last4, items))

    for uid, city in [(2, "Bristol"), (3, "Manchester"), (5, "Leeds"), (6, "Bristol"), (7, "Manchester")]:
        c.execute("UPDATE users SET city = ? WHERE id = ?", (city, uid))

    for uid, brand, num, exp, cvv, holder in CARDS:
        c.execute("INSERT INTO cards(user_id,brand,number,expiry,cvv,cardholder) VALUES(?,?,?,?,?,?)",
                  (uid, brand, num, exp, cvv, holder))

    for to_addr, subject, body in EMAILS:
        c.execute("INSERT INTO emails(to_addr,subject,body,created) VALUES(?,?,?,datetime('now',?))",
                  (to_addr, subject, body, f"-{rng.randint(1,40)} days"))

    for nm, em, bd in [("Grace Campbell", "g.campbell@btinternet.example", "Where is my order KTLY-2025-0318?"),
                       ("Ravi Menon", "ravi.menon@gmail.example", "Please cancel my subscription, thanks.")]:
        c.execute("INSERT INTO messages(name,email,body,created) VALUES(?,?,?,datetime('now',?))",
                  (nm, em, bd, f"-{rng.randint(1,20)} days"))
    for t in ("u8Ht2kLp9QvA", "Zx41Nb7Rm0Ce", "Qa93Vt6Ys2Wd"):
        c.execute("INSERT INTO tracked_users VALUES(?)", (t,))
    for dbms, banner in VERSION_BANNERS.items():
        c.execute("INSERT INTO _versions VALUES(?,?)", (dbms, banner))
    for tname in ("USERS", "PRODUCTS", "ORDERS", "REVIEWS"):
        c.execute("INSERT INTO all_tables VALUES(?, 'KARTLY')", (tname,))
    for tname, cols in (("USERS", ("ID", "USERNAME", "PASSWORD", "EMAIL", "ROLE")),
                        ("PRODUCTS", ("ID", "NAME", "CATEGORY", "PRICE", "RELEASED", "STOCK"))):
        for col in cols:
            c.execute("INSERT INTO all_tab_columns VALUES(?,?)", (tname, col))
    c.execute("CREATE VIEW v_version_ora AS SELECT banner FROM _versions WHERE dbms='oracle'")
    con.commit()

    _inv.seed_all(con)
    con.close()





_cast_err = threading.local()
_oob = threading.local()


def pop_oob():
    fired = getattr(_oob, "fired", False)
    last = getattr(_oob, "last", None)
    _oob.fired = False
    _oob.last = None
    return fired, last


def _pg_sleep(seconds):
    try:
        time.sleep(min(float(seconds), 20))
    except (TypeError, ValueError):
        pass
    return None


def _cast_int(value):
    try:
        return int(str(value))
    except (TypeError, ValueError):
        _cast_err.value = value
        raise ValueError(f"invalid input syntax for type integer: {value}")


def _oob_request(url_or_host):
    s = str(url_or_host or "")
    _oob.fired = True
    _oob.last = s
    try:
        if s.startswith("http://") or s.startswith("https://"):
            urllib.request.urlopen(s, timeout=3).read(32)
        else:
            socket.getaddrinfo(s, 80)
    except Exception:
        pass
    return ""


def _new_conn():
    con = sqlite3.connect(DB_PATH, timeout=25, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=25000")
    return con


def close_request_db(_exc=None):

    try:
        from flask import g
        con = g.pop("_market_db", None)
    except Exception:
        con = None
    if con is not None:
        con.close()


def get_db():





    if not _ready:
        reset_all()
    try:
        from flask import g, has_app_context
        in_ctx = has_app_context()
    except Exception:
        g, in_ctx = None, False
    if in_ctx:
        existing = g.get("_market_db", None)
        if existing is not None:
            return existing
    con = _new_conn()
    con.create_function("pg_sleep", 1, _pg_sleep)
    con.create_function("sleep", 1, _pg_sleep)
    con.create_function("__cast_int", 1, _cast_int)
    con.create_function("utl_http_request", 1, _oob_request)
    con.create_function("utl_inaddr_get_host_address", 1, _oob_request)

    con.execute("ATTACH DATABASE ':memory:' AS information_schema")
    con.execute("CREATE TABLE information_schema.tables(table_catalog, table_schema, table_name)")
    con.execute("CREATE TABLE information_schema.columns(table_catalog, table_schema, table_name, column_name)")
    for (tname,) in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
        con.execute("INSERT INTO information_schema.tables VALUES('kartly','public',?)", (tname,))
        for col in con.execute(f"PRAGMA table_info('{tname}')").fetchall():
            con.execute("INSERT INTO information_schema.columns VALUES('kartly','public',?,?)", (tname, col[1]))
    if in_ctx:
        g._market_db = con
    return con





def rewrite_sql(sql):
    s = sql
    s = re.sub(r"#.*", "", s)
    s = re.sub(r"v\$version", "v_version_ora", s, flags=re.IGNORECASE)
    s = re.sub(r"@@version", "(SELECT banner FROM _versions WHERE dbms='mysql')", s, flags=re.IGNORECASE)
    s = re.sub(r"\bversion\s*\(\s*\)", "(SELECT banner FROM _versions WHERE dbms='postgres')", s, flags=re.IGNORECASE)
    s = re.sub(r"\bSUBSTRING\s*\(", "substr(", s, flags=re.IGNORECASE)
    s = re.sub(r"UTL_HTTP\.request", "utl_http_request", s, flags=re.IGNORECASE)
    s = re.sub(r"UTL_INADDR\.get_host_address", "utl_inaddr_get_host_address", s, flags=re.IGNORECASE)
    s = re.sub(r"CAST\s*\(\s*(.+?)\s+AS\s+(?:int|integer|signed)\s*\)",
               r"__cast_int(\1)", s, flags=re.IGNORECASE | re.DOTALL)
    return s


def _split_top_level(items):
    out, depth, cur = [], 0, ""
    for ch in items:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur)
    return [x.strip() for x in out]


def enforce_union_types(sql, col_types):
    m = re.search(r"\bunion\s+(?:all\s+)?select\b(.*?)(?:--|$)", sql, flags=re.IGNORECASE | re.DOTALL)
    if not m:
        return
    items = _split_top_level(m.group(1))
    if len(items) != len(col_types):
        return
    for item, ctype in zip(items, col_types):
        s = item.strip()
        is_null = s.upper() == "NULL"
        is_string_literal = s.startswith("'") and s.endswith("'")
        if ctype == "num" and is_string_literal and not is_null:
            raise ValueError(f"invalid input syntax for type numeric: \"{s.strip(chr(39))}\"")


def vuln_query(con, raw_sql, col_types=None):

    if col_types:
        try:
            enforce_union_types(raw_sql, col_types)
        except ValueError as e:
            return [], f"ERROR: {e}"
    sql = rewrite_sql(raw_sql)
    _cast_err.value = None
    _oob.fired = False
    _oob.last = None
    try:
        return con.execute(sql).fetchall(), None
    except Exception as e:
        leaked = getattr(_cast_err, "value", None)
        if leaked is not None:
            _cast_err.value = None
            return [], f'ERROR: invalid input syntax for type integer: "{leaked}"'
        return [], f"ERROR: {e}"
