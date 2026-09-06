<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YoYo Shop</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }
        body {
            background-color: #0d0914;
            color: #ffffff;
            padding-bottom: 90px;
        }
        .header {
            padding: 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #0d0914;
            position: sticky;
            top: 0;
            z-index: 100;
        }
        .shop-title {
            font-size: 1.2rem;
            font-weight: 700;
        }
        .shop-url {
            font-size: 0.8rem;
            color: #a09cb0;
        }
        .categories {
            display: flex;
            gap: 10px;
            padding: 0 16px 12px 16px;
            overflow-x: auto;
            scrollbar-width: none;
        }
        .chip {
            background: #1e182d;
            border: 1px solid #2d2442;
            color: #d1cce3;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.85rem;
            white-space: nowrap;
            cursor: pointer;
        }
        .chip.active {
            background: #10b981;
            color: #ffffff;
            border-color: #10b981;
        }
        .section-title {
            padding: 0 16px 12px 16px;
            font-size: 1rem;
            color: #10b981;
            font-weight: 600;
        }
        .products-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            padding: 0 16px;
        }
        .product-card {
            background: #171124;
            border: 1px solid #251d36;
            border-radius: 14px;
            padding: 12px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        .card-preview {
            width: 100%;
            height: 85px;
            background: linear-gradient(135deg, #1f2937, #111827);
            border-radius: 8px;
            padding: 8px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            margin-bottom: 10px;
        }
        .card-number {
            font-family: monospace;
            font-size: 0.75rem;
            color: #e5e7eb;
        }
        .product-name {
            font-size: 0.85rem;
            font-weight: 700;
            margin-bottom: 2px;
        }
        .price {
            font-size: 1rem;
            font-weight: 800;
            color: #fbbf24;
        }
        .card-actions {
            display: flex;
            gap: 6px;
            margin-top: 8px;
        }
        .btn {
            flex: 1;
            padding: 8px 4px;
            border-radius: 8px;
            font-size: 0.75rem;
            font-weight: 600;
            cursor: pointer;
            border: none;
            text-align: center;
        }
        .btn-add {
            background: #231b35;
            color: #d1cce3;
            border: 1px solid #362a4f;
        }
        .btn-buy {
            background: #0f2d22;
            color: #10b981;
            border: 1px solid #144633;
        }
        .bottom-bag {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: #14101e;
            border-top: 1px solid #251d36;
            padding: 14px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .bag-btn {
            background: linear-gradient(135deg, #f59e0b, #d97706);
            color: #ffffff;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            font-weight: 700;
            cursor: pointer;
        }
    </style>
</head>
<body>

    <div class="header">
        <div>
            <div class="shop-title">YoYo Shop</div>
            <div class="shop-url">ccshop01.netlify.app</div>
        </div>
    </div>

    <div class="categories">
        <div class="chip active">All</div>
        <div class="chip">ANTI BAN PANEL</div>
        <div class="chip">APPS SUBSCRIPTION</div>
    </div>

    <div class="section-title">✨ Products</div>

    <div class="products-grid">
        <div class="product-card">
            <div class="card-preview">
                <div style="font-size:0.6rem; color:#fbbf24;">VISA</div>
                <div class="card-number">•••• 8565</div>
            </div>
            <div class="product-name">DEMO VISA CARD</div>
            <div class="price">₹399</div>
            <div class="card-actions">
                <button class="btn btn-add">Add</button>
                <button class="btn btn-buy">Buy Now</button>
            </div>
        </div>

        <div class="product-card">
            <div class="card-preview" style="background: linear-gradient(135deg, #111827, #1f2937);">
                <div style="font-size:0.6rem; color:#fbbf24;">MASTERCARD</div>
                <div class="card-number">•••• 6745</div>
            </div>
            <div class="product-name">DEMO MASTERCARD</div>
            <div class="price">₹399</div>
            <div class="card-actions">
                <button class="btn btn-add">Add</button>
                <button class="btn btn-buy">Buy Now</button>
            </div>
        </div>
    </div>

    <div class="bottom-bag">
        <div>1 item(s) · ₹250</div>
        <button class="bag-btn">View Bag →</button>
    </div>

</body>
</html>
