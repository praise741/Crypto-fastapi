/**
 * Token Gating Utilities
 * 
 * This module provides multiple methods for token gating:
 * 1. Client-side (current) - Uses wallet extension directly
 * 2. Backend-verified - Calls your backend API to verify
 * 3. Signature-based - User signs a message to prove ownership
 */

// Token gate configuration
export const TOKEN_CONFIG = {
  address: process.env.NEXT_PUBLIC_TOKEN_GATE_ADDRESS || '',
  minBalance: process.env.NEXT_PUBLIC_MIN_TOKEN_BALANCE || '1',
  chainId: process.env.NEXT_PUBLIC_TOKEN_CHAIN_ID || '1', // Default: Ethereum mainnet
  // Chain IDs: 1=Ethereum, 56=BSC, 137=Polygon, 8453=Base, 42161=Arbitrum, 10=Optimism
};

// ERC-20 ABI for balanceOf
const ERC20_BALANCE_OF_SELECTOR = '0x70a08231';

/**
 * Method 1: Client-side token check (requires wallet extension)
 * Pros: No backend needed, real-time
 * Cons: Requires extension, can be bypassed
 */
export async function checkTokenBalanceClient(
  walletAddress: string
): Promise<{ hasTokens: boolean; balance: string }> {
  if (!TOKEN_CONFIG.address || !window.ethereum) {
    return { hasTokens: true, balance: 'N/A' }; // No gating configured
  }

  try {
    const paddedAddress = walletAddress.slice(2).padStart(64, '0');
    const data = ERC20_BALANCE_OF_SELECTOR + paddedAddress;

    const balance = await window.ethereum.request({
      method: 'eth_call',
      params: [{ to: TOKEN_CONFIG.address, data }, 'latest'],
    }) as string;

    const balanceBigInt = BigInt(balance);
    const minBalanceBigInt = BigInt(TOKEN_CONFIG.minBalance);

    return {
      hasTokens: balanceBigInt >= minBalanceBigInt,
      balance: balanceBigInt.toString(),
    };
  } catch (error) {
    console.error('Client token check failed:', error);
    return { hasTokens: false, balance: '0' };
  }
}

/**
 * Method 2: Backend-verified token check (more secure)
 * Pros: Can't be bypassed, works without wallet extension for viewing
 * Cons: Requires backend endpoint, slight delay
 * 
 * Your backend should call an RPC provider (Alchemy, Infura, etc.)
 * to verify the token balance server-side.
 */
export async function checkTokenBalanceBackend(
  walletAddress: string,
  signature?: string // Optional: signed message to prove ownership
): Promise<{ hasTokens: boolean; balance: string; verified: boolean }> {
  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
    
    const response = await fetch(`${apiUrl}/api/v1/auth/verify-token-holder`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        wallet_address: walletAddress,
        token_address: TOKEN_CONFIG.address,
        min_balance: TOKEN_CONFIG.minBalance,
        chain_id: TOKEN_CONFIG.chainId,
        signature, // Optional signature for extra verification
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
    console.error('Backend token check failed:', error);
    // Fallback to client-side check
    const clientResult = await checkTokenBalanceClient(walletAddress);
    return { ...clientResult, verified: false };
  }
}

/**
 * Method 3: Signature-based verification
 * User signs a message to prove they own the wallet
 * Combined with backend check for maximum security
 */
export async function signAndVerify(
  walletAddress: string
): Promise<{ signature: string; message: string } | null> {
  if (!window.ethereum) {
    return null;
  }

  try {
    const timestamp = Date.now();
    const message = `Verify token ownership for Market Matrix\n\nWallet: ${walletAddress}\nTimestamp: ${timestamp}`;

    const signature = await window.ethereum.request({
      method: 'personal_sign',
      params: [message, walletAddress],
    }) as string;

    return { signature, message };
  } catch (error) {
    console.error('Signature failed:', error);
    return null;
  }
}

/**
 * Combined verification: Best of both worlds
 * 1. User signs message (proves wallet ownership)
 * 2. Backend verifies signature + checks token balance via RPC
 */
export async function verifyTokenHolderSecure(
  walletAddress: string
): Promise<{ hasTokens: boolean; verified: boolean }> {
  // Step 1: Get signature
  const signResult = await signAndVerify(walletAddress);
  if (!signResult) {
    return { hasTokens: false, verified: false };
  }

  // Step 2: Send to backend for verification
  const result = await checkTokenBalanceBackend(walletAddress, signResult.signature);
  return {
    hasTokens: result.hasTokens,
    verified: result.verified,
  };
}

/**
 * Check if token gating is enabled
 */
export function isTokenGatingEnabled(): boolean {
  return !!TOKEN_CONFIG.address && TOKEN_CONFIG.address !== '0x0000000000000000000000000000000000000000';
}
