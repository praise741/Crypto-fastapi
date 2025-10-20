import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatCurrency(value: number, decimals: number = 2): string {
  // Handle very small numbers by adjusting decimal places
  let adjustedDecimals = decimals;
  if (value > 0 && value < 0.001) {
    adjustedDecimals = 8; // Show more decimals for very small numbers
  } else if (value > 0 && value < 0.01) {
    adjustedDecimals = 6; // Show more decimals for small numbers
  }

  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: adjustedDecimals,
    maximumFractionDigits: adjustedDecimals,
  }).format(value)
}

export function formatNumber(value: number, decimals: number = 2): string {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value)
}

export function formatPercentage(value: number | null, decimals: number = 2): string {
  if (value === null || value === undefined) return 'N/A'
  return `${value >= 0 ? '+' : ''}${value.toFixed(decimals)}%`
}

export function formatLargeNumber(value: number): string {
  if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`
  if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`
  if (value >= 1e3) return `$${(value / 1e3).toFixed(2)}K`
  return formatCurrency(value)
}

export function getChangeColor(value: number | null): string {
  if (value === null || value === undefined) return 'text-gray-500'
  if (value > 0) return 'text-green-500'
  if (value < 0) return 'text-red-500'
  return 'text-gray-500'
}

export function getHealthColor(score: number): string {
  if (score >= 80) return 'text-green-500'
  if (score >= 60) return 'text-yellow-500'
  if (score >= 40) return 'text-orange-500'
  return 'text-red-500'
}

export function getHealthBadgeColor(score: number): string {
  if (score >= 80) return 'bg-green-500/10 text-green-500 border-green-500/20'
  if (score >= 60) return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20'
  if (score >= 40) return 'bg-orange-500/10 text-orange-500 border-orange-500/20'
  return 'bg-red-500/10 text-red-500 border-red-500/20'
}

export function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  });
}
