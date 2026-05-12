'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Activity, Database, GitMerge, LayoutDashboard, LineChart, Repeat, Shield, Workflow } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const NAV_ITEMS = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Workspaces', href: '/workspaces', icon: Database },
  { name: 'Compiler Viz', href: '/compiler', icon: GitMerge },
  { name: 'View Engine', href: '/views', icon: Workflow },
  { name: 'Coordination', href: '/coordination', icon: Activity },
  { name: 'Replay Console', href: '/replay', icon: Repeat },
  { name: 'Governance', href: '/governance', icon: Shield },
  { name: 'Telemetry', href: '/telemetry', icon: LineChart },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="flex h-screen w-64 flex-col border-r border-slate-800 bg-slate-950 text-slate-300">
      <div className="flex h-16 items-center px-6 border-b border-slate-800">
        <Shield className="h-6 w-6 text-indigo-500 mr-2" />
        <span className="text-lg font-bold tracking-tight text-white">MemLayer Kernel</span>
      </div>
      <div className="flex-1 overflow-y-auto py-4">
        <nav className="space-y-1 px-3">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  'group flex items-center rounded-md px-3 py-2 text-sm font-medium',
                  isActive
                    ? 'bg-indigo-500/10 text-indigo-400'
                    : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                )}
              >
                <item.icon
                  className={cn(
                    'mr-3 h-5 w-5 flex-shrink-0',
                    isActive ? 'text-indigo-400' : 'text-slate-500 group-hover:text-slate-300'
                  )}
                  aria-hidden="true"
                />
                {item.name}
              </Link>
            );
          })}
        </nav>
      </div>
      <div className="p-4 border-t border-slate-800 text-xs text-slate-500">
        MemLayer v0.1.0-alpha<br />
        Runtime: Connected
      </div>
    </div>
  );
}
