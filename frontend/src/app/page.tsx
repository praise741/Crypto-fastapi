import Link from 'next/link';
import { ArrowRight, Shield, TrendingUp, Wallet, BarChart3, Zap, Lock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-b from-background to-muted/20 pt-20 pb-32">
        <div className="absolute inset-0 bg-grid-white/10 bg-[size:20px_20px]" />
        <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-4xl font-bold tracking-tight sm:text-6xl bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 bg-clip-text text-transparent">
              Escape the Matrix
            </h1>
            <p className="mt-6 text-lg leading-8 text-muted-foreground max-w-2xl mx-auto">
              An innovative platform designed to empower traders and investors with a full suite of crypto tools all in one place.
            </p>
            <div className="mt-10 flex items-center justify-center gap-x-6">
              <Button size="lg" asChild>
                <Link href="/dashboard">
                  Launch App <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
              <Button size="lg" variant="outline" asChild>
                <Link href="/about">Learn More</Link>
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Problem Statement */}
      <section className="py-24 bg-muted/30">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
              What Problem Does Market Matrix Solve?
            </h2>
          </div>
          <div className="grid gap-8 md:grid-cols-3">
            <Card className="border-2 hover:border-primary/50 transition-colors">
              <CardHeader>
                <div className="h-12 w-12 rounded-lg bg-red-500/10 flex items-center justify-center mb-4">
                  <Zap className="h-6 w-6 text-red-500" />
                </div>
                <CardTitle>Overwhelming Information</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-base">
                  Crypto investors drown in charts, signals, and hype. Market Matrix filters the noise and delivers clear, data-backed insights into token health.
                </CardDescription>
              </CardContent>
            </Card>

            <Card className="border-2 hover:border-primary/50 transition-colors">
              <CardHeader>
                <div className="h-12 w-12 rounded-lg bg-yellow-500/10 flex items-center justify-center mb-4">
                  <TrendingUp className="h-6 w-6 text-yellow-500" />
                </div>
                <CardTitle>Uncertainty in Entry & Exit</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-base">
                  Most people don&apos;t know the right time to buy or sell. Market Matrix provides timely predictions on when to invest and when to exit.
                </CardDescription>
              </CardContent>
            </Card>

            <Card className="border-2 hover:border-primary/50 transition-colors">
              <CardHeader>
                <div className="h-12 w-12 rounded-lg bg-purple-500/10 flex items-center justify-center mb-4">
                  <Shield className="h-6 w-6 text-purple-500" />
                </div>
                <CardTitle>Falling into Scams & Weak Projects</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-base">
                  Too many projects are pump-and-dumps. Market Matrix acts as your reality check, exposing unhealthy tokens before they drain your wallet.
                </CardDescription>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
              Market Predictions Made Clear
            </h2>
            <p className="mt-4 text-lg text-muted-foreground">
              Empowering traders with tools that make market predictions simple, smart, and effective.
            </p>
          </div>

          <div className="grid gap-12 lg:grid-cols-2">
            <div className="space-y-8">
              <div className="flex gap-4">
                <div className="flex-shrink-0">
                  <div className="h-10 w-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
                    <BarChart3 className="h-5 w-5 text-blue-500" />
                  </div>
                </div>
                <div>
                  <h3 className="text-xl font-semibold mb-2">Advanced Trading Tools</h3>
                  <p className="text-muted-foreground">
                    Our platform includes professional-grade tools such as interactive charts and sentiment analysis.
                  </p>
                </div>
              </div>

              <div className="flex gap-4">
                <div className="flex-shrink-0">
                  <div className="h-10 w-10 rounded-lg bg-purple-500/10 flex items-center justify-center">
                    <TrendingUp className="h-5 w-5 text-purple-500" />
                  </div>
                </div>
                <div>
                  <h3 className="text-xl font-semibold mb-2">AI-Powered Price Predictions</h3>
                  <p className="text-muted-foreground">
                    Instead of relying on guesswork, users gain clear insights into short-term spikes, long-term trends, and potential risks.
                  </p>
                </div>
              </div>

              <div className="flex gap-4">
                <div className="flex-shrink-0">
                  <div className="h-10 w-10 rounded-lg bg-green-500/10 flex items-center justify-center">
                    <Wallet className="h-5 w-5 text-green-500" />
                  </div>
                </div>
                <div>
                  <h3 className="text-xl font-semibold mb-2">Portfolio Tracker</h3>
                  <p className="text-muted-foreground">
                    Detailed analytics including profit/loss breakdowns, asset allocation, and diversification analysis to optimize your portfolio for growth.
                  </p>
                </div>
              </div>
            </div>

            <div className="space-y-8">
              <div className="flex gap-4">
                <div className="flex-shrink-0">
                  <div className="h-10 w-10 rounded-lg bg-pink-500/10 flex items-center justify-center">
                    <Shield className="h-5 w-5 text-pink-500" />
                  </div>
                </div>
                <div>
                  <h3 className="text-xl font-semibold mb-2">Web3 Integration</h3>
                  <p className="text-muted-foreground">
                    Market Matrix provides on-chain analysis to measure token health, liquidity pools and smart contract safety.
                  </p>
                </div>
              </div>

              <div className="flex gap-4">
                <div className="flex-shrink-0">
                  <div className="h-10 w-10 rounded-lg bg-orange-500/10 flex items-center justify-center">
                    <BarChart3 className="h-5 w-5 text-orange-500" />
                  </div>
                </div>
                <div>
                  <h3 className="text-xl font-semibold mb-2">All-in-One Crypto Dashboard</h3>
                  <p className="text-muted-foreground">
                    Monitor token performance, market trends, and news updates all in one unified dashboard.
                  </p>
                </div>
              </div>

              <div className="flex gap-4">
                <div className="flex-shrink-0">
                  <div className="h-10 w-10 rounded-lg bg-cyan-500/10 flex items-center justify-center">
                    <Lock className="h-5 w-5 text-cyan-500" />
                  </div>
                </div>
                <div>
                  <h3 className="text-xl font-semibold mb-2">Scam Detection</h3>
                  <p className="text-muted-foreground">
                    Advanced algorithms to identify pump-and-dump schemes and protect your investments from fraudulent projects.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 bg-gradient-to-r from-blue-500 to-purple-600">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Escape the Matrix
          </h2>
          <p className="mt-4 text-lg text-white/90 max-w-2xl mx-auto">
            Market Matrix merges the transparency of blockchain with advanced market intelligence to help users make smarter, faster, and more confident decisions.
          </p>
          <div className="mt-10">
            <Button size="lg" variant="secondary" asChild>
              <Link href="/dashboard">
                Get Started <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-12 bg-muted/30">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center text-sm text-muted-foreground">
            <p>&copy; 2025 Market Matrix. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
