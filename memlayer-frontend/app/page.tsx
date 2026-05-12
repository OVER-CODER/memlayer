'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import { Shield, Database, Zap, Activity } from 'lucide-react';

export default function Dashboard() {
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
    await api.console.seedMockData();
    window.location.reload();
  };

  if (telLoading || healthLoading) {
    return <div className="p-8 text-slate-400">Initializing Kernel Console...</div>;
  }

  const tokenSavings = telemetry?.token_analytics?.overall_savings_ratio || 0;
  const totalRuns = telemetry?.token_analytics?.total_runs || 0;
  const healthScore = health?.overall_health_score || 0;

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Cognition Kernel Status</h1>
          <p className="text-slate-400">Realtime operational overview of MemLayer infrastructure.</p>
        </div>
        <button 
          onClick={seedData}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-md text-sm font-medium transition-colors"
        >
          Seed Kernel Data
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <MetricCard title="System Health" value={`${(healthScore * 100).toFixed(1)}%`} icon={<Activity className="text-emerald-500" />} />
        <MetricCard title="Token Savings Ratio" value={`${(tokenSavings * 100).toFixed(1)}%`} icon={<Zap className="text-amber-500" />} />
        <MetricCard title="Total Coordinations" value={totalRuns} icon={<Database className="text-blue-500" />} />
        <MetricCard title="Tenant Isolation" value="100%" icon={<Shield className="text-indigo-500" />} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-slate-950 border border-slate-800 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Runtime Component Health</h2>
          <div className="space-y-4">
            {health?.components && Object.entries(health.components).map(([name, data]: [string, any]) => (
              <div key={name} className="flex justify-between items-center border-b border-slate-800 pb-2">
                <span className="text-slate-300 font-medium">{name}</span>
                <div className="flex items-center">
                  <div className="w-32 bg-slate-800 rounded-full h-2 mr-3">
                    <div className="bg-emerald-500 h-2 rounded-full" style={{ width: `${data.health_score * 100}%` }}></div>
                  </div>
                  <span className="text-sm text-slate-400 w-12 text-right">{(data.health_score * 100).toFixed(0)}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-slate-950 border border-slate-800 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Recent Kernel Activity</h2>
          <div className="space-y-3">
            {telemetry?.token_analytics?.recent_runs?.slice(0, 5).map((run: any) => (
              <div key={run.report_id} className="text-sm p-3 bg-slate-900 rounded border border-slate-800 flex justify-between items-center">
                <span className="text-slate-400 font-mono">{run.report_id}</span>
                <span className="text-emerald-400">-{run.tokens_saved} tokens saved</span>
              </div>
            ))}
            {(!telemetry?.token_analytics?.recent_runs || telemetry.token_analytics.recent_runs.length === 0) && (
              <div className="text-slate-500 text-sm text-center py-4">No recent activity. Click 'Seed Kernel Data' to begin.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function MetricCard({ title, value, icon }: { title: string, value: string | number, icon: React.ReactNode }) {
  return (
    <div className="bg-slate-950 border border-slate-800 rounded-lg p-6 flex flex-col">
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-sm font-medium text-slate-400">{title}</h3>
        {icon}
      </div>
      <div className="text-3xl font-bold text-white">{value}</div>
    </div>
  );
}
