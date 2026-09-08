const express = require("express");
const path = require("path");
const fs = require("fs");
const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");

const app = express();

const PORT = process.env.PORT || 3000;
const JWT_SECRET = process.env.JWT_SECRET || "xenon-change-this-secret";

const ADMIN_EMAIL = process.env.ADMIN_EMAIL || "admin@xenon.shop";
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || "admin123";

const UPI_ID = process.env.UPI_ID || "yourupi@upi";

const DATA_DIR = path.join(__dirname, "data");
const DATA_FILE = path.join(DATA_DIR, "db.json");

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// ---------------- DATABASE ----------------

function defaultData() {
  return {
    users: [],
    products: [
      {
        id: 1,
        name: "Premium Account",
        price: 99,
        description: "Premium digital account",
        icon: "⭐"
      },
      {
        id: 2,
        name: "VIP Package",
        price: 199,
        description: "VIP digital package",
        icon: "💎"
      },
      {
        id: 3,
        name: "Pro Package",
        price: 299,
        description: "Professional package",
        icon: "🚀"
      }
    ],
    deposits: [],
    purchases: [],
    referrals: []
  };
}

function ensureDatabase() {
  if (!fs.existsSync(DATA_DIR)) {
    fs.mkdirSync(DATA_DIR, { recursive: true });
  }

  if (!fs.existsSync(DATA_FILE)) {
    fs.writeFileSync(
      DATA_FILE,
      JSON.stringify(defaultData(), null, 2)
    );
  }
}

function readData() {
  ensureDatabase();

  try {
    return JSON.parse(fs.readFileSync(DATA_FILE, "utf8"));
  } catch {
    const data = defaultData();
    fs.writeFileSync(DATA_FILE, JSON.stringify(data, null, 2));
    return data;
  }
}

function writeData(data) {
  ensureDatabase();
  fs.writeFileSync(
    DATA_FILE,
    JSON.stringify(data, null, 2)
  );
}

ensureDatabase();

// ---------------- HELPERS ----------------

function publicUser(user) {
  return {
    id: user.id,
    name: user.name,
    email: user.email,
    balance: user.balance || 0,
    referralCode: user.referralCode,
    referralBonus: user.referralBonus || 0,
    createdAt: user.createdAt
  };
}

function makeToken(user) {
  return jwt.sign(
    {
      id: user.id,
      email: user.email
    },
    JWT_SECRET,
    {
      expiresIn: "30d"
    }
  );
}

function generateReferralCode() {
  return (
    "XENON" +
    Math.random()
      .toString(36)
      .substring(2, 8)
      .toUpperCase()
  );
}

function auth(req, res, next) {
  const header = req.headers.authorization || "";

  if (!header.startsWith("Bearer ")) {
    return res.status(401).json({
      error: "Please login"
    });
  }

  const token = header.substring(7);

  try {
    const decoded = jwt.verify(token, JWT_SECRET);
    req.user = decoded;
    next();
  } catch {
    return res.status(401).json({
      error: "Invalid or expired login"
    });
  }
}

function admin(req, res, next) {
  if (req.user.email !== ADMIN_EMAIL) {
    return res.status(403).json({
      error: "Admin access required"
    });
  }

  next();
}

// ---------------- REGISTER ----------------

app.post("/api/register", async (req, res) => {
  try {
    const {
      name,
      email,
      password,
      referralCode
    } = req.body;

    if (!name || !email || !password) {
      return res.status(400).json({
        error: "Name, email and password required"
      });
    }

    if (password.length < 6) {
      return res.status(400).json({
        error: "Password must be at least 6 characters"
      });
    }

    const data = readData();

    const cleanEmail = String(email)
      .trim()
      .toLowerCase();

    const exists = data.users.find(
      u => u.email === cleanEmail
    );

    if (exists) {
      return res.status(400).json({
        error: "Email already registered"
      });
    }

    const passwordHash = await bcrypt.hash(
      password,
      10
    );

    const user = {
      id: Date.now().toString(),
      name: String(name).trim(),
      email: cleanEmail,
      passwordHash,
      balance: 0,
      referralCode: generateReferralCode(),
      referralBonus: 0,
      referredBy: null,
      createdAt: new Date().toISOString()
    };

    // Referral link
    if (referralCode) {
      const referrer = data.users.find(
        u =>
          u.referralCode.toUpperCase() ===
          String(referralCode).trim().toUpperCase()
      );

      if (referrer && referrer.email !== cleanEmail) {
        user.referredBy = referrer.id;
      }
    }

    data.users.push(user);
    writeData(data);

    const token = makeToken(user);

    res.json({
      token,
      user: publicUser(user)
    });
  } catch (error) {
    console.error(error);

    res.status(500).json({
      error: "Registration failed"
    });
  }
});

// ---------------- LOGIN ----------------

app.post("/api/login", async (req, res) => {
  try {
    const {
      email,
      password
    } = req.body;

    const data = readData();

    const cleanEmail = String(email || "")
      .trim()
      .toLowerCase();

    const user = data.users.find(
      u => u.email === cleanEmail
    );

    if (!user) {
      return res.status(401).json({
        error: "Wrong email or password"
      });
    }

    const valid = await bcrypt.compare(
      password || "",
      user.passwordHash
    );

    if (!valid) {
      return res.status(401).json({
        error: "Wrong email or password"
      });
    }

    const token = makeToken(user);

    res.json({
      token,
      user: publicUser(user)
    });
  } catch {
    res.status(500).json({
      error: "Login failed"
    });
  }
});

// ---------------- CURRENT USER ----------------

app.get("/api/me", auth, (req, res) => {
  const data = readData();

  const user = data.users.find(
    u => u.id === req.user.id
  );

  if (!user) {
    return res.status(404).json({
      error: "User not found"
    });
  }

  res.json(publicUser(user));
});

// ---------------- PRODUCTS ----------------

app.get("/api/products", (req, res) => {
  const data = readData();

  res.json(
    data.products.map(p => ({
      id: p.id,
      name: p.name,
      price: p.price,
      description: p.description,
      icon: p.icon
    }))
  );
});

// ---------------- UPI INFO ----------------

app.get("/api/payment-info", (req, res) => {
  res.json({
    upiId: UPI_ID
  });
});

// ---------------- ADD MONEY ----------------

app.post("/api/deposits", auth, (req, res) => {
  const {
    amount,
    utr
  } = req.body;

  const numericAmount = Number(amount);

  if (
    !numericAmount ||
    numericAmount < 1
  ) {
    return res.status(400).json({
      error: "Invalid amount"
    });
  }

  if (!utr || String(utr).trim().length < 4) {
    return res.status(400).json({
      error: "Enter valid UTR"
    });
  }

  const data = readData();

  const deposit = {
    id: Date.now().toString(),
    userId: req.user.id,
    amount: numericAmount,
    utr: String(utr).trim(),
    status: "PENDING",
    createdAt: new Date().toISOString()
  };

  data.deposits.push(deposit);

  writeData(data);

  res.json({
    message: "Payment submitted",
    deposit
  });
});

// ---------------- USER DEPOSITS ----------------

app.get("/api/deposits", auth, (req, res) => {
  const data = readData();

  const deposits = data.deposits
    .filter(x => x.userId === req.user.id)
    .sort(
      (a, b) =>
        new Date(b.createdAt) -
        new Date(a.createdAt)
    );

  res.json(deposits);
});

// ---------------- BUY PRODUCT ----------------

app.post("/api/buy", auth, (req, res) => {
  const {
    productId
  } = req.body;

  const data = readData();

  const user = data.users.find(
    u => u.id === req.user.id
  );

  const product = data.products.find(
    p => Number(p.id) === Number(productId)
  );

  if (!user) {
    return res.status(404).json({
      error: "User not found"
    });
  }

  if (!product) {
    return res.status(404).json({
      error: "Product not found"
    });
  }

  if ((user.balance || 0) < product.price) {
    return res.status(400).json({
      error: "Insufficient balance"
    });
  }

  user.balance -= product.price;

  const purchase = {
    id: Date.now().toString(),
    userId: user.id,
    productId: product.id,
    productName: product.name,
    amount: product.price,
    status: "COMPLETED",
    createdAt: new Date().toISOString()
  };

  data.purchases.push(purchase);

  // Referral bonus ₹50
  if (user.referredBy) {
    const alreadyRewarded = data.referrals.find(
      r =>
        r.referredUserId === user.id &&
        r.status === "PAID"
    );

    if (!alreadyRewarded) {
      const referrer = data.users.find(
        u => u.id === user.referredBy
      );

      if (referrer) {
        referrer.balance =
          (referrer.balance || 0) + 50;

        referrer.referralBonus =
          (referrer.referralBonus || 0) + 50;

        data.referrals.push({
          id: Date.now().toString() + "-ref",
          referrerId: referrer.id,
          referredUserId: user.id,
          amount: 50,
          status: "PAID",
          createdAt: new Date().toISOString()
        });
      }
    }
  }

  writeData(data);

  res.json({
    message: "Purchase successful",
    purchase,
    user: publicUser(user)
  });
});

// ---------------- PURCHASE HISTORY ----------------

app.get("/api/purchases", auth, (req, res) => {
  const data = readData();

  res.json(
    data.purchases
      .filter(
        p => p.userId === req.user.id
      )
      .sort(
        (a, b) =>
          new Date(b.createdAt) -
          new Date(a.createdAt)
      )
  );
});

// ---------------- REFERRALS ----------------

app.get("/api/referrals", auth, (req, res) => {
  const data = readData();

  const referrals = data.referrals.filter(
    r => r.referrerId === req.user.id
  );

  res.json({
    referralCode:
      data.users.find(
        u => u.id === req.user.id
      )?.referralCode || "",
    bonus: referrals.reduce(
      (sum, r) => sum + Number(r.amount || 0),
      0
    ),
    referrals
  });
});

// ---------------- ADMIN LOGIN ----------------

app.post("/api/admin/login", async (req, res) => {
  const {
    email,
    password
  } = req.body;

  if (
    email !== ADMIN_EMAIL ||
    password !== ADMIN_PASSWORD
  ) {
    return res.status(401).json({
      error: "Invalid admin login"
    });
  }

  const token = jwt.sign(
    {
      id: "admin",
      email: ADMIN_EMAIL
    },
    JWT_SECRET,
    {
      expiresIn: "30d"
    }
  );

  res.json({
    token
  });
});

// ---------------- ADMIN DEPOSITS ----------------

app.get(
  "/api/admin/deposits",
  auth,
  admin,
  (req, res) => {
    const data = readData();

    const deposits = data.deposits
      .map(d => {
        const user = data.users.find(
          u => u.id === d.userId
        );

        return {
          ...d,
          userName: user?.name || "Unknown",
          userEmail: user?.email || "Unknown"
        };
      })
      .sort(
        (a, b) =>
          new Date(b.createdAt) -
          new Date(a.createdAt)
      );

    res.json(deposits);
  }
);

// ---------------- ADMIN APPROVE / REJECT ----------------

app.post(
  "/api/admin/deposits/:id",
  auth,
  admin,
  (req, res) => {
    const {
      status
    } = req.body;

    if (
      !["APPROVED", "REJECTED"].includes(status)
    ) {
      return res.status(400).json({
        error: "Invalid status"
      });
    }

    const data = readData();

    const deposit = data.deposits.find(
      d => d.id === req.params.id
    );

    if (!deposit) {
      return res.status(404).json({
        error: "Deposit not found"
      });
    }

    if (deposit.status !== "PENDING") {
      return res.status(400).json({
        error: "Already processed"
      });
    }

    deposit.status = status;
    deposit.updatedAt =
      new Date().toISOString();

    if (status === "APPROVED") {
      const user = data.users.find(
        u => u.id === deposit.userId
      );

      if (user) {
        user.balance =
          (user.balance || 0) +
          Number(deposit.amount);
      }
    }

    writeData(data);

    res.json({
      message:
        status === "APPROVED"
          ? "Payment approved"
          : "Payment rejected",
      deposit
    });
  }
);

// ---------------- ADMIN PRODUCTS ----------------

app.post(
  "/api/admin/products",
  auth,
  admin,
  (req, res) => {
    const {
      name,
      price,
      description,
      icon
    } = req.body;

    if (!name || !price) {
      return res.status(400).json({
        error: "Name and price required"
      });
    }

    const data = readData();

    const product = {
      id: Date.now(),
      name,
      price: Number(price),
      description:
        description || "",
      icon: icon || "🛍️"
    };

    data.products.push(product);

    writeData(data);

    res.json(product);
  }
);

// ---------------- HEALTH ----------------

app.get("/api/health", (req, res) => {
  res.json({
    ok: true,
    service: "Xenon Shop"
  });
});

// ---------------- FRONTEND ----------------

// IMPORTANT:
// Express 5 me app.get("*") use nahi karna.
// Ye middleware unknown frontend routes ko index.html deta hai.

app.use(express.static(
  path.join(__dirname, "public")
));

app.use((req, res, next) => {
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

  next();
});

// ---------------- SERVER ----------------

app.listen(PORT, () => {
  console.log("");
  console.log("⚡ XENON SHOP RUNNING");
  console.log("🌐 PORT:", PORT);
  console.log("");
});
