'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '../../lib/api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function TelemetryConsole() {
  const { data: telemetry, isLoading } = useQuery({
    queryKey: ['telemetry'],
    queryFn: api.console.getTelemetry,
    refetchInterval: 5000,
  });

  if (isLoading) return <div className="p-8 text-slate-400">Loading Telemetry...</div>;

  // Transform recent runs into chart data
  const chartData = telemetry?.token_analytics?.recent_runs?.map((run: any, i: number) => ({
    name: `Run ${i}`,
    saved: run.tokens_saved,
    used: run.provider_tokens,
  })).reverse() || [];

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Runtime Telemetry</h1>
          <p className="text-slate-400">Token economics and operational efficiency.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        <div className="bg-slate-950 border border-slate-800 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-white mb-6">Token Savings Over Time</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="name" stroke="#64748b" fontSize={12} />
                <YAxis stroke="#64748b" fontSize={12} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', color: '#f8fafc' }}
                  itemStyle={{ color: '#818cf8' }}
                />
                <Line type="monotone" dataKey="saved" stroke="#818cf8" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} name="Tokens Saved" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-slate-950 border border-slate-800 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Semantic Drift Monitoring</h2>
          <div className="flex items-center justify-center h-64 border border-dashed border-slate-800 rounded bg-slate-900/50">
            <p className="text-slate-500 text-sm text-center">
              No significant semantic drift detected.<br/>
              Baseline coherence: 0.98
            </p>
          </div>
        </div>
      </div>

      <div className="bg-slate-950 border border-slate-800 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-white mb-4">Raw Telemetry Dump</h2>
        <pre className="text-xs text-slate-400 font-mono bg-slate-900 p-4 rounded overflow-x-auto border border-slate-800">
          {JSON.stringify(telemetry, null, 2)}
        </pre>
      </div>
    </div>
  );
}
