# Market Matrix - Complete Deployment & Frontend Guide

## 📋 Table of Contents
1. [Required API Keys](#required-api-keys)
2. [Backend Functionality Verification](#backend-functionality-verification)
3. [How The Backend Works](#how-the-backend-works)
4. [Frontend Development Plan](#frontend-development-plan)
5. [Design System from marketmatrix.space](#design-system)

---

## 🔑 Required API Keys

### **REQUIRED** (Core Functionality)

#### 1. **Database** (Choose One)
```bash
# Option A: SQLite (Development - FREE)
DATABASE_URL=sqlite:///./crypto.db

# Option B: PostgreSQL (Production - Recommended)
DATABASE_URL=postgresql://user:password@host:5432/marketmatrix
# Free options: Supabase, Neon, Railway
```

#### 2. **Redis** (Caching & Rate Limiting)
```bash
REDIS_URL=redis://localhost:6379/0

# Free cloud options:
# - Redis Cloud (30MB free): https://redis.com/try-free/
# - Upstash (10K commands/day): https://upstash.com/
```

#### 3. **JWT Security**
```bash
# Generate secure keys:
SECRET_KEY=<generate-with: openssl rand -hex 32>
JWT_SECRET=<generate-with: openssl rand -hex 32>
```

---

### **OPTIONAL** (Enhanced Features)

#### 4. **CoinGecko API** (Market Data)
- **Status**: OPTIONAL - Free tier works without key
- **Benefit**: Higher rate limits (500 req/min vs 50 req/min)
- **Get Key**: https://www.coingecko.com/en/api/pricing (Free tier available)
```bash
COINGECKO_API_KEY=your_key_here  # Optional
```

#### 5. **Binance API** (Real-time Prices)
- **Status**: OPTIONAL - Uses public endpoints without key
- **Benefit**: Higher rate limits for market data
- **Get Key**: https://www.binance.com/en/my/settings/api-management (Free)
```bash
BINANCE_API_KEY=your_key_here  # Optional
```

#### 6. **DexScreener** (DEX Data)
- **Status**: FREE - No key required
- **Usage**: Token health scoring, DEX metrics
```bash
DEXSCREENER_BASE_URL=https://api.dexscreener.com/latest/dex
```

#### 7. **Reddit API** (Community Insights)
- **Status**: OPTIONAL - Only needed if FEATURE_INSIGHTS=1
- **Get Key**: https://www.reddit.com/prefs/apps
```bash
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=market-matrix/0.1
```

#### 8. **OpenAI API** (AI Summarization)
- **Status**: OPTIONAL - Not required for core features
- **Usage**: Enhanced insight summaries
- **Get Key**: https://platform.openai.com/api-keys
```bash
OPENAI_API_KEY=your_key_here  # Optional
```

---

### **MINIMAL WORKING SETUP** (100% Free)

```bash
# Core (Required)
DATABASE_URL=sqlite:///./crypto.db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your_generated_secret_here
JWT_SECRET=your_generated_jwt_here

# Feature Flags (Enable core features)
FEATURE_PREDICTIONS=1
FEATURE_DASHBOARD=1
FEATURE_ADVANCED_TOOLS=1
FEATURE_WEB3_HEALTH=1
FEATURE_PORTFOLIO=0  # Disable if not needed
FEATURE_INSIGHTS=0   # Disable if no Reddit keys

# API Endpoints (Free, no keys needed)
COINGECKO_BASE_URL=https://api.coingecko.com/api/v3
BINANCE_BASE_URL=https://api.binance.com/api/v3
DEXSCREENER_BASE_URL=https://api.dexscreener.com/latest/dex
```

**This setup gives you:**
- ✅ Token Health API (scam detection)
- ✅ Price Predictions (Prophet ML)
- ✅ Market Analytics
- ✅ Alerts System
- ✅ Portfolio Tracking
- ✅ Real-time WebSockets

---

## ✅ Backend Functionality Verification

### **Current Status: All Core Features Working**

#### ✅ **Problem #1: Overwhelming Information**
- **Insights API**: ✅ Working (requires FEATURE_INSIGHTS=1 + Reddit keys for full features)
- **Analytics API**: ✅ Working (correlations, volatility, trends, patterns)

#### ✅ **Problem #2: Entry/Exit Timing**
- **Predictions API**: ✅ Working (Prophet ML, 1h/4h/24h/7d horizons)
- **Alerts API**: ✅ Working (price thresholds, percentage changes)

#### ✅ **Problem #3: Scam Detection**
- **Token Health API**: ✅ NEW - Fully working
  - Health scoring ✅
  - Red flag detection ✅
  - Token comparison ✅
  - Investment recommendations ✅

### **Test All Endpoints**

```bash
# 1. Start the server
uvicorn app.main:app --reload

# 2. Run comprehensive tests
pytest tests/ -v

# 3. Manual endpoint tests
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/token-health/BTC
curl http://localhost:8000/api/v1/predictions?symbol=BTC&horizon=24h
curl http://localhost:8000/api/v1/analytics/correlations
curl http://localhost:8000/api/v1/insights/summary?symbol=BTC&window=24h
```

### **Functionality Matrix**

| Feature | Status | Free APIs | Paid APIs | Notes |
|---------|--------|-----------|-----------|-------|
| **Token Health** | ✅ | DexScreener | - | 100% working |
| **Predictions** | ✅ | CoinGecko, Binance | - | Prophet ML model |
| **Analytics** | ✅ | CoinGecko, Binance | - | All metrics working |
| **Alerts** | ✅ | Database | - | Full CRUD |
| **Insights** | ⚠️ | DexScreener | Reddit (optional) | Proxy scores work, Reddit optional |
| **Portfolio** | ✅ | CoinGecko | - | CSV upload working |
| **WebSockets** | ✅ | - | - | Real-time feeds |
| **Auth** | ✅ | - | - | JWT tokens |

---

## 🏗️ How The Backend Works

### **Architecture Overview**

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT (Frontend)                         │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Application Layer                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  API Router (app/api/v1/router.py)                   │  │
│  │  ├─ /token-health  → Token Health Endpoints          │  │
│  │  ├─ /predictions   → ML Predictions                  │  │
│  │  ├─ /analytics     → Market Analysis                 │  │
│  │  ├─ /insights      → Community Insights              │  │
│  │  ├─ /alerts        → Alert Management                │  │
│  │  ├─ /portfolio     → Portfolio Tracking              │  │
│  │  ├─ /market        → Market Data                     │  │
│  │  ├─ /auth          → Authentication                  │  │
│  │  └─ /ws            → WebSocket Feeds                 │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   Middleware Layer                           │
│  • Rate Limiting (Redis-backed burst protection)            │
│  • CORS (Cross-origin requests)                             │
│  • Authentication (JWT Bearer tokens)                       │
│  • Audit Logging (All requests tracked)                     │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   Service Layer                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  token_health.py - Scam Detection Engine            │    │
│  │  ├─ Calculate 5 health metrics                      │    │
│  │  ├─ Detect red flags                                │    │
│  │  ├─ Generate recommendations                        │    │
│  │  └─ Compare multiple tokens                         │    │
│  ├────────────────────────────────────────────────────┤    │
│  │  prediction.py - ML Forecasting                     │    │
│  │  ├─ Prophet time-series model                       │    │
│  │  ├─ Multi-horizon predictions (1h-7d)              │    │
│  │  ├─ Confidence intervals                            │    │
│  │  └─ Historical accuracy tracking                    │    │
│  ├────────────────────────────────────────────────────┤    │
│  │  analytics.py - Market Intelligence                 │    │
│  │  ├─ Correlation matrix                              │    │
│  │  ├─ Volatility scoring                              │    │
│  │  ├─ Trend detection                                 │    │
│  │  ├─ Pattern recognition                             │    │
│  │  └─ Momentum analysis                               │    │
│  ├────────────────────────────────────────────────────┤    │
│  │  insights.py - Community Intelligence               │    │
│  │  ├─ Proxy scoring (DEX data)                        │    │
│  │  ├─ Sentiment analysis (VADER)                      │    │
│  │  └─ Event aggregation                               │    │
│  ├────────────────────────────────────────────────────┤    │
│  │  alerts.py - Notification System                    │    │
│  │  market_data.py - Data Ingestion                    │    │
│  │  portfolio.py - Portfolio Management                │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   Data Layer                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  PostgreSQL/SQLite Database                          │   │
│  │  ├─ users                                            │   │
│  │  ├─ market_data (OHLCV)                             │   │
│  │  ├─ predictions                                      │   │
│  │  ├─ insights                                         │   │
│  │  ├─ alerts                                           │   │
│  │  ├─ portfolios                                       │   │
│  │  └─ notifications                                    │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Redis Cache                                         │   │
│  │  ├─ Rate limit counters                             │   │
│  │  ├─ Cached predictions (1h TTL)                     │   │
│  │  ├─ Cached analytics (5min TTL)                     │   │
│  │  └─ Session storage                                 │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              External API Integrations                       │
│  • CoinGecko - Market prices, historical data               │
│  • Binance - Real-time prices, order books                  │
│  • DexScreener - DEX metrics, liquidity, transactions       │
│  • Reddit - Community sentiment (optional)                  │
└─────────────────────────────────────────────────────────────┘
```

### **Request Flow Example: Token Health Check**

```
1. Frontend sends:
   GET /api/v1/token-health/SCAMTOKEN
   Headers: Authorization: Bearer <token>

2. Middleware checks:
   ✓ CORS validation
   ✓ JWT authentication
   ✓ Rate limit (100 req/min)
   ✓ Audit log entry

3. Router dispatches to:
   app/api/v1/endpoints/token_health.py → get_token_health()

4. Endpoint calls service:
   app/services/token_health.py → get_cached_token_health()

5. Service checks Redis cache:
   Cache key: "token_health:SCAMTOKEN"
   
   IF cached (< 10min old):
     → Return cached result
   
   ELSE:
     → Calculate fresh health score

6. Calculate health (if not cached):
   a) Fetch DEX data (DexScreener API)
      - Liquidity: $8,500 → Score: 25/100
      - Volume 24h: $15K → Score: 30/100
      - Transactions: 8 txns → Score: 20/100
      - Age: 18 hours → Score: 10/100
   
   b) Fetch market data (Database)
      - Query last 24h prices
      - Calculate volatility: 245% swing → Score: 10/100
   
   c) Weighted average:
      Overall = (25×0.30) + (30×0.25) + (20×0.15) + (10×0.20) + (10×0.10)
              = 7.5 + 7.5 + 3.0 + 2.0 + 1.0
              = 21.0 / 100

   d) Detect red flags:
      ⚠️ "Very low liquidity - high rug pull risk"
      ⚠️ "Extremely low trading activity"
      ⚠️ "Token less than 24 hours old - extreme risk"
      ⚠️ "Extreme price volatility: 245.3% swing in 24h"
   
   e) Generate recommendation:
      Score: 21.0
      Flags: 4
      → "AVOID - Multiple red flags detected. High scam risk."

7. Cache result (10min TTL):
   Redis SET token_health:SCAMTOKEN <json> EX 600

8. Return response:
   {
     "success": true,
     "data": {
       "symbol": "SCAMTOKEN",
       "overall_score": 21.0,
       "health_level": "critical",
       "components": {...},
       "red_flags": [...],
       "recommendation": "AVOID - ..."
     },
     "meta": {
       "timestamp": "2024-10-03T12:00:00Z"
     }
   }

9. Frontend receives and displays warning UI
```

### **Key Technologies**

- **FastAPI**: Modern async Python framework (3-5x faster than Flask)
- **Prophet**: Facebook's time-series forecasting library
- **SQLAlchemy**: ORM for database operations
- **Redis**: Caching and rate limiting
- **Pydantic**: Data validation and serialization
- **VADER**: Sentiment analysis
- **httpx**: Async HTTP client
- **pytest**: Testing framework

---

## 🎨 Frontend Development Plan

### **Recommended Framework: Next.js 14 (App Router)**

**Why Next.js?**
1. ✅ **Perfect for Crypto Apps**: Fast, SEO-optimized, supports real-time updates
2. ✅ **Server Components**: Optimal for fetching market data server-side
3. ✅ **TypeScript Native**: Type-safe API integration
4. ✅ **Performance**: Built-in caching, image optimization
5. ✅ **Developer Experience**: Hot reload, great debugging
6. ✅ **Production Ready**: Used by Coinbase, Uniswap, OpenSea

### **Tech Stack**

```yaml
Core Framework:
  - Next.js 14 (App Router)
  - TypeScript 5+
  - React 18

Styling:
  - Tailwind CSS 3
  - Framer Motion (animations)
  - shadcn/ui (component library)

Data Fetching:
  - TanStack Query (React Query)
  - WebSocket (native)
  - Axios/Fetch

Charts & Visualization:
  - Recharts / Lightweight Charts
  - TradingView Widgets
  - D3.js (custom visualizations)

State Management:
  - Zustand (lightweight, simple)
  - Jotai (atomic state)

Forms & Validation:
  - React Hook Form
  - Zod (schema validation)

Testing:
  - Jest
  - React Testing Library
  - Playwright (E2E)

Deployment:
  - Vercel (recommended)
  - Netlify
  - Railway
```

---

### **Project Structure**

```
market-matrix-frontend/
├── app/
│   ├── (auth)/
│   │   ├── login/
│   │   └── register/
│   ├── (dashboard)/
│   │   ├── layout.tsx
│   │   ├── page.tsx              # Main dashboard
│   │   ├── predictions/
│   │   │   └── page.tsx          # Predictions view
│   │   ├── health/
│   │   │   └── page.tsx          # Token health scanner
│   │   ├── analytics/
│   │   │   └── page.tsx          # Market analytics
│   │   ├── portfolio/
│   │   │   └── page.tsx          # Portfolio tracker
│   │   └── alerts/
│   │       └── page.tsx          # Alert management
│   ├── api/                      # API routes (if needed)
│   ├── layout.tsx                # Root layout
│   └── page.tsx                  # Landing page
├── components/
│   ├── ui/                       # shadcn/ui components
│   ├── charts/
│   │   ├── PriceChart.tsx
│   │   ├── HealthScoreGauge.tsx
│   │   └── CorrelationMatrix.tsx
│   ├── cards/
│   │   ├── TokenHealthCard.tsx
│   │   ├── PredictionCard.tsx
│   │   └── AlertCard.tsx
│   ├── layout/
│   │   ├── Navbar.tsx
│   │   ├── Sidebar.tsx
│   │   └── Footer.tsx
│   └── providers/
│       ├── AuthProvider.tsx
│       └── ThemeProvider.tsx
├── lib/
│   ├── api/
│   │   ├── client.ts             # Axios instance
│   │   ├── token-health.ts       # Token health API
│   │   ├── predictions.ts        # Predictions API
│   │   ├── analytics.ts          # Analytics API
│   │   └── websocket.ts          # WebSocket client
│   ├── hooks/
│   │   ├── useTokenHealth.ts
│   │   ├── usePredictions.ts
│   │   ├── useWebSocket.ts
│   │   └── useAuth.ts
│   ├── utils/
│   │   ├── formatters.ts
│   │   ├── validators.ts
│   │   └── colors.ts
│   └── types/
│       ├── api.ts
│       └── components.ts
├── public/
│   ├── fonts/                    # Custom fonts from marketmatrix.space
│   └── images/
├── styles/
│   └── globals.css
├── next.config.js
├── tailwind.config.js
└── tsconfig.json
```

---

### **Design System (from marketmatrix.space)**

#### **Color Palette**

```css
/* Primary Colors */
--background: #0A0A0F;        /* Deep black-blue background */
--foreground: #FFFFFF;        /* White text */

/* Accent Colors */
--primary: #00FFD1;           /* Cyan/Teal - Main accent */
--primary-glow: #00FFD166;    /* Glowing cyan with opacity */
--secondary: #7B61FF;         /* Purple - Secondary accent */
--warning: #FFB800;           /* Yellow - Warnings */
--danger: #FF4757;            /* Red - Errors/critical */
--success: #00E676;           /* Green - Success/positive */

/* Gradients */
--gradient-primary: linear-gradient(135deg, #00FFD1 0%, #7B61FF 100%);
--gradient-card: linear-gradient(135deg, #1A1A2E 0%, #16213E 100%);

/* Matrix Theme */
--matrix-green: #00FF41;      /* Classic Matrix green */
--matrix-dark: #0D1B2A;       /* Dark blue-black */

/* Glass Morphism */
--glass-bg: rgba(255, 255, 255, 0.05);
--glass-border: rgba(255, 255, 255, 0.1);
--glass-blur: 10px;
```

#### **Typography**

```css
/* From marketmatrix.space inspection */
--font-primary: 'Inter', -apple-system, sans-serif;
--font-display: 'Montserrat', sans-serif;  /* For headings */

/* Font Sizes */
--text-xs: 0.75rem;    /* 12px */
--text-sm: 0.875rem;   /* 14px */
--text-base: 1rem;     /* 16px */
--text-lg: 1.125rem;   /* 18px */
--text-xl: 1.25rem;    /* 20px */
--text-2xl: 1.5rem;    /* 24px */
--text-3xl: 1.875rem;  /* 30px */
--text-4xl: 2.25rem;   /* 36px */
--text-5xl: 3rem;      /* 48px */

/* Font Weights */
--font-light: 300;
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

#### **Spacing & Layout**

```css
/* Spacing Scale */
--space-1: 0.25rem;   /* 4px */
--space-2: 0.5rem;    /* 8px */
--space-3: 0.75rem;   /* 12px */
--space-4: 1rem;      /* 16px */
--space-6: 1.5rem;    /* 24px */
--space-8: 2rem;      /* 32px */
--space-12: 3rem;     /* 48px */
--space-16: 4rem;     /* 64px */

/* Border Radius */
--radius-sm: 0.375rem;   /* 6px */
--radius-md: 0.5rem;     /* 8px */
--radius-lg: 0.75rem;    /* 12px */
--radius-xl: 1rem;       /* 16px */
--radius-2xl: 1.5rem;    /* 24px */
--radius-full: 9999px;   /* Pills/circles */
```

#### **Component Styles**

```tsx
// Glass Card (from landing page)
const GlassCard = () => (
  <div className="
    bg-white/5 
    backdrop-blur-lg 
    border border-white/10 
    rounded-2xl 
    p-6 
    shadow-2xl 
    hover:border-primary/50 
    transition-all 
    duration-300
  ">
    {/* Content */}
  </div>
);

// Gradient Button
const GradientButton = () => (
  <button className="
    bg-gradient-to-r 
    from-primary 
    to-secondary 
    text-white 
    font-semibold 
    px-8 
    py-4 
    rounded-full 
    hover:scale-105 
    transition-transform 
    duration-200 
    shadow-lg 
    shadow-primary/50
  ">
    Get Started
  </button>
);

// Health Score Badge
const HealthBadge = ({ score }: { score: number }) => {
  const getColor = (s: number) => {
    if (s >= 80) return 'text-success border-success/50 bg-success/10';
    if (s >= 65) return 'text-primary border-primary/50 bg-primary/10';
    if (s >= 50) return 'text-warning border-warning/50 bg-warning/10';
    return 'text-danger border-danger/50 bg-danger/10';
  };
  
  return (
    <div className={`
      inline-flex items-center gap-2
      px-4 py-2 rounded-full
      border backdrop-blur-sm
      font-semibold text-sm
      ${getColor(score)}
    `}>
      <span className="w-2 h-2 rounded-full bg-current animate-pulse" />
      {score}/100
    </div>
  );
};
```

---

### **Page-by-Page Implementation Plan**

#### **Phase 1: Foundation (Week 1)**

**1.1 Project Setup**
```bash
# Initialize Next.js project
npx create-next-app@latest market-matrix --typescript --tailwind --app

# Install dependencies
cd market-matrix
npm install @tanstack/react-query axios zustand
npm install framer-motion recharts
npm install react-hook-form zod @hookform/resolvers
npm install lucide-react class-variance-authority clsx tailwind-merge

# Install shadcn/ui
npx shadcn-ui@latest init
npx shadcn-ui@latest add button card input badge alert
```

**1.2 API Client Setup**
```typescript
// lib/api/client.ts
import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor (add JWT token)
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor (handle errors)
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login
      window.location.href = '/login';
    }
    throw error;
  }
);

export default apiClient;
```

**1.3 Landing Page** (replicate marketmatrix.space)
```tsx
// app/page.tsx
export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#0A0A0F] text-white">
      {/* Hero Section */}
      <section className="relative overflow-hidden py-32">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/20 to-secondary/20 blur-3xl" />
        <div className="container mx-auto px-6 relative z-10">
          <h1 className="text-7xl font-bold mb-6 bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
            Escape the Matrix
          </h1>
          <p className="text-2xl text-gray-400 mb-12">
            Empower traders with a full suite of crypto tools in one place
          </p>
          <button className="bg-gradient-to-r from-primary to-secondary px-12 py-4 rounded-full text-lg font-semibold hover:scale-105 transition-transform">
            Launch App
          </button>
        </div>
      </section>

      {/* Features Section */}
      <FeaturesSection />

      {/* Integrations */}
      <IntegrationsSection />

      {/* Tokenomics */}
      <TokenomicsSection />

      {/* FAQs */}
      <FAQSection />
    </div>
  );
}
```

---

#### **Phase 2: Dashboard Core (Week 2)**

**2.1 Token Health Scanner** (Main Priority)
```tsx
// app/(dashboard)/health/page.tsx
'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchTokenHealth } from '@/lib/api/token-health';
import HealthScoreGauge from '@/components/charts/HealthScoreGauge';
import RedFlagsList from '@/components/health/RedFlagsList';

export default function TokenHealthPage() {
  const [symbol, setSymbol] = useState('BTC');

  const { data, isLoading } = useQuery({
    queryKey: ['tokenHealth', symbol],
    queryFn: () => fetchTokenHealth(symbol),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-4xl font-bold">Token Health Scanner</h1>
        <TokenSearch onSearch={setSymbol} />
      </div>

      {isLoading ? (
        <LoadingSkeleton />
      ) : (
        <>
          {/* Main Health Score */}
          <div className="grid md:grid-cols-2 gap-6">
            <GlassCard>
              <HealthScoreGauge 
                score={data.overall_score}
                level={data.health_level}
              />
            </GlassCard>

            <GlassCard>
              <h3 className="text-xl font-semibold mb-4">Recommendation</h3>
              <RecommendationBadge text={data.recommendation} />
            </GlassCard>
          </div>

          {/* Component Breakdown */}
          <GlassCard>
            <h3 className="text-xl font-semibold mb-6">Health Metrics</h3>
            <div className="grid grid-cols-5 gap-4">
              {Object.entries(data.components).map(([key, value]) => (
                <MetricCard key={key} label={key} value={value} />
              ))}
            </div>
          </GlassCard>

          {/* Red Flags */}
          {data.red_flags.length > 0 && (
            <GlassCard className="border-danger/50">
              <RedFlagsList flags={data.red_flags} />
            </GlassCard>
          )}

          {/* Token Comparison */}
          <TokenComparison symbol={symbol} />
        </>
      )}
    </div>
  );
}
```

**2.2 Predictions Dashboard**
```tsx
// app/(dashboard)/predictions/page.tsx
'use client';

import { useQuery } from '@tanstack/react-query';
import { fetchPredictions } from '@/lib/api/predictions';
import PriceChart from '@/components/charts/PriceChart';
import PredictionCard from '@/components/cards/PredictionCard';

export default function PredictionsPage() {
  const { data } = useQuery({
    queryKey: ['predictions', 'BTC'],
    queryFn: () => fetchPredictions('BTC', ['1h', '4h', '24h', '7d']),
  });

  return (
    <div className="space-y-8">
      <h1 className="text-4xl font-bold">Price Predictions</h1>

      {/* Current Price + Chart */}
      <GlassCard>
        <PriceChart 
          symbol="BTC"
          currentPrice={data?.current_price}
          predictions={data?.predictions}
        />
      </GlassCard>

      {/* Prediction Cards */}
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        {data?.predictions.map((pred) => (
          <PredictionCard key={pred.horizon} prediction={pred} />
        ))}
      </div>

      {/* Confidence & Factors */}
      <div className="grid md:grid-cols-2 gap-6">
        <ConfidenceChart data={data?.predictions} />
        <FactorsBreakdown factors={data?.predictions[0]?.factors} />
      </div>
    </div>
  );
}
```

---

#### **Phase 3: Advanced Features (Week 3)**

**3.1 Analytics Dashboard**
```tsx
// app/(dashboard)/analytics/page.tsx
- Correlation matrix heatmap
- Volatility metrics chart
- Trend signals table
- Pattern detection cards
- Top performers list
- Momentum leaders
```

**3.2 Portfolio Tracker**
```tsx
// app/(dashboard)/portfolio/page.tsx
- CSV upload
- Holdings table
- Allocation pie chart
- Performance graph
- P&L breakdown
```

**3.3 Alerts Management**
```tsx
// app/(dashboard)/alerts/page.tsx
- Create alert form
- Active alerts list
- Notification history
- Alert triggers stats
```

---

#### **Phase 4: Real-time & Polish (Week 4)**

**4.1 WebSocket Integration**
```typescript
// lib/hooks/useWebSocket.ts
import { useEffect, useState } from 'use';

export function useWebSocket(url: string) {
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    const socket = new WebSocket(url);
    
    socket.onopen = () => {
      console.log('WebSocket connected');
      // Subscribe to channels
      socket.send(JSON.stringify({
        action: 'subscribe',
        symbols: ['BTC', 'ETH']
      }));
    };

    socket.onmessage = (event) => {
      const update = JSON.parse(event.data);
      setData(update);
    };

    setWs(socket);

    return () => socket.close();
  }, [url]);

  return { ws, data };
}
```

**4.2 Animations & Transitions**
```tsx
// Using Framer Motion
import { motion } from 'framer-motion';

const CardVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
};

<motion.div
  variants={CardVariants}
  initial="hidden"
  animate="visible"
  transition={{ duration: 0.3 }}
>
  {/* Card content */}
</motion.div>
```

**4.3 Responsive Design**
- Mobile-first approach
- Tablet optimizations
- Desktop layouts

---

### **Deployment**

#### **Backend (FastAPI)**
```yaml
Options:
  1. Railway (Recommended)
     - Auto-deploy from GitHub
     - Free $5/month credits
     - PostgreSQL + Redis included
  
  2. Render
     - Free tier available
     - Auto-deploy
     - Add-ons for Redis
  
  3. Fly.io
     - Good for global distribution
     - Free tier
```

#### **Frontend (Next.js)**
```bash
# Deploy to Vercel (1-click)
vercel

# Environment variables
NEXT_PUBLIC_API_URL=https://your-api.railway.app/api/v1
NEXT_PUBLIC_WS_URL=wss://your-api.railway.app/api/v1/ws
```

---

## 📊 Development Timeline

| Week | Focus | Deliverables |
|------|-------|--------------|
| **Week 1** | Setup & Landing Page | Project structure, API client, landing page |
| **Week 2** | Core Dashboard | Token health, predictions, main nav |
| **Week 3** | Advanced Features | Analytics, portfolio, alerts |
| **Week 4** | Polish & Deploy | WebSockets, animations, testing, deployment |

---

## ✅ Success Metrics

- **Backend**: All endpoints tested and working ✅
- **Frontend**: Responsive, fast (<3s load), beautiful UI
- **Integration**: Seamless API communication
- **UX**: Intuitive navigation, clear CTAs
- **Performance**: 90+ Lighthouse score

---

**Ready to build! 🚀**
