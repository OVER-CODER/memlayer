'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '../../lib/api';
import { Shield, ShieldAlert, ShieldCheck, Activity } from 'lucide-react';
import { format } from 'date-fns';

export default function GovernanceConsole() {
  const { data: auditTrail, isLoading: auditLoading } = useQuery({
    queryKey: ['audit-trail'],
    queryFn: () => api.console.getAuditTrail(),
    refetchInterval: 5000,
  });

  const { data: policies, isLoading: policyLoading } = useQuery({
    queryKey: ['policies'],
    queryFn: () => api.console.getPolicyDecisions(),
    refetchInterval: 5000,
  });

  if (auditLoading || policyLoading) return <div className="p-8 text-slate-400">Loading Governance Data...</div>;

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Governance & Lineage</h1>
          <p className="text-slate-400">Immutable audit trails and runtime policy enforcement.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Audit Trail */}
        <div className="bg-slate-950 border border-slate-800 rounded-lg overflow-hidden flex flex-col h-[600px]">
          <div className="p-4 border-b border-slate-800 bg-slate-900 flex justify-between items-center">
            <h2 className="text-lg font-semibold text-white flex items-center">
              <Shield className="mr-2 h-5 w-5 text-indigo-400" /> Immutable Audit Trail
            </h2>
            <span className="text-xs font-mono text-slate-500">{auditTrail?.length || 0} Records</span>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {auditTrail?.map((record: any, i: number) => (
              <div key={i} className="p-3 bg-slate-900 border border-slate-800 rounded text-sm">
                <div className="flex justify-between items-start mb-2">
                  <span className="font-mono text-indigo-400 text-xs">{record.record_id || `rec-${i}`}</span>
                  <span className="text-slate-500 text-xs">{format(new Date(record.timestamp || Date.now()), 'HH:mm:ss.SSS')}</span>
                </div>
                <div className="flex items-center text-slate-300 mb-1">
                  <span className="bg-slate-800 px-2 py-0.5 rounded text-xs mr-2">{record.action_type}</span>
                  <span className="text-xs text-slate-400 font-mono">{record.resource_id}</span>
                </div>
                {record.details && (
                  <pre className="mt-2 text-[10px] text-slate-500 bg-slate-950 p-2 rounded overflow-x-auto">
                    {JSON.stringify(record.details, null, 2)}
                  </pre>
                )}
              </div>
            ))}
            {(!auditTrail || auditTrail.length === 0) && (
              <div className="text-slate-500 text-center py-8">No audit records found.</div>
            )}
          </div>
        </div>

        {/* Policy Enforcement */}
        <div className="bg-slate-950 border border-slate-800 rounded-lg overflow-hidden flex flex-col h-[600px]">
          <div className="p-4 border-b border-slate-800 bg-slate-900 flex justify-between items-center">
            <h2 className="text-lg font-semibold text-white flex items-center">
              <Activity className="mr-2 h-5 w-5 text-emerald-400" /> Policy Enforcement
            </h2>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {policies?.map((policy: any, i: number) => {
              const passed = policy.details?.status === 'passed';
              return (
                <div key={i} className={`p-3 border rounded text-sm ${passed ? 'bg-emerald-950/20 border-emerald-900/50' : 'bg-red-950/20 border-red-900/50'}`}>
                  <div className="flex justify-between items-start mb-2">
                    <span className={`font-semibold flex items-center ${passed ? 'text-emerald-400' : 'text-red-400'}`}>
                      {passed ? <ShieldCheck className="mr-2 h-4 w-4" /> : <ShieldAlert className="mr-2 h-4 w-4" />}
                      {policy.details?.policy || 'Unknown Policy'}
                    </span>
                    <span className="text-slate-500 text-xs">{format(new Date(policy.timestamp || Date.now()), 'HH:mm:ss.SSS')}</span>
                  </div>
                  <div className="text-slate-300 text-xs mb-1">
                    Resource: <span className="font-mono">{policy.resource_id}</span>
                  </div>
                </div>
              );
            })}
            {(!policies || policies.length === 0) && (
              <div className="text-slate-500 text-center py-8">No policy decisions found.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
