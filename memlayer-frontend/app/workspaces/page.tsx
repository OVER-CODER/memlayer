'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '../../lib/api';
import { Database, Plus, Search, Layers, Box, Calendar, Cpu } from 'lucide-react';
import Link from 'next/link';
import { useState } from 'react';

export default function WorkspacesConsole() {
  const [search, setSearch] = useState('');
  const { data, isLoading } = useQuery({
    queryKey: ['workspaces'],
    queryFn: api.console.getWorkspaces,
  });

  if (isLoading) {
    return (
      <div className="p-12 flex flex-col items-center justify-center min-h-[60vh]">
        <Cpu className="w-10 h-10 text-indigo-500 animate-pulse mb-4" />
        <div className="text-slate-400 font-mono text-sm">Querying distributed memory bounds...</div>
      </div>
    );
  }

  const allWorkspaces = data?.workspaces || [];
  const filteredWorkspaces = allWorkspaces.filter((ws: any) => 
    ws.workspace_id?.toLowerCase().includes(search.toLowerCase()) || 
    ws.id?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-10">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div>
           <h1 className="text-3xl font-black text-white tracking-tight">Semantic Workspaces</h1>
           <p className="text-slate-400 mt-1">Isolated cognitive enclaves for persistent memory storage.</p>
        </div>
        <div className="flex w-full md:w-auto gap-3">
          <div className="relative flex-1 md:w-64">
             <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
             <input 
              type="text" 
              placeholder="Filter by ID..." 
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl py-2.5 pl-10 pr-4 text-xs text-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all"
             />
          </div>
          <button className="flex items-center px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold transition-all shadow-lg shadow-indigo-600/20 active:scale-95">
            <Plus className="w-4 h-4 mr-2" /> NEW WORKSPACE
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {filteredWorkspaces.map((ws: any) => {
          const wsId = ws.workspace_id || ws.id;
          return (
            <Link href={`/workspace/${wsId}`} key={wsId} className="group">
              <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 hover:border-indigo-500/50 hover:bg-slate-900/50 transition-all cursor-pointer relative overflow-hidden h-full flex flex-col">
                <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
                   <Box className="w-24 h-24 text-white" />
                </div>
                
                <div className="flex justify-between items-start mb-6">
                  <div className="p-2.5 bg-slate-900 rounded-xl border border-slate-800 text-indigo-400 group-hover:scale-110 transition-transform">
                    <Layers className="w-5 h-5" />
                  </div>
                  <div className="flex flex-col items-end">
                    <span className="text-[10px] font-mono text-slate-500">PROVIDER</span>
                    <span className="text-[10px] font-bold text-slate-300 uppercase tracking-wider">{ws.provider || 'unknown'}</span>
                  </div>
                </div>

                <div className="flex-1">
                  <h3 className="text-lg font-bold text-white group-hover:text-indigo-400 transition-colors mb-2 truncate" title={wsId}>
                    {wsId}
                  </h3>
                  <div className="flex items-center text-[10px] text-slate-500 mb-6 font-medium">
                    <Calendar className="w-3 h-3 mr-1.5" /> 
                    CREATED {new Date(ws.created_at).toLocaleDateString()}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 pt-5 border-t border-slate-900 mt-auto">
                   <div className="flex flex-col">
                      <span className="text-[10px] font-bold text-slate-600 uppercase tracking-widest mb-1">Memories</span>
                      <span className="text-sm font-black text-white">{ws.memory_count || 0}</span>
                   </div>
                   <div className="flex flex-col items-end text-right">
                      <span className="text-[10px] font-bold text-slate-600 uppercase tracking-widest mb-1">Token Budget</span>
                      <span className="text-sm font-black text-white">{ws.token_budget || 0}</span>
                   </div>
                </div>
              </div>
            </Link>
          );
        })}

        {filteredWorkspaces.length === 0 && (
          <div className="col-span-full py-24 flex flex-col items-center justify-center bg-slate-950/50 border border-dashed border-slate-800 rounded-3xl text-center space-y-4">
            <div className="p-4 bg-slate-900 rounded-full border border-slate-800">
              <Search className="w-8 h-8 text-slate-600" />
            </div>
            <div>
              <p className="text-slate-400 font-bold">No workspaces found</p>
              <p className="text-slate-600 text-xs mt-1">Try a different search or seed the kernel with data.</p>
            </div>
            <Link href="/" className="text-indigo-400 text-xs font-bold hover:underline">
              Return to Observatory
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
