from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
import requests

app = Flask(__name__)
app.secret_key = "xenon_store_secret_key"

TELEGRAM_BOT_TOKEN = "8822410482:AAEgv8CYy3VKHn6sv6Rezsw9BSQna5vsUJo"
TELEGRAM_CHAT_ID = "7161571409"

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception:
        pass

def init_db():
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE,
                        password TEXT,
                        balance REAL DEFAULT 0.0,
                        is_admin INTEGER DEFAULT 0)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS products (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        category TEXT,
                        price REAL,
                        details TEXT)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS payments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT,
                        amount REAL,
                        utr TEXT,
                        status TEXT DEFAULT 'Pending')''')

    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password, balance, is_admin) VALUES ('admin', 'admin123', 0.0, 1)")

    cursor.execute("SELECT * FROM products")
    if not cursor.fetchone():
        default_items = [
            ("Google Play Redeem Code", "Redeem Code", 699.0, "Balance: ₹5,000 | Code: GPR-9982-XYZ"),
            ("Demo Visa Card", "CC Card", 399.0, "Balance: ₹10,000 | 4532xxxx 09/28 123"),
            ("Mastercard VIP", "CC Card", 1099.0, "Balance: ₹25,000 | 5412xxxx 11/27 456"),
            ("Blackmarket Visa", "CC Card", 499.0, "Balance: ₹15,000 | 4000xxxx 05/29 789")
        ]
        cursor.executemany("INSERT INTO products (name, category, price, details) VALUES (?, ?, ?, ?)", default_items)

    conn.commit()
    conn.close()

init_db()

@app.route("/")
def home():
    if "username" in session:
        return redirect(url_for("shop"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if not username or not password:
            flash("❌ Please fill in all fields", "error")
            return render_template("login.html")

        conn = sqlite3.connect('store.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session["username"] = user[1]
            session["is_admin"] = user[4]
            return redirect(url_for("shop"))
        else:
            flash("❌ Invalid Username or Password", "error")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if not username or not password:
            flash("❌ Please fill in all fields", "error")
            return render_template("register.html")

        try:
            conn = sqlite3.connect('store.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()

            send_telegram_alert(f"👤 *New User Registered in Xenon Store!*\n🆔 User ID: `#{user_id}`\n📛 Username: `{username}`")

            flash("✅ Account created successfully! Please login.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("❌ Username already taken! Choose another.", "error")
    return render_template("register.html")

@app.route("/shop")
def shop():
    if "username" not in session:
        return redirect(url_for("login"))
    
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, balance, is_admin FROM users WHERE username = ?", (session["username"],))
    user_data = cursor.fetchone()
    user_id = user_data[0] if user_data else 0
    balance = user_data[1] if user_data else 0.0
    is_admin = user_data[2] if user_data else 0

    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()

    cursor.execute("SELECT amount, utr, status FROM payments WHERE username = ? ORDER BY id DESC LIMIT 5", (session["username"],))
    my_payments = cursor.fetchall()
    conn.close()

    return render_template("shop.html", user_id=user_id, username=session["username"], balance=balance, is_admin=is_admin, products=products, my_payments=my_payments)

@app.route("/buy/<int:product_id>")
def buy_product(product_id):
    if "username" not in session:
        return redirect(url_for("login"))
    
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, balance FROM users WHERE username = ?", (session["username"],))
    user_res = cursor.fetchone()
    user_id = user_res[0] if user_res else 0
    balance = user_res[1] if user_res else 0.0

    cursor.execute("SELECT name, price, details FROM products WHERE id = ?", (product_id,))
    prod = cursor.fetchone()

    if not prod:
        conn.close()
        flash("❌ Product not found!", "error")
        return redirect(url_for("shop"))

    p_name, p_price, p_details = prod

    if balance >= p_price:
        cursor.execute("UPDATE users SET balance = balance - ? WHERE username = ?", (p_price, session["username"]))
        conn.commit()
        conn.close()

        send_telegram_alert(f"🛍️ *Product Purchased on Xenon Store!*\n🆔 User ID: `#{user_id}`\n👤 User: `{session['username']}`\n📦 Item: `{p_name}`\n💵 Price: `₹{p_price}`\n🔑 Details: `{p_details}`")

        flash(f"🎉 Successfully Purchased {p_name}! Your Details/Code: {p_details}", "success")
    else:
        conn.close()
        shortfall = p_price - balance
        flash(f"⚠️ Insufficient balance! You need ₹{shortfall} more. Please add money via QR.", "error")

    return redirect(url_for("shop"))

@app.route("/add-money", methods=["POST"])
def add_money():
    if "username" not in session:
        return redirect(url_for("login"))
    try:
        amount = float(request.form.get("amount", 0))
    except ValueError:
        amount = 0.0
    utr = request.form.get("utr", "").strip()

    if amount <= 0 or not utr:
        flash("❌ Please enter valid amount and UTR number", "error")
        return redirect(url_for("shop"))

    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO payments (username, amount, utr, status) VALUES (?, ?, ?, 'Pending')", 
                   (session["username"], amount, utr))
    conn.commit()
    conn.close()

    send_telegram_alert(f"🔔 *New Payment Proof submitted on Xenon Store!*\n👤 User: `{session['username']}`\n💰 Amount: `₹{amount}`\n🔢 UTR: `{utr}`\n\n*Aap /admin panel me jaakar approve/reject karein.*")

    flash("⏳ Payment proof submitted! Admin will verify and approve soon.", "success")
    return redirect(url_for("shop"))

@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    if "username" not in session:
        return redirect(url_for("login"))
        
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    cursor.execute("SELECT is_admin FROM users WHERE username = ?", (session["username"],))
    res = cursor.fetchone()
    if not res or res[0] != 1:
        conn.close()
        return redirect(url_for("shop"))

    if request.method == "POST":
        action = request.form.get("action")
        if action == "add_product":
            name = request.form.get("name")
            category = request.form.get("category")
            price = float(request.form.get("price", 0))
            details = request.form.get("details")
            cursor.execute("INSERT INTO products (name, category, price, details) VALUES (?, ?, ?, ?)", (name, category, price, details))
        elif action == "edit_product":
            pid = request.form.get("pid")
            price = float(request.form.get("price", 0))
            details = request.form.get("details")
            cursor.execute("UPDATE products SET price = ?, details = ? WHERE id = ?", (price, details, pid))
        elif action == "delete_product":
            pid = request.form.get("pid")
            cursor.execute("DELETE FROM products WHERE id = ?", (pid,))
        elif action == "approve_payment":
            pay_id = request.form.get("pay_id")
            cursor.execute("SELECT username, amount FROM payments WHERE id = ?", (pay_id,))
            pay_data = cursor.fetchone()
            if pay_data:
                uname, amt = pay_data
                cursor.execute("UPDATE users SET balance = balance + ? WHERE username = ?", (amt, uname))
                cursor.execute("UPDATE payments SET status = 'Approved' WHERE id = ?", (pay_id,))
        elif action == "reject_payment":
            pay_id = request.form.get("pay_id")
            cursor.execute("SELECT status FROM payments WHERE id = ?", (pay_id,))
            pay_status = cursor.fetchone()
            if pay_status and pay_status[0] == 'Pending':
                cursor.execute("UPDATE payments SET status = 'Rejected' WHERE id = ?", (pay_id,))
        conn.commit()

    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    cursor.execute("SELECT * FROM payments ORDER BY id DESC")
    payments = cursor.fetchall()
    conn.close()
    return render_template("admin.html", products=products, payments=payments)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
    
