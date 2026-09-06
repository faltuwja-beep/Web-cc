from flask import Flask, render_template, request, redirect, session
import sqlite3
import os

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "gamehub-demo-secret"
)

DB = "gamehub.db"

ADMIN_USER = os.environ.get("ADMIN_USER", "sonu22")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "333")


def database():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def setup_database():
    con = database()

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
            icon TEXT DEFAULT '🎮'
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            price REAL NOT NULL,
            status TEXT DEFAULT 'Processing'
        )
    """)

    total = con.execute(
        "SELECT COUNT(*) FROM products"
    ).fetchone()[0]

    if total == 0:
        items = [
            (
                "100 Diamonds",
                "Gaming currency package",
                80,
                "💎"
            ),
            (
                "310 Diamonds",
                "Gaming currency package",
                240,
                "💎"
            ),
            (
                "Starter Pack",
                "Beginner gaming pack",
                99,
                "🎁"
            ),
            (
                "Premium Gaming Item",
                "Premium digital gaming item",
                149,
                "🔥"
            )
        ]

        con.executemany(
            """
            INSERT INTO products
            (name, description, price, icon)
            VALUES (?, ?, ?, ?)
            """,
            items
        )

    con.commit()
    con.close()


@app.route("/")
def home():
    con = database()

    products = con.execute(
        "SELECT * FROM products ORDER BY id DESC"
    ).fetchall()

    user = None

    if session.get("user_id"):
        user = con.execute(
            "SELECT * FROM users WHERE id=?",
            (session["user_id"],)
        ).fetchone()

    con.close()

    return render_template(
        "home.html",
        products=products,
        user=user
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    error = ""

    if request.method == "POST":
        username = request.form.get(
            "username", ""
        ).strip()

        password = request.form.get(
            "password", ""
        )

        if len(username) < 3:
            error = "Username must be at least 3 characters."

        elif len(password) < 4:
            error = "Password must be at least 4 characters."

        else:
            try:
                con = database()

                con.execute(
                    """
                    INSERT INTO users
                    (username, password)
                    VALUES (?, ?)
                    """,
                    (username, password)
                )

                con.commit()
                con.close()

                return redirect("/login")

            except sqlite3.IntegrityError:
                error = "Username already exists."

    return render_template(
        "register.html",
        error=error
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""

    if request.method == "POST":
        username = request.form.get(
            "username", ""
        )

        password = request.form.get(
            "password", ""
        )

        con = database()

        user = con.execute(
            """
            SELECT *
            FROM users
            WHERE username=? AND password=?
            """,
            (username, password)
        ).fetchone()

        con.close()

        if user:
            session["user_id"] = user["id"]
            return redirect("/")

        error = "Invalid username or password."

    return render_template(
        "login.html",
        error=error
    )


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect("/")


@app.route("/wallet")
def wallet():
    if not session.get("user_id"):
        return redirect("/login")

    con = database()

    user = con.execute(
        "SELECT * FROM users WHERE id=?",
        (session["user_id"],)
    ).fetchone()

    con.close()

    return render_template(
        "wallet.html",
        user=user
    )


@app.route("/orders")
def orders():
    if not session.get("user_id"):
        return redirect("/login")

    con = database()

    data = con.execute(
        """
        SELECT
            orders.id,
            products.name,
            products.icon,
            orders.price,
            orders.status
        FROM orders
        JOIN products
        ON products.id = orders.product_id
        WHERE orders.user_id=?
        ORDER BY orders.id DESC
        """,
        (session["user_id"],)
    ).fetchall()

    con.close()

    return render_template(
        "orders.html",
        orders=data
    )


@app.route("/buy/<int:product_id>")
def buy(product_id):
    if not session.get("user_id"):
        return redirect("/login")

    con = database()

    user = con.execute(
        "SELECT * FROM users WHERE id=?",
        (session["user_id"],)
    ).fetchone()

    product = con.execute(
        "SELECT * FROM products WHERE id=?",
        (product_id,)
    ).fetchone()

    if product is None:
        con.close()
        return "Product not found", 404

    if user["wallet"] < product["price"]:
        con.close()
        return redirect("/wallet")

    con.execute(
        """
        UPDATE users
        SET wallet=wallet-?
        WHERE id=?
        """,
        (product["price"], user["id"])
    )

    con.execute(
        """
        INSERT INTO orders
        (user_id, product_id, price, status)
        VALUES (?, ?, ?, ?)
        """,
        (
            user["id"],
            product["id"],
            product["price"],
            "Processing"
        )
    )

    con.commit()
    con.close()

    return redirect("/orders")


@app.route("/admin", methods=["GET", "POST"])
def admin():
    error = ""

    if request.method == "POST":
        username = request.form.get(
            "username", ""
        )

        password = request.form.get(
            "password", ""
        )

        if (
            username == ADMIN_USER
            and password == ADMIN_PASS
        ):
            session["admin"] = True
            return redirect("/admin/dashboard")

        error = "Wrong admin credentials."

    return render_template(
        "admin_login.html",
        error=error
    )


@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin"):
        return redirect("/admin")

    con = database()

    users = con.execute(
        "SELECT * FROM users ORDER BY id DESC"
    ).fetchall()

    products = con.execute(
        "SELECT * FROM products ORDER BY id DESC"
    ).fetchall()

    orders = con.execute(
        """
        SELECT
            orders.id,
            users.username,
            products.name,
            orders.price,
            orders.status
        FROM orders
        JOIN users
        ON users.id=orders.user_id
        JOIN products
        ON products.id=orders.product_id
        ORDER BY orders.id DESC
        """
    ).fetchall()

    con.close()

    return render_template(
        "admin_dashboard.html",
        users=users,
        products=products,
        orders=orders
    )


@app.route(
    "/admin/product/add",
    methods=["POST"]
)
def add_product():
    if not session.get("admin"):
        return redirect("/admin")

    name = request.form.get(
        "name", ""
    ).strip()

    description = request.form.get(
        "description", ""
    ).strip()

    icon = request.form.get(
        "icon", "🎮"
    ).strip()

    try:
        price = float(
            request.form.get("price", "0")
        )
    except ValueError:
        price = 0

    if name and price > 0:
        con = database()

        con.execute(
            """
            INSERT INTO products
            (name, description, price, icon)
            VALUES (?, ?, ?, ?)
            """,
            (
                name,
                description,
                price,
                icon
            )
        )

        con.commit()
        con.close()

    return redirect("/admin/dashboard")


@app.route(
    "/admin/product/delete/<int:product_id>"
)
def delete_product(product_id):
    if not session.get("admin"):
        return redirect("/admin")

    con = database()

    con.execute(
        "DELETE FROM products WHERE id=?",
        (product_id,)
    )

    con.commit()
    con.close()

    return redirect("/admin/dashboard")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect("/admin")


setup_database()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get("PORT", 8080)
        ),
        debug=False
  )
