@app.route("/shop")
def shop():
    if "username" not in session:
        return redirect(url_for("login"))
    
    conn = sqlite3.connect('store.db')
    cursor = conn.cursor()
    cursor.execute("SELECT balance, is_admin FROM users WHERE username = ?", (session["username"],))
    user_data = cursor.fetchone()
    balance = user_data[0] if user_data else 0.0
    is_admin = user_data[1] if user_data else 0

    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    conn.close()

    # Yahan stats aur history pass karna zaroori hai
    history = session.get("search_history", [])
    return render_template(
        "shop.html", 
        username=session["username"], 
        balance=balance, 
        is_admin=is_admin, 
        products=products, 
        history=history, 
        stats=site_stats
    )
    
