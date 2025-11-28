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
  X,
  LogOut
} from 'lucide-react';
import { useState, useEffect } from 'react';
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
import { useAuth } from '@/context/auth-context';

interface NavItemProps {
  name: string;
  href: string;
  icon: React.ElementType;
  isExternal?: boolean;
  isComingSoon?: boolean;
  onClick?: () => void;
}

const navigation: NavItemProps[] = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  { name: 'Predictions', href: '/predictions', icon: TrendingUp },
  { name: 'Token Prediction/Health', href: '/token-health', icon: Shield },
  { name: 'News', href: '/news', icon: FileText },
  { name: 'Docs', href: 'http://docs.marketmatrix.space', icon: BookOpen, isExternal: true },
  { name: 'Portfolio', href: '/portfolio', icon: Wallet, isComingSoon: true },
];

const NavLink = ({ item }: { item: NavItemProps }) => {
  const pathname = usePathname();
  const isActive = pathname === item.href;

  const LinkComponent = item.isExternal ? 'a' : Link;
  const linkProps = item.isExternal
    ? { href: item.href, target: '_blank', rel: 'noopener noreferrer' }
    : { href: item.href };

  return (
    <LinkComponent
      {...linkProps}
      onClick={item.onClick}
      className={cn(
        'flex items-center space-x-2 rounded-md px-3 py-2 text-sm font-medium transition-colors',
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
};

const ComingSoonDialog = ({ item, children }: { item: NavItemProps, children: React.ReactNode }) => {
  return (
    <Dialog>
      <DialogTrigger asChild>{children}</DialogTrigger>
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
          <Button>Got it</Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};


export function Navbar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);
  const { isAuthenticated, walletAddress, logout } = useAuth();

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const renderNavLinks = (isMobile = false) => {
    return navigation.map((item) => {
      if (item.isComingSoon) {
        return (
          <ComingSoonDialog key={item.name} item={item}>
            <button
              className={cn(
                'flex items-center space-x-2 rounded-md px-3 py-2 text-sm font-medium transition-colors w-full text-left',
                'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
              )}
            >
              <item.icon className="h-4 w-4" />
              <span>{item.name}</span>
            </button>
          </ComingSoonDialog>
        );
      }
      return <NavLink key={item.name} item={{...item, onClick: isMobile ? () => setMobileMenuOpen(false) : undefined}} />;
    });
  }

  const formatAddress = (addr: string) => {
    if (!addr) return '';
    return `${addr.substring(0, 6)}...${addr.substring(addr.length - 4)}`;
  }

  return (
    <>
      <nav className={cn(
        "sticky top-0 z-50 w-full border-b transition-colors duration-300",
        isScrolled ? "bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60" : "bg-transparent"
      )}>
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
                 <span className="font-bold text-lg">Market Matrix</span>
              </a>
            </div>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center space-x-1">
              {renderNavLinks()}
            </div>

            {/* Right side buttons */}
            <div className="hidden md:flex items-center space-x-4">
              {isAuthenticated ? (
                <>
                    <div className="flex items-center gap-2 bg-secondary/50 px-3 py-1.5 rounded-full text-sm font-mono">
                        <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                        {walletAddress && formatAddress(walletAddress)}
                    </div>
                    <Button variant="ghost" size="icon" onClick={logout} title="Disconnect">
                        <LogOut className="h-5 w-5" />
                    </Button>
                </>
              ) : (
                <>
                    <Button asChild>
                        <Link href="/login">Connect Wallet</Link>
                    </Button>
                </>
              )}
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
      </nav>

       {/* Mobile menu overlay */}
       {mobileMenuOpen && (
         <div 
           className="fixed inset-0 bg-black/50 z-30 md:hidden"
           onClick={() => setMobileMenuOpen(false)}
         />
       )}
       
       {/* Mobile menu */}
       <div className={cn(
        "fixed inset-y-0 left-0 z-40 w-[280px] max-w-[85vw] transform bg-background border-r transition-transform duration-300 ease-in-out md:hidden",
        mobileMenuOpen ? "translate-x-0" : "-translate-x-full"
      )}>
         <div className="flex flex-col h-full">
           {/* Mobile menu header */}
           <div className="flex items-center justify-between p-4 border-b">
             <span className="font-bold text-lg">Menu</span>
             <Button variant="ghost" size="icon" onClick={() => setMobileMenuOpen(false)}>
               <X className="h-5 w-5" />
             </Button>
           </div>
           
           {/* Nav links */}
           <div className="flex-1 overflow-y-auto p-4 space-y-1">
              {renderNavLinks(true)}
           </div>
           
           {/* Bottom section */}
           <div className="border-t p-4 space-y-3">
               {isAuthenticated ? (
                   <>
                     <div className="flex items-center justify-center gap-2 bg-secondary/50 px-3 py-2 rounded-md text-sm font-mono">
                        <div className="w-2 h-2 rounded-full bg-green-500" />
                        {walletAddress && formatAddress(walletAddress)}
                     </div>
                     <Button variant="outline" className="w-full" onClick={() => { logout(); setMobileMenuOpen(false); }}>
                       Disconnect Wallet
                     </Button>
                   </>
               ) : (
                   <Button className="w-full" asChild onClick={() => setMobileMenuOpen(false)}>
                       <Link href="/login">Connect Wallet</Link>
                   </Button>
               )}
            </div>
         </div>
       </div>
    </>
  );
}
