'use client';

import { useState } from 'react';
import { useAuth } from '@/context/auth-context';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Wallet, AlertCircle } from 'lucide-react';

export default function LoginPage() {
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { connectWallet } = useAuth();

  const handleConnect = async () => {
    setError('');
    setLoading(true);

    try {
      await connectWallet();
    } catch (err: unknown) {
      console.error('Connection error:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to connect wallet. Please try again.';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-3 sm:p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1 text-center p-4 sm:p-6">
          <div className="flex justify-center mb-3 sm:mb-4">
            <div className="p-2.5 sm:p-3 rounded-full bg-primary/10">
               <Wallet className="h-6 w-6 sm:h-8 sm:w-8 text-primary" />
            </div>
          </div>
          <CardTitle className="text-xl sm:text-2xl font-bold">Connect Wallet</CardTitle>
          <CardDescription className="text-sm">
            Connect your Solana wallet to access the Market Matrix dashboard
          </CardDescription>
        </CardHeader>
        <CardContent className="p-4 sm:p-6 pt-0">
          <div className="space-y-4">
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle className="text-sm">Error</AlertTitle>
                <AlertDescription className="text-xs sm:text-sm">{error}</AlertDescription>
              </Alert>
            )}
            
            <div className="bg-muted/50 p-3 sm:p-4 rounded-lg text-xs sm:text-sm text-muted-foreground text-center">
              <p>Access is restricted to token holders.</p>
              <p className="mt-1">Connect with Phantom, Solflare, or any Solana wallet to verify ownership.</p>
            </div>

            <Button 
              className="w-full h-10 sm:h-12 text-base sm:text-lg" 
              onClick={handleConnect}
              disabled={loading}
            >
              {loading ? 'Connecting...' : 'Connect Solana Wallet'}
            </Button>
          </div>
        </CardContent>
        <CardFooter className="flex justify-center text-xs sm:text-sm text-muted-foreground p-4 sm:p-6 pt-0">
            By connecting, you agree to our Terms of Service.
        </CardFooter>
      </Card>
    </div>
  );
}
