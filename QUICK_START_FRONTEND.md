# 🚀 Quick Start - Market Matrix Frontend

## Get Your App Running in 3 Steps

### Step 1: Start the Backend API
Open a terminal and run:
```bash
cd c:\Users\Dotmartcodes\Documents\crypto\Crypto-fastapi
uvicorn app.main:app --reload
```

✅ Backend running at: **http://localhost:8000**

---

### Step 2: Start the Frontend
Open a **NEW** terminal and run:
```bash
cd c:\Users\Dotmartcodes\Documents\crypto\Crypto-fastapi\frontend
npm run dev
```

✅ Frontend running at: **http://localhost:3000**

---

### Step 3: Open Your Browser
Visit: **http://localhost:3000**

---

## 🎯 What You'll See

### **Landing Page** (/)
- Hero section with "Escape the Matrix"
- Problem statements
- Feature showcase
- Click "Launch App" to go to dashboard

### **Dashboard** (/dashboard)
- Real-time market data
- Top cryptocurrencies
- AI predictions
- Market metrics

### **Token Health** (/token-health)
- Search for any token (try "BTC" or "ETH")
- Get health score (0-100)
- See scam warnings
- Get investment recommendations

### **Predictions** (/predictions)
- Select a token
- See BUY/SELL/HOLD signals
- View confidence scores
- Check multiple timeframes

### **Portfolio** (/portfolio)
- Upload CSV with your holdings
- Track profit/loss
- See asset allocation
- View performance metrics

### **Analytics** (/analytics)
- Top gainers/losers
- Volatility analysis
- Market trends
- Market insights

---

## 📝 Test Data

### **CSV Format for Portfolio**
Create a file called `portfolio.csv`:
```csv
symbol,amount,avg_buy_price
BTC,0.5,45000
ETH,2.5,3000
SOL,100,50
```

Then upload it on the Portfolio page.

---

## 🔧 Troubleshooting

### **"Cannot connect to API"**
- Make sure backend is running on port 8000
- Check `.env.local` has `NEXT_PUBLIC_API_URL=http://localhost:8000`

### **"Port 3000 already in use"**
```bash
# Kill the process using port 3000
npx kill-port 3000
# Then run npm run dev again
```

### **"Module not found"**
```bash
cd frontend
npm install
```

---

## 🎨 Features to Try

1. **Landing Page**: Click through the features
2. **Dashboard**: Watch real-time updates
3. **Token Health**: Search "BTC" and see the health score
4. **Predictions**: Select "ETH" and view trading signals
5. **Portfolio**: Upload a CSV file
6. **Analytics**: Check top gainers and losers

---

## 📱 Mobile Testing

Open on your phone:
- Find your computer's IP address
- Visit: `http://YOUR_IP:3000`
- Test responsive design

---

## 🚀 Production Build

When ready to deploy:
```bash
cd frontend
npm run build
npm start
```

---

## 📚 More Information

- **Full Setup Guide**: See `FRONTEND_SETUP.md`
- **Deployment Guide**: See `DEPLOYMENT.md`
- **Project Summary**: See `PROJECT_SUMMARY.md`

---

## ✅ You're All Set!

Your Market Matrix crypto intelligence platform is ready to use.

**Enjoy building the future of crypto trading! 🎉**
