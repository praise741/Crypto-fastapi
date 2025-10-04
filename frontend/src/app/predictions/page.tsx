'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  TrendingUp, 
  TrendingDown, 
  Search, 
  Activity,
  ArrowUpCircle,
  ArrowDownCircle,
  Clock,
  Target
} from 'lucide-react';
import { apiClient } from '@/lib/api-client';
import { formatCurrency, formatPercentage, getChangeColor } from '@/lib/utils';

interface Prediction {
  symbol: string;
  current_price: number;
  predictions: {
    horizon: string;
    predicted_price: number;
    confidence_interval: {
      lower: number;
      upper: number;
      confidence: number;
    };
    probability: {
      up: number;
      down: number;
    };
    factors: {
      name: string;
      impact: number;
    }[];
    model_version: string;
    generated_at: string;
  }[];
}

interface Signal {
  type: 'entry' | 'exit' | 'hold';
  strength: 'strong' | 'moderate' | 'weak';
  reason: string;
}

const POPULAR_SYMBOLS = ['BTC', 'ETH', 'SOL', 'BNB', 'ADA', 'XRP', 'DOT', 'MATIC'];

export default function PredictionsPage() {
  const [symbol, setSymbol] = useState('BTC');
  const [loading, setLoading] = useState(false);
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    loadPrediction('BTC');
  }, []);

  const loadPrediction = async (sym: string) => {
    setLoading(true);
    setError('');
    setPrediction(null);

    try {
      const response = await apiClient.getPredictions(sym.toUpperCase());
      setPrediction(response.data);
    } catch (err) {
      const error = err as { response?: { data?: { error?: { message?: string } } } };
      setError(error.response?.data?.error?.message || 'Failed to load predictions');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    if (symbol.trim()) {
      loadPrediction(symbol);
    }
  };

  const getSignal = (pred: Prediction): Signal => {
    if (!pred.predictions || pred.predictions.length === 0) {
      return { type: 'hold', strength: 'weak', reason: 'Insufficient data' };
    }

    const shortTerm = pred.predictions.find(p => p.horizon === '1h' || p.horizon === '4h');
    if (!shortTerm) {
      return { type: 'hold', strength: 'weak', reason: 'No short-term prediction available' };
    }

    const priceChange = ((shortTerm.predicted_price - pred.current_price) / pred.current_price) * 100;
    const upProbability = shortTerm.probability.up;

    if (upProbability > 0.65 && priceChange > 2) {
      return { 
        type: 'entry', 
        strength: 'strong', 
        reason: `Strong bullish signal: ${upProbability * 100}% probability of ${priceChange.toFixed(2)}% gain` 
      };
    } else if (upProbability > 0.55 && priceChange > 1) {
      return { 
        type: 'entry', 
        strength: 'moderate', 
        reason: `Moderate bullish signal: ${upProbability * 100}% probability of ${priceChange.toFixed(2)}% gain` 
      };
    } else if (upProbability < 0.35 && priceChange < -2) {
      return { 
        type: 'exit', 
        strength: 'strong', 
        reason: `Strong bearish signal: ${(1 - upProbability) * 100}% probability of ${Math.abs(priceChange).toFixed(2)}% loss` 
      };
    } else if (upProbability < 0.45 && priceChange < -1) {
      return { 
        type: 'exit', 
        strength: 'moderate', 
        reason: `Moderate bearish signal: ${(1 - upProbability) * 100}% probability of ${Math.abs(priceChange).toFixed(2)}% loss` 
      };
    }

    return { type: 'hold', strength: 'moderate', reason: 'Market conditions uncertain, hold position' };
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight">AI Price Predictions</h1>
          <p className="text-muted-foreground mt-2">
            Know the right time to buy or sell with AI-powered predictions
          </p>
        </div>

        {/* Search and Quick Select */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Select Cryptocurrency</CardTitle>
            <CardDescription>Choose from popular tokens or search for any symbol</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4 mb-4">
              <Input
                placeholder="Enter symbol (e.g., BTC, ETH)"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                className="flex-1"
              />
              <Button onClick={handleSearch} disabled={loading}>
                {loading ? (
                  <Activity className="h-4 w-4 animate-spin" />
                ) : (
                  <Search className="h-4 w-4" />
                )}
              </Button>
            </div>
            <div className="flex flex-wrap gap-2">
              {POPULAR_SYMBOLS.map((sym) => (
                <Button
                  key={sym}
                  variant={symbol === sym ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => {
                    setSymbol(sym);
                    loadPrediction(sym);
                  }}
                >
                  {sym}
                </Button>
              ))}
            </div>
            {error && <p className="text-sm text-destructive mt-2">{error}</p>}
          </CardContent>
        </Card>

        {/* Results */}
        {prediction && (
          <>
            {/* Trading Signal */}
            <Card className="mb-8">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="h-5 w-5" />
                  Trading Signal for {prediction.symbol}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <SignalDisplay prediction={prediction} getSignal={getSignal} />
              </CardContent>
            </Card>

            {/* Current Price */}
            <div className="grid gap-6 md:grid-cols-2 mb-8">
              <Card>
                <CardHeader>
                  <CardTitle>Current Price</CardTitle>
                  <CardDescription>{prediction.symbol}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-4xl font-bold">
                    {formatCurrency(prediction.current_price)}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Prediction Confidence</CardTitle>
                  <CardDescription>Model reliability score</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="text-4xl font-bold text-primary">
                    {prediction.predictions[0]?.confidence_interval.confidence 
                      ? `${(prediction.predictions[0].confidence_interval.confidence * 100).toFixed(0)}%`
                      : 'N/A'}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Predictions by Timeframe */}
            <Card className="mb-8">
              <CardHeader>
                <CardTitle>Price Predictions</CardTitle>
                <CardDescription>AI forecasts across different time horizons</CardDescription>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue={prediction.predictions[0]?.horizon || '24h'}>
                  <TabsList className="grid w-full grid-cols-4">
                    {prediction.predictions.map((pred) => (
                      <TabsTrigger key={pred.horizon} value={pred.horizon}>
                        {pred.horizon}
                      </TabsTrigger>
                    ))}
                  </TabsList>

                  {prediction.predictions.map((pred) => (
                    <TabsContent key={pred.horizon} value={pred.horizon} className="space-y-4 mt-4">
                      <PredictionDetails 
                        prediction={pred} 
                        currentPrice={prediction.current_price}
                        symbol={prediction.symbol}
                      />
                    </TabsContent>
                  ))}
                </Tabs>
              </CardContent>
            </Card>
          </>
        )}

        {/* Info Cards */}
        {!prediction && !loading && (
          <div className="grid gap-6 md:grid-cols-3">
            <Card>
              <CardHeader>
                <ArrowUpCircle className="h-8 w-8 text-green-500 mb-2" />
                <CardTitle>Entry Signals</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Get notified when AI detects optimal buying opportunities based on price predictions and market trends.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <ArrowDownCircle className="h-8 w-8 text-red-500 mb-2" />
                <CardTitle>Exit Signals</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Know when to take profits or cut losses with timely exit signals powered by predictive analytics.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <Clock className="h-8 w-8 text-blue-500 mb-2" />
                <CardTitle>Multiple Timeframes</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  View predictions across 1h, 4h, 24h, and 7d horizons to plan both short and long-term strategies.
                </p>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}

function SignalDisplay({ prediction, getSignal }: { prediction: Prediction; getSignal: (pred: Prediction) => Signal }) {
  const signal = getSignal(prediction);

  return (
    <div className={`p-6 rounded-lg border-2 ${
      signal.type === 'entry' ? 'border-green-500 bg-green-500/10' :
      signal.type === 'exit' ? 'border-red-500 bg-red-500/10' :
      'border-yellow-500 bg-yellow-500/10'
    }`}>
      <div className="flex items-center gap-4 mb-4">
        {signal.type === 'entry' ? (
          <ArrowUpCircle className="h-12 w-12 text-green-500" />
        ) : signal.type === 'exit' ? (
          <ArrowDownCircle className="h-12 w-12 text-red-500" />
        ) : (
          <Activity className="h-12 w-12 text-yellow-500" />
        )}
        <div>
          <h3 className="text-2xl font-bold">
            {signal.type === 'entry' ? 'BUY SIGNAL' : signal.type === 'exit' ? 'SELL SIGNAL' : 'HOLD'}
          </h3>
          <Badge variant={signal.strength === 'strong' ? 'default' : 'secondary'}>
            {signal.strength.toUpperCase()} STRENGTH
          </Badge>
        </div>
      </div>
      <p className="text-sm">{signal.reason}</p>
    </div>
  );
}

function PredictionDetails({ 
  prediction, 
  currentPrice
}: { 
  prediction: Prediction['predictions'][0];
  currentPrice: number;
  symbol: string;
}) {
  const priceChange = ((prediction.predicted_price - currentPrice) / currentPrice) * 100;

  return (
    <div className="space-y-6">
      {/* Price Prediction */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Predicted Price</CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${getChangeColor(priceChange)}`}>
              {formatCurrency(prediction.predicted_price)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {formatPercentage(priceChange)} from current
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Price Range</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-sm space-y-1">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Lower:</span>
                <span className="font-medium">{formatCurrency(prediction.confidence_interval.lower)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Upper:</span>
                <span className="font-medium">{formatCurrency(prediction.confidence_interval.upper)}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Direction Probability</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-green-500" />
                  <span className="text-sm">Up</span>
                </div>
                <span className="font-bold text-green-500">
                  {(prediction.probability.up * 100).toFixed(0)}%
                </span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <TrendingDown className="h-4 w-4 text-red-500" />
                  <span className="text-sm">Down</span>
                </div>
                <span className="font-bold text-red-500">
                  {(prediction.probability.down * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Key Factors */}
      <Card>
        <CardHeader>
          <CardTitle>Key Prediction Factors</CardTitle>
          <CardDescription>Main drivers influencing this forecast</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {prediction.factors.map((factor, index) => (
              <div key={index} className="flex items-center justify-between">
                <span className="text-sm capitalize">{factor.name.replace(/_/g, ' ')}</span>
                <div className="flex items-center gap-2">
                  <div className="w-32 h-2 bg-muted rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-primary rounded-full"
                      style={{ width: `${factor.impact * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-medium w-12 text-right">
                    {(factor.impact * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Model Info */}
      <div className="text-xs text-muted-foreground">
        <p>Model: {prediction.model_version}</p>
        <p>Generated: {new Date(prediction.generated_at).toLocaleString()}</p>
      </div>
    </div>
  );
}
