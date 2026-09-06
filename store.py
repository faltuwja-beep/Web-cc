from flask import Flask, request, redirect, session, render_template_string
import os
import sqlite3
import secrets

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", secrets.token_hex(32))

DB = "store.db"

ADMIN_USER = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASSWORD", "change-me")

UPI_ID = os.getenv("PAYMENT_UPI", "yourupi@upi")


def connect():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def setup():

    con = connect()

    con.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        balance REAL DEFAULT 0
    )
    """)

    con.execute("""
    CREATE TABLE IF NOT EXISTS history(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        title TEXT,
        amount REAL,
        status TEXT
    )
    """)

    con.execute("""
    CREATE TABLE IF NOT EXISTS deposits(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        amount REAL,
        utr TEXT,
        status TEXT DEFAULT 'pending'
    )
    """)

    con.execute("""
    CREATE TABLE IF NOT EXISTS products(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price REAL,
        stock INTEGER
    )
    """)

    if con.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:

        con.executemany(
            "INSERT INTO products(name,price,stock) VALUES(?,?,?)",
            [
                ("🎮 Gaming Credit Pack", 199, 10),
                ("🔥 Premium Gaming Pack", 899, 5),
                ("🏆 Tournament Entry", 50, 20),
                ("👑 VIP Membership", 299, 0)
            ]
        )

    con.commit()
    con.close()


PAGE = """
<!DOCTYPE html>
<html>
<head>

<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">

<title>Cyber Gaming Store</title>

<style>

*{
    box-sizing:border-box;
    font-family:Arial;
}

body{
    margin:0;
    background:#030712;
    color:white;
}

header{
    background:#0f172a;
    padding:20px;
    text-align:center;
}

.logo{
    color:#38bdf8;
    font-size:27px;
    font-weight:bold;
}

.container{
    max-width:900px;
    margin:auto;
    padding:20px;
    padding-bottom:90px;
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
    color:white;
    border:1px solid #334155;
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
    padding:18px;
    border-radius:15px;
    margin:10px 0;
}

.price{
    color:#38bdf8;
    font-size:24px;
    font-weight:bold;
    margin:10px 0;
}

.small{
    color:#94a3b8;
}

.nav{
    position:fixed;
    bottom:0;
    left:0;
    right:0;
    background:#0f172a;
    padding:10px;
    display:flex;
    justify-content:space-around;
}

.nav a{
    color:white;
    text-decoration:none;
    font-size:12px;
    text-align:center;
}

.msg{
    background:#064e3b;
    padding:13px;
    border-radius:10px;
    margin-bottom:15px;
}

</style>

</head>

<body>

<header>
<div class="logo">🎮 CYBER GAMING STORE</div>
</header>

<div class="container">

{% if msg %}
<div class="msg">{{ msg }}</div>
{% endif %}

{{ content|safe }}

</div>

</body>
</html>
"""


def page(content, msg=None):
    return render_template_string(
        PAGE,
        content=content,
        msg=msg
    )


LOGIN = """
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

<button>LOGIN</button>

</form>

<br>

<a href="/register" style="color:#38bdf8">
Create New Account
</a>

</div>
"""


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == ADMIN_USER and password == ADMIN_PASS:

            session["user"] = "admin"

            return redirect("/admin")

        con = connect()

        user = con.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        ).fetchone()

        con.close()

        if user and user["password"] == password:

            session["user"] = username

            return redirect("/")

        return page(
            LOGIN,
            "Wrong username or password"
        )

    return page(LOGIN)


REGISTER = """
<div class="card">

<h2>📝 Register</h2>

<form method="POST">

<input
name="name"
placeholder="Full Name"
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
CREATE ACCOUNT
</button>

</form>

<br>

<a href="/login" style="color:#38bdf8">
Already have account? Login
</a>

</div>
"""


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        username = request.form["username"]
        password = request.form["password"]

        con = connect()

        try:

            con.execute(
                """
                INSERT INTO users
                (name,username,password)
                VALUES(?,?,?)
                """,
                (name, username, password)
            )

            con.commit()

        except sqlite3.IntegrityError:

            con.close()

            return page(
                REGISTER,
                "Username already exists"
            )

        con.close()

        return redirect("/login")

    return page(REGISTER)


@app.route("/")
def home():

    if "user" not in session:
        return redirect("/login")

    username = session["user"]

    con = connect()

    user = con.execute(
        "SELECT * FROM users WHERE username=?",
        (username,)
    ).fetchone()

    products = con.execute(
        "SELECT * FROM products"
    ).fetchall()

    con.close()

    content = render_template_string(
        """
        <div class="card">

        <h2>👋 Welcome {{ user["name"] }}</h2>

        <p class="small">
        Wallet Balance
        </p>

        <h1 style="color:#34d399">
        ₹{{ "%.2f"|format(user["balance"]) }}
        </h1>

        </div>

        <div class="card">

        <h2>🛒 Products</h2>

        {% for p in products %}

        <div class="product">

        <h3>{{ p["name"] }}</h3>

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

    return page(content)


@app.route("/buy/<int:pid>", methods=["POST"])
def buy(pid):

    if "user" not in session:
        return redirect("/login")

    username = session["user"]

    con = connect()

    product = con.execute(
        "SELECT * FROM products WHERE id=?",
        (pid,)
    ).fetchone()

    user = con.execute(
        "SELECT * FROM users WHERE username=?",
        (username,)
    ).fetchone()

    if not product or product["stock"] <= 0:

        con.close()

        return redirect(
            "/?msg=Out+of+stock"
        )

    if user["balance"] < product["price"]:

        con.close()

        return redirect(
            "/?msg=Insufficient+balance"
        )

    con.execute(
        """
        UPDATE users
        SET balance=balance-?
        WHERE username=?
        """,
        (product["price"], username)
    )

    con.execute(
        """
        UPDATE products
        SET stock=stock-1
        WHERE id=?
        """,
        (pid,)
    )

    con.execute(
        """
        INSERT INTO history
        (username,title,amount,status)
        VALUES(?,?,?,?)
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

    return redirect(
        "/?msg=Purchase+successful"
    )


@app.route("/profile")
def profile():

    if "user" not in session:
        return redirect("/login")

    username = session["user"]

    con = connect()

    user = con.execute(
        "SELECT * FROM users WHERE username=?",
        (username,)
    ).fetchone()

    con.close()

    content = f"""
    <div class="card">

    <h2>👤 Profile</h2>

    <br>

    <b>Name</b>
    <p>{user["name"]}</p>

    <b>Username</b>
    <p>{user["username"]}</p>

    <b>Wallet</b>
    <h2 style="color:#34d399">
    ₹{user["balance"]:.2f}
    </h2>

    </div>

    <div class="nav">

    <a href="/">🛒<br>Store</a>
    <a href="/profile">👤<br>Profile</a>
    <a href="/deposit">💰<br>Add Money</a>
    <a href="/history">📜<br>History</a>
    <a href="/logout">🚪<br>Logout</a>

    </div>
    """

    return page(content)


@app.route("/deposit", methods=["GET", "POST"])
def deposit():

    if "user" not in session:
        return redirect("/login")

    username = session["user"]

    if request.method == "POST":

        amount = float(
            request.form["amount"]
        )

        utr = request.form["utr"]

        con = connect()

        con.execute(
            """
            INSERT INTO deposits
            (username,amount,utr)
            VALUES(?,?,?)
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
            VALUES(?,?,?,?)
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

        return redirect(
            "/?msg=Deposit+request+sent"
        )

    content = f"""
    <div class="card">

    <h2>💰 Add Money</h2>

    <p class="small">
    Pay using your UPI app and submit the UTR.
    </p>

    <br>

    <div style="
    background:white;
    color:black;
    padding:20px;
    border-radius:15px;
    text-align:center;
    ">

    <h3>📱 UPI</h3>

    <b>{UPI_ID}</b>

    </div>

    <br>

    <form method="POST">

    <input
    type="number"
    name="amount"
    min="1"
    placeholder="Amount"
    required
    >

    <input
    name="utr"
    placeholder="UTR / Transaction ID"
    required
    >

    <button class="green">
    SUBMIT DEPOSIT
    </button>

    </form>

    </div>
    """

    return page(content)


@app.route("/history")
def history():

    if "user" not in session:
        return redirect("/login")

    username = session["user"]

    con = connect()

    rows = con.execute(
        """
        SELECT * FROM history
        WHERE username=?
        ORDER BY id DESC
        """,
        (username,)
    ).fetchall()

    con.close()

    content = "<div class='card'><h2>📜 History</h2><br>"

    for row in rows:

        content += f"""
        <div class="product">

        <b>{row["title"]}</b>

        <br><br>

        Amount:
        ₹{row["amount"]:.2f}

        <br>

        Status:
        {row["status"]}

        </div>
        """

    content += """
    </div>

    <div class="nav">

    <a href="/">🛒<br>Store</a>
    <a href="/profile">👤<br>Profile</a>
    <a href="/deposit">💰<br>Add Money</a>
    <a href="/history">📜<br>History</a>
    <a href="/logout">🚪<br>Logout</a>

    </div>
    """

    return page(content)


@app.route("/admin")
def admin():

    if session.get("user") != ADMIN_USER:
        return redirect("/login")

    con = connect()

    deposits = con.execute(
        """
        SELECT * FROM deposits
        WHERE status='pending'
        ORDER BY id DESC
        """
    ).fetchall()

    users = con.execute(
        "SELECT * FROM users"
    ).fetchall()

    con.close()

    content = """
    <div class="card">

    <h2>👑 ADMIN PANEL</h2>

    </div>

    <div class="card">

    <h3>💰 Pending Deposits</h3>

    <br>
    """

    if not deposits:

        content += """
        <p class="small">
        No pending deposits.
        </p>
        """

    for d in deposits:

        content += f"""
        <div class="product">

        👤 {d["username"]}

        <br>

        💰 ₹{d["amount"]}

        <br>

        🔢 UTR: {d["utr"]}

        <br><br>

        <a href="/admin/deposit/{d["id"]}/approve">

        <button class="green">
        ✅ APPROVE
        </button>

        </a>

        <a href="/admin/deposit/{d["id"]}/reject">

        <button class="red">
        ❌ REJECT
        </button>

        </a>

        </div>
        """

    content += """
    </div>

    <div class="card">

    <h3>👥 Users</h3>

    <br>
    """

    for u in users:

        content += f"""
        <div class="product">

        <b>{u["username"]}</b>

        <br>

        Balance:
        ₹{u["balance"]:.2f}

        </div>
        """

    content += """
    </div>

    <div class="nav">

    <a href="/admin">
    👑<br>Admin
    </a>

    <a href="/logout">
    🚪<br>Logout
    </a>

    </div>
    """

    return page(content)


@app.route("/admin/deposit/<int:did>/approve")
def approve(did):

    if session.get("user") != ADMIN_USER:
        return redirect("/login")

    con = connect()

    d = con.execute(
        """
        SELECT * FROM deposits
        WHERE id=? AND status='pending'
        """,
        (did,)
    ).fetchone()

    if d:

        con.execute(
            """
            UPDATE users
            SET balance=balance+?
            WHERE username=?
            """,
            (
                d["amount"],
                d["username"]
            )
        )

        con.execute(
            """
            UPDATE deposits
            SET status='approved'
            WHERE id=?
            """,
            (did,)
        )

        con.execute(
            """
            INSERT INTO history
            (username,title,amount,status)
            VALUES(?,?,?,?)
            """,
            (
                d["username"],
                "Deposit Approved",
                d["amount"],
                "approved"
            )
        )

        con.commit()

    con.close()

    return redirect("/admin")


@app.route("/admin/deposit/<int:did>/reject")
def reject(did):

    if session.get("user") != ADMIN_USER:
        return redirect("/login")

    con = connect()

    con.execute(
        """
        UPDATE deposits
        SET status='rejected'
        WHERE id=? AND status='pending'
        """,
        (did,)
    )

    con.commit()
    con.close()

    return redirect("/admin")


@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


setup()


if __name__ == "__main__":

    port = int(
        os.getenv("PORT", "8080")
    )

    app.run(
        host="0.0.0.0",
        port=port
)
