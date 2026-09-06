import os
import sqlite3
import secrets
import urllib.parse
import urllib.request
from functools import wraps

from flask import (
    Flask,
    request,
    redirect,
    session,
    render_template_string,
    url_for
)

app = Flask(__name__)

app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    secrets.token_hex(32)
)

DB = "store.db"

ADMIN_USERNAME = os.getenv(
    "ADMIN_USERNAME",
    "admin"
)

ADMIN_PASSWORD = os.getenv(
    "ADMIN_PASSWORD",
    "change-me"
)

BOT_TOKEN = os.getenv(
    "TELEGRAM_BOT_TOKEN",
    ""
)

ADMIN_CHAT_ID = os.getenv(
    "TELEGRAM_ADMIN_CHAT_ID",
    ""
)

PAYMENT_UPI = os.getenv(
    "PAYMENT_UPI",
    "yourupi@upi"
)


# ==================================================
# DATABASE
# ==================================================

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def init_db():

    con = db()

    con.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            balance REAL DEFAULT 0
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            title TEXT NOT NULL,
            amount REAL DEFAULT 0,
            status TEXT DEFAULT 'completed'
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS deposits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            amount REAL NOT NULL,
            utr TEXT NOT NULL,
            status TEXT DEFAULT 'pending'
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            amount REAL NOT NULL,
            upi TEXT NOT NULL,
            status TEXT DEFAULT 'pending'
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER DEFAULT 0
        )
    """)

    count = con.execute(
        "SELECT COUNT(*) FROM products"
    ).fetchone()[0]

    if count == 0:

        products = [
            (
                "🎮 Gaming Credit Pack - ₹199",
                199,
                10
            ),
            (
                "🔥 Premium Gaming Pack - ₹899",
                899,
                5
            ),
            (
                "🏆 Tournament Entry",
                50,
                20
            ),
            (
                "👑 VIP Gaming Membership",
                299,
                0
            )
        ]

        con.executemany(
            """
            INSERT INTO products
            (name, price, stock)
            VALUES (?, ?, ?)
            """,
            products
        )

    con.commit()
    con.close()


# ==================================================
# TELEGRAM
# ==================================================

def telegram(message):

    if not BOT_TOKEN or not ADMIN_CHAT_ID:
        print("Telegram is not configured.")
        return

    try:

        url = (
            "https://api.telegram.org/"
            f"bot{BOT_TOKEN}/sendMessage"
        )

        data = urllib.parse.urlencode({
            "chat_id": ADMIN_CHAT_ID,
            "text": message
        }).encode()

        req = urllib.request.Request(
            url,
            data=data,
            method="POST"
        )

        urllib.request.urlopen(
            req,
            timeout=10
        )

    except Exception as e:

        print(
            "Telegram error:",
            e
        )


# ==================================================
# LOGIN REQUIRED
# ==================================================

def login_required(fn):

    @wraps(fn)
    def wrapper(*args, **kwargs):

        if "username" not in session:
            return redirect(
                url_for("login")
            )

        return fn(*args, **kwargs)

    return wrapper


def admin_required(fn):

    @wraps(fn)
    def wrapper(*args, **kwargs):

        if session.get("username") != ADMIN_USERNAME:
            return redirect(
                url_for("login")
            )

        return fn(*args, **kwargs)

    return wrapper


# ==================================================
# HTML
# ==================================================

BASE = """
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>Cyber Gaming Store</title>

<style>

*{
    box-sizing:border-box;
    margin:0;
    padding:0;
    font-family:Arial,sans-serif;
}

body{
    background:#030712;
    color:white;
    min-height:100vh;
}

header{
    background:#0f172a;
    padding:18px;
    text-align:center;
    border-bottom:1px solid #1e293b;
}

.logo{
    color:#38bdf8;
    font-size:26px;
    font-weight:bold;
}

.container{
    max-width:900px;
    margin:auto;
    padding:20px 14px 90px;
}

.card{
    background:#0f172a;
    border:1px solid #1e293b;
    border-radius:18px;
    padding:20px;
    margin-bottom:15px;
}

input{
    width:100%;
    padding:13px;
    margin:7px 0;
    background:#020617;
    border:1px solid #334155;
    color:white;
    border-radius:10px;
}

button{
    width:100%;
    padding:13px;
    border:0;
    border-radius:10px;
    background:#0284c7;
    color:white;
    font-weight:bold;
    margin-top:8px;
}

.green{
    background:#059669;
}

.red{
    background:#dc2626;
}

.product{
    background:#020617;
    border:1px solid #263244;
    border-radius:15px;
    padding:18px;
    margin-bottom:12px;
}

.price{
    color:#38bdf8;
    font-size:23px;
    font-weight:bold;
    margin:10px 0;
}

.small{
    color:#94a3b8;
}

.success{
    background:#064e3b;
    padding:12px;
    border-radius:10px;
    margin-bottom:15px;
}

.error{
    background:#7f1d1d;
    padding:12px;
    border-radius:10px;
    margin-bottom:15px;
}

.nav{
    position:fixed;
    bottom:0;
    left:0;
    right:0;
    background:#0f172a;
    border-top:1px solid #1e293b;
    display:flex;
    justify-content:space-around;
    padding:10px;
}

.nav a{
    color:#cbd5e1;
    text-decoration:none;
    font-size:12px;
    text-align:center;
}

.grid{
    display:grid;
    grid-template-columns:
    repeat(auto-fit,minmax(220px,1fr));
    gap:12px;
}

</style>

</head>

<body>

<header>

<div class="logo">
🎮 CYBER GAMING STORE
</div>

</header>

<div class="container">

{% if msg %}
<div class="success">
{{ msg }}
</div>
{% endif %}

{% if error %}
<div class="error">
{{ error }}
</div>
{% endif %}

{{ content|safe }}

</div>

</body>

</html>
"""


# ==================================================
# LOGIN
# ==================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        if (
            username == ADMIN_USERNAME
            and password == ADMIN_PASSWORD
        ):

            session["username"] = username

            return redirect(
                url_for("admin")
            )

        con = db()

        user = con.execute(
            """
            SELECT * FROM users
            WHERE username=?
            """,
            (username,)
        ).fetchone()

        con.close()

        if user and user["password"] == password:

            session["username"] = username

            return redirect(
                url_for("home")
            )

        return render_template_string(
            BASE,
            content=LOGIN_HTML,
            error="Wrong username or password"
        )

    return render_template_string(
        BASE,
        content=LOGIN_HTML
    )


LOGIN_HTML = """
<div class="card">

<h2>🔐 Login</h2>

<form method="POST">

<input
name="username"
placeholder="Username"
required
>

<input
name="password"
type="password"
placeholder="Password"
required
>

<button>
LOGIN
</button>

</form>

<br>

<p class="small">
New user?
<a
href="/register"
style="color:#38bdf8">
Create account
</a>
</p>

</div>
"""


# ==================================================
# REGISTER
# ==================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        if not name or not username or not password:

            return render_template_string(
                BASE,
                content=REGISTER_HTML,
                error="Fill all fields"
            )

        if username == ADMIN_USERNAME:

            return render_template_string(
                BASE,
                content=REGISTER_HTML,
                error="Username unavailable"
            )

        con = db()

        try:

            con.execute(
                """
                INSERT INTO users
                (name, username, password)
                VALUES (?, ?, ?)
                """,
                (
                    name,
                    username,
                    password
                )
            )

            con.commit()

        except sqlite3.IntegrityError:

            con.close()

            return render_template_string(
                BASE,
                content=REGISTER_HTML,
                error="Username already exists"
            )

        con.close()

        return redirect(
            "/login"
        )

    return render_template_string(
        BASE,
        content=REGISTER_HTML
    )


REGISTER_HTML = """
<div class="card">

<h2>📝 Create Account</h2>

<form method="POST">

<input
name="name"
placeholder="Your Name"
required
>

<input
name="username"
placeholder="Username"
required
>

<input
name="password"
type="password"
placeholder="Password"
required
>

<button class="green">
REGISTER
</button>

</form>

<br>

<a
href="/login"
style="color:#38bdf8">
Already have account? Login
</a>

</div>
"""


# ==================================================
# HOME
# ==================================================

@app.route("/")
@login_required
def home():

    username = session["username"]

    con = db()

    user = con.execute(
        """
        SELECT * FROM users
        WHERE username=?
        """,
        (username,)
    ).fetchone()

    products = con.execute(
        "SELECT * FROM products"
    ).fetchall()

    con.close()

    content = render_template_string(
        """
        <div class="card">

        <h2>
        👋 Welcome, {{ user["name"] }}
        </h2>

        <p class="small">
        Wallet Balance
        </p>

        <h1 style="color:#34d399">
        ₹{{ "%.2f"|format(user["balance"]) }}
        </h1>

        </div>

        <div class="card">

        <h2>🛒 Gaming Store</h2>

        <br>

        <div class="grid">

        {% for p in products %}

        <div class="product">

        <h3>
        {{ p["name"] }}
        </h3>

        <div class="price">
        ₹{{ p["price"] }}
        </div>

        {% if p["stock"] > 0 %}

        <p class="small">
        🟢 Stock: {{ p["stock"] }}
        </p>

        <form method="POST"
              action="/buy/{{ p['id'] }}">

        <button class="green">
        BUY NOW
        </button>

        </form>

        {% else %}

        <p style="color:#f87171">
        🔴 OUT OF STOCK
        </p>

        <button disabled>
        OUT OF STOCK
        </button>

        {% endif %}

        </div>

        {% endfor %}

        </div>

        </div>

        <div class="nav">

        <a href="/">
        🛒<br>Store
        </a>

        <a href="/profile">
        👤<br>Profile
        </a>

        <a href="/deposit">
        💰<br>Add Money
        </a>

        <a href="/withdraw">
        💸<br>Withdraw
        </a>

        <a href="/history">
        📜<br>History
        </a>

        <a href="/logout">
        🚪<br>Logout
        </a>

        </div>
        """,
        user=user,
        products=products
    )

    return render_template_string(
        BASE,
        content=content
    )


# ==================================================
# BUY
# ==================================================

@app.route("/buy/<int:product_id>", methods=["POST"])
@login_required
def buy(product_id):

    username = session["username"]

    con = db()

    user = con.execute(
        """
        SELECT * FROM users
        WHERE username=?
        """,
        (username,)
    ).fetchone()

    product = con.execute(
        """
        SELECT * FROM products
        WHERE id=?
        """,
        (product_id,)
    ).fetchone()

    if not product:

        con.close()

        return redirect(
            "/?error=Product+not+found"
        )

    if product["stock"] <= 0:

        con.close()

        return redirect(
            "/?error=Out+of+stock"
        )

    if user["balance"] < product["price"]:

        con.close()

        return redirect(
            "/?error=Insufficient+wallet+balance"
        )

    con.execute(
        """
        UPDATE users
        SET balance=balance-?
        WHERE username=?
        """,
        (
            product["price"],
            username
        )
    )

    con.execute(
        """
        UPDATE products
        SET stock=stock-1
        WHERE id=?
        """,
        (product_id,)
    )

    con.execute(
        """
        INSERT INTO history
        (username,title,amount,status)
        VALUES (?,?,?,?)
        """,
        (
            username,
            product["name"],
            -product["price"],
            "completed"
        )
    )

    con.commit()
    con.close()

    telegram(
        "🛒 NEW ORDER\n\n"
        f"👤 User: {username}\n"
        f"📦 Product: {product['name']}\n"
        f"💰 Price: ₹{product['price']}"
    )

    return redirect(
        "/?msg=Purchase+successful"
    )


# ==================================================
# PROFILE
# ==================================================

@app.route("/profile")
@login_required
def profile():

    username = session["username"]

    con = db()

    user = con.execute(
        """
        SELECT * FROM users
        WHERE username=?
        """,
        (username,)
    ).fetchone()

    con.close()

    content = render_template_string(
        """
        <div class="card">

        <h2>👤 My Profile</h2>

        <br>

        <p>Name</p>
        <h3>{{ user["name"] }}</h3>

        <br>

        <p>Username</p>
        <h3>{{ user["username"] }}</h3>

        <br>

        <p>Wallet</p>
        <h2 style="color:#34d399">
        ₹{{ "%.2f"|format(user["balance"]) }}
        </h2>

        </div>

        <div class="nav">

        <a href="/">🛒<br>Store</a>
        <a href="/profile">👤<br>Profile</a>
        <a href="/deposit">💰<br>Add Money</a>
        <a href="/withdraw">💸<br>Withdraw</a>
        <a href="/history">📜<br>History</a>

        </div>
        """,
        user=user
    )

    return render_template_string(
        BASE,
        content=content
    )


# ==================================================
# DEPOSIT
# ==================================================

@app.route("/deposit", methods=["GET", "POST"])
@login_required
def deposit():

    username = session["username"]

    if request.method == "POST":

        try:
            amount = float(
                request.form.get(
                    "amount",
                    "0"
                )
            )
        except:
            amount = 0

        utr = request.form.get(
            "utr",
            ""
        ).strip()

        if amount <= 0 or not utr:

            return redirect(
                "/deposit?error=Invalid+details"
            )

        con = db()

        con.execute(
            """
            INSERT INTO deposits
            (username,amount,utr)
            VALUES (?,?,?)
            """,
            (
                username,
                amount,
                utr
            )
        )

        con.execute(
            """
            INSERT INTO history
            (username,title,amount,status)
            VALUES (?,?,?,?)
            """,
            (
                username,
                "Wallet Deposit",
                amount,
                "pending"
            )
        )

        con.commit()
        con.close()

        telegram(
            "💰 NEW DEPOSIT\n\n"
            f"👤 User: {username}\n"
            f"💵 Amount: ₹{amount:.2f}\n"
            f"🔢 UTR: {utr}\n\n"
            "Admin panel se approve/reject karein."
        )

        return redirect(
            "/?msg=Deposit+request+submitted"
        )

    content = render_template_string(
        """
        <div class="card">

        <h2>💰 Add Money</h2>

        <p class="small">
        QR/UPI payment ke baad UTR submit karein.
        </p>

        <br>

        <div style="
        background:white;
        color:black;
        padding:20px;
        text-align:center;
        border-radius:15px;
        ">

        <h3>📱 PAYMENT UPI</h3>

        <p>{{ upi }}</p>

        </div>

        <br>

        <form method="POST">

        <input
        type="number"
        step="0.01"
        min="1"
        name="amount"
        placeholder="Amount"
        required
        >

        <input
        name="utr"
        placeholder="UTR / Transaction ID"
        required
        >

        <button class="green">
        SUBMIT PAYMENT
        </button>

        </form>

        </div>

        <div class="nav">

        <a href="/">🛒<br>Store</a>
        <a href="/profile">👤<br>Profile</a>
        <a href="/deposit">💰<br>Add Money</a>
        <a href="/withdraw">💸<br>Withdraw</a>
        <a href="/history">📜<br>History</a>

        </div>
        """,
        upi=PAYMENT_UPI
    )

    return render_template_string(
        BASE,
        content=content
    )


# ==================================================
# WITHDRAW
# ==================================================

@app.route("/withdraw", methods=["GET", "POST"])
@login_required
def withdraw():

    username = session["username"]

    if request.method == "POST":

        try:
            amount = float(
                request.form.get(
                    "amount",
                    "0"
                )
            )
        except:
            amount = 0

        upi = request.form.get(
            "upi",
            ""
        ).strip()

        con = db()

        user = con.execute(
            """
            SELECT * FROM users
            WHERE username=?
            """,
            (username,)
        ).fetchone()

        if amount <= 0 or not upi:

            con.close()

            return redirect(
                "/withdraw?error=Invalid+details"
            )

        if user["balance"] < amount:

            con.close()

            return redirect(
                "/withdraw?error=Insufficient+balance"
            )

        con.execute(
            """
            UPDATE users
            SET balance=balance-?
            WHERE username=?
            """,
            (
                amount,
                username
            )
        )

        con.execute(
            """
            INSERT INTO withdrawals
            (username,amount,upi)
            VALUES (?,?,?)
    
