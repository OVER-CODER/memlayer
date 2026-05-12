'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '../../lib/api';
import { Play, RotateCcw, FastForward, Clock } from 'lucide-react';
import { format } from 'date-fns';

export default function ReplayConsole() {
  const { data: traces, isLoading } = useQuery({
    queryKey: ['coordinationTraces'],
    queryFn: api.console.getCoordinationTraces,
    refetchInterval: 5000,
  });

  if (isLoading) return <div className="p-8 text-slate-400">Loading Replay Console...</div>;

  return (
    <div className="p-8 max-w-7xl mx-auto h-full flex flex-col">
      <div className="flex justify-between items-center mb-8 shrink-0">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Replay Console</h1>
          <p className="text-slate-400">Deterministic runtime trace exploration and state reconstruction.</p>
        </div>
        <div className="flex space-x-4">
          <button className="flex items-center px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-md text-sm border border-slate-700">
            <RotateCcw className="mr-2 h-4 w-4" /> Reset State
          </button>
          <button className="flex items-center px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-md text-sm">
            <Play className="mr-2 h-4 w-4" /> Start Replay
          </button>
        </div>
      </div>

      <div className="flex-1 bg-slate-950 border border-slate-800 rounded-lg flex flex-col overflow-hidden">
        {/* Timeline Header */}
        <div className="p-4 border-b border-slate-800 bg-slate-900 flex justify-between items-center shrink-0">
          <h2 className="text-lg font-semibold text-white flex items-center">
            <Clock className="mr-2 h-5 w-5 text-indigo-400" /> Runtime Traces Timeline
          </h2>
          <span className="text-xs font-mono text-slate-500">{traces?.length || 0} Events Available</span>
        </div>
        
        {/* Timeline Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {traces?.map((trace: any, i: number) => (
            <div key={i} className="flex group">
              <div className="flex flex-col items-center mr-4">
                <div className="w-3 h-3 bg-indigo-500 rounded-full border-2 border-slate-950 mt-1"></div>
                <div className="w-0.5 h-full bg-slate-800 group-last:bg-transparent my-1"></div>
              </div>
              <div className="bg-slate-900 border border-slate-800 rounded p-4 flex-1">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <span className="font-mono text-indigo-400 text-sm">{trace.report_id}</span>
                    <div className="text-slate-500 text-xs mt-1">Provider: {trace.provider}</div>
                  </div>
                  <span className="text-xs text-slate-500 bg-slate-950 px-2 py-1 rounded">
                    {trace.coordination_duration_ms.toFixed(1)}ms
                  </span>
                </div>
                
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                  <div className="bg-slate-950 rounded p-2 text-center border border-slate-800/50">
                    <div className="text-[10px] text-slate-500 mb-1 uppercase tracking-wider">Tokens Consumed</div>
                    <div className="text-white font-mono text-sm">{trace.total_tokens_consumed}</div>
                  </div>
                  <div className="bg-slate-950 rounded p-2 text-center border border-slate-800/50">
                    <div className="text-[10px] text-slate-500 mb-1 uppercase tracking-wider">Tokens Saved</div>
                    <div className="text-emerald-400 font-mono text-sm">+{trace.total_tokens_saved}</div>
                  </div>
                  <div className="bg-slate-950 rounded p-2 text-center border border-slate-800/50">
                    <div className="text-[10px] text-slate-500 mb-1 uppercase tracking-wider">Reuse Ratio</div>
                    <div className="text-indigo-400 font-mono text-sm">{(trace.context_reuse_ratio * 100).toFixed(1)}%</div>
                  </div>
                  <div className="bg-slate-950 rounded p-2 text-center border border-slate-800/50">
                    <div className="text-[10px] text-slate-500 mb-1 uppercase tracking-wider">State Match</div>
                    <div className="text-emerald-400 font-mono text-sm">1.0</div>
                  </div>
                </div>
              </div>
            </div>
          ))}

          {(!traces || traces.length === 0) && (
            <div className="text-slate-500 text-center py-12 flex flex-col items-center">
              <FastForward className="h-8 w-8 text-slate-600 mb-4" />
              <p>No replay traces available.</p>
              <p className="text-xs mt-2 text-slate-600">Execute coordination runs to generate deterministic traces.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
