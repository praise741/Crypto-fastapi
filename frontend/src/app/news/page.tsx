'use client';

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Newspaper,
  Search,
  ExternalLink,
  Clock,
  TrendingUp,
  AlertCircle,
  Filter
} from 'lucide-react';
import { apiClient } from '@/lib/api-client';
import { formatDate } from '@/lib/utils';

interface NewsArticle {
  id: string;
  title: string;
  summary: string;
  url: string;
  source: string;
  published_at: string;
  sentiment?: 'positive' | 'negative' | 'neutral';
  symbols: string[];
  category?: string;
}

interface NewsFilters {
  symbol?: string;
  category?: string;
  sentiment?: string;
}

interface NewsResponse {
  success: boolean;
  data: {
    articles?: NewsArticle[];
  };
}

export default function NewsPage() {
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [filteredArticles, setFilteredArticles] = useState<NewsArticle[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState<NewsFilters>({});
  const [showFilters, setShowFilters] = useState(false);

  const filterArticles = useCallback(() => {
    let filtered = [...articles];

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(article =>
        article.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        article.summary.toLowerCase().includes(searchTerm.toLowerCase()) ||
        article.symbols.some(symbol => symbol.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }

    // Filter by symbol
    if (filters.symbol) {
      filtered = filtered.filter(article =>
        article.symbols.includes(filters.symbol!.toUpperCase())
      );
    }

    // Filter by sentiment
    if (filters.sentiment) {
      filtered = filtered.filter(article =>
        article.sentiment === filters.sentiment
      );
    }

    // Filter by category
    if (filters.category) {
      filtered = filtered.filter(article =>
        article.category === filters.category
      );
    }

    setFilteredArticles(filtered);
  }, [articles, searchTerm, filters]);

  useEffect(() => {
    loadNews();
  }, []);

  useEffect(() => {
    filterArticles();
  }, [filterArticles]);

  const loadNews = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.getNews({ limit: 50 });

      // Accept both { data: { articles: [...] } } and { data: { news: [...] } }
      if ((response as unknown as NewsResponse).success && (response as { data?: unknown }).data) {
        type RawNews = {
          id?: string;
          title?: string;
          summary?: string;
          description?: string;
          url?: string;
          source?: string;
          published_at?: string;
          sentiment?: 'positive' | 'negative' | 'neutral' | string;
          symbols?: string[];
          category?: string;
        };

        const data = (response as { data: { articles?: RawNews[]; news?: RawNews[] } }).data;
        const sourceArr: RawNews[] = (data.articles ?? data.news) ?? [];

        const normalized: NewsArticle[] = Array.isArray(sourceArr)
          ? sourceArr.map((item, idx): NewsArticle => ({
              id: item.id ?? item.url ?? String(idx),
              title: item.title ?? '',
              summary: item.summary ?? item.description ?? '',
              url: item.url ?? '#',
              source: item.source ?? 'Unknown',
              published_at: item.published_at ?? new Date().toISOString(),
              sentiment: (item.sentiment as NewsArticle['sentiment']) ?? 'neutral',
              symbols: Array.isArray(item.symbols) ? item.symbols : [],
              category: item.category,
            }))
          : [];

        setArticles(normalized);
      } else {
        // Use mock data if API fails
        const mockArticles: NewsArticle[] = [
          {
            id: '1',
            title: 'Bitcoin Surges Past $70,000 as Institutional Adoption Accelerates',
            summary: 'Bitcoin reaches new all-time high as major financial institutions announce increased cryptocurrency holdings and integration plans.',
            url: 'https://example.com/news1',
            source: 'CryptoNews',
            published_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
            sentiment: 'positive',
            symbols: ['BTC'],
            category: 'Market'
          },
          {
            id: '2',
            title: 'Ethereum 2.0 Upgrade Shows Promising Results in Network Performance',
            summary: 'The latest Ethereum network upgrade demonstrates significant improvements in transaction speed and energy efficiency.',
            url: 'https://example.com/news2',
            source: 'BlockchainDaily',
            published_at: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
            sentiment: 'positive',
            symbols: ['ETH'],
            category: 'Technology'
          },
          {
            id: '3',
            title: 'Regulatory Clarity Improves as Governments Release New Crypto Frameworks',
            summary: 'Several countries announce comprehensive regulatory frameworks for digital assets, providing more certainty for investors.',
            url: 'https://example.com/news3',
            source: 'FinanceTimes',
            published_at: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
            sentiment: 'neutral',
            symbols: ['BTC', 'ETH', 'USDT'],
            category: 'Regulation'
          },
          {
            id: '4',
            title: 'DeFi Protocols Experience Record Growth in Total Value Locked',
            summary: 'Decentralized finance platforms see unprecedented growth as users seek higher yields and financial sovereignty.',
            url: 'https://example.com/news4',
            source: 'DeFiWeekly',
            published_at: new Date(Date.now() - 8 * 60 * 60 * 1000).toISOString(),
            sentiment: 'positive',
            symbols: ['UNI', 'AAVE', 'COMP'],
            category: 'DeFi'
          },
          {
            id: '5',
            title: 'Market Volatility Increases Amid Global Economic Uncertainty',
            summary: 'Cryptocurrency markets experience heightened volatility as investors react to global economic indicators and policy changes.',
            url: 'https://example.com/news5',
            source: 'MarketWatch',
            published_at: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString(),
            sentiment: 'negative',
            symbols: ['BTC', 'ETH'],
            category: 'Market'
          }
        ];
        setArticles(mockArticles);
      }
    } catch (err: unknown) {
      console.error('Failed to load news:', err);
      const errorMessage = err && typeof err === 'object' && 'response' in err
        ? (err as { response?: { data?: { error?: { message?: string } } } }).response?.data?.error?.message
        : 'Failed to load news articles';
      setError(errorMessage || 'Failed to load news articles');

      // Set mock data on error
      const mockArticles: NewsArticle[] = [
        {
          id: '1',
          title: 'Bitcoin Shows Strong Momentum as Market Sentiment Improves',
          summary: 'Market analysts observe positive trends in Bitcoin trading patterns and institutional interest.',
          url: 'https://example.com/news1',
          source: 'CryptoNews',
          published_at: new Date().toISOString(),
          sentiment: 'positive',
          symbols: ['BTC'],
          category: 'Market'
        }
      ];
      setArticles(mockArticles);
    } finally {
      setLoading(false);
    }
  };

  const getSentimentColor = (sentiment?: string) => {
    switch (sentiment) {
      case 'positive': return 'text-green-600 bg-green-100';
      case 'negative': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getSentimentIcon = (sentiment?: string) => {
    switch (sentiment) {
      case 'positive': return <TrendingUp className="h-3 w-3" />;
      case 'negative': return <AlertCircle className="h-3 w-3" />;
      default: return <Newspaper className="h-3 w-3" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Newspaper className="h-12 w-12 animate-spin mx-auto mb-4 text-primary" />
          <p className="text-muted-foreground">Loading latest news...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Newspaper className="h-8 w-8 text-primary" />
            Crypto News
          </h1>
          <p className="text-muted-foreground mt-2">
            Stay updated with the latest cryptocurrency news and market insights
          </p>
        </div>

        {/* Search and Filters */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              Search & Filter News
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowFilters(!showFilters)}
              >
                <Filter className="h-4 w-4 mr-2" />
                {showFilters ? 'Hide' : 'Show'} Filters
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Search */}
            <div className="flex gap-2">
              <Input
                placeholder="Search news, symbols, or keywords..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="flex-1"
              />
              <Button variant="outline">
                <Search className="h-4 w-4" />
              </Button>
            </div>

            {/* Filters */}
            {showFilters && (
              <div className="grid gap-4 md:grid-cols-3">
                <div>
                  <label className="text-sm font-medium mb-2 block">Symbol</label>
                  <Input
                    placeholder="e.g., BTC, ETH"
                    value={filters.symbol || ''}
                    onChange={(e) => setFilters({ ...filters, symbol: e.target.value.toUpperCase() })}
                  />
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">Sentiment</label>
                  <select
                    className="w-full p-2 border rounded-md"
                    value={filters.sentiment || ''}
                    onChange={(e) => setFilters({ ...filters, sentiment: e.target.value || undefined })}
                  >
                    <option value="">All Sentiments</option>
                    <option value="positive">Positive</option>
                    <option value="neutral">Neutral</option>
                    <option value="negative">Negative</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">Category</label>
                  <select
                    className="w-full p-2 border rounded-md"
                    value={filters.category || ''}
                    onChange={(e) => setFilters({ ...filters, category: e.target.value || undefined })}
                  >
                    <option value="">All Categories</option>
                    <option value="Market">Market</option>
                    <option value="Technology">Technology</option>
                    <option value="Regulation">Regulation</option>
                    <option value="DeFi">DeFi</option>
                  </select>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Error Display */}
        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* News Articles */}
        <div className="space-y-6">
          {filteredArticles.length > 0 ? (
            filteredArticles.map((article) => (
              <Card key={article.id} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        {article.sentiment && (
                          <Badge className={getSentimentColor(article.sentiment)}>
                            {getSentimentIcon(article.sentiment)}
                            <span className="ml-1 capitalize">{article.sentiment}</span>
                          </Badge>
                        )}
                        {article.category && (
                          <Badge variant="outline">{article.category}</Badge>
                        )}
                        {article.symbols.length > 0 && (
                          <div className="flex gap-1">
                            {article.symbols.slice(0, 3).map((symbol) => (
                              <Badge key={symbol} variant="secondary" className="text-xs">
                                {symbol}
                              </Badge>
                            ))}
                            {article.symbols.length > 3 && (
                              <Badge variant="secondary" className="text-xs">
                                +{article.symbols.length - 3}
                              </Badge>
                            )}
                          </div>
                        )}
                      </div>
                      <CardTitle className="text-xl mb-2 leading-tight">
                        {article.title}
                      </CardTitle>
                      <CardDescription className="text-sm">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="font-medium">{article.source}</span>
                          <span>•</span>
                          <div className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            <span>{formatDate(article.published_at)}</span>
                          </div>
                        </div>
                        <p className="text-base leading-relaxed">{article.summary}</p>
                      </CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex justify-between items-center">
                    <div className="text-sm text-muted-foreground">
                      {article.symbols.length > 0 && (
                        <span>Related: {article.symbols.join(', ')}</span>
                      )}
                    </div>
                    <Button variant="outline" size="sm" asChild>
                      <a
                        href={article.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-2"
                      >
                        Read More
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-16">
                <Newspaper className="h-16 w-16 text-muted-foreground mb-4" />
                <h3 className="text-xl font-semibold mb-2">No News Found</h3>
                <p className="text-muted-foreground text-center">
                  {searchTerm || filters.symbol || filters.sentiment || filters.category
                    ? 'Try adjusting your search or filters to find relevant news articles.'
                    : 'No news articles are available at the moment.'}
                </p>
                {(searchTerm || Object.values(filters).some(v => v)) && (
                  <Button
                    variant="outline"
                    onClick={() => {
                      setSearchTerm('');
                      setFilters({});
                    }}
                    className="mt-4"
                  >
                    Clear All Filters
                  </Button>
                )}
              </CardContent>
            </Card>
          )}
        </div>

        {/* Refresh Button */}
        <div className="mt-8 text-center">
          <Button onClick={loadNews} variant="outline">
            <Newspaper className="h-4 w-4 mr-2" />
            Refresh News
          </Button>
        </div>
      </div>
    </div>
  );
}
