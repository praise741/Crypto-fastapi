'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/auth-context';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ShieldAlert, Wallet, RefreshCw } from 'lucide-react';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requireTokenHolder?: boolean; // If true, also requires token ownership (defaults to true for real token gating)
}

export function ProtectedRoute({ children, requireTokenHolder = true }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, isTokenHolder, walletAddress, checkTokenBalance } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null; // Will redirect
  }

  // If token holder check is required but user doesn't hold tokens
  if (requireTokenHolder && !isTokenHolder) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background p-3 sm:p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="space-y-1 text-center p-4 sm:p-6">
            <div className="flex justify-center mb-3 sm:mb-4">
              <div className="p-2.5 sm:p-3 rounded-full bg-destructive/10">
                <ShieldAlert className="h-6 w-6 sm:h-8 sm:w-8 text-destructive" />
              </div>
            </div>
            <CardTitle className="text-xl sm:text-2xl font-bold">Token Required</CardTitle>
            <CardDescription className="text-sm">
              This feature requires you to hold Market Matrix tokens
            </CardDescription>
          </CardHeader>
          <CardContent className="p-4 sm:p-6 pt-0">
            <div className="space-y-4">
              <div className="bg-muted/50 p-3 sm:p-4 rounded-lg text-xs sm:text-sm text-muted-foreground">
                <p className="flex items-center gap-2 mb-2 flex-wrap">
                  <Wallet className="h-4 w-4 flex-shrink-0" />
                  <span className="font-medium">Connected:</span>
                  <code className="text-xs break-all">{walletAddress?.slice(0, 6)}...{walletAddress?.slice(-4)}</code>
                </p>
                <p className="text-center mt-3">
                  You need to hold the required tokens to access this feature.
                </p>
              </div>
              
              <Button 
                className="w-full h-10 sm:h-11 text-sm" 
                variant="outline"
                onClick={() => checkTokenBalance()}
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Check Balance Again
              </Button>
              
              <Button 
                className="w-full h-10 sm:h-11 text-sm" 
                variant="default"
                onClick={() => router.push('/')}
              >
                Go to Home
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return <>{children}</>;
}
