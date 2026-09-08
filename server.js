const express = require("express");
const fs = require("fs");
const path = require("path");
const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");

const app = express();

const PORT = process.env.PORT || 3000;
const JWT_SECRET =
  process.env.JWT_SECRET || "CHANGE_THIS_SECRET_IN_RENDER";

const ADMIN_EMAIL =
  process.env.ADMIN_EMAIL || "admin@xenon.shop";

const ADMIN_PASSWORD =
  process.env.ADMIN_PASSWORD || "ChangeMe123!";

const DATA_DIR = path.join(__dirname, "data");
const DB_FILE = path.join(DATA_DIR, "db.json");

app.use(express.json({ limit: "1mb" }));
app.use(express.static(path.join(__dirname, "public")));

function makeDB() {
  return {
    users: [],
    products: [
      {
        id: 1,
        name: "₹500 Redeem Code",
        price: 500,
        icon: "🎟️",
        description: "Digital ₹500 redeem code"
      },
      {
        id: 2,
        name: "₹1000 Redeem Code",
        price: 1000,
        icon: "💳",
        description: "Digital ₹1000 redeem code"
      },
      {
        id: 3,
        name: "₹5000 Redeem Code",
        price: 5000,
        icon: "💎",
        description: "Premium ₹5000 redeem code"
      }
    ],
    coupons: [],
    deposits: [],
    orders: [],
    support: [],
    nextUserId: 1,
    nextProductId: 4,
    nextCouponId: 1,
    nextDepositId: 1,
    nextOrderId: 1,
    nextSupportId: 1
  };
}

function ensureDB() {
  if (!fs.existsSync(DATA_DIR)) {
    fs.mkdirSync(DATA_DIR, { recursive: true });
  }

  if (!fs.existsSync(DB_FILE)) {
    saveDB(makeDB());
  }
}

function loadDB() {
  ensureDB();

  try {
    return JSON.parse(fs.readFileSync(DB_FILE, "utf8"));
  } catch {
    const db = makeDB();
    saveDB(db);
    return db;
  }
}

function saveDB(db) {
  if (!fs.existsSync(DATA_DIR)) {
    fs.mkdirSync(DATA_DIR, { recursive: true });
  }

  fs.writeFileSync(
    DB_FILE,
    JSON.stringify(db, null, 2)
  );
}

function uid() {
  return (
    "XENON-" +
    Math.random().toString(36).substring(2, 8).toUpperCase()
  );
}

function referralCode() {
  return (
    "REF-" +
    Math.random().toString(36).substring(2, 8).toUpperCase()
  );
}

function makeToken(user) {
  return jwt.sign(
    {
      id: user.id,
      email: user.email
    },
    JWT_SECRET,
    { expiresIn: "7d" }
  );
}

function auth(req, res, next) {
  const header = req.headers.authorization || "";

  if (!header.startsWith("Bearer ")) {
    return res.status(401).json({
      error: "Login required"
    });
  }

  const token = header.substring(7);

  try {
    req.user = jwt.verify(token, JWT_SECRET);
    next();
  } catch {
    return res.status(401).json({
      error: "Invalid or expired login"
    });
  }
}

function adminAuth(req, res, next) {
  const email = req.headers["x-admin-email"];
  const password = req.headers["x-admin-password"];

  if (
    email !== ADMIN_EMAIL ||
    password !== ADMIN_PASSWORD
  ) {
    return res.status(401).json({
      error: "Admin authentication failed"
    });
  }

  next();
}

function publicUser(user) {
  return {
    id: user.id,
    uid: user.uid,
    name: user.name,
    email: user.email,
    wallet: user.wallet,
    referralCode: user.referralCode,
    membership: user.membership,
    createdAt: user.createdAt
  };
}

/* =========================
   AUTH
========================= */

app.post("/api/register", async (req, res) => {
  const db = loadDB();

  const {
    name,
    email,
    password,
    referralCode: ref
  } = req.body;

  if (!name || !email || !password) {
    return res.status(400).json({
      error: "Name, email and password required"
    });
  }

  if (password.length < 6) {
    return res.status(400).json({
      error: "Password minimum 6 characters"
    });
  }

  const cleanEmail = String(email)
    .trim()
    .toLowerCase();

  if (
    db.users.some(
      u => u.email === cleanEmail
    )
  ) {
    return res.status(400).json({
      error: "Email already registered"
    });
  }

  let referredBy = null;

  if (ref) {
    const parent = db.users.find(
      u => u.referralCode.toLowerCase() ===
        String(ref).trim().toLowerCase()
    );

    if (parent) {
      referredBy = parent.id;
    }
  }

  const passwordHash =
    await bcrypt.hash(password, 10);

  const user = {
    id: db.nextUserId++,
    uid: uid(),
    name: String(name).trim(),
    email: cleanEmail,
    passwordHash,
    wallet: 0,
    referralCode: referralCode(),
    referredBy,
    referralRewardGiven: false,
    membership: "VIP",
    createdAt: new Date().toISOString()
  };

  db.users.push(user);
  saveDB(db);

  res.json({
    token: makeToken(user),
    user: publicUser(user)
  });
});

app.post("/api/login", async (req, res) => {
  const db = loadDB();

  const email = String(req.body.email || "")
    .trim()
    .toLowerCase();

  const password = String(
    req.body.password || ""
  );

  const user = db.users.find(
    u => u.email === email
  );

  if (!user) {
    return res.status(401).json({
      error: "Invalid email or password"
    });
  }

  const ok =
    await bcrypt.compare(
      password,
      user.passwordHash
    );

  if (!ok) {
    return res.status(401).json({
      error: "Invalid email or password"
    });
  }

  res.json({
    token: makeToken(user),
    user: publicUser(user)
  });
});

app.get("/api/me", auth, (req, res) => {
  const db = loadDB();

  const user = db.users.find(
    u => u.id === req.user.id
  );

  if (!user) {
    return res.status(404).json({
      error: "User not found"
    });
  }

  res.json(publicUser(user));
});

/* =========================
   PRODUCTS
========================= */

app.get("/api/products", (req, res) => {
  const db = loadDB();

  res.json(db.products);
});

/* =========================
   COUPONS
========================= */

app.post(
  "/api/coupon/check",
  auth,
  (req, res) => {
    const db = loadDB();

    const product = db.products.find(
      p => p.id === Number(req.body.productId)
    );

    if (!product) {
      return res.status(404).json({
        error: "Product not found"
      });
    }

    const code = String(
      req.body.code || ""
    ).trim().toUpperCase();

    const coupon = db.coupons.find(
      c =>
        c.code === code &&
        c.active === true
    );

    if (!coupon) {
      return res.status(400).json({
        error: "Invalid coupon"
      });
    }

    if (
      coupon.expiresAt &&
      new Date(coupon.expiresAt) < new Date()
    ) {
      return res.status(400).json({
        error: "Coupon expired"
      });
    }

    const discount =
      Math.floor(
        product.price *
        coupon.discountPercent /
        100
      );

    const finalPrice =
      Math.max(0, product.price - discount);

    res.json({
      discountPercent: coupon.discountPercent,
      discount,
      finalPrice
    });
  }
);

/* =========================
   ORDERS
========================= */

app.post("/api/orders", auth, (req, res) => {
  const db = loadDB();

  const user = db.users.find(
    u => u.id === req.user.id
  );

  const product = db.products.find(
    p => p.id === Number(req.body.productId)
  );

  if (!user || !product) {
    return res.status(404).json({
      error: "User or product not found"
    });
  }

  let price = product.price;
  let couponUsed = null;

  const code = String(
    req.body.coupon || ""
  ).trim().toUpperCase();

  if (code) {
    const coupon = db.coupons.find(
      c =>
        c.code === code &&
        c.active === true
    );

    if (coupon) {
      const discount =
        Math.floor(
          product.price *
          coupon.discountPercent /
          100
        );

      price =
        Math.max(
          0,
          product.price - discount
        );

      couponUsed = coupon.code;
    }
  }

  if (user.wallet < price) {
    return res.status(400).json({
      error:
        "Insufficient wallet balance. Add money first."
    });
  }

  user.wallet -= price;

  const digitalCode =
    "XENON-" +
    Math.random()
      .toString(36)
      .substring(2, 10)
      .toUpperCase() +
    "-" +
    Math.random()
      .toString(36)
      .substring(2, 8)
      .toUpperCase();

  const order = {
    id: db.nextOrderId++,
    userId: user.id,
    productId: product.id,
    productName: product.name,
    amount: price,
    coupon: couponUsed,
    code: digitalCode,
    createdAt: new Date().toISOString()
  };

  db.orders.push(order);

  /*
    Referral reward:
    ₹50 only on referred user's first purchase.
  */

  if (
    user.referredBy &&
    !user.referralRewardGiven
  ) {
    const parent = db.users.find(
      u => u.id === user.referredBy
    );

    if (parent) {
      parent.wallet += 50;

      user.referralRewardGiven = true;
    }
  }

  saveDB(db);

  res.json({
    success: true,
    orderId: order.id,
    code: digitalCode,
    amount: price,
    wallet: user.wallet
  });
});

/* =========================
   DEPOSITS
========================= */

app.post("/api/deposits", auth, (req, res) => {
  const db = loadDB();

  const amount = Number(req.body.amount);
  const utr = String(
    req.body.utr || ""
  ).trim();

  if (!Number.isFinite(amount) || amount < 10) {
    return res.status(400).json({
      error: "Minimum deposit is ₹10"
    });
  }

  if (!utr) {
    return res.status(400).json({
      error: "UTR required"
    });
  }

  const duplicate = db.deposits.find(
    d => d.utr.toLowerCase() === utr.toLowerCase()
  );

  if (duplicate) {
    return res.status(400).json({
      error: "This UTR has already been submitted"
    });
  }

  const deposit = {
    id: db.nextDepositId++,
    userId: req.user.id,
    amount,
    utr,
    status: "PENDING",
    createdAt: new Date().toISOString(),
    reviewedAt: null,
    reviewNote: ""
  };

  db.deposits.push(deposit);

  saveDB(db);

  res.json({
    success: true,
    deposit
  });
});

/* =========================
   HISTORY
========================= */

app.get("/api/history", auth, (req, res) => {
  const db = loadDB();

  res.json({
    orders: db.orders.filter(
      o => o.userId === req.user.id
    ),
    deposits: db.deposits.filter(
      d => d.userId === req.user.id
    ),
    transactions: []
  });
});

/* =========================
   SUPPORT
========================= */

app.post("/api/support", auth, (req, res) => {
  const db = loadDB();

  const subject = String(
    req.body.subject || ""
  ).trim();

  const message = String(
    req.body.message || ""
  ).trim();

  if (!message) {
    return res.status(400).json({
      error: "Message required"
    });
  }

  const ticket = {
    id: db.nextSupportId++,
    userId: req.user.id,
    subject,
    message,
    status: "OPEN",
    createdAt: new Date().toISOString()
  };

  db.support.push(ticket);

  saveDB(db);

  res.json({
    success: true,
    ticket
  });
});

/* =========================
   ADMIN
========================= */

app.get(
  "/api/admin/dashboard",
  adminAuth,
  (req, res) => {
    const db = loadDB();

    res.json({
      users: db.users.length,
      products: db.products.length,
      orders: db.orders.length,
      pendingDeposits:
        db.deposits.filter(
          d => d.status === "PENDING"
        ).length,
      coupons: db.coupons.length,
      supportOpen:
        db.support.filter(
          s => s.status === "OPEN"
        ).length
    });
  }
);

app.get(
  "/api/admin/deposits",
  adminAuth,
  (req, res) => {
    const db = loadDB();

    res.json(
      db.deposits.map(d => ({
        ...d,
        user: (() => {
          const u = db.users.find(
            x => x.id === d.userId
          );

          return u
            ? {
                uid: u.uid,
                name: u.name,
                email: u.email
              }
            : null;
        })()
      }))
    );
  }
);

app.post(
  "/api/admin/deposits/:id",
  adminAuth,
  (req, res) => {
    const db = loadDB();

    const deposit = db.deposits.find(
      d => d.id === Number(req.params.id)
    );

    if (!deposit) {
      return res.status(404).json({
        error: "Deposit not found"
      });
    }

    if (deposit.status !== "PENDING") {
      return res.status(400).json({
        error: "Deposit already reviewed"
      });
    }

    const action = String(
      req.body.action || ""
    ).toUpperCase();

    const user = db.users.find(
      u => u.id === deposit.userId
    );

    if (!user) {
      return res.status(404).json({
        error: "User not found"
      });
    }

    if (action === "ACCEPT") {
      deposit.status = "ACCEPTED";
      user.wallet += deposit.amount;
    } else if (action === "REJECT") {
      deposit.status = "REJECTED";
      deposit.reviewNote =
        String(req.body.note || "Payment rejected");
    } else {
      return res.status(400).json({
        error: "Action must be ACCEPT or REJECT"
      });
    }

    deposit.reviewedAt =
      new Date().toISOString();

    saveDB(db);

    res.json({
      success: true,
      deposit,
      user: publicUser(user)
    });
  }
);

app.post(
  "/api/admin/products",
  adminAuth,
  (req, res) => {
    const db = loadDB();

    const name = String(
      req.body.name || ""
    ).trim();

    const price = Number(req.body.price);

    const description = String(
      req.body.description || ""
    ).trim();

    const icon = String(
      req.body.icon || "🎟️"
    );

    if (!name || !Number.isFinite(price) || price <= 0) {
      return res.status(400).json({
        error: "Valid name and price required"
      });
    }

    const product = {
      id: db.nextProductId++,
      name,
      price,
      icon,
      description
    };

    db.products.push(product);

    saveDB(db);

    res.json({
      success: true,
      product
    });
  }
);

app.delete(
  "/api/admin/products/:id",
  adminAuth,
  (req, res) => {
    const db = loadDB();

    const id = Number(req.params.id);

    const before = db.products.length;

    db.products =
      db.products.filter(
        p => p.id !== id
      );

    if (before === db.products.length) {
      return res.status(404).json({
        error: "Product not found"
      });
    }

    saveDB(db);

    res.json({
      success: true
    });
  }
);

app.post(
  "/api/admin/coupons",
  adminAuth,
  (req, res) => {
    const db = loadDB();

    const code = String(
      req.body.code || ""
    ).trim().toUpperCase();

    const discountPercent =
      Number(req.body.discountPercent);

    if (
      !code ||
      !Number.isFinite(discountPercent) ||
      discountPercent <= 0 ||
      discountPercent > 100
    ) {
      return res.status(400).json({
        error:
          "Coupon and discount 1-100 required"
      });
    }

    if (
      db.coupons.some(
        c => c.code === code
      )
    ) {
      return res.status(400).json({
        error: "Coupon already exists"
      });
    }

    const coupon = {
      id: db.nextCouponId++,
      code,
      discountPercent,
      active: true,
      expiresAt:
        req.body.expiresAt || null,
      createdAt: new Date().toISOString()
    };

    db.coupons.push(coupon);

    saveDB(db);

    res.json({
      success: true,
      coupon
    });
  }
);

app.get(
  "/api/admin/coupons",
  adminAuth,
  (req, res) => {
    const db = loadDB();
    res.json(db.coupons);
  }
);

app.post(
  "/api/admin/coupons/:id/toggle",
  adminAuth,
  (req, res) => {
    const db = loadDB();

    const coupon = db.coupons.find(
      c => c.id === Number(req.params.id)
    );

    if (!coupon) {
      return res.status(404).json({
        error: "Coupon not found"
      });
    }

    coupon.active = !coupon.active;

    saveDB(db);

    res.json({
      success: true,
      coupon
    });
  }
);

app.get(
  "/api/admin/users",
  adminAuth,
  (req, res) => {
    const db = loadDB();

    res.json(
      db.users.map(publicUser)
    );
  }
);

app.get(
  "/api/admin/support",
  adminAuth,
  (req, res) => {
    const db = loadDB();

    res.json(
      db.support.map(ticket => ({
        ...ticket,
        user: (() => {
          const u = db.users.find(
            x => x.id === ticket.userId
          );

          return u
            ? {
                uid: u.uid,
                name: u.name,
                email: u.email
              }
            : null;
        })()
      }))
    );
  }
);

app.use((req, res) => {
  if (
    req.method === "GET" &&
    !req.path.startsWith("/api/")
  ) {
    return res.sendFile(
      path.join(
        __dirname,
        "public",
        "index.html"
      )
    );
  }

  res.status(404).json({
    error: "Not found"
  });
});

ensureDB();

app.listen(PORT, () => {
  console.log(
    `Xenon Shop running on port ${PORT}`
  );
});
