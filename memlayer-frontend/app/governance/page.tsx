'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '../../lib/api';
import { Shield, ShieldAlert, ShieldCheck, Activity, GitBranch } from 'lucide-react';
import { format } from 'date-fns';
import ReactFlow, { Background, Controls, Edge, Node, MarkerType } from 'reactflow';
import 'reactflow/dist/style.css';
import { useMemo } from 'react';

const LineageNode = ({ data }: { data: any }) => {
  return (
    <div className="bg-slate-950 border border-indigo-900/50 rounded-lg p-3 min-w-[200px] shadow-lg">
      <div className="font-bold text-white text-sm mb-1">{data.label}</div>
      <div className="flex justify-between items-center text-xs mb-1">
        <span className="text-slate-500">Hash</span>
        <span className="text-indigo-400 font-mono">{data.hash}</span>
      </div>
      <div className="text-[10px] text-slate-500 text-right">
        {format(new Date(data.timestamp), 'HH:mm:ss.SSS')}
      </div>
    </div>
  );
};

const nodeTypes = {
  lineageNode: LineageNode,
};

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

  const { data: lineageData, isLoading: lineageLoading } = useQuery({
    queryKey: ['lineage'],
    queryFn: () => api.console.getLineage(),
    refetchInterval: 5000,
  });

  const { nodes, edges } = useMemo(() => {
    if (!lineageData || !lineageData.nodes) {
      return { nodes: [], edges: [] };
    }

    const flowNodes: Node[] = lineageData.nodes.map((n: any, i: number) => ({
      id: n.id,
      type: 'lineageNode',
      position: { x: 250, y: 50 + i * 150 }, // Simple linear layout for now
      data: {
        label: n.label,
        hash: n.hash,
        timestamp: n.timestamp,
      }
    }));

    const flowEdges: Edge[] = lineageData.edges.map((e: any, i: number) => ({
      id: `e_${i}`,
      source: e.source,
      target: e.target,
      animated: true,
      style: { stroke: '#6366f1', strokeWidth: 2 },
      markerEnd: { type: MarkerType.ArrowClosed, color: '#6366f1' },
    }));

    return { nodes: flowNodes, edges: flowEdges };
  }, [lineageData]);

  if (auditLoading || policyLoading || lineageLoading) return <div className="p-8 text-slate-400">Loading Governance Data...</div>;

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

      {/* Lineage Graph */}
      <div className="mt-8 bg-slate-950 border border-slate-800 rounded-lg overflow-hidden flex flex-col h-[500px]">
        <div className="p-4 border-b border-slate-800 bg-slate-900 flex justify-between items-center shrink-0">
          <h2 className="text-lg font-semibold text-white flex items-center">
            <GitBranch className="mr-2 h-5 w-5 text-indigo-400" /> Semantic Ancestry Graph
          </h2>
        </div>
        <div className="flex-1 relative bg-slate-950">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={nodeTypes}
            fitView
            className="bg-slate-950"
          >
            <Background color="#1e293b" gap={16} />
            <Controls className="bg-slate-900 border-slate-800 fill-slate-400" />
          </ReactFlow>
        </div>
      </div>
    </div>
  );
}
