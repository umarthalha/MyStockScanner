# AI Khan — Swing Intelligence Platform v3.1

## ── LOCAL SETUP ────────────────────────────────────────────────────────────

### 1. Backend
```bash
pip install -r requirements.txt
python main.py
# Runs on http://localhost:8000
# Docs at http://localhost:8000/docs
```

### 2. Frontend
Double-click `index.html` — no build step, no Node, nothing to install.

---

## ── FREE DEPLOYMENT (public URL, 0 cost) ─────────────────────────────────

### Backend → Render.com (free tier)
1. Push `main.py` + `requirements.txt` to a GitHub repo
2. Go to https://render.com → New → Web Service → connect repo
3. Set these fields:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance type:** Free
4. Click Deploy. Wait ~3 min.
5. Copy your URL e.g. `https://ai-khan-backend.onrender.com`

### Update frontend with your backend URL
Open `index.html`, find line ~685:
```
const RENDER_URL = 'https://ai-khan-backend.onrender.com';
```
Replace with your actual Render URL.

### Frontend → Netlify (free tier, drag & drop)
1. Go to https://app.netlify.com/drop
2. Drag `index.html` onto the page
3. Done — you get a URL like `https://ai-khan-abc.netlify.app`

---

## ── FREE PLAN LIMITS — WHAT TO KNOW ──────────────────────────────────────

| Service      | Free limit            | Will it hit limits? |
|--------------|-----------------------|---------------------|
| Render.com   | 750 hrs/month compute | ✅ Enough (1 server) |
| Render.com   | Sleeps after 15 min idle | ⚠ First request slow (~30s wake) |
| Netlify      | 100 GB bandwidth/month | ✅ More than enough |
| yfinance     | No limit (Yahoo data)  | ✅ Free forever |
| RSS news     | No limit               | ✅ Free forever |

### Render free tier sleep issue
On free tier Render sleeps after 15 minutes of no traffic.
First visit will take 20-30 seconds for the backend to wake up,
then scanning starts. This is normal and free.

To avoid this: upgrade to Render Starter ($7/month) — stays awake.

---

## ── API ENDPOINTS ──────────────────────────────────────────────────────────

| Endpoint                | Description                    | Cache  |
|-------------------------|--------------------------------|--------|
| GET /api/health         | Server status                  | —      |
| GET /api/signals        | Current swing signals          | 30 min |
| GET /api/signals/refresh| Trigger new scan (background)  | —      |
| GET /api/market-intel   | Fear & Greed + sector strength | 15 min |
| GET /api/overview       | Nifty, Sensex, VIX, IT, Mid    | 5 min  |
| GET /api/news           | Live RSS news (ET + MC)        | 10 min |

---

## ── SIGNAL SCORING (max 100 pts, fires at ≥ 80) ───────────────────────────

| Condition                        | Points |
|----------------------------------|--------|
| Price > 200 EMA (bull trend)     | 20     |
| Price reclaims 21 EMA            | 20     |
| MACD bullish crossover           | 20     |
| RSI 35–62 (ideal entry zone)     | 15     |
| Volume ≥ 1.5× 20-day average     | 15     |
| EMA stack: 9 > 21 > 50           | 10     |
| Bonus: Bullish RSI divergence    | +5     |

## ── FILTERS ────────────────────────────────────────────────────────────────
- Min avg daily volume: 50,000 (removes illiquid stocks)
- Min price: ₹10 (removes penny stocks)
- Max 2 signals per sector (prevents sector concentration)
- Max 12 signals total per scan

## ── UNIVERSE ────────────────────────────────────────────────────────────────
~165 stocks: Nifty 50 + Nifty 100 + Midcap additions + BSE liquid stocks
