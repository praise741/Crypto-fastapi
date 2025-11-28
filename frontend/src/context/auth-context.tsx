'use client';

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { checkTokenBalanceBackend, checkTokenBalanceClient, isTokenGatingEnabled } from '@/lib/token-gate';
// Window type definition is in src/types/window.d.ts (auto-included by TypeScript)

interface AuthContextType {
  walletAddress: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isTokenHolder: boolean;
  tokenBalance: string | null;
  connectWallet: () => Promise<void>;
  logout: () => void;
  checkTokenBalance: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [walletAddress, setWalletAddress] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isTokenHolder, setIsTokenHolder] = useState(false);
  const [tokenBalance, setTokenBalance] = useState<string | null>(null);
  const router = useRouter();

  // Check if user holds the required token
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
      // Try backend verification first (more secure, doesn't require wallet extension for check)
      const result = await checkTokenBalanceBackend(walletAddress);
      if (result.verified) {
        setIsTokenHolder(result.hasTokens);
        setTokenBalance(result.balance);
        return result.hasTokens;
      }
      
      // Fallback to client-side if backend verification failed
      if (window.ethereum) {
        const clientResult = await checkTokenBalanceClient(walletAddress);
        setIsTokenHolder(clientResult.hasTokens);
        setTokenBalance(clientResult.balance);
        return clientResult.hasTokens;
      }
      
      // No verification method available
      console.warn('No verification method available');
      setIsTokenHolder(false);
      setTokenBalance(null);
      return false;
    } catch (error) {
      console.error('Failed to check token balance:', error);
      setIsTokenHolder(false);
      setTokenBalance(null);
      return false;
    }
  }, [walletAddress]);

  useEffect(() => {
    const checkConnection = async () => {
      try {
        // Check if previously connected
        const storedAddress = localStorage.getItem('wallet_address');
        
        if (storedAddress && window.ethereum) {
            // Verify if we still have access
            const accounts = await window.ethereum.request({ method: 'eth_accounts' }) as string[];
            if (accounts.length > 0 && accounts[0].toLowerCase() === storedAddress.toLowerCase()) {
                setWalletAddress(accounts[0]);
            } else {
                // Disconnected or changed account
                localStorage.removeItem('wallet_address');
                setWalletAddress(null);
            }
        }
      } catch (error) {
        console.error("Failed to check wallet connection", error);
      } finally {
        setIsLoading(false);
      }
    };

    checkConnection();
    
    // Listen for account changes
    if (window.ethereum) {
        const handleAccountsChanged = (params: unknown) => {
            const accounts = params as string[];
            if (accounts.length > 0) {
                setWalletAddress(accounts[0]);
                localStorage.setItem('wallet_address', accounts[0]);
            } else {
                setWalletAddress(null);
                localStorage.removeItem('wallet_address');
                router.push('/login');
            }
        };
        
        window.ethereum.on('accountsChanged', handleAccountsChanged);
        
        return () => {
             if (window.ethereum?.removeListener) {
                window.ethereum.removeListener('accountsChanged', handleAccountsChanged);
             }
        };
    }
  }, [router]);

  // Check token balance when wallet address changes
  useEffect(() => {
    if (walletAddress) {
      checkTokenBalance();
    } else {
      setIsTokenHolder(false);
      setTokenBalance(null);
    }
  }, [walletAddress, checkTokenBalance]);

  const connectWallet = async () => {
    if (!window.ethereum) {
      alert("Please install MetaMask or another Web3 wallet!");
      return;
    }

    try {
      const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' }) as string[];
      if (accounts.length > 0) {
        setWalletAddress(accounts[0]);
        localStorage.setItem('wallet_address', accounts[0]);
        router.push('/dashboard');
      }
    } catch (error) {
      console.error("User denied wallet connection", error);
      throw error;
    }
  };

  const logout = () => {
    setWalletAddress(null);
    setIsTokenHolder(false);
    setTokenBalance(null);
    localStorage.removeItem('wallet_address');
    router.push('/login');
  };

  return (
    <AuthContext.Provider
      value={{
        walletAddress,
        isLoading,
        isAuthenticated: !!walletAddress,
        isTokenHolder,
        tokenBalance,
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
