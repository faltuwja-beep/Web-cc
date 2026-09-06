from flask import Flask, request, redirect, session, render_template_string
import sqlite3
import os
import secrets
import urllib.parse
import urllib.request

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", secrets.token_hex(32))

DB = "store.db"

ADMIN_USER = os.getenv("ADMIN_USERNAME", "sonu22")
ADMIN_PASS = os.getenv("ADMIN_PASSWORD", "333")

UPI_ID = os.getenv("PAYMENT_UPI", "yourupi@upi")

TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TG_CHAT_ID = os.getenv("TELEGRAM_ADMIN_CHAT_ID", "")


# =========================
# DATABASE
# =========================

def get_db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def setup_db():
    con = get_db()

    con.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            wallet REAL DEFAULT 0
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            stock INTEGER DEFAULT 0
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            product_id INTEGER,
            product_name TEXT,
            price REAL,
            status TEXT DEFAULT 'Processing',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS deposits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            amount REAL,
            utr TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    total = con.execute(
        "SELECT COUNT(*) AS n FROM products"
    ).fetchone()["n"]

    if total == 0:
        con.executemany(
            """
            INSERT INTO products
            (name, description, price, stock)
            VALUES (?, ?, ?, ?)
            """,
            [
                (
                    "Gaming Credit Pack",
                    "Gaming credit package",
                    199,
                    20
                ),
                (
                    "Premium Gaming Pack",
                    "Premium gaming package",
                    499,
                    10
                ),
                (
                    "Tournament Entry",
                    "Tournament entry pass",
                    50,
                    50
                ),
                (
                    "VIP Membership",
                    "Gaming VIP membership",
                    299,
                    15
                )
            ]
        )

    con.commit()
    con.close()


# =========================
# TELEGRAM
# =========================

def send_telegram(text):
    if not TG_TOKEN or not TG_CHAT_ID:
        return

    try:
        params = urllib.parse.urlencode({
            "chat_id": TG_CHAT_ID,
            "text": text
        })

        url = (
            "https://api.telegram.org/bot"
            + TG_TOKEN
            + "/sendMessage?"
            + params
        )

        urllib.request.urlopen(url, timeout=10)

    except Exception:
        pass


# =========================
# DESIGN
# =========================

STYLE = """
<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    background: #070b14;
    color: white;
    font-family: Arial, sans-serif;
}

.nav {
    background: #101827;
    border-bottom: 1px solid #263246;
    padding: 15px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    position: sticky;
    top: 0;
}

.logo {
    color: #60a5fa;
    font-size: 20px;
    font-weight: bold;
}

.nav a {
    color: white;
    text-decoration: none;
    margin-left: 10px;
    font-size: 13px;
}

.container {
    max-width: 1050px;
    margin: auto;
    padding: 20px 15px;
}

.hero {
    padding: 30px 20px;
    border-radius: 22px;
    background: linear-gradient(
        135deg,
        #111827,
        #172554
    );
    border: 1px solid #263b68;
    margin-bottom: 25px;
}

.hero h1 {
    font-size: 32px;
    margin: 0 0 10px;
}

.card {
    background: #111827;
    border: 1px solid #263246;
    border-radius: 18px;
    padding: 20px;
}

.grid {
    display: grid;
    grid-template-columns:
        repeat(auto-fit, minmax(220px, 1fr));
    gap: 16px;
}

.price {
    color: #4ade80;
    font-size: 25px;
    font-weight: bold;
    margin: 15px 0;
}

.muted {
    color: #94a3b8;
}

.btn {
    display: inline-block;
    width: 100%;
    padding: 12px;
    border: 0;
    border-radius: 10px;
    background: #2563eb;
    color: white;
    text-align: center;
    text-decoration: none;
    cursor: pointer;
    font-weight: bold;
}

.btn.green {
    background: #16a34a;
}

.btn.red {
    background: #dc2626;
}

input {
    width: 100%;
    padding: 13px;
    margin: 7px 0 12px;
    border-radius: 10px;
    border: 1px solid #334155;
    background: #080d18;
    color: white;
}

table {
    width: 100%;
    border-collapse: collapse;
}

th, td {
    padding: 10px;
    border-bottom: 1px solid #263246;
    text-align: left;
}

th {
    color: #93c5fd;
}

.stat {
    font-size: 28px;
    font-weight: bold;
}

.alert {
    background: #172033;
    padding: 12px;
    border-radius: 10px;
    margin-bottom: 15px;
}

.footer {
    text-align: center;
    padding: 30px;
    color: #64748b;
}

@media(max-width: 600px) {

    .hero h1 {
        font-size: 26px;
    }

    .nav {
        flex-direction: column;
        gap: 10px;
    }

    table {
        font-size: 12px;
    }

}

</style>
"""


def render_page(title, body):
    html = """
    <!doctype html>
    <html>
    <head>
        <meta name="viewport"
              content="width=device-width, initial-scale=1">
        <title>""" + title + """</title>
        """ + STYLE + """
    </head>

    <body>

    <div class="nav">

        <div class="logo">
            🎮 SONU GAMING
        </div>

        <div>
    """

    if session.get("user"):
        html += """
            <a href="/">Home</a>
            <a href="/wallet">Wallet</a>
            <a href="/orders">Orders</a>
            <a href="/profile">Profile</a>
            <a href="/logout">Logout</a>
        """
    else:
        html += """
            <a href="/login">Login</a>
            <a href="/register">Register</a>
        """

    html += """
        </div>

    </div>

    <div class="container">
    """

    html += body

    html += """
    </div>

    <div class="footer">
        SONU GAMING STORE
    </div>

    </body>
    </html>
    """

    return render_template_string(html)


# =========================
# HOME
# =========================

@app.route("/")
def home():

    con = get_db()

    products = con.execute(
        "SELECT * FROM products ORDER BY id DESC"
    ).fetchall()

    con.close()

    cards = ""

    for p in products:

        if p["stock"] > 0:
            action = (
                '<a class="btn" href="/buy/'
                + str(p["id"])
                + '">Buy Now</a>'
            )
        else:
            action = (
                '<button class="btn red" disabled>'
                'Out of Stock'
                '</button>'
            )

        cards += """
        <div class="card">

            <h3>""" + p["name"] + """</h3>

            <p class="muted">
                """ + p["description"] + """
            </p>

            <div class="price">
                ₹""" + f"{p['price']:.2f}" + """
            </div>

            <p class="muted">
                Stock: """ + str(p["stock"]) + """
            </p>

            """ + action + """

        </div>
        """

    body = """
    <div class="hero">

        <h1>Level Up Your Gaming 🎮</h1>

        <p class="muted">
            Premium gaming products in one place.
        </p>

    </div>

    <h2>🔥 Products</h2>

    <div class="grid">
    """ + cards + """
    </div>
    """

    return render_page("SONU GAMING", body)


# =========================
# REGISTER
# =========================

@app.route("/register", methods=["GET", "POST"])
def register():

    message = ""

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if len(username) < 3 or len(password) < 3:

            message = "Username aur password kam se kam 3 characters ke hon."

        else:

            try:

                con = get_db()

                con.execute(
                    """
                    INSERT INTO users(username, password)
                    VALUES (?, ?)
                    """,
                    (username, password)
                )

                con.commit()
                con.close()

                return redirect("/login")

            except sqlite3.IntegrityError:

                message = "Username already exists."

    body = """
    <div class="card">

        <h2>✨ Create Account</h2>

        <div class="alert">
            """ + message + """
        </div>

        <form method="post">

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

            <button class="btn">
                Register
            </button>

        </form>

    </div>
    """

    return render_page("Register", body)


# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    message = ""

    if request.method == "POST":

        username = request.form.get("username", "")
        password = request.form.get("password", "")

        con = get_db()

        user = con.execute(
            """
            SELECT * FROM users
            WHERE username = ? AND password = ?
            """,
            (username, password)
        ).fetchone()

        con.close()

        if user:

            session["user"] = username

            return redirect("/")

        message = "Wrong username or password."

    body = """
    <div class="card">

        <h2>🔐 Login</h2>

        <div class="alert">
            """ + message + """
        </div>

        <form method="post">

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

            <button class="btn">
                Login
            </button>

        </form>

    </div>
    """

    return render_page("Login", body)


# =========================
# BUY
# =========================

@app.route("/buy/<int:product_id>")
def buy(product_id):

    if not session.get("user"):
        return redirect("/login")

    username = session["user"]

    con = get_db()

    product = con.execute(
        "SELECT * FROM products WHERE id = ?",
        (product_id,)
    ).fetchone()

    user = con.execute(
        "SELECT * FROM users WHERE username = ?",
        (username,)
    ).fetchone()

    if not product:

        con.close()
        return "Product not found.", 404

    if product["stock"] <= 0:

        con.close()
        return "Product out of stock."

    if user["wallet"] < product["price"]:

        con.close()

        body = """
        <div class="card">

            <h2>💰 Insufficient Balance</h2>

            <p class="muted">
                Wallet me enough balance nahi hai.
            </p>

            <a class="btn" href="/wallet">
                Add Money
            </a>

        </div>
        """

        return render_page("Balance", body)

    con.execute(
        """
        UPDATE users
        SET wallet = wallet - ?
        WHERE username = ?
        """,
        (product["price"], username)
    )

    con.execute(
        """
        UPDATE products
        SET stock = stock - 1
        WHERE id = ?
        """,
        (product_id,)
    )

    con.execute(
        """
        INSERT INTO orders
        (username, product_id, product_name, price)
        VALUES (?, ?, ?, ?)
        """,
        (
            username,
            product["id"],
            product["name"],
            product["price"]
        )
    )

    con.commit()
    con.close()

    send_telegram(
        "🛒 NEW ORDER\n"
        "User: " + username + "\n"
        "Product: " + product["name"] + "\n"
        "Amount: ₹" + str(product["price"])
    )

    return redirect("/orders")


# =========================
# WALLET
# =========================

@app.route("/wallet")
def wallet():

    if not session.get("user"):
        return redirect("/login")

    username = session["user"]

    con = get_db()

    user = con.execute(
        "SELECT * FROM users WHERE username = ?",
        (username,)
    ).fetchone()

    deposits = con.execute(
        """
        SELECT * FROM deposits
        WHERE username = ?
        ORDER BY id DESC
        """,
        (username,)
    ).fetchall()

    con.close()

    rows = ""

    for d in deposits:

        rows += """
        <tr>
            <td>₹""" + f"{d['amount']:.2f}" + """</td>
            <td>""" + d["utr"] + """</td>
            <td>""" + d["status"] + """</td>
            <td>""" + d["created_at"] + """</td>
        </tr>
        """

    body = """
    <div class="hero">

        <h2>💰 My Wallet</h2>

        <div class="stat">
            ₹""" + f"{user['wallet']:.2f}" + """
        </div>

    </div>

    <div class="card">

        <h2>➕ Add Money</h2>

        <p class="muted">
            UPI ID:
            <b>""" + UPI_ID + """</b>
        </p>

        <p class="muted">
            Payment karne ke baad UTR submit karein.
            Admin verification ke baad balance add hoga.
        </p>

        <form method="post" action="/deposit">

            <input
                name="amount"
                type="number"
                min="1"
                step="0.01"
                placeholder="Amount"
                required
            >

            <input
                name="utr"
                placeholder="UTR / Transaction ID"
                required
            >

            <button class="btn green">
                Submit Deposit
            </button>

        </form>

    </div>

    <br>

    <div class="card">

        <h2>Deposit History</h2>

        <table>

            <tr>
                <th>Amount</th>
                <th>UTR</th>
                <th>Status</th>
                <th>Date</th>
            </tr>

            """ + rows + """

        </table>

    </div>
    """

    return render_page("Wallet", body)


# =========================
# DEPOSIT
# =========================

@app.route("/deposit", methods=["POST"])
def deposit():

    if not session.get("user"):
        return redirect("/login")

    username = session["user"]

    try:
        amount = float(
            request.form.get("amount", "0")
        )
    except ValueError:
        amount = 0

    utr = request.form.get("utr", "").strip()

    if amount <= 0 or not utr:
        return "Invalid deposit."

    con = get_db()

    con.execute(
        """
        INSERT INTO deposits
        (username, amount, utr)
        VALUES (?, ?, ?)
        """,
        (username, amount, utr)
    )

    con.commit()
    con.close()

    send_telegram(
        "💰 NEW DEPOSIT\n"
        "User: " + username + "\n"
        "Amount: ₹" + str(amount) + "\n"
        "UTR: " + utr
    )

    return redirect("/wallet")


# =========================
# ORDERS
# =========================

@app.route("/orders")
def orders():

    if not session.get("user"):
        return redirect("/login")

    username = session["user"]

    con = get_db()

    data = con.execute(
        """
        SELECT * FROM orders
        WHERE username = ?
        ORDER BY id DESC
        """,
        (username,)
    ).fetchall()

    con.close()

    rows = ""

    for o in data:

        rows += """
        <tr>
            <td>#""" + str(o["id"]) + """</td>
            <td>""" + o["product_name"] + """</td>
            <td>₹""" + f"{o['price']:.2f}" + """</td>
            <td>""" + o["status"] + """</td>
            <td>""" + o["created_at"] + """</td>
        </tr>
        """

    body = """
    <div class="card">

        <h2>📦 My Orders</h2>

        <table>

            <tr>
                <th>ID</th>
                <th>Product</th>
                <th>Amount</th>
                <th>Status</th>
                <th>Date</th>
            </tr>

            """ + rows + """

        </table>

    </div>
    """

    return render_page("Orders", body)


# =========================
# PROFILE
# =========================

@app.route("/profile")
def profile():

    if not session.get("user"):
        return redirect("/login")

    username = session["user"]

    con = get_db()

    user = con.execute(
        "SELECT * FROM users WHERE username = ?",
        (username,)
    ).fetchone()

    con.close()

    body = """
    <div class="card">

        <h2>👤 Profile</h2>

        <p>
            Username:
            <b>""" + user["username"] + """</b>
        </p>

        <p>
            Wallet:
            <b>₹""" + f"{user['wallet']:.2f}" + """</b>
        </p>

    </div>
    """

    return render_page("Profile", body)


# =========================
# ADMIN LOGIN
# =========================

@app.route("/admin", methods=["GET", "POST"])
def admin_login():

    if session.get("admin"):
        return redirect("/admin/dashboard")

    message = ""

    if request.method == "POST":

        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if username == ADMIN_USER and password == ADMIN_PASS:

            session["admin"] = True

            return redirect("/admin/dashboard")

        message = "Wrong admin login."

    body = """
    <div class="card">

        <h2>👑 Admin Login</h2>

        <div class="alert">
            """ + message + """
        </div>

        <form method="post">

            <input
                name="username"
                placeholder="Admin Username"
                required
            >

            <input
                name="password"
                type="password"
                placeholder="Admin Password"
                required
            >

            <button class="btn">
                Login
            </button>

        </form>

    </div>
    """

    return render_page("Admin Login", body)


# =========================
# ADMIN DASHBOARD
# =========================

@app.route("/admin/dashboard")
def admin_dashboard():

    if not session.get("admin"):
        return redirect("/admin")

    con = get_db()

    users = con.execute(
        "SELECT COUNT(*) AS n FROM users"
    ).fetchone()["n"]

    products = con.execute(
        "SELECT COUNT(*) AS n FROM products"
    ).fetchone()["n"]

    orders = con.execute(
        "SELECT COUNT(*) AS n FROM orders"
    ).fetchone()["n"]

    deposits = con.execute(
        """
        SELECT COUNT(*) AS n
        FROM deposits
        WHERE status = 'Pending'
        """
    ).fetchone()["n"]

    con.close()

    body = """
    <div class="hero">

        <h1>👑 Admin Dashboard</h1>

        <p class="muted">
            Welcome, """ + ADMIN_USER + """
        </p>

    </div>

    <div class="grid">

        <div class="card">
            <h3>👥 Users</h3>
           
