import './globals.css';
import Link from 'next/link';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Pioneer Studio — AI Video Production',
  description: 'Turn any idea into cinematic short-form video. Hook-first scripts, loopable endings, burned-in captions, and automatic YouTube publishing.',
};

function PioneerLogo() {
  return (
    <svg className="logo-mark" viewBox="0 0 44 44" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="logo-grad" x1="0" y1="0" x2="44" y2="44" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#7c3aed" />
          <stop offset="60%" stopColor="#4f46e5" />
          <stop offset="100%" stopColor="#06b6d4" />
        </linearGradient>
        <linearGradient id="peak-grad" x1="0" y1="0" x2="44" y2="44" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#f59e0b" />
          <stop offset="100%" stopColor="#f97316" />
        </linearGradient>
      </defs>
      {/* Background square */}
      <rect width="44" height="44" rx="14" fill="url(#logo-grad)" />
      {/* Mountain / Pioneer peak */}
      <path d="M8 34 L22 12 L36 34 Z" fill="none" stroke="rgba(255,255,255,0.18)" strokeWidth="1.5" strokeLinejoin="round" />
      <path d="M13 34 L22 18 L31 34 Z" fill="rgba(255,255,255,0.12)" stroke="none" />
      {/* Gold summit accent */}
      <path d="M19 20 L22 13 L25 20 Z" fill="url(#peak-grad)" />
      {/* Play button / frame lines */}
      <rect x="10" y="28" width="24" height="1.5" rx="0.75" fill="rgba(255,255,255,0.25)" />
      <rect x="14" y="31" width="16" height="1.5" rx="0.75" fill="rgba(255,255,255,0.15)" />
    </svg>
  );
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body>
        <div className="shell">
          <nav className="nav">
            <Link href="/" className="brand">
              <PioneerLogo />
              <div className="brand-text">
                <h1>Pioneer Studio</h1>
                <span>AI Video Production</span>
              </div>
            </Link>
            <div className="navlinks">
              <Link href="/generate/">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                Generate
              </Link>
              <Link href="/library/">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
                Library
              </Link>
            </div>
          </nav>
          {children}
        </div>
      </body>
    </html>
  );
}
