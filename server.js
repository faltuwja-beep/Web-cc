const express = require("express");
const path = require("path");
const fs = require("fs");
const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");

const app = express();

const PORT = process.env.PORT || 10000;

const JWT_SECRET =
  process.env.JWT_SECRET || "xenon-secret-change-me";

const ADMIN_EMAIL =
  process.env.ADMIN_EMAIL || "admin@xenon.shop";

const ADMIN_PASSWORD =
  process.env.ADMIN_PASSWORD || "admin123";

const UPI_ID =
  process.env.UPI_ID || "yourupi@upi";

const DATA_DIR = path.join(__dirname, "data");
const DATA_FILE = path.join(DATA_DIR, "db.json");
const PUBLIC_DIR = path.join(__dirname, "public");


app.use(express.json({ limit: "2mb" }));
app.use(express.urlencoded({ extended: true }));
app.use(express.static(PUBLIC_DIR));


function defaultData() {
  return {
    users: [],
    deposits: [],
    products: [],
    purchases: []
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
    const data = JSON.parse(
      fs.readFileSync(DATA_FILE, "utf8")
    );

    return {
      users: Array.isArray(data.users) ? data.users : [],
      deposits: Array.isArray(data.deposits)
        ? data.deposits
        : [],
      products: Array.isArray(data.products)
        ? data.products
        : [],
      purchases: Array.isArray(data.purchases)
        ? data.purchases
        : []
    };
  } catch (error) {
    console.error("Database error:", error);
    return defaultData();
  }
}


function saveData(data) {
  ensureDatabase();

  fs.writeFileSync(
    DATA_FILE,
    JSON.stringify(data, null, 2)
  );
}


function id() {
  return (
    Date.now().toString(36) +
    Math.random().toString(36).slice(2, 9)
  );
}


function referralCode(name) {
  const text = String(name || "USER")
    .replace(/[^a-zA-Z0-9]/g, "")
    .toUpperCase()
    .slice(0, 5);

  return (
    text +
    Math.random()
      .toString(36)
      .slice(2, 7)
      .toUpperCase()
  );
}


function publicUser(user) {
  return {
    id: user.id,
    name: user.name,
    email: user.email,
    balance: Number(user.balance || 0),
    referralCode: user.referralCode || "",
    referralCount: Number(user.referralCount || 0),
    referralEarnings: Number(user.referralEarnings || 0),
    createdAt: user.createdAt
  };
}


function tokenFor(user) {
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

  const token = header.slice(7);

  try {
    req.user = jwt.verify(token, JWT_SECRET);
    next();
  } catch (error) {
    return res.status(401).json({
      error: "Invalid or expired token"
    });
  }
}


function adminOnly(req, res, next) {
  const data = readData();

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


ensureDatabase();


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
    upiId: UPI_ID
  });
});


/* REGISTER */

app.post("/api/register", async (req, res) => {
  try {
    const name = String(req.body.name || "").trim();
    const email = String(req.body.email || "")
      .trim()
      .toLowerCase();
    const password = String(req.body.password || "");
    const referral = String(req.body.referral || "").trim();

    if (!name) {
      return res.status(400).json({
        error: "Name is required"
      });
    }

    if (!email) {
      return res.status(400).json({
        error: "Email is required"
      });
    }

    if (password.length < 6) {
      return res.status(400).json({
        error: "Password must be at least 6 characters"
      });
    }

    const data = readData();

    if (data.users.some(x => x.email === email)) {
      return res.status(400).json({
        error: "Email already registered"
      });
    }

    let code = referralCode(name);

    while (
      data.users.some(x => x.referralCode === code)
    ) {
      code = referralCode(name);
    }

    const user = {
      id: id(),
      name,
      email,
      password: await bcrypt.hash(password, 10),
      balance: 0,
      referralCode: code,
      referralCount: 0,
      referralEarnings: 0,
      referredBy: referral,
      role: "user",
      createdAt: new Date().toISOString()
    };

    if (referral) {
      const referrer = data.users.find(
        x => x.referralCode === referral
      );

      if (referrer) {
        referrer.referralCount =
          Number(referrer.referralCount || 0) + 1;
      }
    }

    data.users.push(user);
    saveData(data);

    res.status(201).json({
      token: tokenFor(user),
      user: publicUser(user)
    });

  } catch (error) {
    console.error(error);

    res.status(500).json({
      error: "Registration failed"
    });
  }
});


/* LOGIN */

app.post("/api/login", async (req, res) => {
  try {
    const email = String(req.body.email || "")
      .trim()
      .toLowerCase();

    const password = String(req.body.password || "");

    const data = readData();

    const user = data.users.find(
      x => x.email === email
    );

    if (!user) {
      return res.status(401).json({
        error: "Invalid email or password"
      });
    }

    const valid = await bcrypt.compare(
      password,
      user.password
    );

    if (!valid) {
      return res.status(401).json({
        error: "Invalid email or password"
      });
    }

    res.json({
      token: tokenFor(user),
      user: publicUser(user)
    });

  } catch (error) {
    console.error(error);

    res.status(500).json({
      error: "Login failed"
    });
  }
});


/* CURRENT USER */

app.get("/api/me", auth, (req, res) => {
  const data = readData();

  const user = data.users.find(
    x => x.id === req.user.id
  );

  if (!user) {
    return res.status(404).json({
      error: "User not found"
    });
  }

  res.json(publicUser(user));
});


/* PRODUCTS */

app.get("/api/products", (req, res) => {
  const data = readData();

  res.json(
    data.products.map(product => ({
      id: product.id,
      name: product.name,
      price: Number(product.price || 0),
      description: product.description || "",
      image: product.image || "",
      icon: product.icon || "📦"
    }))
  );
});


/* BUY */

app.post("/api/buy", auth, (req, res) => {
  const productId = String(
    req.body.productId || ""
  );

  const data = readData();

  const user = data.users.find(
    x => x.id === req.user.id
  );

  if (!user) {
    return res.status(404).json({
      error: "User not found"
    });
  }

  const product = data.products.find(
    x => String(x.id) === productId
  );

  if (!product) {
    return res.status(404).json({
      error: "Product not found"
    });
  }

  const price = Number(product.price);

  if (!Number.isFinite(price) || price <= 0) {
    return res.status(400).json({
      error: "Invalid product price"
    });
  }

  if (Number(user.balance || 0) < price) {
    return res.status(400).json({
      error: "Insufficient wallet balance"
    });
  }

  user.balance =
    Number(user.balance || 0) - price;

  const purchase = {
    id: id(),
    userId: user.id,
    name: user.name,
    product: product.name,
    productId: product.id,
    amount: price,
    createdAt: new Date().toISOString()
  };

  data.purchases.push(purchase);

  saveData(data);

  res.json({
    success: true,
    message: "Purchase successful",
    purchase,
    balance: user.balance
  });
});


/* PUBLIC ACTIVITY */

app.get("/api/activity", (req, res) => {
  const data = readData();

  res.json(
    data.purchases
      .slice(-30)
      .reverse()
  );
});


/* ADD MONEY */

app.post("/api/deposits", auth, (req, res) => {
  const amount = Number(req.body.amount);
  const utr = String(req.body.utr || "").trim();

  if (!Number.isFinite(amount) || amount <= 0) {
    return res.status(400).json({
      error: "Invalid amount"
    });
  }

  if (!utr) {
    return res.status(400).json({
      error: "UTR is required"
    });
  }

  const data = readData();

  const user = data.users.find(
    x => x.id === req.user.id
  );

  if (!user) {
    return res.status(404).json({
      error: "User not found"
    });
  }

  const deposit = {
    id: id(),
    userId: user.id,
    userName: user.name,
    userEmail: user.email,
    amount,
    utr,
    status: "PENDING",
    createdAt: new Date().toISOString()
  };

  data.deposits.push(deposit);

  saveData(data);

  res.status(201).json({
    success: true,
    deposit
  });
});


/* USER DEPOSITS */

app.get("/api/deposits", auth, (req, res) => {
  const data = readData();

  res.json(
    data.deposits.filter(
      x => x.userId === req.user.id
    )
  );
});


/* ADMIN LOGIN */

app.post("/api/admin/login", async (req, res) => {
  const email = String(req.body.email || "")
    .trim()
    .toLowerCase();

  const password = String(req.body.password || "");

  if (
    email !== ADMIN_EMAIL.toLowerCase() ||
    password !== ADMIN_PASSWORD
  ) {
    return res.status(401).json({
      error: "Invalid admin login"
    });
  }

  const data = readData();

  let user = data.users.find(
    x => x.email === ADMIN_EMAIL.toLowerCase()
  );

  if (!user) {
    user = {
      id: "admin",
      name: "Xenon Admin",
      email: freefireidaskgamer@gmail.com.toLowerCase(),
      password: await bcrypt.hash(
        sonusha333,
        10
      ),
      balance: 0,
      referralCode: "ADMIN",
      referralCount: 0,
      referralEarnings: 0,
      role: "admin",
      createdAt: new Date().toISOString()
    };

    data.users.push(user);
  } else {
    user.role = "admin";
  }

  saveData(data);

  res.json({
    token: tokenFor(user),
    user: publicUser(user)
  });
});


/* ADMIN DEPOSITS */

app.get(
  "/api/admin/deposits",
  auth,
  adminOnly,
  (req, res) => {
    const data = readData();

    res.json(
      data.deposits.slice().reverse()
    );
  }
);


/* APPROVE / REJECT */

app.post(
  "/api/admin/deposits/:id",
  auth,
  adminOnly,
  (req, res) => {

    const depositId = String(
      req.params.id
    );

    const status = String(
      req.body.status || ""
    ).toUpperCase();

    if (
      status !== "APPROVED" &&
      status !== "REJECTED"
    ) {
      return res.status(400).json({
        error:
          "Status must be APPROVED or REJECTED"
      });
    }

    const data = readData();

    const deposit = data.deposits.find(
      x => String(x.id) === depositId
    );

    if (!deposit) {
      return res.status(404).json({
        error: "Deposit not found"
      });
    }

    if (deposit.status !== "PENDING") {
      return res.status(400).json({
        error: "Deposit already processed"
      });
    }

    deposit.status = status;
    deposit.updatedAt =
      new Date().toISOString();

    if (status === "APPROVED") {
      const user = data.users.find(
        x => x.id === deposit.userId
      );

      if (!user) {
        return res.status(404).json({
          error: "User not found"
        });
      }

      user.balance =
        Number(user.balance || 0) +
        Number(deposit.amount);
    }

    saveData(data);

    res.json({
      success: true,
      deposit
    });
  }
);


/* ADD PRODUCT */

app.post(
  "/api/admin/products",
  auth,
  adminOnly,
  (req, res) => {

    const name = String(
      req.body.name || ""
    ).trim();

    const price = Number(
      req.body.price
    );

    const description = String(
      req.body.description || ""
    ).trim();

    const image = String(
      req.body.image || ""
    ).trim();

    const icon = String(
      req.body.icon || "📦"
    ).trim();

    if (!name) {
      return res.status(400).json({
        error: "Product name required"
      });
    }

    if (!Number.isFinite(price) || price <= 0) {
      return res.status(400).json({
        error: "Valid price required"
      });
    }

    const data = readData();

    const product = {
      id: id(),
      name,
      price,
      description,
      image,
      icon,
      createdAt: new Date().toISOString()
    };

    data.products.push(product);

    saveData(data);

    res.status(201).json({
      success: true,
      product
    });
  }
);


/* UPDATE PRODUCT */

app.put(
  "/api/admin/products/:id",
  auth,
  adminOnly,
  (req, res) => {

    const data = readData();

    const product = data.products.find(
      x =>
        String(x.id) ===
        String(req.params.id)
    );

    if (!product) {
      return res.status(404).json({
        error: "Product not found"
      });
    }

    if (req.body.name !== undefined) {
      product.name =
        String(req.body.name).trim();
    }

    if (req.body.price !== undefined) {
      const price =
        Number(req.body.price);

      if (!Number.isFinite(price) || price <= 0) {
        return res.status(400).json({
          error: "Invalid price"
        });
      }

      product.price = price;
    }

    if (req.body.description !== undefined) {
      product.description =
        String(req.body.description).trim();
    }

    if (req.body.image !== undefined) {
      product.image =
        String(req.body.image).trim();
    }

    if (req.body.icon !== undefined) {
      product.icon =
        String(req.body.icon).trim();
    }

    product.updatedAt =
      new Date().toISOString();

    saveData(data);

    res.json({
      success: true,
      product
    });
  }
);


/* DELETE PRODUCT */

app.delete(
  "/api/admin/products/:id",
  auth,
  adminOnly,
  (req, res) => {

    const data = readData();

    const index =
      data.products.findIndex(
        x =>
          String(x.id) ===
          String(req.params.id)
      );

    if (index === -1) {
      return res.status(404).json({
        error: "Product not found"
      });
    }

    const product =
      data.products.splice(index, 1)[0];

    saveData(data);

    res.json({
      success: true,
      product
    });
  }
);


/* ADMIN STATS */

app.get(
  "/api/admin/stats",
  auth,
  adminOnly,
  (req, res) => {

    const data = readData();

    const approved =
      data.deposits
        .filter(
          x => x.status === "APPROVED"
        )
        .reduce(
          (total, x) =>
            total + Number(x.amount || 0),
          0
        );

    res.json({
      users: data.users.filter(
        x => x.role !== "admin"
      ).length,

      products: data.products.length,

      pendingDeposits:
        data.deposits.filter(
          x => x.status === "PENDING"
        ).length,

      approvedDeposits:
        data.deposits.filter(
          x => x.status === "APPROVED"
        ).length,

      approvedAmount: approved,

      purchases:
        data.purchases.length
    });
  }
);


/* FRONTEND FALLBACK */

/*
   Express 5 ke saath "*" route
   use nahi kar rahe hain.
*/

app.use((req, res, next) => {

  if (req.method !== "GET") {
    return next();
  }

  if (req.path.startsWith("/api/")) {
    return res.status(404).json({
      error: "API endpoint not found"
    });
  }

  const indexFile =
    path.join(PUBLIC_DIR, "index.html");

  if (fs.existsSync(indexFile)) {
    return res.sendFile(indexFile);
  }

  res.status(404).send(
    "Xenon Shop: public/index.html not found"
  );
});


/* START */

app.listen(PORT, () => {
  console.log("");
  console.log("⚡ XENON SHOP RUNNING");
  console.log("🌐 PORT:", PORT);
  console.log("");
});
