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

interface TopPerformer {
  symbol: string;
  price: number;
  change_24h: number;
  volume_24h: number;
  market_cap: number;
}

interface Volatility {
  symbol: string;
  volatility_24h: number;
  volatility_7d: number;
  volatility_30d: number;
  risk_level: 'low' | 'medium' | 'high';
}

interface Trend {
  category: string;
  trend: 'bullish' | 'bearish' | 'neutral';
  strength: number;
  description: string;
}

interface Index {
  name: string;
  value: number;
  change_24h: number;
  classification: string;
}

export default function AnalyticsPage() {
  const [topPerformers, setTopPerformers] = useState<TopPerformer[]>([]);
  const [volatility, setVolatility] = useState<Volatility[]>([]);
  const [trends, setTrends] = useState<Trend[]>([]);
  const [indices, setIndices] = useState<Index[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAnalyticsData();
  }, []);

  const loadAnalyticsData = async () => {
    try {
      const [performersRes, volatilityRes, trendsRes, indicesRes] = await Promise.all([
        apiClient.getTopPerformers(10).catch(() => ({ data: [] })),
        apiClient.getVolatility().catch(() => ({ data: [] })),
        apiClient.getTrends().catch(() => ({ data: [] })),
        apiClient.getIndices().catch(() => ({ data: [] })),
      ]);

      setTopPerformers(performersRes.data || []);
      setVolatility(volatilityRes.data || []);
      setTrends(trendsRes.data || []);
      setIndices(indicesRes.data || []);
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
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight">Market Analytics</h1>
          <p className="text-muted-foreground mt-2">
            Advanced market insights and trend analysis
          </p>
        </div>

        {/* Market Indices */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-8">
          {indices.map((index) => (
            <Card key={index.name}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{index.name}</CardTitle>
                <BarChart3 className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{index.value}</div>
                <div className="flex items-center gap-2 mt-1">
                  <span className={`text-xs font-medium ${getChangeColor(index.change_24h)}`}>
                    {formatPercentage(index.change_24h)}
                  </span>
                  <Badge variant="outline" className="text-xs">
                    {index.classification}
                  </Badge>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Main Content */}
        <Tabs defaultValue="performers" className="space-y-4">
          <TabsList>
            <TabsTrigger value="performers">Top Performers</TabsTrigger>
            <TabsTrigger value="volatility">Volatility</TabsTrigger>
            <TabsTrigger value="trends">Market Trends</TabsTrigger>
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
                      .filter(p => p.change_24h > 0)
                      .sort((a, b) => b.change_24h - a.change_24h)
                      .slice(0, 5)
                      .map((performer) => (
                        <PerformerRow key={performer.symbol} performer={performer} />
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
                      .filter(p => p.change_24h < 0)
                      .sort((a, b) => a.change_24h - b.change_24h)
                      .slice(0, 5)
                      .map((performer) => (
                        <PerformerRow key={performer.symbol} performer={performer} />
                      ))}
                  </div>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Volume Leaders</CardTitle>
                <CardDescription>Highest trading volume in 24h</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {topPerformers
                    .sort((a, b) => b.volume_24h - a.volume_24h)
                    .slice(0, 5)
                    .map((performer) => (
                      <div key={performer.symbol} className="flex items-center justify-between p-4 rounded-lg border">
                        <div className="flex items-center gap-4">
                          <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                            <span className="font-bold text-primary">{performer.symbol.slice(0, 2)}</span>
                          </div>
                          <div>
                            <p className="font-semibold">{performer.symbol}</p>
                            <p className="text-sm text-muted-foreground">{formatCurrency(performer.price)}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="font-semibold">{formatCurrency(performer.volume_24h, 0)}</p>
                          <p className="text-xs text-muted-foreground">24h Volume</p>
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
                <CardDescription>Price volatility across different timeframes</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {volatility.map((vol) => (
                    <div key={vol.symbol} className="p-4 rounded-lg border">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                            <span className="font-bold text-primary">{vol.symbol.slice(0, 2)}</span>
                          </div>
                          <span className="font-semibold">{vol.symbol}</span>
                        </div>
                        <Badge variant={
                          vol.risk_level === 'low' ? 'default' :
                          vol.risk_level === 'medium' ? 'secondary' : 'destructive'
                        }>
                          {vol.risk_level.toUpperCase()} RISK
                        </Badge>
                      </div>
                      <div className="grid grid-cols-3 gap-4 text-sm">
                        <div>
                          <p className="text-muted-foreground">24h</p>
                          <p className="font-semibold">{vol.volatility_24h.toFixed(2)}%</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">7d</p>
                          <p className="font-semibold">{vol.volatility_7d.toFixed(2)}%</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">30d</p>
                          <p className="font-semibold">{vol.volatility_30d.toFixed(2)}%</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="trends" className="space-y-4">
            <div className="grid gap-6 md:grid-cols-2">
              {trends.map((trend, index) => (
                <Card key={index}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="capitalize">{trend.category}</CardTitle>
                      <Badge variant={
                        trend.trend === 'bullish' ? 'default' :
                        trend.trend === 'bearish' ? 'destructive' : 'secondary'
                      }>
                        {trend.trend === 'bullish' ? (
                          <TrendingUp className="h-3 w-3 mr-1" />
                        ) : trend.trend === 'bearish' ? (
                          <TrendingDown className="h-3 w-3 mr-1" />
                        ) : (
                          <Activity className="h-3 w-3 mr-1" />
                        )}
                        {trend.trend.toUpperCase()}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div>
                        <p className="text-sm text-muted-foreground mb-2">Trend Strength</p>
                        <div className="flex items-center gap-2">
                          <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                            <div 
                              className={`h-full rounded-full ${
                                trend.trend === 'bullish' ? 'bg-green-500' :
                                trend.trend === 'bearish' ? 'bg-red-500' : 'bg-yellow-500'
                              }`}
                              style={{ width: `${trend.strength}%` }}
                            />
                          </div>
                          <span className="text-sm font-medium w-12 text-right">
                            {trend.strength}%
                          </span>
                        </div>
                      </div>
                      <p className="text-sm">{trend.description}</p>
                    </div>
                  </CardContent>
                </Card>
              ))}
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
                    {topPerformers.filter(p => p.change_24h > 0).length > topPerformers.length / 2
                      ? 'The market is showing bullish momentum with more gainers than losers in the top performers.'
                      : 'The market is experiencing bearish pressure with more assets declining than advancing.'}
                  </p>
                </div>
              )}
              
              <div className="p-4 rounded-lg border bg-card">
                <h4 className="font-semibold mb-2">Trading Activity</h4>
                <p className="text-sm text-muted-foreground">
                  High trading volumes indicate strong market participation and liquidity across major cryptocurrencies.
                </p>
              </div>

              {volatility.some(v => v.risk_level === 'high') && (
                <div className="p-4 rounded-lg border bg-yellow-500/10 border-yellow-500/20">
                  <div className="flex items-start gap-2">
                    <AlertCircle className="h-5 w-5 text-yellow-500 mt-0.5" />
                    <div>
                      <h4 className="font-semibold mb-1">High Volatility Alert</h4>
                      <p className="text-sm text-muted-foreground">
                        Several assets are showing elevated volatility. Exercise caution and consider risk management strategies.
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function PerformerRow({ performer }: { performer: TopPerformer }) {
  return (
    <div className="flex items-center justify-between p-4 rounded-lg border hover:bg-accent/50 transition-colors">
      <div className="flex items-center gap-3">
        <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
          <span className="font-bold text-primary">{performer.symbol.slice(0, 2)}</span>
        </div>
        <div>
          <p className="font-semibold">{performer.symbol}</p>
          <p className="text-sm text-muted-foreground">{formatCurrency(performer.price)}</p>
        </div>
      </div>
      <div className="text-right">
        <div className={`flex items-center gap-1 ${getChangeColor(performer.change_24h)}`}>
          {performer.change_24h >= 0 ? (
            <TrendingUp className="h-4 w-4" />
          ) : (
            <TrendingDown className="h-4 w-4" />
          )}
          <span className="font-semibold">{formatPercentage(performer.change_24h)}</span>
        </div>
        <p className="text-xs text-muted-foreground mt-1">
          MCap: {formatCurrency(performer.market_cap, 0)}
        </p>
      </div>
    </div>
  );
}
