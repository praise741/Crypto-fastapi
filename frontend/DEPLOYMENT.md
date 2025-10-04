# Market Matrix Frontend - Deployment Guide

## 🚀 Deployment Options

### Option 1: Vercel (Recommended)

Vercel is the easiest way to deploy Next.js applications.

#### Steps:

1. **Push to GitHub**:
```bash
git add .
git commit -m "Add Market Matrix frontend"
git push origin main
```

2. **Deploy to Vercel**:
- Go to [vercel.com](https://vercel.com)
- Click "New Project"
- Import your GitHub repository
- Configure environment variables:
  - `NEXT_PUBLIC_API_URL`: Your backend API URL
- Click "Deploy"

3. **Custom Domain** (Optional):
- Go to Project Settings → Domains
- Add your custom domain
- Update DNS records as instructed

---

### Option 2: Netlify

#### Steps:

1. **Build the project**:
```bash
npm run build
```

2. **Deploy to Netlify**:
- Go to [netlify.com](https://netlify.com)
- Drag and drop the `.next` folder
- Or connect your GitHub repository
- Set environment variables in Site Settings

---

### Option 3: Docker

#### Dockerfile (already optimized):

```dockerfile
FROM node:18-alpine AS base

# Install dependencies only when needed
FROM base AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED 1
RUN npm run build

# Production image
FROM base AS runner
WORKDIR /app
ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000
ENV PORT 3000

CMD ["node", "server.js"]
```

#### Build and Run:

```bash
docker build -t market-matrix-frontend .
docker run -p 3000:3000 -e NEXT_PUBLIC_API_URL=http://your-api-url market-matrix-frontend
```

---

### Option 4: Traditional VPS (Ubuntu/Debian)

#### Steps:

1. **Install Node.js**:
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

2. **Clone and Setup**:
```bash
git clone your-repo-url
cd frontend
npm install
```

3. **Build**:
```bash
npm run build
```

4. **Run with PM2**:
```bash
npm install -g pm2
pm2 start npm --name "market-matrix-frontend" -- start
pm2 save
pm2 startup
```

5. **Nginx Configuration**:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

---

## 🔐 Environment Variables

### Production Environment Variables:

```env
# Production API URL
NEXT_PUBLIC_API_URL=https://api.your-domain.com

# Optional: Analytics
NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX

# Optional: Sentry Error Tracking
NEXT_PUBLIC_SENTRY_DSN=https://xxx@sentry.io/xxx
```

---

## ⚡ Performance Optimization

### 1. Enable Compression
Already configured in Next.js by default.

### 2. Image Optimization
Use Next.js `<Image>` component for automatic optimization.

### 3. Code Splitting
Automatic with Next.js App Router.

### 4. Caching Strategy
Configure in `next.config.ts`:

```typescript
const nextConfig = {
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=3600, must-revalidate',
          },
        ],
      },
    ];
  },
};
```

---

## 🔒 Security Best Practices

### 1. Environment Variables
- Never commit `.env.local` to Git
- Use platform-specific environment variable management
- Rotate API keys regularly

### 2. CORS Configuration
Ensure your backend API allows requests from your frontend domain.

### 3. Content Security Policy
Add to `next.config.ts`:

```typescript
const nextConfig = {
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
        ],
      },
    ];
  },
};
```

---

## 📊 Monitoring

### 1. Vercel Analytics
Automatically enabled on Vercel deployments.

### 2. Google Analytics
Add to `src/app/layout.tsx`:

```typescript
import Script from 'next/script';

export default function RootLayout({ children }) {
  return (
    <html>
      <head>
        <Script
          src={`https://www.googletagmanager.com/gtag/js?id=${process.env.NEXT_PUBLIC_GA_ID}`}
          strategy="afterInteractive"
        />
        <Script id="google-analytics" strategy="afterInteractive">
          {`
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', '${process.env.NEXT_PUBLIC_GA_ID}');
          `}
        </Script>
      </head>
      <body>{children}</body>
    </html>
  );
}
```

### 3. Error Tracking with Sentry
```bash
npm install @sentry/nextjs
npx @sentry/wizard@latest -i nextjs
```

---

## 🧪 Pre-Deployment Checklist

- [ ] All environment variables configured
- [ ] Build completes without errors (`npm run build`)
- [ ] All pages load correctly
- [ ] API integration tested
- [ ] Mobile responsiveness verified
- [ ] Browser compatibility tested (Chrome, Firefox, Safari, Edge)
- [ ] Performance metrics acceptable (Lighthouse score > 90)
- [ ] SEO meta tags added
- [ ] Error handling tested
- [ ] Loading states work correctly
- [ ] WebSocket connections stable
- [ ] CORS configured on backend
- [ ] SSL certificate configured (HTTPS)

---

## 🔄 CI/CD Pipeline

### GitHub Actions Example:

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy Frontend

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          
      - name: Install dependencies
        run: npm ci
        working-directory: ./frontend
        
      - name: Build
        run: npm run build
        working-directory: ./frontend
        env:
          NEXT_PUBLIC_API_URL: ${{ secrets.API_URL }}
          
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.ORG_ID }}
          vercel-project-id: ${{ secrets.PROJECT_ID }}
          working-directory: ./frontend
```

---

## 📈 Scaling Considerations

### 1. CDN
- Vercel includes CDN by default
- For other platforms, use Cloudflare

### 2. Load Balancing
- Use multiple instances behind a load balancer
- Configure health checks

### 3. Database
- Ensure backend API can handle increased load
- Implement caching (Redis)

### 4. WebSocket Scaling
- Use sticky sessions
- Consider WebSocket gateway (Socket.io with Redis adapter)

---

## 🐛 Troubleshooting

### Build Fails
```bash
# Clear cache and rebuild
rm -rf .next node_modules
npm install
npm run build
```

### API Connection Issues
- Check `NEXT_PUBLIC_API_URL` is correct
- Verify CORS settings on backend
- Check network/firewall rules

### WebSocket Not Connecting
- Ensure WebSocket protocol matches (ws:// or wss://)
- Check proxy configuration
- Verify backend WebSocket endpoint

### Slow Performance
- Enable production mode
- Check bundle size: `npm run build` shows size analysis
- Optimize images
- Implement lazy loading

---

## 📞 Support

For issues or questions:
1. Check the [Next.js Documentation](https://nextjs.org/docs)
2. Review API integration in `src/lib/api-client.ts`
3. Check browser console for errors
4. Verify backend API is running and accessible

---

## 🎉 Success!

Your Market Matrix frontend is now ready for production deployment!

**Recommended Stack**:
- **Frontend**: Vercel (automatic deployments, CDN, SSL)
- **Backend**: Railway or Render (FastAPI hosting)
- **Database**: PostgreSQL (managed service)
- **Cache**: Redis (managed service)

**Total Setup Time**: ~5 minutes with Vercel
**Cost**: Free tier available for all services

Happy deploying! 🚀
