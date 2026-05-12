'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '../../lib/api';
import ReactFlow, { Background, Controls, Edge, Node, MarkerType } from 'reactflow';
import 'reactflow/dist/style.css';
import { useMemo } from 'react';
import { format } from 'date-fns';

const AgentNode = ({ data }: { data: any }) => {
  return (
    <div className="bg-slate-950 border border-indigo-900 rounded-lg p-4 min-w-[250px] shadow-lg shadow-indigo-900/20">
      <div className="flex justify-between items-start mb-2">
        <div className="font-bold text-white">{data.label}</div>
        <span className="text-[10px] font-mono bg-indigo-950 text-indigo-300 px-1.5 py-0.5 rounded border border-indigo-800">
          {data.provider}
        </span>
      </div>
      
      {data.tokens_saved !== undefined && (
        <div className="flex justify-between items-center text-xs mb-1">
          <span className="text-slate-500">Tokens Saved</span>
          <span className="text-emerald-400 font-mono">+{data.tokens_saved}</span>
        </div>
      )}
      
      {data.reuse_ratio !== undefined && (
        <div className="flex justify-between items-center text-xs mb-1">
          <span className="text-slate-500">Context Reuse</span>
          <span className="text-indigo-400 font-mono">{(data.reuse_ratio * 100).toFixed(1)}%</span>
        </div>
      )}

      {data.duration_ms !== undefined && (
        <div className="flex justify-between items-center text-xs">
          <span className="text-slate-500">Latency</span>
          <span className="text-slate-300 font-mono">{data.duration_ms.toFixed(1)}ms</span>
        </div>
      )}
    </div>
  );
};

const nodeTypes = {
  agentNode: AgentNode,
};

export default function CoordinationConsole() {
  const { data: traces, isLoading } = useQuery({
    queryKey: ['coordinationTraces'],
    queryFn: api.console.getCoordinationTraces,
    refetchInterval: 5000,
  });

  const { nodes, edges } = useMemo(() => {
    if (!traces || traces.length === 0) {
      return { nodes: [], edges: [] };
    }

    const flowNodes: Node[] = [];
    const flowEdges: Edge[] = [];
    
    // We will lay out the 5 most recent traces as a sequence of coordination runs
    const recentTraces = traces.slice(0, 5);
    
    let yPos = 50;
    const xPosBase = 250;

    recentTraces.forEach((trace: any, idx: number) => {
      const traceId = trace.report_id;
      
      flowNodes.push({
        id: `t_${traceId}`,
        type: 'agentNode',
        position: { x: xPosBase, y: yPos },
        data: {
          label: `Coordination Agent`,
          provider: trace.provider,
          tokens_saved: trace.total_tokens_saved,
          reuse_ratio: trace.context_reuse_ratio,
          duration_ms: trace.coordination_duration_ms,
        }
      });

      if (idx > 0) {
        const prevTrace = recentTraces[idx - 1];
        flowEdges.push({
          id: `e_${prevTrace.report_id}_${traceId}`,
          source: `t_${prevTrace.report_id}`,
          target: `t_${traceId}`,
          animated: true,
          label: 'Semantic Delegation',
          labelStyle: { fill: '#94a3b8', fontSize: 10 },
          style: { stroke: '#4f46e5', strokeWidth: 2 },
          markerEnd: { type: MarkerType.ArrowClosed, color: '#4f46e5' },
        });
      }
      
      yPos += 150;
    });

    return { nodes: flowNodes, edges: flowEdges };
  }, [traces]);

  if (isLoading) return <div className="p-8 text-slate-400">Loading Coordination Runtime Graph...</div>;

  return (
    <div className="flex flex-col h-full w-full">
      <div className="p-6 border-b border-slate-800 bg-slate-900 shrink-0">
        <h1 className="text-2xl font-bold text-white mb-2">Coordination Runtime Graph</h1>
        <p className="text-sm text-slate-400">Realtime topology of shared cognition and delegation chains.</p>
        
        {traces?.length === 0 && (
          <div className="mt-4 p-3 bg-indigo-950/30 border border-indigo-900 rounded text-sm text-indigo-300">
            No coordination traces active. Run a coordination query to see the delegation graph.
          </div>
        )}
      </div>

      <div className="flex-1 bg-slate-950 relative">
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
  );
}
