'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Shield, 
  AlertTriangle, 
  Search, 
  TrendingUp, 
  Users, 
  Lock,
  Activity,
  CheckCircle,
  XCircle
} from 'lucide-react';
import { apiClient } from '@/lib/api-client';
import { getHealthColor, getHealthBadgeColor } from '@/lib/utils';

interface TokenHealth {
  symbol: string;
  overall_score: number;
  liquidity_score: number;
  holder_distribution_score: number;
  contract_safety_score: number;
  volume_score: number;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  warnings: string[];
  strengths: string[];
  liquidity_locked: boolean;
  contract_verified: boolean;
  honeypot_risk: boolean;
  pump_dump_risk: number;
}

export default function TokenHealthPage() {
  const [symbol, setSymbol] = useState('');
  const [loading, setLoading] = useState(false);
  const [healthData, setHealthData] = useState<TokenHealth | null>(null);
  const [error, setError] = useState('');

  const analyzeToken = async () => {
    if (!symbol.trim()) {
      setError('Please enter a token symbol');
      return;
    }

    setLoading(true);
    setError('');
    setHealthData(null);

    try {
      const response = await apiClient.getTokenHealth(symbol.toUpperCase());
      setHealthData(response.data);
    } catch (err) {
      const error = err as { response?: { data?: { error?: { message?: string } } } };
      setError(error.response?.data?.error?.message || 'Failed to analyze token. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      analyzeToken();
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight">Token Health Analyzer</h1>
          <p className="text-muted-foreground mt-2">
            Expose weak projects and scams before they drain your wallet
          </p>
        </div>

        {/* Search Section */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Analyze Token Health</CardTitle>
            <CardDescription>
              Enter a token symbol to get comprehensive health analysis and scam detection
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4">
              <Input
                placeholder="Enter token symbol (e.g., BTC, ETH, SOL)"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                onKeyPress={handleKeyPress}
                className="flex-1"
              />
              <Button onClick={analyzeToken} disabled={loading}>
                {loading ? (
                  <>
                    <Activity className="mr-2 h-4 w-4 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Search className="mr-2 h-4 w-4" />
                    Analyze
                  </>
                )}
              </Button>
            </div>
            {error && (
              <p className="text-sm text-destructive mt-2">{error}</p>
            )}
          </CardContent>
        </Card>

        {/* Results */}
        {healthData && (
          <>
            {/* Overall Health Score */}
            <Card className="mb-8">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-2xl">{healthData.symbol}</CardTitle>
                    <CardDescription>Overall Health Assessment</CardDescription>
                  </div>
                  <Badge 
                    className={getHealthBadgeColor(healthData.overall_score)}
                    variant="outline"
                  >
                    {healthData.risk_level.toUpperCase()}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {/* Score Display */}
                  <div className="text-center">
                    <div className={`text-6xl font-bold ${getHealthColor(healthData.overall_score)}`}>
                      {healthData.overall_score}
                    </div>
                    <p className="text-muted-foreground mt-2">Health Score (0-100)</p>
                  </div>

                  {/* Risk Indicators */}
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="flex items-center gap-3 p-4 rounded-lg border">
                      {healthData.contract_verified ? (
                        <CheckCircle className="h-5 w-5 text-green-500" />
                      ) : (
                        <XCircle className="h-5 w-5 text-red-500" />
                      )}
                      <div>
                        <p className="font-medium">Contract Verified</p>
                        <p className="text-sm text-muted-foreground">
                          {healthData.contract_verified ? 'Source code verified' : 'Not verified - High risk'}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 p-4 rounded-lg border">
                      {healthData.liquidity_locked ? (
                        <CheckCircle className="h-5 w-5 text-green-500" />
                      ) : (
                        <XCircle className="h-5 w-5 text-red-500" />
                      )}
                      <div>
                        <p className="font-medium">Liquidity Locked</p>
                        <p className="text-sm text-muted-foreground">
                          {healthData.liquidity_locked ? 'Liquidity is locked' : 'Liquidity not locked - Rug pull risk'}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 p-4 rounded-lg border">
                      {!healthData.honeypot_risk ? (
                        <CheckCircle className="h-5 w-5 text-green-500" />
                      ) : (
                        <XCircle className="h-5 w-5 text-red-500" />
                      )}
                      <div>
                        <p className="font-medium">Honeypot Check</p>
                        <p className="text-sm text-muted-foreground">
                          {!healthData.honeypot_risk ? 'No honeypot detected' : 'WARNING: Honeypot detected!'}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 p-4 rounded-lg border">
                      {healthData.pump_dump_risk < 50 ? (
                        <CheckCircle className="h-5 w-5 text-green-500" />
                      ) : (
                        <AlertTriangle className="h-5 w-5 text-yellow-500" />
                      )}
                      <div>
                        <p className="font-medium">Pump & Dump Risk</p>
                        <p className="text-sm text-muted-foreground">
                          {healthData.pump_dump_risk}% risk score
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Detailed Metrics */}
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 mb-8">
              <MetricCard
                title="Liquidity Score"
                score={healthData.liquidity_score}
                icon={<TrendingUp className="h-5 w-5" />}
                description="Token liquidity depth"
              />
              <MetricCard
                title="Holder Distribution"
                score={healthData.holder_distribution_score}
                icon={<Users className="h-5 w-5" />}
                description="Token holder spread"
              />
              <MetricCard
                title="Contract Safety"
                score={healthData.contract_safety_score}
                icon={<Lock className="h-5 w-5" />}
                description="Smart contract security"
              />
              <MetricCard
                title="Volume Score"
                score={healthData.volume_score}
                icon={<Activity className="h-5 w-5" />}
                description="Trading volume health"
              />
            </div>

            {/* Warnings and Strengths */}
            <div className="grid gap-6 md:grid-cols-2">
              {/* Warnings */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <AlertTriangle className="h-5 w-5 text-yellow-500" />
                    Warnings
                  </CardTitle>
                  <CardDescription>Potential risks and red flags</CardDescription>
                </CardHeader>
                <CardContent>
                  {healthData.warnings.length > 0 ? (
                    <ul className="space-y-2">
                      {healthData.warnings.map((warning, index) => (
                        <li key={index} className="flex items-start gap-2">
                          <XCircle className="h-4 w-4 text-red-500 mt-0.5 flex-shrink-0" />
                          <span className="text-sm">{warning}</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-sm text-muted-foreground">No major warnings detected</p>
                  )}
                </CardContent>
              </Card>

              {/* Strengths */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Shield className="h-5 w-5 text-green-500" />
                    Strengths
                  </CardTitle>
                  <CardDescription>Positive indicators</CardDescription>
                </CardHeader>
                <CardContent>
                  {healthData.strengths.length > 0 ? (
                    <ul className="space-y-2">
                      {healthData.strengths.map((strength, index) => (
                        <li key={index} className="flex items-start gap-2">
                          <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                          <span className="text-sm">{strength}</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-sm text-muted-foreground">No notable strengths identified</p>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Investment Recommendation */}
            <Card className="mt-6">
              <CardHeader>
                <CardTitle>Investment Recommendation</CardTitle>
              </CardHeader>
              <CardContent>
                <div className={`p-4 rounded-lg border-2 ${
                  healthData.risk_level === 'low' ? 'border-green-500 bg-green-500/10' :
                  healthData.risk_level === 'medium' ? 'border-yellow-500 bg-yellow-500/10' :
                  healthData.risk_level === 'high' ? 'border-orange-500 bg-orange-500/10' :
                  'border-red-500 bg-red-500/10'
                }`}>
                  <p className="font-semibold mb-2">
                    {healthData.risk_level === 'low' ? '✅ Low Risk - Generally Safe' :
                     healthData.risk_level === 'medium' ? '⚠️ Medium Risk - Proceed with Caution' :
                     healthData.risk_level === 'high' ? '🚨 High Risk - Not Recommended' :
                     '🛑 Critical Risk - AVOID'}
                  </p>
                  <p className="text-sm">
                    {healthData.risk_level === 'low' 
                      ? 'This token shows healthy metrics and low risk indicators. However, always do your own research.'
                      : healthData.risk_level === 'medium'
                      ? 'This token has some concerning indicators. Only invest what you can afford to lose.'
                      : healthData.risk_level === 'high'
                      ? 'This token shows multiple red flags. High risk of loss. Not recommended for investment.'
                      : 'CRITICAL: This token shows severe warning signs. Very high probability of scam or rug pull. DO NOT INVEST.'}
                  </p>
                </div>
              </CardContent>
            </Card>
          </>
        )}

        {/* Info Section */}
        {!healthData && !loading && (
          <div className="grid gap-6 md:grid-cols-3">
            <Card>
              <CardHeader>
                <Shield className="h-8 w-8 text-blue-500 mb-2" />
                <CardTitle>Scam Detection</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Advanced algorithms identify pump-and-dump schemes, honeypots, and fraudulent projects.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <Lock className="h-8 w-8 text-purple-500 mb-2" />
                <CardTitle>Contract Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Deep analysis of smart contract code to identify security vulnerabilities and malicious functions.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <TrendingUp className="h-8 w-8 text-green-500 mb-2" />
                <CardTitle>Liquidity Check</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Verify liquidity locks and assess the risk of rug pulls before investing.
                </p>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}

function MetricCard({ 
  title, 
  score, 
  icon, 
  description 
}: { 
  title: string; 
  score: number; 
  icon: React.ReactNode; 
  description: string;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {icon}
      </CardHeader>
      <CardContent>
        <div className={`text-2xl font-bold ${getHealthColor(score)}`}>
          {score}
        </div>
        <p className="text-xs text-muted-foreground mt-1">{description}</p>
      </CardContent>
    </Card>
  );
}
