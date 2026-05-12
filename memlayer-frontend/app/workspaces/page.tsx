'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '../../lib/api';
import { Database, Plus } from 'lucide-react';
import Link from 'next/link';

export default function WorkspacesConsole() {
  const { data, isLoading } = useQuery({
    queryKey: ['workspaces'],
    queryFn: api.console.getWorkspaces,
  });

  if (isLoading) return <div className="p-8 text-slate-400">Loading Workspaces...</div>;

  const workspaces = data?.workspaces || [];

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Tenant Workspaces</h1>
          <p className="text-slate-400">Manage isolated semantic memory bounds.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {workspaces.map((ws: any) => (
          <Link href={`/workspaces/${ws.workspace_id}`} key={ws.workspace_id}>
            <div className="bg-slate-950 border border-slate-800 rounded-lg p-6 hover:border-indigo-500 transition-colors cursor-pointer group">
              <div className="flex justify-between items-start mb-4">
                <Database className="text-indigo-400 group-hover:text-indigo-300 transition-colors" />
                <span className="text-xs font-mono text-slate-500">{ws.workspace_id.slice(-8)}</span>
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">{ws.workspace_id}</h3>
              <div className="flex items-center text-sm text-slate-400 mb-4">
                <span className="bg-slate-900 px-2 py-1 rounded text-xs border border-slate-800 mr-2">Provider: {ws.provider}</span>
                <span className="bg-slate-900 px-2 py-1 rounded text-xs border border-slate-800">Budget: {ws.token_budget}</span>
              </div>
              <div className="text-sm text-slate-500 border-t border-slate-800 pt-3">
                {ws.memory_count} semantic memories
              </div>
            </div>
          </Link>
        ))}
        {workspaces.length === 0 && (
          <div className="col-span-3 text-center py-12 bg-slate-950 border border-dashed border-slate-800 rounded-lg text-slate-500">
            No active workspaces. Return to dashboard to seed data.
          </div>
        )}
      </div>
    </div>
  );
}
