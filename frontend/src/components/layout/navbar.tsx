'use client';

import Link from 'next/link';
import Image from 'next/image';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  TrendingUp,
  Shield,
  Wallet,
  BarChart3,
  FileText,
  BookOpen,
  Menu,
  X
} from 'lucide-react';
import { useState } from 'react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';

interface NavItem {
  name: string;
  href: string;
  icon: React.ElementType;
  isExternal?: boolean;
  isComingSoon?: boolean;
}

const navigation: NavItem[] = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  { name: 'Predictions', href: '/predictions', icon: TrendingUp },
  { name: 'Token Prediction/Health', href: '/token-health', icon: Shield },
  { name: 'News', href: '/news', icon: FileText },
  { name: 'Docs', href: 'http://docs.marketmatrix.space', icon: BookOpen, isExternal: true },
  { name: 'Portfolio', href: '/portfolio', icon: Wallet, isComingSoon: true },
  { name: 'All-in-One Dashboard', href: '/all-in-one', icon: LayoutDashboard, isComingSoon: true },
];

export function Navbar() {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [portfolioDialogOpen, setPortfolioDialogOpen] = useState(false);

  return (
    <nav className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <div className="flex items-center">
            <a href="http://www.marketmatrix.space" target="_blank" rel="noopener noreferrer" className="flex items-center space-x-2 hover:opacity-80 transition-opacity">
              <Image
                src="/logo.png"
                alt="Market Matrix"
                width={32}
                height={32}
                className="h-8 w-auto"
              />
            </a>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:block">
            <div className="flex flex-wrap items-center space-x-1">
              {navigation.map((item) => {
                const isActive = pathname === item.href;

                if (item.isComingSoon) {
                  return (
                    <Dialog key={item.name} open={portfolioDialogOpen} onOpenChange={setPortfolioDialogOpen}>
                      <DialogTrigger asChild>
                        <button
                          className={cn(
                            'flex items-center space-x-2 rounded-md px-3 py-2 text-sm font-subheading font-medium transition-colors w-full text-left',
                            'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                          )}
                        >
                          <item.icon className="h-4 w-4" />
                          <span>{item.name}</span>
                        </button>
                      </DialogTrigger>
                      <DialogContent>
                        <DialogHeader>
                          <DialogTitle className="flex items-center gap-2">
                            <item.icon className="h-5 w-5" />
                            {item.name} Coming Soon
                          </DialogTitle>
                          <DialogDescription>
                            Our portfolio management feature is currently under development. Soon you&apos;ll be able to:
                          </DialogDescription>
                        </DialogHeader>
                        <div className="space-y-4 py-4">
                          <ul className="space-y-2 text-sm text-muted-foreground">
                            <li>• Track your cryptocurrency holdings</li>
                            <li>• Monitor portfolio performance over time</li>
                            <li>• Get insights on asset allocation</li>
                            <li>• Set up price alerts and notifications</li>
                            <li>• Import transactions from exchanges</li>
                          </ul>
                          <div className="bg-muted/50 rounded-lg p-4">
                            <p className="text-sm font-medium mb-2">Stay tuned!</p>
                            <p className="text-xs text-muted-foreground">
                              We&apos;re working hard to bring you comprehensive portfolio management tools.
                              Follow our progress for updates on the release.
                            </p>
                          </div>
                        </div>
                        <div className="flex justify-end">
                          <Button onClick={() => setPortfolioDialogOpen(false)}>
                            Got it
                          </Button>
                        </div>
                      </DialogContent>
                    </Dialog>
                  );
                }

                const LinkComponent = item.isExternal ? 'a' : Link;
                const linkProps = item.isExternal
                  ? { href: item.href, target: '_blank', rel: 'noopener noreferrer' }
                  : { href: item.href };

                return (
                  <LinkComponent
                    key={item.name}
                    {...linkProps}
                    className={cn(
                      'flex items-center space-x-2 rounded-md px-3 py-2 text-sm font-subheading font-medium transition-colors',
                      isActive
                        ? 'bg-accent text-accent-foreground'
                        : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                    )}
                  >
                    <item.icon className="h-4 w-4" />
                    <span>{item.name}</span>
                    {item.isExternal && (
                      <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                    )}
                  </LinkComponent>
                );
              })}
            </div>
          </div>

          {/* Right side buttons */}
          <div className="hidden md:flex items-center space-x-4">
            <Button asChild>
              <Link href="/dashboard">Launch App</Link>
            </Button>
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? (
                <X className="h-6 w-6" />
              ) : (
                <Menu className="h-6 w-6" />
              )}
            </Button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t">
          <div className="space-y-1 px-2 pb-3 pt-2">
            {navigation.map((item: NavItem) => {
              const isActive = pathname === item.href;

              if (item.isComingSoon) {
                return (
                  <button
                    key={item.name}
                    className={cn(
                      'flex items-center space-x-2 rounded-md px-3 py-2 text-base font-subheading font-medium w-full text-left',
                      'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                    )}
                    onClick={() => {
                      setPortfolioDialogOpen(true);
                      setMobileMenuOpen(false);
                    }}
                  >
                    <item.icon className="h-5 w-5" />
                    <span>{item.name}</span>
                  </button>
                );
              }

              const LinkComponent = item.isExternal ? 'a' : Link;
                const linkProps = item.isExternal
                  ? { href: item.href, target: '_blank', rel: 'noopener noreferrer' }
                  : { href: item.href };

                return (
                  <LinkComponent
                    key={item.name}
                    {...linkProps}
                    className={cn(
                      'flex items-center space-x-2 rounded-md px-3 py-2 text-base font-subheading font-medium',
                      isActive
                        ? 'bg-accent text-accent-foreground'
                        : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                    )}
                    onClick={() => !item.isExternal && setMobileMenuOpen(false)}
                  >
                    <item.icon className="h-5 w-5" />
                    <span>{item.name}</span>
                    {item.isExternal && (
                      <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                    )}
                  </LinkComponent>
                );
            })}
            <div className="mt-4 space-y-2 px-3">
              <Button className="w-full" asChild>
                <Link href="/dashboard">Launch App</Link>
              </Button>
            </div>
          </div>
        </div>
      )}
    </nav>
  );
}

