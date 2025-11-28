/**
 * Token Gating Utilities for Solana SPL Tokens
 * 
 * This module provides token gating for Solana/pump.fun tokens:
 * 1. Client-side check via Solana RPC
 * 2. Backend-verified check for extra security
 */

// Token gate configuration for Solana
export const TOKEN_CONFIG = {
  // SPL Token mint address (from pump.fun or any Solana token)
  address: process.env.NEXT_PUBLIC_TOKEN_GATE_ADDRESS || '',
  // Minimum balance required (in smallest units - for 6 decimals: 500000 = 0.5 tokens)
  minBalance: process.env.NEXT_PUBLIC_MIN_TOKEN_BALANCE || '1',
  // Solana RPC endpoint
  rpcUrl: process.env.NEXT_PUBLIC_SOLANA_RPC_URL || 'https://api.mainnet-beta.solana.com',
};

/**
 * Check SPL token balance using Solana RPC
 * Works with pump.fun tokens and any SPL token
 */
export async function checkSolanaTokenBalance(
  walletAddress: string
): Promise<{ hasTokens: boolean; balance: string }> {
  if (!TOKEN_CONFIG.address) {
    return { hasTokens: true, balance: 'N/A' }; // No gating configured
  }

  try {
    // Use Solana RPC to get token accounts
    const response = await fetch(TOKEN_CONFIG.rpcUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        jsonrpc: '2.0',
        id: 1,
        method: 'getTokenAccountsByOwner',
        params: [
          walletAddress,
          { mint: TOKEN_CONFIG.address },
          { encoding: 'jsonParsed' }
        ]
      })
    });

    const data = await response.json();
    
    if (data.error) {
      console.error('Solana RPC error:', data.error);
      return { hasTokens: false, balance: '0' };
    }

    // Check if user has any token accounts for this mint
    const accounts = data.result?.value || [];
    
    if (accounts.length === 0) {
      return { hasTokens: false, balance: '0' };
    }

    // Sum up balance from all token accounts
    let totalBalance = BigInt(0);
    for (const account of accounts) {
      const amount = account.account?.data?.parsed?.info?.tokenAmount?.amount || '0';
      totalBalance += BigInt(amount);
    }

    const minBalanceBigInt = BigInt(TOKEN_CONFIG.minBalance);
    const hasTokens = totalBalance >= minBalanceBigInt;

    return {
      hasTokens,
      balance: totalBalance.toString(),
    };
  } catch (error) {
    console.error('Solana token check failed:', error);
    return { hasTokens: false, balance: '0' };
  }
}

/**
 * Backend-verified Solana token check (more secure)
 * Your backend should verify using Solana RPC
 */
export async function checkSolanaTokenBalanceBackend(
  walletAddress: string
): Promise<{ hasTokens: boolean; balance: string; verified: boolean }> {
  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
    
    const response = await fetch(`${apiUrl}/api/v1/auth/verify-solana-token-holder`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        wallet_address: walletAddress,
        token_mint: TOKEN_CONFIG.address,
        min_balance: TOKEN_CONFIG.minBalance,
      }),
    });

    if (!response.ok) {
      throw new Error('Backend verification failed');
    }

    const data = await response.json();
    return {
      hasTokens: data.is_holder || false,
      balance: data.balance || '0',
      verified: data.verified || false,
    };
  } catch (error) {
    console.error('Backend Solana token check failed:', error);
    // Fallback to client-side check
    const clientResult = await checkSolanaTokenBalance(walletAddress);
    return { ...clientResult, verified: false };
  }
}

/**
 * Check if token gating is enabled
 */
export function isTokenGatingEnabled(): boolean {
  return !!TOKEN_CONFIG.address && 
         TOKEN_CONFIG.address.length > 30 && // Solana addresses are ~44 chars
         TOKEN_CONFIG.address !== '0x0000000000000000000000000000000000000000';
}

/**
 * Format token balance for display
 * pump.fun tokens typically have 6 decimals
 */
export function formatTokenBalance(balance: string, decimals: number = 6): string {
  if (balance === 'N/A') return balance;
  
  try {
    const balanceBigInt = BigInt(balance);
    const divisor = BigInt(10 ** decimals);
    const wholePart = balanceBigInt / divisor;
    const fractionalPart = balanceBigInt % divisor;
    
    if (fractionalPart === BigInt(0)) {
      return wholePart.toString();
    }
    
    const fractionalStr = fractionalPart.toString().padStart(decimals, '0');
    return `${wholePart}.${fractionalStr.replace(/0+$/, '')}`;
  } catch {
    return balance;
  }
}
