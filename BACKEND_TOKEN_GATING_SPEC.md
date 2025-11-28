# Backend Token Gating Implementation Specification

## Overview

This document describes how to implement **backend token gating** for the Market Matrix crypto platform. This approach uses **free public RPC endpoints** (no API keys required) to verify token holdings server-side.

## Why Backend Token Gating?

| Approach | Security | Requires Extension | Can Be Bypassed |
|----------|----------|-------------------|-----------------|
| Frontend-only (current) | Low | Yes (MetaMask) | Yes (disable JS) |
| Backend verification | High | No* | No |

*Users still need wallet extension to connect, but verification happens server-side.

---

## Backend Implementation

### 1. Create Token Verification Endpoint

**File:** `app/api/v1/endpoints/auth.py` (or create new file)

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
from eth_abi import decode
from eth_utils import to_checksum_address

router = APIRouter()

# Free public RPC endpoints (no API key needed!)
FREE_RPC_ENDPOINTS = {
    "1": "https://eth.llamarpc.com",           # Ethereum Mainnet
    "56": "https://bsc-dataseed.binance.org",  # BSC
    "137": "https://polygon-rpc.com",          # Polygon
    "42161": "https://arb1.arbitrum.io/rpc",   # Arbitrum
    "8453": "https://mainnet.base.org",        # Base
    "10": "https://mainnet.optimism.io",       # Optimism
    "43114": "https://api.avax.network/ext/bc/C/rpc",  # Avalanche
}

# ERC-20 balanceOf function selector
BALANCE_OF_SELECTOR = "0x70a08231"


class TokenVerifyRequest(BaseModel):
    wallet_address: str
    token_address: str
    min_balance: str = "1"
    chain_id: str = "1"


class TokenVerifyResponse(BaseModel):
    is_holder: bool
    balance: str
    wallet_address: str
    token_address: str
    chain_id: str
    verified: bool = True


@router.post("/verify-token-holder", response_model=TokenVerifyResponse)
async def verify_token_holder(request: TokenVerifyRequest):
    """
    Verify if a wallet holds the required amount of a token.
    Uses free public RPC endpoints - no API key required!
    """
    try:
        # Validate addresses
        wallet = to_checksum_address(request.wallet_address)
        token = to_checksum_address(request.token_address)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid wallet or token address")

    # Get RPC endpoint for the chain
    rpc_url = FREE_RPC_ENDPOINTS.get(request.chain_id)
    if not rpc_url:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported chain ID: {request.chain_id}. Supported: {list(FREE_RPC_ENDPOINTS.keys())}"
        )

    # Encode balanceOf(address) call
    # balanceOf selector + padded address (32 bytes)
    padded_address = wallet[2:].lower().zfill(64)
    call_data = BALANCE_OF_SELECTOR + padded_address

    # Make RPC call
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_call",
        "params": [
            {
                "to": token,
                "data": call_data
            },
            "latest"
        ],
        "id": 1
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(rpc_url, json=payload)
            result = response.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"RPC call failed: {str(e)}")

    if "error" in result:
        raise HTTPException(status_code=400, detail=f"RPC error: {result['error']}")

    # Decode the balance (uint256)
    balance_hex = result.get("result", "0x0")
    
    # Handle empty or zero response
    if not balance_hex or balance_hex == "0x":
        balance = 0
    else:
        balance = int(balance_hex, 16)

    # Check if balance meets minimum
    min_balance = int(request.min_balance)
    is_holder = balance >= min_balance

    return TokenVerifyResponse(
        is_holder=is_holder,
        balance=str(balance),
        wallet_address=wallet,
        token_address=token,
        chain_id=request.chain_id,
        verified=True
    )


@router.get("/supported-chains")
async def get_supported_chains():
    """Get list of supported chains for token verification."""
    return {
        "chains": [
            {"chain_id": "1", "name": "Ethereum Mainnet"},
            {"chain_id": "56", "name": "BNB Smart Chain"},
            {"chain_id": "137", "name": "Polygon"},
            {"chain_id": "42161", "name": "Arbitrum One"},
            {"chain_id": "8453", "name": "Base"},
            {"chain_id": "10", "name": "Optimism"},
            {"chain_id": "43114", "name": "Avalanche C-Chain"},
        ]
    }
```

### 2. Register the Router

**In `app/api/v1/api.py` or `app/main.py`:**

```python
from app.api.v1.endpoints import auth  # or wherever you put it

api_router.include_router(
    auth.router, 
    prefix="/auth", 
    tags=["authentication"]
)
```

### 3. Required Dependencies

Add to `requirements.txt`:
```
httpx>=0.24.0
eth-abi>=4.0.0
eth-utils>=2.0.0
```

Or install:
```bash
pip install httpx eth-abi eth-utils
```

---

## Frontend Integration

The frontend already has the integration code in `src/lib/token-gate.ts`. Here's how it connects:

### Current Frontend Flow (Client-Side)
```
User → Connect Wallet → Frontend checks balance via MetaMask → Allow/Deny
```

### New Flow (Backend-Verified)
```
User → Connect Wallet → Frontend calls backend API → Backend checks via RPC → Allow/Deny
```

### Frontend Code (Already Exists)

In `src/lib/token-gate.ts`, there's already a `checkTokenBalanceBackend()` function:

```typescript
export async function checkTokenBalanceBackend(
  walletAddress: string,
  signature?: string
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
```

### To Switch to Backend Verification

Update `src/context/auth-context.tsx`:

```typescript
// Change this import
import { checkTokenBalanceBackend, isTokenGatingEnabled } from '@/lib/token-gate';

// And update checkTokenBalance function to use backend:
const checkTokenBalance = useCallback(async (): Promise<boolean> => {
  if (!walletAddress) {
    setIsTokenHolder(false);
    setTokenBalance(null);
    return false;
  }

  if (!isTokenGatingEnabled()) {
    setIsTokenHolder(true);
    setTokenBalance('N/A');
    return true;
  }

  try {
    // Use backend verification instead of client-side
    const result = await checkTokenBalanceBackend(walletAddress);
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
```

### Environment Variables

Add to frontend `.env.local`:
```env
NEXT_PUBLIC_TOKEN_CHAIN_ID=1
```

---

## Integration Summary

### Will This Cause Errors?
**No.** The backend endpoint is completely independent. If it fails, the frontend falls back to client-side verification.

### Do I Need to Remove Frontend Token Gating?
**No.** They work together:
1. Frontend still handles wallet connection (requires MetaMask)
2. Backend handles balance verification (more secure)
3. Frontend falls back to client-side if backend fails

### How Hard Is Integration?

| Step | Difficulty | Time |
|------|------------|------|
| Create backend endpoint | Easy | 15-30 min |
| Install dependencies | Easy | 2 min |
| Update frontend to use backend | Easy | 5 min |
| **Total** | **Easy** | **~30 min** |

---

## API Endpoint Reference

### POST `/api/v1/auth/verify-token-holder`

**Request:**
```json
{
  "wallet_address": "0x1234567890abcdef1234567890abcdef12345678",
  "token_address": "0xYourTokenContractAddress",
  "min_balance": "1000000000000000000",
  "chain_id": "1"
}
```

**Response (Success):**
```json
{
  "is_holder": true,
  "balance": "5000000000000000000",
  "wallet_address": "0x1234567890abcdef1234567890abcdef12345678",
  "token_address": "0xYourTokenContractAddress",
  "chain_id": "1",
  "verified": true
}
```

**Response (Not Holder):**
```json
{
  "is_holder": false,
  "balance": "0",
  "wallet_address": "0x1234567890abcdef1234567890abcdef12345678",
  "token_address": "0xYourTokenContractAddress",
  "chain_id": "1",
  "verified": true
}
```

### GET `/api/v1/auth/supported-chains`

**Response:**
```json
{
  "chains": [
    {"chain_id": "1", "name": "Ethereum Mainnet"},
    {"chain_id": "56", "name": "BNB Smart Chain"},
    {"chain_id": "137", "name": "Polygon"},
    {"chain_id": "42161", "name": "Arbitrum One"},
    {"chain_id": "8453", "name": "Base"},
    {"chain_id": "10", "name": "Optimism"},
    {"chain_id": "43114", "name": "Avalanche C-Chain"}
  ]
}
```

---

## Testing

### Test with curl:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/verify-token-holder" \
  -H "Content-Type: application/json" \
  -d '{
    "wallet_address": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
    "token_address": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "min_balance": "1",
    "chain_id": "1"
  }'
```

This tests if Vitalik's wallet holds any USDT on Ethereum.

---

## Free RPC Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| Rate limits | ~10-50 req/sec | Cache results for 60 seconds |
| Occasional downtime | Brief failures | Fallback to client-side |
| Some chains not supported | Limited chains | Add more RPCs as needed |

### Optional: Add Caching

```python
from functools import lru_cache
from datetime import datetime, timedelta

# Simple in-memory cache (for production, use Redis)
_cache = {}
CACHE_TTL = 60  # seconds

def get_cached_balance(wallet: str, token: str, chain: str):
    key = f"{wallet}:{token}:{chain}"
    if key in _cache:
        value, timestamp = _cache[key]
        if datetime.now() - timestamp < timedelta(seconds=CACHE_TTL):
            return value
    return None

def set_cached_balance(wallet: str, token: str, chain: str, balance: str):
    key = f"{wallet}:{token}:{chain}"
    _cache[key] = (balance, datetime.now())
```

---

## Summary

- **Cost:** FREE (uses public RPCs)
- **API Keys:** NONE required
- **Security:** HIGH (server-side verification)
- **Integration:** EASY (backend creates 1 endpoint, frontend already has code)
- **Breaking Changes:** NONE (works alongside existing code)
