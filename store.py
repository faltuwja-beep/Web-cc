<!DOCTYPE html>
<html lang="hi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Colorful Login Page</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    body {
      background: linear-gradient(135deg, #6366f1, #a855f7, #ec4899);
      height: 100vh;
      display: flex;
      justify-content: center;
      align-items: center;
      padding: 16px;
    }
    .login-card {
      background: rgba(255, 255, 255, 0.1);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border: 1px solid rgba(255, 255, 255, 0.3);
      padding: 30px;
      border-radius: 20px;
      width: 100%;
      max-width: 380px;
      box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
      color: #fff;
      text-align: center;
    }
    .login-card h2 {
      font-size: 2rem;
      margin-bottom: 8px;
      font-weight: 800;
      text-shadow: 0 2px 10px rgba(0,0,0,0.2);
    }
    .login-card p {
      font-size: 0.9rem;
      color: rgba(255, 255, 255, 0.8);
      margin-bottom: 24px;
    }
    .inp-group {
      margin-bottom: 16px;
      text-align: left;
    }
    .inp-group label {
      display: block;
      font-size: 0.85rem;
      margin-bottom: 6px;
      font-weight: 600;
    }
    .inp-group input {
      width: 100%;
      padding: 12px 16px;
      background: rgba(0, 0, 0, 0.2);
      border: 1px solid rgba(255, 255, 255, 0.3);
      border-radius: 10px;
      color: #fff;
      font-size: 1rem;
      outline: none;
      transition: 0.3s;
    }
    .inp-group input:focus {
      border-color: #fff;
      box-shadow: 0 0 12px rgba(255, 255, 255, 0.5);
      background: rgba(0, 0, 0, 0.3);
    }
    .btn {
      width: 100%;
      padding: 14px;
      background: linear-gradient(135deg, #3b82f6, #1d4ed8);
      color: #white;
      border: none;
      border-radius: 10px;
      font-size: 1.05rem;
      font-weight: 700;
      cursor: pointer;
      box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
      transition: 0.3s;
      margin-top: 10px;
    }
    .btn:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(59, 130, 246, 0.6);
    }
  </style>
</head>
<body>

  <div class="login-card">
    <h2>Welcome Back</h2>
    <p>Apna account access karein</p>
    
    <form>
      <div class="inp-group">
        <label>Username / Email</label>
        <input type="text" placeholder="Enter username" required>
      </div>
      
      <div class="inp-group">
        <label>Password</label>
        <input type="password" placeholder="Enter password" required>
      </div>
      
      <button type="submit" class="btn">Login Now</button>
    </form>
  </div>

</body>
</html>
