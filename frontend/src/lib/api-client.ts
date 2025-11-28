import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';

// Extend InternalAxiosRequestConfig to include metadata
interface ExtendedAxiosRequestConfig extends InternalAxiosRequestConfig {
  metadata?: {
    startTime: number;
  };
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.102-212-247-217.sslip.io';
const API_VERSION = '/api/v1';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: `${API_BASE_URL}${API_VERSION}`,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000,
    });

    // Request interceptor with timing
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const token = this.getToken();
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`;
        }

        // Add request start time for timing measurement
        const extendedConfig = config as ExtendedAxiosRequestConfig;
        extendedConfig.metadata = { startTime: Date.now() };

        return extendedConfig;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor with timing
    this.client.interceptors.response.use(
      (response) => {
        // Handle backend response structure { success, data, meta }
        if (response.data && typeof response.data === 'object' && 'success' in response.data) {
          return response.data;
        }

        // Fallback for direct response data
        return response.data;
      },
      (error: AxiosError) => {
        // Note: Removed 401 redirect since we removed auth pages
        return Promise.reject(error);
      }
    );
  }

  private getToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('access_token');
    }
    return null;
  }

  private clearToken(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
  }

  setToken(token: string): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', token);
    }
  }

  setRefreshToken(token: string): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem('refresh_token', token);
    }
  }

  // Health endpoints
  async getHealth() {
    return this.client.get('/health');
  }

  async getDetailedHealth() {
    return this.client.get('/health/detailed');
  }

  // Market data endpoints
  async getMarketPrices() {
    return this.client.get('/market/prices');
  }

  async getTrending() {
    return this.client.get('/market/trending');
  }

  async getSymbolPrice(symbol: string) {
    return this.client.get(`/market/${symbol}/price`);
  }

  async getSymbolTicker(symbol: string) {
    return this.client.get(`/market/${symbol}/ticker`);
  }

  async getOHLCV(symbol: string, params?: { interval?: string; start_time?: string; end_time?: string; limit?: number }) {
    return this.client.get(`/market/${symbol}/ohlcv`, { params });
  }

  async getIndicators(symbol: string, params?: { set?: string; period?: number; interval?: string }) {
    return this.client.get(`/market/${symbol}/indicators`, { params });
  }

  async getMarketDepth(symbol: string) {
    return this.client.get(`/market/${symbol}/depth`);
  }

  async getTrades(symbol: string, limit: number = 50) {
    return this.client.get(`/market/${symbol}/trades`, { params: { limit } });
  }

  // Prediction endpoints
  async getPredictions(symbol: string, params?: { horizons?: string; include_confidence?: boolean; include_factors?: boolean }) {
    return this.client.get(`/predictions/${symbol}`, { params });
  }

  // New: predictions by contract address (backend now supports this)
  async getPredictionsByContract(contractAddress: string, chainId?: string | number, params?: { horizons?: string; include_confidence?: boolean; include_factors?: boolean }) {
    return this.client.post('/predictions/by-contract', {
      contract_address: contractAddress,
      ...(chainId !== undefined && chainId !== null ? { chain_id: chainId } : {}),
      ...(params?.horizons ? { horizons: params.horizons } : {}),
      ...(params?.include_confidence !== undefined ? { include_confidence: params.include_confidence } : {}),
      ...(params?.include_factors !== undefined ? { include_factors: params.include_factors } : {}),
    });
  }

  // Contract endpoints
  async getContractData(contractAddress: string) {
    return this.client.get(`/contracts/${contractAddress}`);
  }

  async getContractPairs(contractAddress: string) {
    return this.client.get(`/contracts/${contractAddress}/pairs`);
  }

  async getBatchPredictions(symbols: string[], horizons: string[]) {
    return this.client.post('/predictions/batch', { symbols, horizons });
  }

  async getPredictionHistory(symbol: string, params?: { start_date?: string; end_date?: string }) {
    return this.client.get(`/predictions/${symbol}/history`, { params });
  }

  // Token Health endpoints
  async getTokenHealth(symbol: string) {
    return this.client.get(`/token-health/${symbol}`);
  }

  async analyzeToken(symbol: string) {
    return this.client.get(`/token-health/${symbol}`);
  }

  // Token Analytics endpoints
  async analyzeTokenByContract(contractAddress: string, chainId?: string) {
    return this.client.post('/token-analytics/analyze', {
      contract_address: contractAddress,
      ...(chainId && { chain_id: chainId })
    });
  }

  // Portfolio endpoints
  async uploadPortfolio(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    return this.client.post('/portfolio/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  }

  async getHoldings() {
    return this.client.get('/portfolio/holdings');
  }

  async getPerformance(window: string = '30d') {
    return this.client.get('/portfolio/performance', { params: { window } });
  }

  async getAllocation() {
    return this.client.get('/portfolio/allocation');
  }

  // Insights endpoints
  async getInsightsSummary(symbol: string, window: string = '24h') {
    return this.client.get('/insights/summary', { params: { symbol, window } });
  }

  async getInsightsEvents(symbol: string, limit: number = 10) {
    return this.client.get('/insights/events', { params: { symbol, limit } });
  }

  // Analytics endpoints
  async getCorrelations(symbols?: string[]) {
    return this.client.get('/analytics/correlations', { params: { symbols: symbols?.join(',') } });
  }

  async getVolatility(symbol?: string) {
    return this.client.get('/analytics/volatility', { params: { symbol } });
  }

  async getTrends() {
    return this.client.get('/analytics/trends');
  }

  async getTopPerformers(limit: number = 10) {
    return this.client.get('/analytics/top-performers', { params: { limit } });
  }

  // Indices endpoints
  async getIndices() {
    return this.client.get('/indices');
  }

  async getFearGreedIndex() {
    return this.client.get('/indices/fear-greed');
  }

  async getAltseasonIndex() {
    return this.client.get('/indices/altseason');
  }

  async getDominance() {
    return this.client.get('/indices/dominance');
  }

  // Dashboard endpoints
  async getDashboard() {
    return this.client.get('/dashboard');
  }

  async getDashboardMetrics() {
    return this.client.get('/dashboard/metrics');
  }

  // News endpoints
  async getNews(params?: { symbol?: string; limit?: number }) {
    return this.client.get('/news', { params });
  }

  // Alerts endpoints
  async getAlerts() {
    return this.client.get('/alerts');
  }

  async createAlert(data: Record<string, unknown>) {
    return this.client.post('/alerts', data);
  }

  async updateAlert(id: string, data: Record<string, unknown>) {
    return this.client.put(`/alerts/${id}`, data);
  }

  async deleteAlert(id: string) {
    return this.client.delete(`/alerts/${id}`);
  }

  // Auth endpoints
  async login(email: string, password: string) {
    return this.client.post('/auth/login', { email, password });
  }

  async register(email: string, password: string) {
    return this.client.post('/auth/register', { email, password });
  }

  async logout() {
    this.clearToken();
  }

  async refreshToken() {
    const refreshToken = typeof window !== 'undefined' ? localStorage.getItem('refresh_token') : null;
    if (!refreshToken) throw new Error('No refresh token');
    return this.client.post('/auth/refresh', { refresh_token: refreshToken });
  }

  async getMe() {
    return this.client.get('/auth/me');
  }
}

export const apiClient = new ApiClient();
export default apiClient;
