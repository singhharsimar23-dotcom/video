import './globals.css';
import Link from 'next/link';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'AI Video Studio',
  description: 'Personal AI video studio for retention-first Reels and Shorts.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <main className="shell">
          <nav className="nav">
            <Link href="/" className="brand">
              <span className="logo" />
              <span>
                <h1>AI Video Studio</h1>
                <p>Hook-first. Loop-designed. Caption-complete.</p>
              </span>
            </Link>
            <div className="navlinks">
              <Link href="/generate/">Generate</Link>
              <Link href="/library/">Library</Link>
            </div>
          </nav>
          {children}
        </main>
      </body>
    </html>
  );
}
