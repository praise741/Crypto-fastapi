'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, TrendingDown, Activity, DollarSign, AlertTriangle } from 'lucide-react';
import { apiClient } from '@/lib/api-client';
import { formatCurrency, formatPercentage, getChangeColor, formatDate } from '@/lib/utils';

interface MarketData {
  symbol: string;
  price: number;
  change_24h: number | null;
  volume_24h: number;
  timestamp: string;
}

interface Prediction {
  symbol: string;
  current_price: number;
  predicted_price: number;
  horizon: string;
  confidence: number;
  direction: 'up' | 'down';
}

interface DashboardMetrics {
  total_market_cap: number;
  total_volume_24h: number;
  btc_dominance: number;
  fear_greed_index: number;
}

interface DashboardResponse {
  success: boolean;
  data: {
    metrics?: DashboardMetrics;
    predictions?: Prediction[];
  };
}

interface PricesResponse {
  success: boolean;
  data: {
    prices?: MarketData[];
  };
}

export default function DashboardPage() {
  const [marketData, setMarketData] = useState<MarketData[]>([]);
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
    const interval = setInterval(loadDashboardData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      const [dashboardRes, pricesRes] = await Promise.all([
        apiClient.getDashboard().catch(() => ({ success: false, data: null })),
        apiClient.getMarketPrices().catch(() => ({ success: false, data: null })),
      ]);

      // Handle dashboard response
      if ((dashboardRes as unknown as DashboardResponse).success && (dashboardRes as unknown as DashboardResponse).data?.metrics) {
        setMetrics((dashboardRes as unknown as DashboardResponse).data.metrics || null);
        if ((dashboardRes as unknown as DashboardResponse).data.predictions) {
          setPredictions((dashboardRes as unknown as DashboardResponse).data.predictions || []);
        }
      }

      // Handle market prices response
      if ((pricesRes as unknown as PricesResponse).success && (pricesRes as unknown as PricesResponse).data?.prices) {
        setMarketData((pricesRes as unknown as PricesResponse).data.prices || []);
      }
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const topGainers = [...marketData]
    .filter(asset => asset.change_24h !== null)
    .sort((a, b) => (b.change_24h || 0) - (a.change_24h || 0))
    .slice(0, 5);

  const topLosers = [...marketData]
    .filter(asset => asset.change_24h !== null)
    .sort((a, b) => (a.change_24h || 0) - (b.change_24h || 0))
    .slice(0, 5);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Activity className="h-12 w-12 animate-spin mx-auto mb-4 text-primary" />
          <p className="text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground mt-2">
            Real-time market overview and AI-powered predictions
          </p>
        </div>

        {/* Metrics Cards */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Market Cap</CardTitle>
              <DollarSign className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {metrics?.total_market_cap ? formatCurrency(metrics.total_market_cap, 0) : '📊 Loading...'}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">24h Volume</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {metrics?.total_volume_24h ? formatCurrency(metrics.total_volume_24h, 0) : '📊 Loading...'}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">BTC Dominance</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {metrics?.btc_dominance ? `${metrics.btc_dominance.toFixed(2)}%` : '📊 Loading...'}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Fear & Greed</CardTitle>
              <AlertTriangle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {metrics?.fear_greed_index || '📊 Loading...'}
              </div>
              {metrics?.fear_greed_index && (
                <p className="text-xs text-muted-foreground mt-1">
                  {metrics.fear_greed_index > 75 ? 'Extreme Greed' :
                   metrics.fear_greed_index > 55 ? 'Greed' :
                   metrics.fear_greed_index > 45 ? 'Neutral' :
                   metrics.fear_greed_index > 25 ? 'Fear' : 'Extreme Fear'}
                </p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Main Content */}
        <div className="grid gap-8 lg:grid-cols-3">
          {/* Market Overview */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle>Market Overview</CardTitle>
                <CardDescription>Top cryptocurrencies by market cap</CardDescription>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue="all" className="w-full">
                  <TabsList className="grid w-full grid-cols-3">
                    <TabsTrigger value="all">All</TabsTrigger>
                    <TabsTrigger value="gainers">Top Gainers</TabsTrigger>
                    <TabsTrigger value="losers">Top Losers</TabsTrigger>
                  </TabsList>

                  <TabsContent value="all" className="space-y-4 mt-4">
                    {marketData.slice(0, 10).map((asset) => (
                      <MarketAssetRow key={asset.symbol} asset={asset} />
                    ))}
                  </TabsContent>

                  <TabsContent value="gainers" className="space-y-4 mt-4">
                    {topGainers.map((asset) => (
                      <MarketAssetRow key={asset.symbol} asset={asset} />
                    ))}
                  </TabsContent>

                  <TabsContent value="losers" className="space-y-4 mt-4">
                    {topLosers.map((asset) => (
                      <MarketAssetRow key={asset.symbol} asset={asset} />
                    ))}
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          </div>

          {/* AI Predictions */}
          <div>
            <Card>
              <CardHeader>
                <CardTitle>AI Predictions</CardTitle>
                <CardDescription>Next 24h price forecasts</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {predictions.length > 0 ? (
                  predictions.map((pred) => (
                    <PredictionCard key={pred.symbol} prediction={pred} />
                  ))
                ) : (
                  <div className="text-center py-8">
                    <Activity className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
                    <p className="text-sm text-muted-foreground">No predictions available</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}

function MarketAssetRow({ asset }: { asset: MarketData }) {
  return (
    <div className="flex items-center justify-between p-4 rounded-lg border hover:bg-accent/50 transition-colors">
      <div className="flex items-center gap-4">
        <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
          <span className="font-bold text-primary">{asset.symbol.slice(0, 2)}</span>
        </div>
        <div>
          <p className="font-semibold">{asset.symbol}</p>
          <p className="text-sm text-muted-foreground">{formatCurrency(asset.price)}</p>
          <p className="text-xs text-muted-foreground">{formatDate(asset.timestamp)}</p>
        </div>
      </div>
      <div className="text-right">
        <div className={`flex items-center gap-1 ${getChangeColor(asset.change_24h)}`}>
          {asset.change_24h !== null && asset.change_24h >= 0 ? (
            <TrendingUp className="h-4 w-4" />
          ) : asset.change_24h !== null ? (
            <TrendingDown className="h-4 w-4" />
          ) : (
            <Activity className="h-4 w-4 text-gray-400" />
          )}
          <span className="font-semibold">{formatPercentage(asset.change_24h)}</span>
        </div>
        <p className="text-xs text-muted-foreground mt-1">
          Vol: {formatCurrency(asset.volume_24h, 0)}
        </p>
      </div>
    </div>
  );
}

function PredictionCard({ prediction }: { prediction: Prediction }) {
  const priceChange = ((prediction.predicted_price - prediction.current_price) / prediction.current_price) * 100;
  
  return (
    <div className="p-4 rounded-lg border bg-card">
      <div className="flex items-center justify-between mb-2">
        <span className="font-semibold">{prediction.symbol}</span>
        <Badge variant={prediction.direction === 'up' ? 'default' : 'destructive'}>
          {prediction.direction === 'up' ? 'Bullish' : 'Bearish'}
        </Badge>
      </div>
      <div className="space-y-1">
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Current</span>
          <span className="font-medium">{formatCurrency(prediction.current_price)}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Predicted</span>
          <span className={`font-medium ${getChangeColor(priceChange)}`}>
            {formatCurrency(prediction.predicted_price)}
          </span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Confidence</span>
          <span className="font-medium">{(prediction.confidence * 100).toFixed(0)}%</span>
        </div>
      </div>
    </div>
  );
}
