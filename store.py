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

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_ADMIN_CHAT_ID", "")


# =========================
# DATABASE
# =========================

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def setup():
    con = db()

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
            stock INTEGER DEFAULT 0,
            category TEXT DEFAULT 'Gaming'
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            product_id INTEGER,
            product_name TEXT,
            price REAL,
            status TEXT DEFAULT 'Pending',
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

    # Default products
    count = con.execute(
        "SELECT COUNT(*) AS c FROM products"
    ).fetchone()["c"]

    if count == 0:
        products = [
            (
                "🎮 Gaming Credit Pack",
                "Gaming credits for supported games.",
                199,
                20,
                "Gaming"
            ),
            (
                "🔥 Premium Gaming Pack",
                "Premium gaming package.",
                499,
                10,
                "Gaming"
            ),
            (
                "🏆 Tournament Entry",
                "Entry pass for an eligible tournament.",
                50,
                50,
                "Tournament"
            ),
            (
                "👑 VIP Membership",
                "VIP membership for the store.",
                299,
                15,
                "Membership"
            )
        ]

        con.executemany("""
            INSERT INTO products
            (name, description, price, stock, category)
            VALUES (?, ?, ?, ?, ?)
        """, products)

    con.commit()
    con.close()


# =========================
# TELEGRAM
# =========================

def telegram(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return

    try:
        url = (
            "https://api.telegram.org/bot"
            + TELEGRAM_TOKEN
            + "/sendMessage?"
            + urllib.parse.urlencode({
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message
            })
        )

        urllib.request.urlopen(url, timeout=10)

    except Exception:
        pass


# =========================
# HTML / CSS
# =========================

BASE = """
<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">

<title>{{ title }}</title>

<style>

*{
    box-sizing:border-box;
}

body{
    margin:0;
    font-family:Arial,sans-serif;
    background:#080b14;
    color:#fff;
}

.nav{
    background:#111827;
    padding:16px;
    display:flex;
    justify-content:space-between;
    align-items:center;
    position:sticky;
    top:0;
    z-index:10;
    border-bottom:1px solid #263044;
}

.logo{
    font-size:22px;
    font-weight:bold;
    color:#60a5fa;
}

.nav a{
    color:#fff;
    text-decoration:none;
    margin-left:12px;
    font-size:14px;
}

.container{
    max-width:1100px;
    margin:auto;
    padding:25px 15px;
}

.hero{
    padding:35px 20px;
    border-radius:22px;
    background:
      linear-gradient(135deg,#111827,#172554);
    border:1px solid #263b68;
    margin-bottom:25px;
}

.hero h1{
    font-size:35px;
    margin:0 0 10px;
}

.hero p{
    color:#aab4c7;
}

.grid{
    display:grid;
    grid-template-columns:
      repeat(auto-fit,minmax(220px,1fr));
    gap:18px;
}

.card{
    background:#111827;
    border:1px solid #263044;
    border-radius:18px;
    padding:20px;
    box-shadow:0 8px 30px rgba(0,0,0,.25);
}

.card h3{
    margin-top:0;
}

.price{
    font-size:25px;
    font-weight:bold;
    color:#4ade80;
    margin:15px 0;
}

.stock{
    color:#94a3b8;
    font-size:13px;
}

.btn{
    display:inline-block;
    width:100%;
    border:0;
    padding:13px;
    border-radius:12px;
    background:#2563eb;
    color:white;
    text-decoration:none;
    text-align:center;
    cursor:pointer;
    font-weight:bold;
}

.btn:hover{
    background:#1d4ed8;
}

.btn.green{
    background:#16a34a;
}

.btn.red{
    background:#dc2626;
}

input,select{
    width:100%;
    padding:13px;
    margin:7px 0 13px;
    background:#0b1220;
    color:white;
    border:1px solid #334155;
    border-radius:10px;
}

table{
    width:100%;
    border-collapse:collapse;
    background:#111827;
    border-radius:12px;
    overflow:hidden;
}

th,td{
    padding:12px;
    border-bottom:1px solid #263044;
    text-align:left;
}

th{
    color:#93c5fd;
}

.stat{
    font-size:28px;
    font-weight:bold;
}

.muted{
    color:#94a3b8;
}

.alert{
    padding:13px;
    border-radius:10px;
    margin-bottom:15px;
    background:#172033;
}

.footer{
    text-align:center;
    padding:35px;
    color:#64748b;
}

@media(max-width:600px){
    .hero h1{
        font-size:27px;
    }

    table{
        font-size:13px;
    }

    th,td{
        padding:8px;
    }
}

</style>
</head>

<body>

<div class="nav">

<div class="logo">🎮 SONU GAMING</div>

<div>
{% if session.get("user") %}
<a href="/">Home</a>
<a href="/wallet">₹ Wallet</a>
<a href="/orders">Orders</a>
<a href="/profile">Profile</a>
<a href="/logout">Logout</a>
{% else %}
<a href="/login">Login</a>
<a href="/register">Register</a>
{% endif %}
</div>

</div>

<div class="container">

{{ content|safe }}

</div>

<div class="footer">
SONU GAMING STORE • Digital Gaming Products
</div>

</body>
</html>
"""


def page(title, content):
    return render_template_string(
        BASE,
        title=title,
        content=content
    )


# =========================
# HOME
# =========================

@app.route("/")
def home():

    con = db()
    products = con.execute(
        "SELECT * FROM products ORDER BY id DESC"
    ).fetchall()
    con.close()

    cards = ""

    for p in products:

        if p["stock"] > 0:
            button = f"""
            <a class="btn" href="/buy/{p['id']}">
                Buy Now
            </a>
            """
        else:
            button = """
            <button class="btn" disabled>
                Out of Stock
            </button>
            """

        cards += f"""
        <div class="card">

            <h3>{p['name']}</h3>

            <p class="muted">
                {p['description']}
            </p>

            <div class="price">
                ₹{p['price']:.2f}
            </div>

            <div class="stock">
                Stock: {p['stock']}
            </div>

            <br>

            {button}

        </div>
        """

    content = f"""
    <div class="hero">

        <h1>Level Up Your Gaming 🎮</h1>

        <p>
        Fast • Simple • Secure gaming store
        </p>

        <a class="btn" href="#products">
            Explore Products
        </a>

    </div>

    <h2 id="products">
        🔥 Featured Products
    </h2>

    <div class="grid">
        {cards}
    </div>
    """

    return page("SONU GAMING", content)


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
            message = "Username/password too short."

        else:

            try:

                con = db()

                con.execute(
                    "INSERT INTO users(username,password) VALUES(?,?)",
                    (username, password)
                )

                con.commit()
                con.close()

                return redirect("/login")

            except sqlite3.IntegrityError:

                message = "Username already exists."

    content = f"""
    <div class="card">

        <h2>✨ Create Account</h2>

        <div class="alert">
            {message}
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

    return page("Register", content)


# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    message = ""

    if request.method == "POST":

        username = request.form.get("username", "")
        password = request.form.get("password", "")

        con = db()

        user = con.execute(
            """
            SELECT * FROM users
            WHERE username=? AND password=?
            """,
            (username, password)
        ).fetchone()

        con.close()

        if user:

            session["user"] = username

            return redirect("/")

        message = "Invalid username or password."

    content = f"""
    <div class="card">

        <h2>🔐 Login</h2>

        <div class="alert">
            {message}
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

    return page("Login", content)


# =========================
# BUY
# =========================

@app.route("/buy/<int:product_id>")
def buy(product_id):

    if not session.get("user"):
        return redirect("/login")

    username = session["user"]

    con = db()

    product = con.execute(
        "SELECT * FROM products WHERE id=?",
        (product_id,)
    ).fetchone()

    user = con.execute(
        "SELECT * FROM users WHERE username=?",
        (username,)
    ).fetchone()

    if not product:
        con.close()
        return "Product not found", 404

    if product["stock"] <= 0:
        con.close()
        return "Product is out of stock."

    if user["wallet"] < product["price"]:

        con.close()

        return page(
            "Insufficient Balance",
            """
            <div class="card">
                <h2>💰 Insufficient Balance</h2>
                <p>
                Please add money to your wallet first.
                </p>
                <a class="btn" href="/wallet">
                    Add Money
                </a>
            </div>
            """
        )

    con.execute(
        """
        UPDATE users
        SET wallet = wallet - ?
        WHERE username=?
        """,
        (product["price"], username)
    )

    con.execute(
        """
        UPDATE products
        SET stock = stock - 1
        WHERE id=?
        """,
        (product_id,)
    )

    con.execute(
        """
        INSERT INTO orders
        (username,product_id,product_name,price,status)
        VALUES(?,?,?,?,?)
        """,
        (
            username,
            product["id"],
            product["name"],
            product["price"],
            "Processing"
        )
    )

    con.commit()
    con.close()

    telegram(
        f"🛒 NEW ORDER\n\n"
        f"User: {username}\n"
        f"Product: {product['name']}\n"
        f"Amount: ₹{product['price']}"
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

    con = db()

    user = con.execute(
        "SELECT * FROM users WHERE username=?",
        (username,)
    ).fetchone()

    deposits = con.execute(
        """
        SELECT * FROM deposits
        WHERE username=?
        ORDER BY id DESC
        """,
        (username,)
    ).fetchall()

    con.close()

    rows = ""

    for d in deposits:
        rows += f"""
        <tr>
            <td>₹{d['amount']:.2f}</td>
            <td>{d['utr']}</td>
            <td>{d['status']}</td>
            <td>{d['created_at']}</td>
        </tr>
        """

    content = f"""
    <div class="hero">

        <h2>💰 My Wallet</h2>

        <div class="stat">
            ₹{user['wallet']:.2f}
        </div>

    </div>

    <div class="card">

        <h2>➕ Add Money</h2>

        <p class="muted">
            UPI ID:
            <b>{UPI_ID}</b>
        </p>

        <p>
            Payment karne ke baad UTR/Transaction ID
            submit karein. Admin verification ke baad
            wallet balance add hoga.
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

        {rows}

        </table>

    </div>
    """

    return page("Wallet", content)


# =========================
# DEPOSIT
# =========================

@app.route("/deposit", methods=["POST"])
def deposit():

    if not session.get("user"):
        return redirect("/login")

    username = session["user"]

    try:
        amount = float(request.form.get("amount", 0))
    except ValueError:
        amount = 0

    utr = request.form.get("utr", "").strip()

    if amount <= 0 or not utr:
        return "Invalid deposit."

    con = db()

    con.execute(
        """
        INSERT INTO deposits
        (username,amount,utr,status)
        VALUES(?,?,?,'Pending')
        """,
        (username, amount, utr)
    )

    con.commit()
    con.close()

    telegram(
        f"💰 NEW DEPOSIT REQUEST\n\n"
        f"User: {username}\n"
        f"Amount: ₹{amount:.2f}\n"
        f"UTR: {utr}"
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

    con = db()

    orders = con.execute(
        """
        SELECT * FROM orders
        WHERE username=?
        ORDER BY id DESC
        """,
        (username,)
    ).fetchall()

    con.close()

    rows = ""

    for o in orders:

        rows += f"""
        <tr>
            <td>#{o['id']}</td>
            <td>{o['product_name']}</td>
            <td>₹{o['price']:.2f}</td>
            <td>{o['status']}</td>
            <td>{o['created_at']}</td>
        </tr>
        """

    content = f"""
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

        {rows}

        </table>

    </div>
    """

    return page("Orders", content)


# =========================
# PROFILE
# =========================

@app.route("/profile")
def profile():

    if not session.get("user"):
        return redirect("/login")

    username = session["user"]

    con = db()

    user = con.execute(
        "SELECT * FROM users WHERE username=?",
        (username,)
    ).fetchone()

    con.close()

    content = f"""
    <div class="card">

        <h2>👤 Profile</h2>

        <p>
            Username:
            <b>{user['username']}</b>
        </p>

        <p>
            Wallet:
            <b>₹{user['wallet']:.2f}</b>
        </p>

    </div>
    """

    return page("Profile", content)


# =========================
# ADMIN LOGIN
# =========================

@app.route("/admin", methods=["GET", "POST"])
def admin():

    if session.get("admin"):
        return redirect("/admin/dashboard")

    message = ""

    if request.method == "POST":

        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if username == ADMIN_USER and password == ADMIN_PASS:

            session["admin"] = True

            return redirect("/admin/dashboard")

        message = "Wrong admin username/password."

    content = f"""
    <div class="card">

        <h2>🔐 Admin Login</h2>

        <div class="alert">
            {message}
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
                Admin Login
            </button>

        </form>

    </div>
    """

    return page("Admin Login", content)


# =========================
# ADMIN DASHBOARD
# =========================

@app.route("/admin/dashboard")
def admin_dashboard():

    if not session.get("admin"):
        return redirect("/admin")

    con = db()

    users = con.execute(
        "SELECT COUNT(*) AS c FROM users"
    ).fetchone()["c"]

    products = con.execute(
        "SELECT COUNT(*) AS c FROM products"
    ).fetchone()["c"]

    orders = con.execute(
        "SELECT COUNT(*) AS c FROM orders"
    ).fetchone()["c"]

    pending = con.execute(
        """
        SELECT COUNT(*) AS c
        FROM deposits
        WHERE status='Pending'
        """
    ).fetchone()["c"]

    con.close()

    content = f"""
    <div class="hero">

        <h1>👑 Admin Dashboard</h1>

        <p>
            Welcome, {ADMIN_USER}
        </p>

    </div>

    <div class="grid">

        <div class="card">
            <h3>👥 Users</h3>
            <div class="stat">{users}</div>
        </div>

        <div class="card">
            <h3>📦 Products</h3>
            <div class="stat">{products}</div>
        </div>

        <div class="card">
            <h3>🛒 Orders</h3>
            <div class="stat">{orders}</div>
        </div>

        <div class="card">
            <h3>💰 Pending Deposits</h3>
 
