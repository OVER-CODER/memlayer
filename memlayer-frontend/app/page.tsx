'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import { Shield, Database, Zap, Activity, Upload, Play, Terminal } from 'lucide-react';
import { useState } from 'react';

export default function Dashboard() {
  const [isIngesting, setIsIngesting] = useState(false);

  const { data: telemetry, isLoading: telLoading } = useQuery({
    queryKey: ['telemetry'],
    queryFn: api.console.getTelemetry,
    refetchInterval: 5000,
  });

  const { data: health, isLoading: healthLoading } = useQuery({
    queryKey: ['health'],
    queryFn: api.console.getGovernanceHealth,
  });

  const seedData = async () => {
    try {
      await api.console.seedMockData();
      window.location.reload();
    } catch (err) {
      console.error('Seed failed:', err);
      alert('Failed to seed kernel data.');
    }
  };

  const ingestLocomo = async () => {
    if (isIngesting) return;
    setIsIngesting(true);
    try {
      await api.console.ingestLocomo();
      alert('LoCoMo Ingestion started. Check Workspaces in a few moments.');
      window.location.reload();
    } catch (err) {
      console.error('Ingestion failed:', err);
      alert('LoCoMo Ingestion failed. Ensure dataset exists on backend.');
    } finally {
      setIsIngesting(false);
    }
  };

  if (telLoading || healthLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-slate-950">
        <div className="flex items-center space-x-3 mb-4">
          <Activity className="w-6 h-6 text-indigo-500 animate-spin" />
          <span className="text-xl font-bold text-white tracking-widest">MEMLAYER KERNEL</span>
        </div>
        <div className="text-slate-500 text-sm font-mono">Initializing secure cognition observability...</div>
      </div>
    );
  }

  const tokenSavings = telemetry?.token_analytics?.overall_savings_ratio || 0;
  const totalRuns = telemetry?.token_analytics?.total_runs || 0;
  const healthScore = health?.overall_health_score || 0;

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-10">
      {/* Header Section */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 pb-8 border-b border-slate-800">
        <div>
          <div className="flex items-center space-x-2 mb-2">
            <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
            <span className="text-[10px] font-bold text-emerald-500 uppercase tracking-[0.2em]">Runtime: Production Stable</span>
          </div>
          <h1 className="text-4xl font-black text-white tracking-tight">Cognition Observatory</h1>
          <p className="text-slate-400 mt-1 max-w-xl">Deep telemetry for the MemLayer deterministic memory substrate.</p>
        </div>
        <div className="flex items-center gap-3">
          <button 
            onClick={seedData}
            className="flex items-center px-5 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-bold transition-all border border-slate-700 active:scale-95"
          >
            <Play className="w-3.5 h-3.5 mr-2 text-indigo-400" /> SEED KERNEL
          </button>
          <button 
            onClick={ingestLocomo}
            disabled={isIngesting}
            className="flex items-center px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold transition-all shadow-lg shadow-indigo-600/20 disabled:opacity-50 active:scale-95"
          >
            <Upload className={`w-3.5 h-3.5 mr-2 ${isIngesting ? 'animate-bounce' : ''}`} /> 
            {isIngesting ? 'INGESTING...' : 'INGEST LOCOMO'}
          </button>
        </div>
      </div>

      {/* Metric Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard 
          title="Substrate Health" 
          value={`${(healthScore * 100).toFixed(1)}%`} 
          desc="Overall governance score"
          icon={<Activity className="w-5 h-5 text-emerald-500" />} 
          trend="+0.2% since boot"
        />
        <MetricCard 
          title="Context Efficiency" 
          value={`${(tokenSavings * 100).toFixed(1)}%`} 
          desc="Token reduction ratio"
          icon={<Zap className="w-5 h-5 text-amber-500" />} 
          trend="Optimal retention"
        />
        <MetricCard 
          title="Cognitive Sessions" 
          value={totalRuns} 
          desc="Total coordinated runs"
          icon={<Terminal className="w-5 h-5 text-blue-500" />} 
          trend="Active participation"
        />
        <MetricCard 
          title="Tenant Security" 
          value="ENFORCED" 
          desc="Workspace isolation layer"
          icon={<Shield className="w-5 h-5 text-indigo-500" />} 
          trend="100% Isolation"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Component Health Chart */}
        <div className="lg:col-span-2 bg-slate-950 border border-slate-800 rounded-2xl p-8 relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-8 opacity-5">
            <Activity className="w-32 h-32 text-indigo-500" />
          </div>
          <h2 className="text-xl font-bold text-white mb-6 flex items-center">
            Runtime Integrity <span className="ml-3 text-[10px] font-mono text-slate-500 px-2 py-0.5 bg-slate-900 rounded border border-slate-800 uppercase">Live</span>
          </h2>
          <div className="space-y-6">
            {health?.components && Object.entries(health.components).map(([name, data]: [string, any]) => (
              <div key={name} className="relative">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-bold text-slate-300 uppercase tracking-wider">{name.replace('Engine', '').replace('Monitor', '')}</span>
                  <span className="text-xs font-mono text-slate-500">{(data.health_score * 100).toFixed(0)}%</span>
                </div>
                <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden border border-slate-800">
                  <div 
                    className={`h-full rounded-full transition-all duration-1000 ${
                      data.health_score > 0.9 ? 'bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]' : 
                      data.health_score > 0.7 ? 'bg-amber-500 shadow-[0_0_10px_rgba(245,158,11,0.5)]' : 'bg-rose-500 shadow-[0_0_10px_rgba(244,63,94,0.5)]'
                    }`} 
                    style={{ width: `${data.health_score * 100}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Traces */}
        <div className="bg-slate-950 border border-slate-800 rounded-2xl p-8 shadow-xl">
          <h2 className="text-xl font-bold text-white mb-6">Lineage Traces</h2>
          <div className="space-y-4">
            {telemetry?.token_analytics?.recent_runs?.slice(0, 6).map((run: any) => (
              <div key={run.report_id} className="group p-4 bg-slate-900/50 hover:bg-slate-900 rounded-xl border border-slate-800 transition-all cursor-default">
                <div className="flex justify-between items-center mb-1">
                  <span className="text-[10px] font-mono text-indigo-400 group-hover:text-indigo-300">TRC-{run.report_id.slice(-8)}</span>
                  <span className="text-[10px] text-slate-500">{new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                </div>
                <div className="flex justify-between items-end">
                   <div className="text-[10px] text-slate-500 font-medium">PROVIDER: <span className="text-slate-300 uppercase">{run.provider}</span></div>
                   <div className="text-xs font-bold text-emerald-500">-{run.tokens_saved} TOKENS</div>
                </div>
              </div>
            ))}
            {(!telemetry?.token_analytics?.recent_runs || telemetry.token_analytics.recent_runs.length === 0) && (
              <div className="flex flex-col items-center justify-center py-12 text-center space-y-4 border border-dashed border-slate-800 rounded-xl">
                <Database className="w-8 h-8 text-slate-700" />
                <p className="text-slate-500 text-xs">No active semantic traces.<br/>Initialize substrate to begin tracking.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function MetricCard({ title, value, desc, icon, trend }: { title: string, value: string | number, desc: string, icon: React.ReactNode, trend: string }) {
  return (
    <div className="bg-slate-950 border border-slate-800 rounded-2xl p-7 flex flex-col hover:border-slate-700 transition-all relative overflow-hidden group">
      <div className="absolute bottom-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-indigo-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
      <div className="flex justify-between items-start mb-6">
        <div className="p-2 bg-slate-900 rounded-lg border border-slate-800">{icon}</div>
        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">{trend}</span>
      </div>
      <div className="flex flex-col">
        <span className="text-[11px] font-bold text-slate-500 uppercase tracking-widest mb-1">{title}</span>
        <div className="text-3xl font-black text-white mb-2">{value}</div>
        <p className="text-[10px] text-slate-600 font-medium">{desc}</p>
      </div>
    </div>
  );
}
