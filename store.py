from flask import Flask, render_template_string, request, redirect

app = Flask(__name__)

# =========================
# PRODUCTS
# =========================

products = [
    {
        "id": 1,
        "name": "Free Fire Tournament Entry",
        "price": 50,
        "stock": 10,
        "emoji": "🎮"
    },
    {
        "id": 2,
        "name": "Premium Gaming Pass",
        "price": 100,
        "stock": 5,
        "emoji": "🔥"
    },
    {
        "id": 3,
        "name": "VIP Gaming Membership",
        "price": 199,
        "stock": 0,
        "emoji": "👑"
    },
    {
        "id": 4,
        "name": "Tournament Special Pass",
        "price": 299,
        "stock": 3,
        "emoji": "🏆"
    }
]


# =========================
# WEBSITE DESIGN
# =========================

HTML = """
<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>Cyber Gaming Store</title>

<style>

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    background: #050816;
    color: white;
    font-family: Arial, sans-serif;
}

header {
    background: #0b1120;
    padding: 25px 15px;
    text-align: center;
    border-bottom: 1px solid #1e293b;
}

.logo {
    font-size: 30px;
    font-weight: bold;
    color: #38bdf8;
}

.subtitle {
    margin-top: 8px;
    color: #94a3b8;
}

.container {
    max-width: 1000px;
    margin: auto;
    padding: 25px 15px;
}

.hero {
    text-align: center;
    padding: 25px 10px;
}

.hero h1 {
    font-size: 32px;
    margin-bottom: 10px;
}

.hero p {
    color: #94a3b8;
}

.products {
    display: grid;
    grid-template-columns:
    repeat(auto-fit, minmax(230px, 1fr));

    gap: 18px;
}

.product {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 18px;
    padding: 20px;

    transition: 0.2s;
}

.product:hover {
    transform: translateY(-4px);
    border-color: #38bdf8;
}

.emoji {
    font-size: 45px;
    margin-bottom: 12px;
}

.product h2 {
    font-size: 20px;
    margin-bottom: 12px;
}

.price {
    color: #38bdf8;
    font-size: 25px;
    font-weight: bold;
    margin-bottom: 10px;
}

.stock {
    color: #94a3b8;
    margin-bottom: 15px;
}

.buy {
    width: 100%;
    padding: 13px;

    border: none;
    border-radius: 10px;

    background: #0284c7;
    color: white;

    font-size: 16px;
    font-weight: bold;

    cursor: pointer;
}

.buy:hover {
    background: #0369a1;
}

.disabled {
    width: 100%;
    padding: 13px;

    border: none;
    border-radius: 10px;

    background: #374151;
    color: #9ca3af;

    font-weight: bold;
}

.message {
    background: #064e3b;
    border: 1px solid #10b981;

    padding: 14px;
    border-radius: 12px;

    text-align: center;
    margin-bottom: 20px;
}

footer {
    text-align: center;
    padding: 30px;

    color: #64748b;
}

</style>

</head>

<body>


<header>

<div class="logo">
🎮 CYBER GAMING STORE
</div>

<div class="subtitle">
Gaming Products & Tournament Services
</div>

</header>


<div class="container">


<div class="hero">

<h1>
🔥 Welcome Gamer
</h1>

<p>
Choose your gaming product
</p>

</div>


{% if message %}

<div class="message">
{{ message }}
</div>

{% endif %}


<div class="products">


{% for product in products %}

<div class="product">


<div class="emoji">
{{ product.emoji }}
</div>


<h2>
{{ product.name }}
</h2>


<div class="price">
₹{{ product.price }}
</div>


<div class="stock">

{% if product.stock > 0 %}

🟢 {{ product.stock }} Available

{% else %}

🔴 OUT OF STOCK

{% endif %}

</div>


{% if product.stock > 0 %}

<form method="POST" action="/buy">

<input
type="hidden"
name="product_id"
value="{{ product.id }}"
>

<button class="buy"
type="submit">

BUY NOW

</button>

</form>

{% else %}

<button
class="disabled"
disabled>

OUT OF STOCK

</button>

{% endif %}


</div>

{% endfor %}


</div>


</div>


<footer>

© 2026 Cyber Gaming Store

</footer>


</body>

</html>
"""


# =========================
# HOME
# =========================

@app.route("/")
def home():

    message = request.args.get("message")

    return render_template_string(
        HTML,
        products=products,
        message=message
    )


# =========================
# BUY
# =========================

@app.route("/buy", methods=["POST"])
def buy():

    try:
        product_id = int(
            request.form.get("product_id")
        )
    except:
        return redirect(
            "/?message=Invalid+product"
        )


    for product in products:

        if product["id"] == product_id:

            if product["stock"] <= 0:

                return redirect(
                    "/?message=Product+is+out+of+stock"
                )


            # Reduce stock

            product["stock"] -= 1


            return redirect(
                "/?message=Order+received+successfully!"
            )


    return redirect(
        "/?message=Product+not+found"
    )


# =========================
# START SERVER
# =========================

if __name__ == "__main__":

    port = 8080

    print("")
    print("==============================")
    print("🎮 CYBER GAMING STORE")
    print("==============================")
    print(f"🌐 Port: {port}")
    print("==============================")
    print("")

    app.run(
        host="0.0.0.0",
        port=port
    )
