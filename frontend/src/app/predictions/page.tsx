'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  TrendingUp,
  TrendingDown,
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

interface ApiResponse {
  success: boolean;
  data?: {
    predictions?: PredictionData[];
    current_price?: number | string;
    [key: string]: unknown;
  };
}

interface PredictionData {
  horizon: string;
  predicted_price: number | string;
  confidence_interval: {
    lower: number | string;
    upper: number | string;
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
  [key: string]: unknown;
}

interface ContractResponse {
  success: boolean;
  data?: {
    token?: {
      symbol: string;
    };
    pricing?: {
      price_usd: number | string;
    };
    [key: string]: unknown;
  };
}

// Helper function to safely parse scientific notation
function parseFloatSafe(value: string | number): number {
  if (typeof value === 'number') return value;
  if (typeof value === 'string') {
    // Handle scientific notation
    const parsed = parseFloat(value);
    return isNaN(parsed) ? 0 : parsed;
  }
  return 0;
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
      let symbol = sym.trim();
      let contractData = null;

      // Check if input is a contract address (starts with 0x)
      if (symbol.toLowerCase().startsWith('0x')) {
        // Try backend /predictions/by-contract first
        try {
          const byContract = await apiClient.getPredictionsByContract(symbol, undefined, {
            horizons: '1h,4h,24h,7d',
            include_confidence: true,
            include_factors: true,
          });
          const byC = byContract as unknown as ApiResponse;
          if (
            byC.success &&
            byC.data &&
            Array.isArray(byC.data.predictions) &&
            byC.data.predictions.length > 0
          ) {
            const responseData = byC.data as { symbol?: string; current_price?: number | string; predictions: PredictionData[] };
            const fixedData = {
              symbol: responseData.symbol ?? symbol,
              current_price: parseFloatSafe(responseData.current_price || 0),
              predictions: (responseData.predictions as PredictionData[]).map((pred: PredictionData) => ({
                ...pred,
                predicted_price: parseFloatSafe(pred.predicted_price),
                confidence_interval: {
                  ...pred.confidence_interval,
                  lower: parseFloatSafe(pred.confidence_interval.lower),
                  upper: parseFloatSafe(pred.confidence_interval.upper),
                },
              })),
            } as Prediction;
            setPrediction(fixedData);
            setLoading(false);
            return;
          }
        } catch { /* ignore and fallback */ }

        // Fallback to GET /contracts to resolve symbol
        const contractResponse = await apiClient.getContractData(symbol);
        if ((contractResponse as unknown as ContractResponse).success) {
          const data = (contractResponse as unknown as ContractResponse).data as ContractResponse['data'];
          const maybeSymbol = data?.token?.symbol || (data as { symbol?: string })?.symbol;
          if (maybeSymbol) {
            symbol = maybeSymbol;
            contractData = data;
          } else {
            setError('Contract address not found or token data unavailable');
            return;
          }
        } else {
          setError('Contract address not found or token data unavailable');
          return;
        }
      }

      // Get predictions with proper parameters
      const response = await apiClient.getPredictions(symbol.toUpperCase(), {
        horizons: '1h,4h,24h,7d',
        include_confidence: true,
        include_factors: true
      });

      if ((response as unknown as ApiResponse).success && (response as unknown as ApiResponse).data) {
          // Check if we have prediction data with probability info
          const responseData = (response as unknown as ApiResponse).data!;
          if (responseData?.predictions &&
              responseData.predictions.length > 0 &&
              responseData.predictions[0]?.probability) {
            // Fix scientific notation parsing
          const fixedData = {
            symbol: symbol,
            current_price: parseFloatSafe(responseData.current_price || 0),
            predictions: responseData.predictions.map((pred: PredictionData) => ({
              ...pred,
              predicted_price: parseFloatSafe(pred.predicted_price),
              confidence_interval: {
                ...pred.confidence_interval,
                lower: parseFloatSafe(pred.confidence_interval.lower),
                upper: parseFloatSafe(pred.confidence_interval.upper)
              }
            }))
          };

          // If predictions API returns 0 price but we have contract data, use contract price
          if (fixedData.current_price === 0 && contractData && (contractData as ContractResponse['data'])?.pricing) {
            fixedData.current_price = parseFloatSafe((contractData as ContractResponse['data'])!.pricing!.price_usd);
          }
          setPrediction(fixedData);
        } else {
          setError('No valid prediction data available for this token');
        }
      } else {
        setError('No predictions available for this symbol');
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { error?: { message?: string } } } };
      setError(error.response?.data?.error?.message || 'Failed to load predictions');
    } finally {
      setLoading(false);
    }
  };

  
  const getSignal = (pred: Prediction): Signal => {
    if (!pred.predictions || pred.predictions.length === 0) {
      return { type: 'hold', strength: 'weak', reason: 'Insufficient data' };
    }

    // Evaluate all horizons and pick the strongest risk-adjusted edge
    let bestScore = -Infinity;
    let best: Signal = { type: 'hold', strength: 'weak', reason: 'No strong edge' };
    for (const p of pred.predictions) {
      const up = p.probability?.up ?? 0.5;
      const conf = p.confidence_interval?.confidence ?? 0.5;
      const pc = pred.current_price > 0 ? ((p.predicted_price - pred.current_price) / pred.current_price) * 100 : 0;
      const edge = (up - 0.5) * 2; // -1..1
      const score = edge * (Math.abs(pc) / 100) * conf;

      let type: Signal['type'] = 'hold';
      let strength: Signal['strength'] = 'weak';
      if (conf >= 0.6) {
        if (score >= 0.2 && pc > 0.3) { type = 'entry'; strength = score >= 0.3 ? 'strong' : 'moderate'; }
        else if (score <= -0.2 && pc < -0.3) { type = 'exit'; strength = score <= -0.3 ? 'strong' : 'moderate'; }
        else { type = 'hold'; strength = 'moderate'; }
      }

      const reason = `${type === 'entry' ? 'Bullish' : type === 'exit' ? 'Bearish' : 'Neutral'} signal (${p.horizon}): ${(up*100).toFixed(0)}% up, ${pc.toFixed(2)}% expected change, ${(conf*100).toFixed(0)}% confidence`;
      const thisSignal: Signal = { type, strength, reason };
      if (Math.abs(score) > Math.abs(bestScore)) {
        bestScore = score;
        best = thisSignal;
      }
    }

    return best;
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight">AI-Powered Predictions & Token Health</h1>
          <p className="text-muted-foreground mt-2">
            Know the right time to buy or sell with AI-powered predictions
          </p>
        </div>

        {/* Popular Symbols */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Popular Cryptocurrencies</CardTitle>
            <CardDescription>Click on any cryptocurrency to view AI-powered predictions</CardDescription>
          </CardHeader>
          <CardContent>
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
            {prediction.factors?.map((factor, index) => (
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
