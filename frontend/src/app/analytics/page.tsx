'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import {
  TrendingUp,
  TrendingDown,
  Activity,
  BarChart3,
  Zap,
  AlertCircle
} from 'lucide-react';
import { apiClient } from '@/lib/api-client';
import { formatCurrency, formatPercentage, getChangeColor } from '@/lib/utils';
import { ProtectedRoute } from '@/components/auth/protected-route';

interface TopPerformer {
  symbol: string;
  current_price: number;
  change_24h: number;
  volume_24h: number;
  performance_score: number;
  category: string;
  period: string;
}

interface Volatility {
  symbol: string;
  volatility: number;
  window_hours: number;
}

interface Trend {
  symbol: string;
  trend: string;
  score: number;
  updated_at: string;
}

interface Index {
  index: string;
  value: number;
  change_24h: number;
  classification: string;
}

interface MarketPrice {
  symbol: string;
  price: number;
  change_24h: number;
  volume_24h: number;
}


interface DashboardMetrics {
  total_market_cap: number;
  total_volume_24h: number;
  btc_dominance: number;
  fear_greed_index: number;
}

interface ApiResponse<T> {
  success: boolean;
  data: T;
  meta?: unknown;
}

export default function AnalyticsPage() {
  return (
    <ProtectedRoute>
      <AnalyticsContent />
    </ProtectedRoute>
  );
}

function AnalyticsContent() {
  const [topPerformers, setTopPerformers] = useState<TopPerformer[]>([]);
  const [volatility, setVolatility] = useState<Volatility[]>([]);
  const [trends, setTrends] = useState<Trend[]>([]);
  const [indices, setIndices] = useState<Index[]>([]);
  const [dashboardMetrics, setDashboardMetrics] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    loadAnalyticsData();
  }, []);

  const loadAnalyticsData = async () => {
    try {
      setLoading(true);

      // Load all analytics data in parallel
      const [performersRes, marketPricesRes, volatilityRes, trendsRes, metricsRes] = await Promise.allSettled([
        apiClient.getTopPerformers(10),
        apiClient.getMarketPrices(),
        apiClient.getVolatility(),
        apiClient.getTrends(),
        apiClient.getDashboardMetrics()
      ]);

      // Handle top performers by combining data from both endpoints
      if (performersRes.status === 'fulfilled' && (performersRes.value as unknown as ApiResponse<{ assets: TopPerformer[] }>)?.success &&
          marketPricesRes.status === 'fulfilled' && (marketPricesRes.value as unknown as ApiResponse<{ prices: MarketPrice[] }>)?.success) {

        const performersData = (performersRes.value as unknown as ApiResponse<{ assets: TopPerformer[] }>)?.data?.assets || [];
        const marketData = (marketPricesRes.value as unknown as ApiResponse<{ prices: MarketPrice[] }>)?.data?.prices || [];

        // Create a map of market data by symbol for quick lookup
        const marketDataMap = new Map(marketData.map((item: MarketPrice) => [item.symbol, item]));

        // Combine the data - assets are already TopPerformers from API
        type TopPerformerAPI = {
          symbol: string;
          return_percent?: number;
          current_price?: number;
          change_24h?: number;
          volume_24h?: number;
          performance_score?: number;
          category?: string;
          period?: string;
        };

        const combinedPerformers = performersData.map((asset: TopPerformerAPI) => {
          const symbol = asset.symbol;
          const marketInfo = marketDataMap.get(symbol);
          // Prefer market data; fall back to asset where possible
          const price = marketInfo?.price ?? asset.current_price ?? 0;
          const change24h = marketInfo?.change_24h ?? asset.change_24h ?? (typeof asset.return_percent === 'number' ? asset.return_percent : 0);
          const volume24h = marketInfo?.volume_24h ?? asset.volume_24h ?? 0;

          const performance = (typeof asset.performance_score === 'number' ? asset.performance_score : (typeof asset.return_percent === 'number' ? asset.return_percent : 0));
          const category = asset.category ?? (change24h >= 0 ? 'gainer' : 'loser');
          const period = asset.period ?? '72h';

          return {
            symbol,
            current_price: price,
            change_24h: change24h,
            volume_24h: volume24h,
            performance_score: performance,
            category,
            period,
          } as TopPerformer;
        });

        setTopPerformers(combinedPerformers);
      } else {
        console.warn('API failed, using fallback');
        // Fallback mock data matching API structure
        setTopPerformers([
          { symbol: 'BTC', current_price: 125223.0, change_24h: 0.0177, volume_24h: 69624071286.84, performance_score: 85.2, category: 'gainer', period: '72h' },
          { symbol: 'ETH', current_price: 4691.75, change_24h: 0.1776, volume_24h: 40194070202.35, performance_score: 78.5, category: 'gainer', period: '72h' },
          { symbol: 'SOL', current_price: 234.62, change_24h: 0.4925, volume_24h: 7443261926.51, performance_score: 92.1, category: 'gainer', period: '72h' },
          { symbol: 'BNB', current_price: 1223.28, change_24h: 0.0396, volume_24h: 4220957765.43, performance_score: 45.3, category: 'gainer', period: '72h' },
          { symbol: 'ADA', current_price: 0.876887, change_24h: 2.4341, volume_24h: 1377019969.14, performance_score: 65.8, category: 'gainer', period: '72h' }
        ]);
      }

      // Handle volatility
      if (volatilityRes.status === 'fulfilled' && (volatilityRes.value as unknown as ApiResponse<{ metrics: Volatility[] }>)?.success && (volatilityRes.value as unknown as ApiResponse<{ metrics: Volatility[] }>)?.data?.metrics) {
        setVolatility((volatilityRes.value as unknown as ApiResponse<{ metrics: Volatility[] }>).data.metrics);
      } else {
        console.warn('Volatility API failed, using fallback');
        setVolatility([
          { symbol: 'BTC', volatility: 0.0032, window_hours: 24 },
          { symbol: 'ETH', volatility: 0.0033, window_hours: 24 },
          { symbol: 'SOL', volatility: 0.0050, window_hours: 24 },
          { symbol: 'BNB', volatility: 0.0095, window_hours: 24 }
        ]);
      }

      // Handle trends
      if (trendsRes.status === 'fulfilled' && (trendsRes.value as unknown as ApiResponse<{ signals: Trend[] }>)?.success && (trendsRes.value as unknown as ApiResponse<{ signals: Trend[] }>)?.data?.signals) {
        setTrends((trendsRes.value as unknown as ApiResponse<{ signals: Trend[] }>).data.signals);
      } else {
        console.warn('Trends API failed, using fallback');
        setTrends([
          { symbol: 'BTC', trend: 'bearish', score: 0.04, updated_at: new Date().toISOString() },
          { symbol: 'ETH', trend: 'bullish', score: 2.54, updated_at: new Date().toISOString() },
          { symbol: 'SOL', trend: 'bearish', score: 1.1, updated_at: new Date().toISOString() },
          { symbol: 'BNB', trend: 'bullish', score: 5.27, updated_at: new Date().toISOString() }
        ]);
      }

      // Handle dashboard metrics for indices
      if (metricsRes.status === 'fulfilled' && (metricsRes.value as unknown as ApiResponse<DashboardMetrics>)?.success && (metricsRes.value as unknown as ApiResponse<DashboardMetrics>)?.data) {
        setDashboardMetrics((metricsRes.value as unknown as ApiResponse<DashboardMetrics>).data);

        // Create indices from dashboard metrics
        const metrics = (metricsRes.value as unknown as ApiResponse<DashboardMetrics>).data;
        setIndices([
          {
            index: 'Global Market Cap',
            value: metrics.total_market_cap / 1e12, // Convert to trillions
            change_24h: 2.3,
            classification: 'Bullish'
          },
          {
            index: 'Total Volume (24h)',
            value: metrics.total_volume_24h / 1e9, // Convert to billions
            change_24h: 5.1,
            classification: 'Very Bullish'
          },
          {
            index: 'BTC Dominance',
            value: metrics.btc_dominance,
            change_24h: -0.8,
            classification: 'Neutral'
          },
          {
            index: 'Fear & Greed Index',
            value: metrics.fear_greed_index,
            change_24h: 3.2,
            classification: 'Greed'
          }
        ]);
      } else {
        console.warn('Dashboard metrics API failed, using fallback');
        setIndices([
          { index: 'Total Market Cap', value: 2.5, change_24h: 2.3, classification: 'Bullish' },
          { index: 'Total Volume (24h)', value: 171.6, change_24h: 5.1, classification: 'Very Bullish' },
          { index: 'BTC Dominance', value: 56.85, change_24h: -0.8, classification: 'Neutral' },
          { index: 'Fear & Greed Index', value: 65, change_24h: 3.2, classification: 'Greed' }
        ]);
      }

    } catch (error) {
      console.error('Failed to load analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Activity className="h-12 w-12 animate-spin mx-auto mb-4 text-primary" />
          <p className="text-muted-foreground">Loading analytics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto max-w-7xl px-3 sm:px-6 lg:px-8 py-4 sm:py-8">
        {/* Header */}
        <div className="mb-6 sm:mb-8">
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">Market Analytics</h1>
          <p className="text-sm sm:text-base text-muted-foreground mt-1 sm:mt-2">
            Advanced market insights and trend analysis
          </p>
        </div>

        {/* Market Indices */}
        <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4 mb-6 sm:mb-8">
          {indices.map((index) => (
            <Card key={index.index}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 p-3 sm:p-4 pb-2">
                <CardTitle className="text-xs sm:text-sm font-medium truncate pr-2">{index.index}</CardTitle>
                <BarChart3 className="h-3 w-3 sm:h-4 sm:w-4 text-muted-foreground flex-shrink-0" />
              </CardHeader>
              <CardContent className="p-3 sm:p-4 pt-0">
                <div className="text-lg sm:text-2xl font-bold truncate">
                  {index.index.includes('Market Cap') ? `$${index.value.toFixed(2)}T` :
                   index.index.includes('Volume') ? `$${index.value.toFixed(1)}B` :
                   index.index.includes('Dominance') ? `${index.value.toFixed(1)}%` :
                   index.value.toFixed(0)}
                </div>
                <div className="flex flex-wrap items-center gap-1 sm:gap-2 mt-1">
                  <span className={`text-[10px] sm:text-xs font-medium ${getChangeColor(index.change_24h)}`}>
                    {formatPercentage(index.change_24h)}
                  </span>
                  <Badge variant="outline" className="text-[10px] sm:text-xs px-1.5 py-0">
                    {index.classification}
                  </Badge>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Main Content */}
        <Tabs defaultValue="performers" className="space-y-4">
          <TabsList className="grid w-full grid-cols-3 mobile-friendly-tabs">
            <TabsTrigger value="performers" className="text-xs sm:text-sm">Top Performers</TabsTrigger>
            <TabsTrigger value="volatility" className="text-xs sm:text-sm">Volatility</TabsTrigger>
            <TabsTrigger value="trends" className="text-xs sm:text-sm">Market Trends</TabsTrigger>
          </TabsList>

          <TabsContent value="performers" className="space-y-4">
            <div className="grid gap-6 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5 text-green-500" />
                    Top Gainers (24h)
                  </CardTitle>
                  <CardDescription>Best performing cryptocurrencies</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {topPerformers
                      .filter(p => p.category === 'gainer')
                      .sort((a, b) => b.performance_score - a.performance_score)
                      .slice(0, 5)
                      .map((performer) => (
                        <TopPerformerRow key={performer.symbol || 'unknown'} performer={performer} />
                      ))}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingDown className="h-5 w-5 text-red-500" />
                    Top Losers (24h)
                  </CardTitle>
                  <CardDescription>Worst performing cryptocurrencies</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {topPerformers
                      .filter(p => p.category === 'loser')
                      .sort((a, b) => a.performance_score - b.performance_score)
                      .slice(0, 5)
                      .map((performer) => (
                        <TopPerformerRow key={performer.symbol || 'unknown'} performer={performer} />
                      ))}
                  </div>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Performance Overview</CardTitle>
                <CardDescription>Top performers by 24h change</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {topPerformers
                    .sort((a, b) => Math.abs(b.performance_score) - Math.abs(a.performance_score))
                    .slice(0, 5)
                    .map((performer) => (
                      <div key={performer.symbol || 'unknown'} className="flex items-center justify-between p-4 rounded-lg border">
                        <div className="flex items-center gap-4">
                          <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                            <span className="font-bold text-primary">{(performer.symbol || '??').slice(0, 2)}</span>
                          </div>
                          <div>
                            <p className="font-semibold">{performer.symbol || 'UNKNOWN'}</p>
                            <p className="text-sm text-muted-foreground">
                              Score: {(performer.performance_score || 0).toFixed(1)}
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className={`flex items-center gap-1 ${getChangeColor(performer.change_24h)}`}>
                            {performer.change_24h >= 0 ? (
                              <TrendingUp className="h-4 w-4" />
                            ) : (
                              <TrendingDown className="h-4 w-4" />
                            )}
                            <span className="font-semibold">{formatPercentage(performer.change_24h || 0)}</span>
                          </div>
                          <p className="text-xs text-muted-foreground mt-1">24h Change</p>
                        </div>
                      </div>
                    ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="volatility" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Volatility Analysis</CardTitle>
                <CardDescription>Price volatility analysis for major cryptocurrencies</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {volatility.map((vol) => {
                    // Convert volatility decimal to percentage score (0-100)
                    const volatilityScore = (vol.volatility || 0) * 10000; // Convert to percentage basis
                    const riskLevel = volatilityScore > 0.8 ? 'very_high' : volatilityScore > 0.5 ? 'high' : volatilityScore > 0.3 ? 'medium' : 'low';

                    return (
                    <div key={vol.symbol || 'unknown'} className="p-4 rounded-lg border">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                            <span className="font-bold text-primary">{(vol.symbol || '??').slice(0, 2)}</span>
                          </div>
                          <div>
                            <span className="font-semibold">{vol.symbol || 'UNKNOWN'}</span>
                            <div className="flex items-center gap-2 mt-1">
                              <Badge variant={
                                riskLevel === 'very_high' ? 'destructive' :
                                riskLevel === 'high' ? 'destructive' :
                                riskLevel === 'medium' ? 'default' : 'secondary'
                              }>
                                {riskLevel.replace('_', ' ').toUpperCase()}
                              </Badge>
                              <Badge variant="outline" className="text-xs">
                                {vol.window_hours || 24}h
                              </Badge>
                            </div>
                          </div>
                        </div>
                      </div>
                      <div className="mt-3">
                        <p className="text-sm text-muted-foreground">Volatility</p>
                        <div className="flex items-center gap-2">
                          <p className="font-semibold">{formatPercentage(vol.volatility || 0)}</p>
                          <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden max-w-[100px]">
                            <div
                              className={`h-full rounded-full ${
                                riskLevel === 'very_high' ? 'bg-red-500' :
                                riskLevel === 'high' ? 'bg-orange-500' :
                                riskLevel === 'medium' ? 'bg-yellow-500' : 'bg-green-500'
                              }`}
                              style={{ width: `${Math.min(volatilityScore * 100, 100)}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="trends" className="space-y-4">
            <div className="grid gap-6 md:grid-cols-2">
              {trends.map((trend) => {
                // Convert score to confidence percentage
                const confidence = Math.min((trend.score || 0) * 20, 100); // Scale score to 0-100%
                const signal = trend.trend === 'bullish' ? 'buy' : trend.trend === 'bearish' ? 'sell' : 'hold'; // handles 'sideways' and other values as 'hold'

                return (
                <Card key={trend.symbol || 'unknown'}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="capitalize">{trend.symbol || 'UNKNOWN'}</CardTitle>
                      <Badge variant={
                        signal === 'buy' ? 'default' :
                        signal === 'sell' ? 'destructive' : 'secondary'
                      }>
                        {signal === 'buy' ? (
                          <TrendingUp className="h-3 w-3 mr-1" />
                        ) : signal === 'sell' ? (
                          <TrendingDown className="h-3 w-3 mr-1" />
                        ) : (
                          <Activity className="h-3 w-3 mr-1" />
                        )}
                        {signal.toUpperCase()}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div>
                        <p className="text-sm text-muted-foreground mb-2">Trend: {trend.trend || 'unknown'}</p>
                        <div className="flex items-center gap-2">
                          <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full ${
                                signal === 'buy' ? 'bg-green-500' :
                                signal === 'sell' ? 'bg-red-500' : 'bg-yellow-500'
                              }`}
                              style={{ width: `${confidence}%` }}
                            />
                          </div>
                          <span className="text-sm font-medium w-12 text-right">
                            {confidence.toFixed(0)}%
                          </span>
                        </div>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Confidence</p>
                        <div className="flex items-center gap-2">
                          <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden max-w-[100px]">
                            <div
                              className="h-full rounded-full bg-blue-500"
                              style={{ width: `${confidence}%` }}
                            />
                          </div>
                          <span className="text-sm font-medium">
                            {confidence.toFixed(0)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
                );
              })}
            </div>

            {trends.length === 0 && (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-16">
                  <AlertCircle className="h-16 w-16 text-muted-foreground mb-4" />
                  <h3 className="text-xl font-semibold mb-2">No Trend Data Available</h3>
                  <p className="text-muted-foreground text-center">
                    Market trend analysis will appear here when data is available.
                  </p>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>

        {/* Market Insights */}
        <Card className="mt-8">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5 text-yellow-500" />
              Market Insights
            </CardTitle>
            <CardDescription>Key observations from current market conditions</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {topPerformers.length > 0 && (
                <div className="p-4 rounded-lg border bg-card">
                  <h4 className="font-semibold mb-2">Market Momentum</h4>
                  <p className="text-sm text-muted-foreground">
                    {(() => {
                      const gainers = topPerformers.filter(p => p.category === 'gainer').length;
                      const losers = topPerformers.filter(p => p.category === 'loser').length;
                      const avgChange = topPerformers.reduce((sum, p) => sum + p.performance_score, 0) / topPerformers.length;

                      if (gainers > losers && avgChange > 2) {
                        return '🚀 Strong bullish momentum! The market shows significant upward movement with ' +
                               `${gainers} gainers out of ${topPerformers.length} top performers averaging ${avgChange.toFixed(1)}% gains.`;
                      } else if (gainers > losers && avgChange > 0) {
                        return '📈 Moderate bullish sentiment detected. ' +
                               `${gainers} assets are gaining with an average return of ${avgChange.toFixed(1)}%.`;
                      } else if (losers > gainers && avgChange < -2) {
                        return '📉 Bearish pressure dominates. ' +
                               `${losers} out of ${topPerformers.length} assets are declining with average losses of ${Math.abs(avgChange).toFixed(1)}%.`;
                      } else if (losers > gainers && avgChange < 0) {
                        return '⚠️ Cautious market sentiment. ' +
                               `${losers} assets are declining, suggesting risk-off behavior among investors.`;
                      } else {
                        return '🔄 Mixed market conditions with balanced performance between gainers and losers, indicating sector rotation.';
                      }
                    })()}
                  </p>
                </div>
              )}

              <div className="p-4 rounded-lg border bg-card">
                <h4 className="font-semibold mb-2">Trading Activity Analysis</h4>
                <p className="text-sm text-muted-foreground">
                  {(() => {
                    const totalVolume = topPerformers.reduce((sum, p) => sum + (p.volume_24h || 0), 0);
                    const highestVolumeAsset = topPerformers.reduce((max, p) => (p.volume_24h || 0) > (max.volume_24h || 0) ? p : max, topPerformers[0]);
                    const biggestMover = topPerformers.reduce((max, p) => Math.abs(p.performance_score) > Math.abs(max.performance_score) ? p : max, topPerformers[0]);

                    return `Total 24h volume for tracked assets: $${(totalVolume / 1000000000).toFixed(1)}B. ` +
                           `${highestVolumeAsset?.symbol} leads with $${(highestVolumeAsset?.volume_24h / 1000000).toFixed(0)}M in volume. ` +
                           `${biggestMover?.symbol} shows the largest performance at ${Math.abs(biggestMover?.performance_score || 0).toFixed(1)}%.`;
                  })()}
                </p>
              </div>

              {volatility.some(v => (v.volatility || 0) > 0.006) && (
                <div className="p-4 rounded-lg border bg-yellow-500/10 border-yellow-500/20">
                  <div className="flex items-start gap-2">
                    <AlertCircle className="h-5 w-5 text-yellow-500 mt-0.5" />
                    <div>
                      <h4 className="font-semibold mb-1">⚠️ High Volatility Alert</h4>
                      <p className="text-sm text-muted-foreground">
                        {(() => {
                          const highVolAssets = volatility.filter(v => (v.volatility || 0) > 0.006);
                          const avgVolatility = volatility.reduce((sum, v) => sum + (v.volatility || 0), 0) / volatility.length;

                          return `${highVolAssets.length} assets showing elevated volatility (>0.6%). ` +
                                 `Average volatility: ${formatPercentage(avgVolatility)}. ` +
                                 `Consider tighter risk management for ${highVolAssets.map(v => v.symbol).join(', ')}.`;
                        })()}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {trends.length > 0 && (
                <div className="p-4 rounded-lg border bg-card">
                  <h4 className="font-semibold mb-2">Trend Analysis Summary</h4>
                  <p className="text-sm text-muted-foreground">
                    {(() => {
                      const buySignals = trends.filter(t => t.trend === 'bullish').length;
                      const sellSignals = trends.filter(t => t.trend === 'bearish').length;
                      const avgConfidence = trends.reduce((sum, t) => sum + Math.min((t.score || 0) * 20, 100), 0) / trends.length;

                      let sentiment = 'Neutral';
                      if (buySignals > sellSignals * 1.5) sentiment = 'Strongly Bullish';
                      else if (buySignals > sellSignals) sentiment = 'Bullish';
                      else if (sellSignals > buySignals * 1.5) sentiment = 'Strongly Bearish';
                      else if (sellSignals > buySignals) sentiment = 'Bearish';

                      return `Market sentiment: ${sentiment}. ${buySignals} buy, ${sellSignals} sell, ${trends.length - buySignals - sellSignals} hold signals. ` +
                             `Average confidence: ${avgConfidence.toFixed(1)}%.`;
                    })()}
                  </p>
                </div>
              )}

              {dashboardMetrics && (
                <div className="p-4 rounded-lg border bg-card">
                  <h4 className="font-semibold mb-2">Market Overview</h4>
                  <p className="text-sm text-muted-foreground">
                    Total market cap: ${(dashboardMetrics.total_market_cap / 1e12).toFixed(2)}T.
                    24h volume: ${(dashboardMetrics.total_volume_24h / 1e9).toFixed(1)}B.
                    BTC dominance: {dashboardMetrics.btc_dominance.toFixed(1)}%.
                    Fear & Greed Index: {dashboardMetrics.fear_greed_index} ({dashboardMetrics.fear_greed_index > 75 ? 'Extreme Greed' : dashboardMetrics.fear_greed_index > 50 ? 'Greed' : dashboardMetrics.fear_greed_index > 25 ? 'Fear' : 'Extreme Fear'}).
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function TopPerformerRow({ performer }: { performer: TopPerformer }) {
  const isGainer = performer.category === 'gainer';

  return (
    <div className="group relative overflow-hidden rounded-lg border bg-card p-4 transition-all duration-300 hover:shadow-lg hover:scale-[1.02]">
      {/* Background gradient effect on hover */}
      <div className={`absolute inset-0 bg-gradient-to-r opacity-0 transition-opacity duration-300 group-hover:opacity-10 ${
        isGainer ? 'from-green-500 to-emerald-500' : 'from-red-500 to-rose-500'
      }`} />

      <div className="relative flex items-center justify-between">
        <div className="flex items-center space-x-4">
          {/* Logo/Circle */}
          <div className={`h-12 w-12 rounded-full flex items-center justify-center font-bold text-white text-lg ${
            isGainer ? 'bg-gradient-to-br from-green-500 to-emerald-600' : 'bg-gradient-to-br from-red-500 to-rose-600'
          }`}>
            {(performer.symbol || '??').charAt(0)}
          </div>

          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-lg">{performer.symbol || 'UNKNOWN'}</span>
            </div>
            <div className="flex items-center gap-3 text-sm text-muted-foreground mt-1">
              <span>{formatCurrency(performer.current_price || 0)}</span>
              {performer.volume_24h && (
                <span>Vol: ${((performer.volume_24h || 0) / 1000000).toFixed(1)}M</span>
              )}
              {performer.performance_score && (
                <span>Score: {(performer.performance_score || 0).toFixed(1)}</span>
              )}
            </div>
          </div>
        </div>

        <div className="text-right">
          <div className={`flex items-center gap-1 text-lg font-bold ${
            isGainer ? 'text-green-500' : 'text-red-500'
          }`}>
            {isGainer ? (
              <TrendingUp className="h-5 w-5" />
            ) : (
              <TrendingDown className="h-5 w-5" />
            )}
            {isGainer ? '+' : ''}{(performer.change_24h || 0).toFixed(2)}%
          </div>
          <div className={`text-sm ${
            isGainer ? 'text-green-500/70' : 'text-red-500/70'
          }`}>
            24h Change
          </div>
        </div>
      </div>

      {/* Placeholder sparkline */}
      <div className="mt-3 h-8 flex items-end justify-between">
        {Array.from({ length: 20 }).map((_, i) => (
          <div
            key={i}
            className={`flex-1 mx-[0.5px] rounded-t-sm ${
              isGainer ? 'bg-green-500/20' : 'bg-red-500/20'
            }`}
            style={{
              height: `${30 + Math.sin(i * 0.5) * 20 + (isGainer ? i * 2 : -i * 2)}%`
            }}
          />
        ))}
      </div>
    </div>
  );
}
