# Market Matrix Frontend

Modern Next.js frontend for the Market Matrix crypto intelligence platform.

## Features

### 🎯 Core Functionality
- **Landing Page**: Beautiful hero section showcasing platform features and problem solutions
- **Dashboard**: Real-time market overview with AI predictions and top movers
- **Token Health Analyzer**: Expose scams and weak projects before investing
- **AI Predictions**: Entry/exit signals with confidence scores across multiple timeframes
- **Portfolio Tracker**: Track holdings with P&L, allocation, and performance analytics
- **Market Analytics**: Top performers, volatility analysis, and market trends

### 🎨 UI/UX
- Modern, responsive design with TailwindCSS
- Dark mode support
- Smooth animations with Framer Motion
- Professional UI components (shadcn/ui style)
- Mobile-friendly navigation

### 🔌 Integration
- Full API integration with FastAPI backend
- WebSocket support for real-time updates
- Axios-based API client with interceptors
- Error handling and loading states

## Getting Started

### Prerequisites
- Node.js 18+ 
- npm or yarn
- Running Market Matrix API backend

### Installation

1. Install dependencies:
```bash
npm install
```

2. Configure environment:
```bash
cp .env.local.example .env.local
```

Edit `.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

3. Run development server:
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the application.

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js app directory
│   │   ├── page.tsx           # Landing page
│   │   ├── dashboard/         # Dashboard page
│   │   ├── predictions/       # Predictions page
│   │   ├── token-health/      # Token health analyzer
│   │   ├── portfolio/         # Portfolio tracker
│   │   └── analytics/         # Market analytics
│   ├── components/
│   │   ├── ui/                # Reusable UI components
│   │   └── layout/            # Layout components (Navbar, etc.)
│   └── lib/
│       ├── api-client.ts      # API client
│       ├── websocket.ts       # WebSocket client
│       └── utils.ts           # Utility functions
├── public/                     # Static assets
└── tailwind.config.ts         # Tailwind configuration
```

## Key Pages

### Landing Page (`/`)
- Hero section with gradient text
- Problem statement cards
- Feature showcase
- Call-to-action sections

### Dashboard (`/dashboard`)
- Market overview with top cryptocurrencies
- Real-time price updates
- AI predictions sidebar
- Market metrics (market cap, volume, dominance, fear & greed)

### Token Health (`/token-health`)
- Token analysis search
- Overall health score (0-100)
- Risk indicators (contract verified, liquidity locked, honeypot detection)
- Detailed metrics (liquidity, holder distribution, contract safety)
- Investment recommendations

### Predictions (`/predictions`)
- Symbol search with popular tokens
- Trading signals (BUY/SELL/HOLD)
- Multi-timeframe predictions (1h, 4h, 24h, 7d)
- Confidence intervals and probability scores
- Key prediction factors

### Portfolio (`/portfolio`)
- CSV upload for holdings
- Total value and P&L tracking
- Asset allocation visualization
- Performance metrics (24h, 7d, 30d)
- Diversification analysis

### Analytics (`/analytics`)
- Top gainers and losers
- Volume leaders
- Volatility analysis
- Market trends
- Market indices

## API Integration

The frontend connects to the FastAPI backend through the API client (`src/lib/api-client.ts`):

```typescript
import { apiClient } from '@/lib/api-client';

// Example usage
const predictions = await apiClient.getPredictions('BTC');
const health = await apiClient.getTokenHealth('ETH');
const portfolio = await apiClient.getHoldings();
```

## WebSocket Support

Real-time updates via WebSocket:

```typescript
import { getWebSocketClient } from '@/lib/websocket';

const ws = getWebSocketClient();
await ws.connect();
ws.subscribe(['price:BTC', 'predictions:*']);
ws.on('price_update', (data) => {
  console.log('Price update:', data);
});
```

## Building for Production

```bash
npm run build
npm start
```

## Technologies Used

- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe development
- **TailwindCSS**: Utility-first CSS framework
- **Radix UI**: Accessible component primitives
- **Lucide React**: Beautiful icon library
- **Axios**: HTTP client
- **Zustand**: State management (optional)
- **Framer Motion**: Animation library
- **Recharts**: Chart library

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` |

## Contributing

1. Follow the existing code style
2. Use TypeScript for type safety
3. Keep components modular and reusable
4. Test on multiple screen sizes
5. Ensure API error handling

## License

Copyright 2025 Market Matrix. All rights reserved.
