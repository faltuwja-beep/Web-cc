const express = require("express");
const path = require("path");
const fs = require("fs");
const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");

const app = express();
const PORT = process.env.PORT || 10000;

const ADMIN_EMAIL = "freefireidaskgamer@gmail.com";
const ADMIN_PASSWORD = "sonu333";
const JWT_SECRET = process.env.JWT_SECRET || "xenon-secret-123";

const DATA_DIR = path.join(__dirname, "data");
const DATA_FILE = path.join(DATA_DIR, "db.json");
const PUBLIC_DIR = path.join(__dirname, "public");

app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(PUBLIC_DIR));

function database() {
  if (!fs.existsSync(DATA_DIR)) {
    fs.mkdirSync(DATA_DIR, { recursive: true });
  }

  if (!fs.existsSync(DATA_FILE)) {
    fs.writeFileSync(
      DATA_FILE,
      JSON.stringify({
        users: [],
        products: [],
        deposits: [],
        purchases: []
      }, null, 2)
    );
  }

  try {
    return JSON.parse(
      fs.readFileSync(DATA_FILE, "utf8")
    );
  } catch (e) {
    return {
      users: [],
      products: [],
      deposits: [],
      purchases: []
    };
  }
}

function save(data) {
  fs.writeFileSync(
    DATA_FILE,
    JSON.stringify(data, null, 2)
  );
}

function makeId() {
  return Date.now().toString(36) +
    Math.random().toString(36).slice(2);
}

function token(user) {
  return jwt.sign(
    { id: user.id },
    JWT_SECRET,
    { expiresIn: "30d" }
  );
}

function auth(req, res, next) {
  const header = req.headers.authorization || "";

  if (!header.startsWith("Bearer ")) {
    return res.status(401).json({
      error: "Login required"
    });
  }

  try {
    req.user = jwt.verify(
      header.substring(7),
      JWT_SECRET
    );

    next();
  } catch (e) {
    return res.status(401).json({
      error: "Invalid token"
    });
  }
}

function admin(req, res, next) {
  const data = database();

  const user = data.users.find(
    x => x.id === req.user.id
  );

  if (!user || user.role !== "admin") {
    return res.status(403).json({
      error: "Admin access required"
    });
  }

  next();
}

/* HEALTH */

app.get("/api/health", (req, res) => {
  res.json({
    success: true,
    message: "Xenon Shop is running"
  });
});

/* CONFIG */

app.get("/api/config", (req, res) => {
  res.json({
    upiId: process.env.UPI_ID || "yourupi@upi"
  });
});

/* REGISTER */

app.post("/api/register", async (req, res) => {
  try {
    const name = String(req.body.name || "").trim();
    const email = String(req.body.email || "").trim().toLowerCase();
    const password = String(req.body.password || "");

    if (!name || !email || password.length < 6) {
      return res.status(400).json({
        error: "Name, email and 6 character password required"
      });
    }

    const data = database();

    if (data.users.some(x => x.email === email)) {
      return res.status(400).json({
        error: "Email already registered"
      });
    }

    const user = {
      id: makeId(),
      name: name,
      email: email,
      password: await bcrypt.hash(password, 10),
      balance: 0,
      role: "user",
      referralCode: name.substring(0, 4).toUpperCase() + Math.floor(Math.random() * 9999),
      createdAt: new Date().toISOString()
    };

    data.users.push(user);
    save(data);

    res.json({
      success: true,
      token: token(user),
      user: {
        id: user.id,
        name: user.name,
        email: user.email,
        balance: user.balance
      }
    });
  } catch (e) {
    console.error(e);
    res.status(500).json({
      error: "Registration failed"
    });
  }
});

/* USER LOGIN */

app.post("/api/login", async (req, res) => {
  try {
    const email = String(req.body.email || "").trim().toLowerCase();
    const password = String(req.body.password || "");

    const data = database();

    const user = data.users.find(
      x => x.email === email
    );

    if (!user) {
      return res.status(401).json({
        error: "Invalid email or password"
      });
    }

    const ok = await bcrypt.compare(
      password,
      user.password
    );

    if (!ok) {
      return res.status(401).json({
        error: "Invalid email or password"
      });
    }

    res.json({
      success: true,
      token: token(user),
      user: {
        id: user.id,
        name: user.name,
        email: user.email,
        balance: user.balance,
        role: user.role
      }
    });
  } catch (e) {
    res.status(500).json({
      error: "Login failed"
    });
  }
});

/* ADMIN LOGIN */

app.post("/api/admin/login", async (req, res) => {
  try {
    const email = String(req.body.email || "").trim().toLowerCase();
    const password = String(req.body.password || "");

    if (
      email !== ADMIN_EMAIL.toLowerCase() ||
      password !== ADMIN_PASSWORD
    ) {
      return res.status(401).json({
        error: "Invalid admin login"
      });
    }

    const data = database();

    let user = data.users.find(
      x => x.email === ADMIN_EMAIL.toLowerCase()
    );

    if (!user) {
      user = {
        id: "admin",
        name: "Xenon Admin",
        email: ADMIN_EMAIL.toLowerCase(),
        password: await bcrypt.hash(ADMIN_PASSWORD, 10),
        balance: 0,
        role: "admin",
        referralCode: "ADMIN",
        createdAt: new Date().toISOString()
      };

      data.users.push(user);
    } else {
      user.role = "admin";
      user.password = await bcrypt.hash(ADMIN_PASSWORD, 10);
    }

    save(data);

    res.json({
      success: true,
      token: token(user),
      user: {
        id: user.id,
        name: user.name,
        email: user.email,
        role: "admin"
      }
    });
  } catch (e) {
    console.error(e);
    res.status(500).json({
      error: "Admin login failed"
    });
  }
});

/* CURRENT USER */

app.get("/api/me", auth, (req, res) => {
  const data = database();

  const user = data.users.find(
    x => x.id === req.user.id
  );

  if (!user) {
    return res.status(404).json({
      error: "User not found"
    });
  }

  res.json({
    id: user.id,
    name: user.name,
    email: user.email,
    balance: Number(user.balance || 0),
    role: user.role
  });
});

/* PRODUCTS */

app.get("/api/products", (req, res) => {
  const data = database();

  res.json(data.products || []);
});

/* ACTIVITY */

app.get("/api/activity", (req, res) => {
  const data = database();

  res.json(
    (data.purchases || []).slice(-30).reverse()
  );
});

/* BUY */

app.post("/api/buy", auth, (req, res) => {
  const data = database();

  const user = data.users.find(
    x => x.id === req.user.id
  );

  const product = data.products.find(
    x => String(x.id) === String(req.body.productId)
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

  const price = Number(product.price);

  if (user.balance < price) {
    return res.status(400).json({
      error: "Insufficient balance"
    });
  }

  user.balance -= price;

  const purchase = {
    id: makeId(),
    userId: user.id,
    name: user.name,
    product: product.name,
    amount: price,
    createdAt: new Date().toISOString()
  };

  data.purchases.push(purchase);
  save(data);

  res.json({
    success: true,
    balance: user.balance,
    purchase: purchase
  });
});

/* ADD MONEY REQUEST */

app.post("/api/deposits", auth, (req, res) => {
  const amount = Number(req.body.amount);
  const utr = String(req.body.utr || "").trim();

  if (!amount || amount <= 0 || !utr) {
    return res.status(400).json({
      error: "Amount and UTR required"
    });
  }

  const data = database();

  const deposit = {
    id: makeId(),
    userId: req.user.id,
    amount: amount,
    utr: utr,
    status: "PENDING",
    createdAt: new Date().toISOString()
  };

  data.deposits.push(deposit);
  save(data);

  res.json({
    success: true,
    deposit: deposit
  });
});

/* USER DEPOSITS */

app.get("/api/deposits", auth, (req, res) => {
  const data = database();

  res.json(
    data.deposits.filter(
      x => x.userId === req.user.id
    )
  );
});

/* ADMIN PRODUCTS */

app.post(
  "/api/admin/products",
  auth,
  admin,
  (req, res) => {
    const name = String(req.body.name || "").trim();
    const price = Number(req.body.price);
    const description = String(req.body.description || "").trim();
    const image = String(req.body.image || "").trim();

    if (!name || !price || price <= 0) {
      return res.status(400).json({
        error: "Name and valid price required"
      });
    }

    const data = database();

    const product = {
      id: makeId(),
      name: name,
      price: price,
      description: description,
      image: image,
      icon: "📦",
      createdAt: new Date().toISOString()
    };

    data.products.push(product);
    save(data);

    res.json({
      success: true,
      product: product
    });
  }
);

/* ADMIN PRODUCT DELETE */

app.delete(
  "/api/admin/products/:id",
  auth,
  admin,
  (req, res) => {
    const data = database();

    const index = data.products.findIndex(
      x => String(x.id) === String(req.params.id)
    );

    if (index === -1) {
      return res.status(404).json({
        error: "Product not found"
      });
    }

    data.products.splice(index, 1);
    save(data);

    res.json({
      success: true
    });
  }
);

/* ADMIN DEPOSITS */

app.get(
  "/api/admin/deposits",
  auth,
  admin,
  (req, res) => {
    const data = database();

    res.json(
      data.deposits.slice().reverse()
    );
  }
);

/* APPROVE / REJECT */

app.post(
  "/api/admin/deposits/:id",
  auth,
  admin,
  (req, res) => {
    const status =
      String(req.body.status || "").toUpperCase();

    if (
      status !== "APPROVED" &&
      status !== "REJECTED"
    ) {
      return res.status(400).json({
        error: "Invalid status"
      });
    }

    const data = database();

    const deposit = data.deposits.find(
      x => String(x.id) === String(req.params.id)
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

    if (status === "APPROVED") {
      const user = data.users.find(
        x => x.id === deposit.userId
      );

      if (user) {
        user.balance =
          Number(user.balance || 0) +
          Number(deposit.amount || 0);
      }
    }

    save(data);

    res.json({
      success: true,
      deposit: deposit
    });
  }
);

/* ADMIN STATS */

app.get(
  "/api/admin/stats",
  auth,
  admin,
  (req, res) => {
    const data = database();

    const approved =
      data.deposits
        .filter(x => x.status === "APPROVED")
        .reduce(
          (sum, x) => sum + Number(x.amount || 0),
          0
        );

    res.json({
      users: data.users.filter(
        x => x.role !== "admin"
      ).length,
      products: data.products.length,
      deposits: data.deposits.length,
      purchases: data.purchases.length,
      approvedAmount: approved
    });
  }
);

/* FRONTEND */

app.use((req, res, next) => {
  if (req.method !== "GET") {
    return next();
  }

  if (req.path.startsWith("/api/")) {
    return res.status(404).json({
      error: "API endpoint not found"
    });
  }

  const file = path.join(
    PUBLIC_DIR,
    "index.html"
  );

  if (fs.existsSync(file)) {
    return res.sendFile(file);
  }

  res.status(404).send(
    "Xenon Shop: index.html not found"
  );
});

/* START */

app.listen(PORT, () => {
  console.log(
    "XENON SHOP RUNNING ON PORT " + PORT
  );
});
