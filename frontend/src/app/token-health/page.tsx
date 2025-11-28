'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
// Removed unused select imports
import { Shield, Activity, AlertTriangle, CheckCircle, Search, RefreshCw, TrendingUp, Lock, DollarSign } from 'lucide-react';
import { apiClient } from '@/lib/api-client';
import { ProtectedRoute } from '@/components/auth/protected-route';


interface TokenAnalytics {
  contract_address: string;
  symbol: string;
  name: string;
  chain_id: number | string; // numeric for EVM chains or string key for non‑EVM
  chain_name?: string; // friendly chain name when provided by backend
  price_usd: number | null;
  liquidity_usd: number | null;
  volume_24h: number | null;
  market_cap: number | null;
  holders_count: number | null;
  contract_verified: boolean;
  renounced_ownership: boolean;
  mintable: boolean;
  blacklist_function: boolean;
  hidden_taxes: boolean;
  honeypot_risk: boolean;
  pump_dump_risk: number;
  buy_tax: number | null;
  sell_tax: number | null;
  transfer_tax: number | null;
  liquidity_locked: boolean;
  liquidity_lock_percentage: number;
  lp_burned: boolean;
  buys_24h: number | null;
  sells_24h: number | null;
  total_transactions_24h: number;
  overall_security_score: number;
  liquidity_score: number;
  contract_safety_score: number;
  holder_distribution_score: number;
  trading_activity_score: number;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  warnings: string[];
  strengths: string[];
  recommendation: string;
  created_at: string | null;
  last_updated: string;
  data_sources: string[];
}

// Optional backend extensions we might receive
type TaxSource = 'goplus' | '0x' | 'simulated' | string;
type TaxConfidence = 'high' | 'low' | string;
interface TokenAnalyticsExtended extends TokenAnalytics {
  tax_source?: TaxSource;
  tax_confidence?: TaxConfidence;
}

export default function TokenHealthPage() {
  return (
    <ProtectedRoute>
      <TokenHealthContent />
    </ProtectedRoute>
  );
}

function TokenHealthContent() {
  const [contractAddress, setContractAddress] = useState('');
  // Chain ID input removed; backend auto-detects
  const [tokenAnalytics, setTokenAnalytics] = useState<TokenAnalytics | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Check for pending contract address from home page search
  useEffect(() => {
    const pendingAddress = localStorage.getItem('pendingContractAddress');
    if (pendingAddress) {
      setContractAddress(pendingAddress);
      analyzeContract(pendingAddress);
      localStorage.removeItem('pendingContractAddress'); // Clean up after using
    }
  }, []);


  const analyzeContract = async (address: string) => {
    if (!address.trim()) return;

    setLoading(true);
    setError(null);
    setTokenAnalytics(null);

    try {
      const response = await apiClient.analyzeTokenByContract(address, undefined);
      if ((response as { success?: boolean; data?: TokenAnalytics }).success && (response as { success?: boolean; data?: TokenAnalytics }).data) {
        setTokenAnalytics((response as { success?: boolean; data?: TokenAnalytics }).data!);
      } else {
        setError('No data found for this contract address. Please verify the address and chain ID.');
      }
    } catch (apiError: unknown) {
      // Surface backend error details when available (detail or error.message)
      type BackendError = { response?: { data?: { detail?: string; error?: { message?: string } }; status?: number } };
      const err = apiError as BackendError;
      const detail = err?.response?.data?.detail || err?.response?.data?.error?.message;
      console.error('API call failed:', detail || apiError);
      setError(
        detail || 'Failed to analyze contract address. Please verify the address and try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  
  const handleContractSearch = () => {
    analyzeContract(contractAddress);
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-500';
    if (score >= 60) return 'text-yellow-500';
    return 'text-red-500';
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low': return 'bg-green-500/10 text-green-500 border-green-500/20';
      case 'medium': return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20';
      default: return 'bg-red-500/10 text-red-500 border-red-500/20';
    }
  };

  const getScoreBg = (score: number) => {
    if (score >= 80) return 'bg-green-500';
    if (score >= 60) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const formatNumber = (num: number | null, decimals: number = 2) => {
    if (num === null || num === undefined) return 'N/A';
    if (num === 0) return '$0.00';

    // Handle very small numbers (like token prices)
    if (num < 0.01) {
      // Show appropriate decimal places for small numbers
      const absNum = Math.abs(num);
      if (absNum < 0.000001) {
        return `$${num.toExponential(2)}`;
      } else if (absNum < 0.00001) {
        return `$${num.toFixed(8)}`;
      } else if (absNum < 0.001) {
        return `$${num.toFixed(6)}`;
      } else {
        return `$${num.toFixed(4)}`;
      }
    }

    if (num >= 1e9) return `$${(num / 1e9).toFixed(decimals)}B`;
    if (num >= 1e6) return `$${(num / 1e6).toFixed(decimals)}M`;
    if (num >= 1e3) return `$${(num / 1e3).toFixed(decimals)}K`;
    return `$${num.toFixed(decimals)}`;
  };

  
  const formatAddress = (address: string | number) => {
    if (!address) return 'N/A';
    // Convert to string if it's a number (handle potential API issues)
    const addressStr = typeof address === 'number' ? `0x${address.toString(16)}` : address.toString();
    return `${addressStr.slice(0, 6)}...${addressStr.slice(-4)}`;
  };

  const getChainDisplayName = (chainId: string | number, chainName?: string) => {
    if (chainName) return chainName;

    const id = typeof chainId === 'number' ? chainId : parseInt(chainId);
    const chainMap: Record<number, string> = {
      1: 'Ethereum',
      56: 'BSC',
      137: 'Polygon',
      250: 'Fantom',
      43114: 'Avalanche',
      42161: 'Arbitrum',
      10: 'Optimism',
      8453: 'Base',
      421614: 'Base Sepolia',
    };

    return chainMap[id] || `Chain ${id}`;
  };

  // Removed unused formatPercentage (eslint)

  const formatTaxPercentage = (tax: number | null) => {
  if (tax === null || tax === undefined) return 'N/A';
  const n = Number(tax);
  if (Number.isNaN(n)) return 'N/A';
  const pct = n > 0 && n <= 1 ? n * 100 : n;
  const clamped = Math.max(0, Math.min(100, pct));
  return `${Math.round(clamped)}%`;
};

  const getOverallScore = (data: TokenAnalytics | null | undefined) => {
    if (!data) return 0;

    if ('overall_security_score' in data) {
      const tokenAnalytics = data as TokenAnalytics;
      // Calculate weighted average of all available scores
      const scores = [
        tokenAnalytics.liquidity_score,
        tokenAnalytics.contract_safety_score,
        tokenAnalytics.holder_distribution_score,
        tokenAnalytics.trading_activity_score
      ].filter(score => typeof score === 'number' && score > 0);

      if (scores.length === 0) return 0;
      return Math.round(scores.reduce((sum, score) => sum + score, 0) / scores.length);
    }

    return 0;
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto max-w-7xl px-3 sm:px-6 lg:px-8 py-4 sm:py-8">
        {/* Header */}
        <div className="mb-6 sm:mb-8">
          <h1 className="text-xl sm:text-2xl md:text-3xl font-bold tracking-tight flex items-center gap-2">
            <Shield className="h-6 w-6 sm:h-8 sm:w-8 text-primary flex-shrink-0" />
            Token Health Checker
          </h1>
          <p className="text-sm sm:text-base text-muted-foreground mt-1 sm:mt-2">
            Analyze cryptocurrency tokens for safety, liquidity, and potential risks
          </p>
        </div>

        {/* Search Section */}
        <Card className="mb-6 sm:mb-8">
          <CardHeader className="p-4 sm:p-6">
            <CardTitle className="flex items-center gap-2 text-base sm:text-lg">
              <Shield className="h-4 w-4 sm:h-5 sm:w-5 flex-shrink-0" />
              Contract Address Analysis
            </CardTitle>
            <CardDescription className="text-xs sm:text-sm">
              Analyze cryptocurrency tokens by contract address for comprehensive security and liquidity insights
            </CardDescription>
          </CardHeader>
          <CardContent>
            {/* Contract Address Analysis */}
              <div className="space-y-3">
                <div className="flex gap-2">
                  <Input
                    placeholder="Contract address (0x...)"
                    value={contractAddress}
                    onChange={(e) => setContractAddress(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleContractSearch()}
                    className="flex-1"
                  />
                  <Button onClick={handleContractSearch} disabled={loading}>
                    {loading ? (
                      <RefreshCw className="h-4 w-4 animate-spin" />
                    ) : (
                      <Search className="h-4 w-4" />
                    )}
                    {loading ? 'Analyzing...' : 'Analyze'}
                  </Button>
                </div>
                
              </div>
          </CardContent>
        </Card>

        {/* Error Display */}
        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Results Display */}
        {tokenAnalytics && (
          <div className="space-y-6">
            {/* Overall Score */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>
                    {tokenAnalytics.symbol} Health Score
                    <span className="text-sm font-normal text-muted-foreground ml-2">
                      ({formatAddress(tokenAnalytics.contract_address)})
                    </span>
                  </span>
                  <Badge variant="outline" className={getRiskColor(tokenAnalytics.risk_level || 'medium')}>
                    {tokenAnalytics.risk_level?.toUpperCase()} RISK
                  </Badge>
                </CardTitle>
                {tokenAnalytics && (
                  <CardDescription>
                    {tokenAnalytics.name} • Chain: {getChainDisplayName(tokenAnalytics.chain_id, tokenAnalytics.chain_name)}
                  </CardDescription>
                )}
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-center">
                  <div className="relative">
                    <div className="h-32 w-32 rounded-full border-8 border-muted flex items-center justify-center">
                      <div className="text-center">
                        <div className={`text-3xl font-bold ${getScoreColor(getOverallScore(tokenAnalytics))}`}>
                          {getOverallScore(tokenAnalytics)}
                        </div>
                        <div className="text-sm text-muted-foreground">Overall Score</div>
                      </div>
                    </div>
                    {getOverallScore(tokenAnalytics) > 0 && (
                      <div
                        className={`absolute top-0 left-0 h-32 w-32 rounded-full border-8 ${getScoreBg(getOverallScore(tokenAnalytics))}`}
                        style={{
                          clipPath: `polygon(50% 50%, 50% 0%, ${50 + (getOverallScore(tokenAnalytics) / 100) * 50}% 0%)`
                        }}
                      />
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Token Analytics Details (for contract analysis) */}
            {tokenAnalytics && (
              <>
                {/* Token Basic Info */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <DollarSign className="h-5 w-5" />
                      Token Information
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                      <div>
                        <p className="text-sm font-medium text-muted-foreground">Symbol</p>
                        <p className="text-lg font-semibold">{tokenAnalytics.symbol}</p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-muted-foreground">Name</p>
                        <p className="text-lg font-semibold">{tokenAnalytics.name}</p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-muted-foreground">Chain</p>
                        <p className="text-lg font-semibold">{getChainDisplayName(tokenAnalytics.chain_id, tokenAnalytics.chain_name)}</p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-muted-foreground">Contract</p>
                        <p className="text-lg font-semibold font-mono">{formatAddress(tokenAnalytics.contract_address)}</p>
                      </div>
                    </div>

                    {(tokenAnalytics.price_usd || tokenAnalytics.market_cap || tokenAnalytics.holders_count) && (
                      <div className="grid gap-4 md:grid-cols-3 mt-4 pt-4 border-t">
                        <div>
                          <p className="text-sm font-medium text-muted-foreground">Price</p>
                          <p className="text-lg font-semibold">
                            {tokenAnalytics.price_usd ? formatNumber(tokenAnalytics.price_usd) : 'N/A'}
                          </p>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-muted-foreground">Market Cap</p>
                          <p className="text-lg font-semibold">
                            {tokenAnalytics.market_cap ? formatNumber(tokenAnalytics.market_cap) : 'N/A'}
                          </p>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-muted-foreground">Holders</p>
                          <p className="text-lg font-semibold">
                            {tokenAnalytics.holders_count ? tokenAnalytics.holders_count.toLocaleString() : 'N/A'}
                          </p>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Security Analysis */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Lock className="h-5 w-5" />
                      Security Analysis
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                      <div className="flex items-center gap-2">
                        <Badge variant={tokenAnalytics.contract_verified ? "default" : "destructive"}>
                          {tokenAnalytics.contract_verified ? "✓ Verified" : "⚠ Not Verified"}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant={tokenAnalytics.honeypot_risk ? "destructive" : "default"}>
                          {tokenAnalytics.honeypot_risk ? "⚠ Honeypot Risk" : "✓ No Honeypot"}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant={tokenAnalytics.renounced_ownership ? "default" : "secondary"}>
                          {tokenAnalytics.renounced_ownership ? "Ownership Renounced" : "Owner Active"}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">Security Score:</span>
                        <span className={`font-bold ${getScoreColor(tokenAnalytics.overall_security_score)}`}>
                          {tokenAnalytics.overall_security_score}
                        </span>
                      </div>
                    </div>

                      <div className="grid gap-4 md:grid-cols-3 mt-4 pt-4 border-t">
                        <div>
                          <p className="text-sm font-medium text-muted-foreground">Buy Tax</p>
                          <p className="text-lg font-semibold">
                            {formatTaxPercentage(tokenAnalytics.buy_tax)}
                          </p>
                          {('tax_source' in (tokenAnalytics as TokenAnalyticsExtended)) && (
                            <p className="text-xs text-muted-foreground mt-1">
                              Source: {(tokenAnalytics as TokenAnalyticsExtended).tax_source || 'unknown'}{((tokenAnalytics as TokenAnalyticsExtended).tax_confidence ? ` • ${(tokenAnalytics as TokenAnalyticsExtended).tax_confidence}` : '')}
                            </p>
                          )}
                        </div>
                        <div>
                          <p className="text-sm font-medium text-muted-foreground">Sell Tax</p>
                          <p className="text-lg font-semibold">
                            {formatTaxPercentage(tokenAnalytics.sell_tax)}
                          </p>
                          {('tax_source' in (tokenAnalytics as TokenAnalyticsExtended)) && (
                            <p className="text-xs text-muted-foreground mt-1">
                              Source: {(tokenAnalytics as TokenAnalyticsExtended).tax_source || 'unknown'}{((tokenAnalytics as TokenAnalyticsExtended).tax_confidence ? ` • ${(tokenAnalytics as TokenAnalyticsExtended).tax_confidence}` : '')}
                            </p>
                          )}
                        </div>
                      <div>
                        <p className="text-sm font-medium text-muted-foreground">Pump & Dump Risk</p>
                        <p className={`text-lg font-semibold ${getScoreColor(100 - tokenAnalytics.pump_dump_risk)}`}>
                          {tokenAnalytics.pump_dump_risk.toFixed(1)}%
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Detailed Scores */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Activity className="h-5 w-5" />
                      Analysis Scores
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                      <div>
                        <p className="text-sm font-medium text-muted-foreground">Liquidity Score</p>
                        <p className={`text-2xl font-bold ${getScoreColor(tokenAnalytics.liquidity_score)}`}>
                          {tokenAnalytics.liquidity_score}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-muted-foreground">Contract Safety</p>
                        <p className={`text-2xl font-bold ${getScoreColor(tokenAnalytics.contract_safety_score)}`}>
                          {tokenAnalytics.contract_safety_score}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-muted-foreground">Holder Distribution</p>
                        <p className={`text-2xl font-bold ${getScoreColor(tokenAnalytics.holder_distribution_score)}`}>
                          {tokenAnalytics.holder_distribution_score}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-muted-foreground">Trading Activity</p>
                        <p className={`text-2xl font-bold ${getScoreColor(tokenAnalytics.trading_activity_score)}`}>
                          {tokenAnalytics.trading_activity_score}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Liquidity Analysis */}
                {(tokenAnalytics.liquidity_usd !== null || tokenAnalytics.liquidity_locked) && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Activity className="h-5 w-5" />
                        Liquidity Analysis
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                        <div>
                          <p className="text-sm font-medium text-muted-foreground">Total Liquidity</p>
                          <p className="text-lg font-semibold">
                            {tokenAnalytics.liquidity_usd ? formatNumber(tokenAnalytics.liquidity_usd) : 'N/A'}
                          </p>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-muted-foreground">Liquidity Locked</p>
                          <p className="text-lg font-semibold">
                            {tokenAnalytics.liquidity_locked ?
                              `${tokenAnalytics.liquidity_lock_percentage}%` : 'Not Locked'
                            }
                          </p>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-muted-foreground">LP Burned</p>
                          <p className="text-lg font-semibold">
                            {tokenAnalytics.lp_burned ? 'Yes' : 'No'}
                          </p>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-muted-foreground">24h Volume</p>
                          <p className="text-lg font-semibold">
                            {tokenAnalytics.volume_24h ? formatNumber(tokenAnalytics.volume_24h) : 'N/A'}
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Trading Activity */}
                {(tokenAnalytics.buys_24h !== null || tokenAnalytics.sells_24h !== null || tokenAnalytics.total_transactions_24h > 0) && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <TrendingUp className="h-5 w-5" />
                        Trading Activity (24h)
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid gap-4 md:grid-cols-3">
                        <div>
                          <p className="text-sm font-medium text-muted-foreground">Buys (24h)</p>
                          <p className="text-lg font-semibold text-green-500">
                            {tokenAnalytics.buys_24h !== null && tokenAnalytics.buys_24h !== undefined
                              ? tokenAnalytics.buys_24h.toLocaleString()
                              : tokenAnalytics.volume_24h && tokenAnalytics.volume_24h > 0
                                ? '📊 Active'
                                : '📊 No Data'
                            }
                          </p>
                          {tokenAnalytics.buys_24h === null && tokenAnalytics.volume_24h && tokenAnalytics.volume_24h > 0 && (
                            <p className="text-xs text-muted-foreground mt-1">Volume detected</p>
                          )}
                          {tokenAnalytics.buys_24h === null && (!tokenAnalytics.volume_24h || tokenAnalytics.volume_24h === 0) && (
                            <p className="text-xs text-muted-foreground mt-1">Trading data unavailable</p>
                          )}
                        </div>
                        <div>
                          <p className="text-sm font-medium text-muted-foreground">Sells (24h)</p>
                          <p className="text-lg font-semibold text-red-500">
                            {tokenAnalytics.sells_24h !== null && tokenAnalytics.sells_24h !== undefined
                              ? tokenAnalytics.sells_24h.toLocaleString()
                              : tokenAnalytics.volume_24h && tokenAnalytics.volume_24h > 0
                                ? '📊 Active'
                                : '📊 No Data'
                            }
                          </p>
                          {tokenAnalytics.sells_24h === null && tokenAnalytics.volume_24h && tokenAnalytics.volume_24h > 0 && (
                            <p className="text-xs text-muted-foreground mt-1">Volume detected</p>
                          )}
                          {tokenAnalytics.sells_24h === null && (!tokenAnalytics.volume_24h || tokenAnalytics.volume_24h === 0) && (
                            <p className="text-xs text-muted-foreground mt-1">Trading data unavailable</p>
                          )}
                        </div>
                        <div>
                          <p className="text-sm font-medium text-muted-foreground">Total Transactions</p>
                          <p className="text-lg font-semibold">
                            {tokenAnalytics.total_transactions_24h?.toLocaleString() || '0'}
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Security Assessment */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <AlertTriangle className="h-5 w-5" />
                      Security Assessment
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {/* Warnings */}
                      {tokenAnalytics.warnings && tokenAnalytics.warnings.length > 0 && (
                        <div>
                          <p className="text-sm font-medium text-muted-foreground mb-2">⚠️ Warnings</p>
                          <div className="space-y-1">
                            {tokenAnalytics.warnings.map((warning, index) => (
                              <p key={index} className="text-sm text-red-600">{warning}</p>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Strengths */}
                      {tokenAnalytics.strengths && tokenAnalytics.strengths.length > 0 && (
                        <div>
                          <p className="text-sm font-medium text-muted-foreground mb-2">✅ Strengths</p>
                          <div className="space-y-1">
                            {tokenAnalytics.strengths.map((strength, index) => (
                              <p key={index} className="text-sm text-green-600">{strength}</p>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Recommendation */}
                      <div className="pt-2 border-t">
                        <p className="text-sm font-medium text-muted-foreground mb-2">📊 Recommendation</p>
                        <p className={`text-lg font-semibold ${
                          tokenAnalytics.recommendation.includes('AVOID') ? 'text-red-600' :
                          tokenAnalytics.recommendation.includes('CAUTION') ? 'text-yellow-600' :
                          'text-green-600'
                        }`}>
                          {tokenAnalytics.recommendation}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </>
            )}

            
            {/* Recommendations */}
            {tokenAnalytics && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <CheckCircle className="h-5 w-5" />
                    Key Insights & Recommendations
                  </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                      <div>
                        <p className="text-lg font-semibold mb-2">📊 Recommendation</p>
                        <p className={`text-lg ${
                          tokenAnalytics.recommendation.includes('AVOID') ? 'text-red-600' :
                          tokenAnalytics.recommendation.includes('CAUTION') ? 'text-yellow-600' :
                          'text-green-600'
                        }`}>
                          {tokenAnalytics.recommendation}
                        </p>
                      </div>

                      {tokenAnalytics.warnings && tokenAnalytics.warnings.length > 0 && (
                        <div>
                          <p className="text-sm font-medium text-muted-foreground mb-2">⚠️ Warnings</p>
                          <ul className="space-y-1">
                            {tokenAnalytics.warnings.map((warning, index) => (
                              <li key={index} className="flex items-start gap-2">
                                <div className="w-2 h-2 rounded-full bg-red-500 mt-2 flex-shrink-0" />
                                <span className="text-sm text-red-600">{warning}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {tokenAnalytics.strengths && tokenAnalytics.strengths.length > 0 && (
                        <div>
                          <p className="text-sm font-medium text-muted-foreground mb-2">✅ Strengths</p>
                          <ul className="space-y-1">
                            {tokenAnalytics.strengths.map((strength, index) => (
                              <li key={index} className="flex items-start gap-2">
                                <div className="w-2 h-2 rounded-full bg-green-500 mt-2 flex-shrink-0" />
                                <span className="text-sm text-green-600">{strength}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                </CardContent>
              </Card>
            )}

            {/* Last Updated */}
            <div className="text-center text-sm text-muted-foreground">
              Last updated: {new Date(tokenAnalytics?.last_updated || new Date()).toLocaleString()}
            </div>
          </div>
        )}

        {/* Empty State */}
        {!tokenAnalytics && !loading && (
          <Card>
            <CardContent className="py-12">
              <div className="text-center">
                <Shield className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-lg font-semibold mb-2">No Token Analyzed</h3>
                <p className="text-muted-foreground">
                  Enter a cryptocurrency symbol above to get started with token health analysis.
                </p>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}



