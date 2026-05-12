import './globals.css';
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { Sidebar } from '../components/Sidebar';
import { Providers } from './providers';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'MemLayer Kernel Console',
  description: 'Operational cognition runtime console',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-slate-950 text-slate-100 flex h-screen overflow-hidden`}>
        <Providers>
          <Sidebar />
          <main className="flex-1 overflow-y-auto bg-slate-900 border-l border-slate-800">
            {children}
          </main>
        </Providers>
      </body>
    </html>
  );
}
