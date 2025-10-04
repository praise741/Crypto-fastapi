'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Wallet, 
  Upload, 
  TrendingUp, 
  TrendingDown,
  PieChart,
  Activity,
  DollarSign
} from 'lucide-react';
import { apiClient } from '@/lib/api-client';
import { formatCurrency, formatPercentage, getChangeColor } from '@/lib/utils';

interface Holding {
  symbol: string;
  amount: number;
  avg_buy_price: number;
  current_price: number;
  value: number;
  profit_loss: number;
  profit_loss_percentage: number;
}

interface Performance {
  total_value: number;
  total_invested: number;
  total_profit_loss: number;
  total_profit_loss_percentage: number;
  best_performer: string;
  worst_performer: string;
  daily_change: number;
  weekly_change: number;
  monthly_change: number;
}

interface Allocation {
  symbol: string;
  percentage: number;
  value: number;
}

export default function PortfolioPage() {
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [performance, setPerformance] = useState<Performance | null>(null);
  const [allocation, setAllocation] = useState<Allocation[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    loadPortfolioData();
  }, []);

  const loadPortfolioData = async () => {
    try {
      const [holdingsRes, performanceRes, allocationRes] = await Promise.all([
        apiClient.getHoldings().catch(() => ({ data: [] })),
        apiClient.getPerformance('30d').catch(() => ({ data: null })),
        apiClient.getAllocation().catch(() => ({ data: [] })),
      ]);

      setHoldings(holdingsRes.data || []);
      setPerformance(performanceRes.data);
      setAllocation(allocationRes.data || []);
    } catch (error) {
      console.error('Failed to load portfolio:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      await apiClient.uploadPortfolio(file);
      await loadPortfolioData();
    } catch (error) {
      console.error('Failed to upload portfolio:', error);
    } finally {
      setUploading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Activity className="h-12 w-12 animate-spin mx-auto mb-4 text-primary" />
          <p className="text-muted-foreground">Loading portfolio...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Portfolio Tracker</h1>
            <p className="text-muted-foreground mt-2">
              Track your holdings with detailed analytics and performance insights
            </p>
          </div>
          <div>
            <input
              type="file"
              accept=".csv"
              onChange={handleFileUpload}
              className="hidden"
              id="portfolio-upload"
            />
            <Button asChild disabled={uploading}>
              <label htmlFor="portfolio-upload" className="cursor-pointer">
                {uploading ? (
                  <>
                    <Activity className="mr-2 h-4 w-4 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="mr-2 h-4 w-4" />
                    Upload CSV
                  </>
                )}
              </label>
            </Button>
          </div>
        </div>

        {holdings.length === 0 ? (
          <EmptyPortfolio />
        ) : (
          <>
            {/* Performance Summary */}
            {performance && (
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-8">
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Total Value</CardTitle>
                    <DollarSign className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {formatCurrency(performance.total_value)}
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      Invested: {formatCurrency(performance.total_invested)}
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Total P&L</CardTitle>
                    <Activity className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className={`text-2xl font-bold ${getChangeColor(performance.total_profit_loss)}`}>
                      {formatCurrency(performance.total_profit_loss)}
                    </div>
                    <p className={`text-xs mt-1 ${getChangeColor(performance.total_profit_loss_percentage)}`}>
                      {formatPercentage(performance.total_profit_loss_percentage)}
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Best Performer</CardTitle>
                    <TrendingUp className="h-4 w-4 text-green-500" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold text-green-500">
                      {performance.best_performer}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Worst Performer</CardTitle>
                    <TrendingDown className="h-4 w-4 text-red-500" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold text-red-500">
                      {performance.worst_performer}
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Main Content */}
            <Tabs defaultValue="holdings" className="space-y-4">
              <TabsList>
                <TabsTrigger value="holdings">Holdings</TabsTrigger>
                <TabsTrigger value="allocation">Allocation</TabsTrigger>
                <TabsTrigger value="performance">Performance</TabsTrigger>
              </TabsList>

              <TabsContent value="holdings" className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Your Holdings</CardTitle>
                    <CardDescription>Current portfolio positions</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {holdings.map((holding) => (
                        <HoldingRow key={holding.symbol} holding={holding} />
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="allocation" className="space-y-4">
                <div className="grid gap-6 md:grid-cols-2">
                  <Card>
                    <CardHeader>
                      <CardTitle>Asset Allocation</CardTitle>
                      <CardDescription>Portfolio distribution by value</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        {allocation.map((item) => (
                          <div key={item.symbol} className="space-y-2">
                            <div className="flex items-center justify-between text-sm">
                              <span className="font-medium">{item.symbol}</span>
                              <span className="text-muted-foreground">
                                {item.percentage.toFixed(2)}%
                              </span>
                            </div>
                            <div className="h-2 bg-muted rounded-full overflow-hidden">
                              <div 
                                className="h-full bg-primary rounded-full"
                                style={{ width: `${item.percentage}%` }}
                              />
                            </div>
                            <p className="text-xs text-muted-foreground">
                              {formatCurrency(item.value)}
                            </p>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>Diversification Analysis</CardTitle>
                      <CardDescription>Portfolio concentration metrics</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <div className="flex justify-between items-center p-4 rounded-lg border">
                          <div>
                            <p className="text-sm font-medium">Number of Assets</p>
                            <p className="text-2xl font-bold">{holdings.length}</p>
                          </div>
                          <PieChart className="h-8 w-8 text-muted-foreground" />
                        </div>

                        <div className="p-4 rounded-lg border">
                          <p className="text-sm font-medium mb-2">Concentration Risk</p>
                          {allocation[0] && (
                            <div className="space-y-1">
                              <p className="text-xs text-muted-foreground">
                                Top asset: {allocation[0].symbol} ({allocation[0].percentage.toFixed(1)}%)
                              </p>
                              <Badge variant={
                                allocation[0].percentage > 50 ? 'destructive' :
                                allocation[0].percentage > 30 ? 'secondary' : 'default'
                              }>
                                {allocation[0].percentage > 50 ? 'High Risk' :
                                 allocation[0].percentage > 30 ? 'Moderate' : 'Well Diversified'}
                              </Badge>
                            </div>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>

              <TabsContent value="performance" className="space-y-4">
                {performance && (
                  <div className="grid gap-6 md:grid-cols-3">
                    <Card>
                      <CardHeader>
                        <CardTitle>24h Change</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className={`text-3xl font-bold ${getChangeColor(performance.daily_change)}`}>
                          {formatPercentage(performance.daily_change)}
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle>7d Change</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className={`text-3xl font-bold ${getChangeColor(performance.weekly_change)}`}>
                          {formatPercentage(performance.weekly_change)}
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle>30d Change</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className={`text-3xl font-bold ${getChangeColor(performance.monthly_change)}`}>
                          {formatPercentage(performance.monthly_change)}
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                )}
              </TabsContent>
            </Tabs>
          </>
        )}
      </div>
    </div>
  );
}

function HoldingRow({ holding }: { holding: Holding }) {
  return (
    <div className="flex items-center justify-between p-4 rounded-lg border hover:bg-accent/50 transition-colors">
      <div className="flex items-center gap-4">
        <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
          <span className="font-bold text-primary">{holding.symbol.slice(0, 2)}</span>
        </div>
        <div>
          <p className="font-semibold">{holding.symbol}</p>
          <p className="text-sm text-muted-foreground">
            {holding.amount.toFixed(4)} @ {formatCurrency(holding.avg_buy_price)}
          </p>
        </div>
      </div>

      <div className="text-right">
        <p className="font-semibold">{formatCurrency(holding.value)}</p>
        <div className="flex items-center gap-2 justify-end">
          {holding.profit_loss >= 0 ? (
            <TrendingUp className="h-4 w-4 text-green-500" />
          ) : (
            <TrendingDown className="h-4 w-4 text-red-500" />
          )}
          <span className={`text-sm font-medium ${getChangeColor(holding.profit_loss)}`}>
            {formatCurrency(holding.profit_loss)} ({formatPercentage(holding.profit_loss_percentage)})
          </span>
        </div>
      </div>
    </div>
  );
}

function EmptyPortfolio() {
  return (
    <Card>
      <CardContent className="flex flex-col items-center justify-center py-16">
        <Wallet className="h-16 w-16 text-muted-foreground mb-4" />
        <h3 className="text-xl font-semibold mb-2">No Portfolio Data</h3>
        <p className="text-muted-foreground text-center max-w-md mb-6">
          Upload a CSV file with your holdings to start tracking your portfolio performance and get detailed analytics.
        </p>
        <div className="text-sm text-muted-foreground">
          <p className="mb-2">CSV format: symbol, amount, avg_buy_price</p>
          <p>Example: BTC, 0.5, 45000</p>
        </div>
      </CardContent>
    </Card>
  );
}
