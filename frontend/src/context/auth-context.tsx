'use client';

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useWallet } from '@solana/wallet-adapter-react';
import { useWalletModal } from '@solana/wallet-adapter-react-ui';
import { checkSolanaTokenBalance, isTokenGatingEnabled } from '@/lib/token-gate';

interface AuthContextType {
  walletAddress: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isTokenHolder: boolean;
  tokenBalance: string | null;
  walletType: 'solana' | 'evm' | null;
  connectWallet: () => Promise<void>;
  logout: () => void;
  checkTokenBalance: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isLoading, setIsLoading] = useState(true);
  const [isTokenHolder, setIsTokenHolder] = useState(false);
  const [tokenBalance, setTokenBalance] = useState<string | null>(null);
  const router = useRouter();
  
  // Solana wallet adapter hooks
  const { publicKey, connected, disconnect, connecting } = useWallet();
  const { setVisible } = useWalletModal();
  
  // Derive wallet address from Solana wallet
  const walletAddress = publicKey?.toBase58() || null;
  const walletType = connected ? 'solana' : null;

  // Check if user holds the required SPL token
  const checkTokenBalance = useCallback(async (): Promise<boolean> => {
    if (!walletAddress) {
      setIsTokenHolder(false);
      setTokenBalance(null);
      return false;
    }

    // If no token gate is configured, everyone is considered a token holder
    if (!isTokenGatingEnabled()) {
      setIsTokenHolder(true);
      setTokenBalance('N/A');
      return true;
    }

    try {
      const result = await checkSolanaTokenBalance(walletAddress);
      setIsTokenHolder(result.hasTokens);
      setTokenBalance(result.balance);
      return result.hasTokens;
    } catch (error) {
      console.error('Failed to check token balance:', error);
      setIsTokenHolder(false);
      setTokenBalance(null);
      return false;
    }
  }, [walletAddress]);

  // Handle initial loading state
  useEffect(() => {
    // Give wallet adapter time to auto-connect
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 1000);
    
    return () => clearTimeout(timer);
  }, []);

  // Update loading state when connecting
  useEffect(() => {
    if (connecting) {
      setIsLoading(true);
    } else {
      setIsLoading(false);
    }
  }, [connecting]);

  // Check token balance when wallet connects
  useEffect(() => {
    if (walletAddress && connected) {
      checkTokenBalance();
    } else {
      setIsTokenHolder(false);
      setTokenBalance(null);
    }
  }, [walletAddress, connected, checkTokenBalance]);

  // Redirect to dashboard after successful connection
  useEffect(() => {
    if (connected && walletAddress && !isLoading) {
      const currentPath = window.location.pathname;
      if (currentPath === '/login') {
        router.push('/dashboard');
      }
    }
  }, [connected, walletAddress, isLoading, router]);

  const connectWallet = async () => {
    // Open Solana wallet modal (Phantom, Solflare, etc.)
    setVisible(true);
  };

  const logout = async () => {
    try {
      await disconnect();
    } catch (error) {
      console.error('Failed to disconnect:', error);
    }
    setIsTokenHolder(false);
    setTokenBalance(null);
    router.push('/login');
  };

  return (
    <AuthContext.Provider
      value={{
        walletAddress,
        isLoading,
        isAuthenticated: connected && !!walletAddress,
        isTokenHolder,
        tokenBalance,
        walletType,
        connectWallet,
        logout,
        checkTokenBalance,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
