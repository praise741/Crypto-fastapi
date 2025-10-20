'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import {
  TrendingUp,
  TrendingDown,
  Activity,
  Search,
  ArrowUpRight,
  BarChart3,
  Zap,
  Star
} from 'lucide-react';
import { formatCurrency, formatPercentage, getChangeColor } from '@/lib/utils';

interface TrendingToken {
  symbol: string;
  price: number;
  change_24h: number;
  volume_24h: number;
  trend_score: number;
  timestamp: string;
}

export default function Home() {
  const [trendingTokens, setTrendingTokens] = useState<TrendingToken[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchSymbol, setSearchSymbol] = useState('');

  useEffect(() => {
    loadTrendingTokens();
  }, []);

  const loadTrendingTokens = async () => {
    try {
      const response = await fetch('https://api-102-212-247-217.sslip.io/api/v1/market/trending').then(r => r.json());
      if ((response as { success?: boolean; data?: { trending_tokens?: TrendingToken[] } }).success) {
        const data = response as { success?: boolean; data?: { trending_tokens?: TrendingToken[] } };
        setTrendingTokens(data.data?.trending_tokens || []);
      }
    } catch (error) {
      console.error('Failed to load trending tokens:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    if (searchSymbol.trim()) {
      // Store the contract address in localStorage and redirect to token-health
      localStorage.setItem('pendingContractAddress', searchSymbol.trim());
      window.location.href = `/token-health`;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/10">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 py-16">
          <div className="text-center">
            <div className="flex justify-center mb-6">
              <div className="relative">
                <div className="absolute inset-0 bg-primary/20 blur-xl rounded-full" />
                <div className="relative bg-primary text-primary-foreground rounded-full p-4">
                  <BarChart3 className="h-12 w-12" />
                </div>
              </div>
            </div>

            <h1 className="font-heading text-4xl sm:text-5xl font-bold tracking-tight mb-4">
              AI‑Powered
              <span className="text-primary"> Crypto Analytics</span>
            </h1>

            <p className="font-subheading text-base sm:text-lg text-muted-foreground mb-10 max-w-2xl mx-auto leading-relaxed">
              Get real-time market insights, AI predictions, and comprehensive token analysis
              to make smarter trading decisions.
            </p>

            {/* Quick Search */}
            <div className="max-w-xl mx-auto mb-12">
              <div className="flex gap-2">
                <Input
                  placeholder="Enter contract address (0x...)"
                  value={searchSymbol}
                  onChange={(e) => setSearchSymbol(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                  className="flex-1 h-11 rounded-lg"
                />
                <Button onClick={handleSearch} className="px-6 h-11 rounded-lg">
                  <Search className="h-4 w-4 mr-2" />
                  Analyze
                </Button>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 sm:gap-5 max-w-4xl mx-auto mb-16">
              <Link href="/predictions">
                <Card className="w-full h-20 hover:border-primary/40 transition border-border/60 bg-card/60 backdrop-blur supports-[backdrop-filter]:bg-card/50">
                  <CardContent className="h-20 flex items-center justify-center gap-2">
                    <TrendingUp className="h-5 w-5" />
                    <span className="text-sm font-medium">Predictions</span>
                  </CardContent>
                </Card>
              </Link>
              <Link href="/analytics">
                <Card className="w-full h-20 hover:border-primary/40 transition border-border/60 bg-card/60 backdrop-blur supports-[backdrop-filter]:bg-card/50">
                  <CardContent className="h-20 flex items-center justify-center gap-2">
                    <Activity className="h-5 w-5" />
                    <span className="text-sm font-medium">Analytics</span>
                  </CardContent>
                </Card>
              </Link>
              <Link href="/token-health">
                <Card className="w-full h-20 hover:border-primary/40 transition border-border/60 bg-card/60 backdrop-blur supports-[backdrop-filter]:bg-card/50">
                  <CardContent className="h-20 flex items-center justify-center gap-2">
                    <Zap className="h-5 w-5" />
                    <span className="text-sm font-medium">Token Health</span>
                  </CardContent>
                </Card>
              </Link>
              <Link href="/news">
                <Card className="w-full h-20 hover:border-primary/40 transition border-border/60 bg-card/60 backdrop-blur supports-[backdrop-filter]:bg-card/50">
                  <CardContent className="h-20 flex items-center justify-center gap-2">
                    <Star className="h-5 w-5" />
                    <span className="text-sm font-medium">News</span>
                  </CardContent>
                </Card>
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Trending Tokens Section */}
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 pb-16">
        <Card className="mb-16 border-border/60 bg-card/60 backdrop-blur supports-[backdrop-filter]:bg-card/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-primary" />
              🔥 Trending Tokens Now
            </CardTitle>
            <CardDescription>
              Top trending cryptocurrencies based on volume and price movement
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <Activity className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : trendingTokens.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                No trending data available
              </div>
            ) : (
              <div className="grid gap-5 sm:gap-6 md:grid-cols-2 lg:grid-cols-3">
                {trendingTokens.map((token, index) => (
                  <Card key={token.symbol} className="relative overflow-hidden border-border/60 bg-card hover:border-primary/40 transition">
                    {index === 0 && (
                      <div className="absolute top-2 right-2">
                        <Badge className="bg-gradient-to-r from-yellow-500 to-orange-500 text-white">
                          <Star className="h-3 w-3 mr-1" />
                          #1 Trending
                        </Badge>
                      </div>
                    )}
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between mb-4">
                        <div>
                          <h3 className="font-heading font-semibold text-lg tracking-tight">{token.symbol}</h3>
                          <p className="text-xs text-muted-foreground">
                            Score: {token.trend_score.toFixed(0)}
                          </p>
                        </div>
                        <div className={`text-right ${getChangeColor(token.change_24h)}`}>
                          <div className="flex items-center gap-1">
                            {token.change_24h >= 0 ? (
                              <TrendingUp className="h-4 w-4" />
                            ) : (
                              <TrendingDown className="h-4 w-4" />
                            )}
                            <span className="font-semibold">
                              {formatPercentage(token.change_24h)}
                            </span>
                          </div>
                          <p className="text-[11px] text-muted-foreground mt-1">24h Change</p>
                        </div>
                      </div>

                      <div className="flex items-center justify-between mb-4">
                        <div>
                          <p className="text-sm text-muted-foreground">Current Price</p>
                          <p className="font-semibold tracking-tight">{formatCurrency(token.price)}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm text-muted-foreground">24h Volume</p>
                          <p className="font-semibold tracking-tight">
                            ${(token.volume_24h / 1e9).toFixed(1)}B
                          </p>
                        </div>
                      </div>

                      <Link href={`/predictions?symbol=${token.symbol}`}>
                        <Button className="w-full rounded-md">
                          <ArrowUpRight className="h-4 w-4 mr-2" />
                          Get AI Prediction
                        </Button>
                      </Link>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Features Grid */}
        <div className="grid md:grid-cols-3 gap-6 sm:gap-8">
          <Card className="border-border/60 bg-card/60 backdrop-blur supports-[backdrop-filter]:bg-card/50 h-full flex flex-col">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 font-heading">
                <TrendingUp className="h-5 w-5 text-green-500" />
                AI Predictions
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col justify-between">
              <p className="text-muted-foreground mb-5 font-subheading leading-relaxed">
                Get accurate price predictions powered by advanced machine learning models.
              </p>
              <Link href="/predictions">
                <Button variant="outline" className="w-full rounded-md mt-auto">
                  View Predictions
                </Button>
              </Link>
            </CardContent>
          </Card>

          <Card className="border-border/60 bg-card/60 backdrop-blur supports-[backdrop-filter]:bg-card/50 h-full flex flex-col">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 font-heading">
                <Activity className="h-5 w-5 text-blue-500" />
                Market Analytics
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col justify-between">
              <p className="text-muted-foreground mb-5 font-subheading leading-relaxed">
                Comprehensive market analysis with volatility metrics and trend indicators.
              </p>
              <Link href="/analytics">
                <Button variant="outline" className="w-full rounded-md mt-auto">
                  View Analytics
                </Button>
              </Link>
            </CardContent>
          </Card>

          <Card className="border-border/60 bg-card/60 backdrop-blur supports-[backdrop-filter]:bg-card/50 h-full flex flex-col">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 font-heading">
                <Zap className="h-5 w-5 text-yellow-500" />
                Token Health
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col justify-between">
              <p className="text-muted-foreground mb-5 font-subheading leading-relaxed">
                Analyze token safety, liquidity, and potential risks before investing.
              </p>
              <Link href="/token-health">
                <Button variant="outline" className="w-full rounded-md mt-auto">
                  Check Tokens
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

