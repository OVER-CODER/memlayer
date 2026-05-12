'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '../../lib/api';
import ReactFlow, { Background, Controls, Edge, Node, MarkerType } from 'reactflow';
import 'reactflow/dist/style.css';
import { useMemo } from 'react';

const ViewNode = ({ data }: { data: any }) => {
  return (
    <div className="bg-slate-950 border border-slate-700 rounded-lg p-4 min-w-[250px] shadow-lg">
      <div className="flex justify-between items-start mb-2">
        <div className="font-bold text-white capitalize">{data.view_type} View</div>
        <span className="text-[10px] font-mono bg-slate-900 text-slate-300 px-1.5 py-0.5 rounded border border-slate-800">
          {data.provider}
        </span>
      </div>
      
      {data.quality !== undefined && (
        <div className="flex justify-between items-center text-xs mb-1">
          <span className="text-slate-500">Quality Score</span>
          <span className="text-emerald-400 font-mono">{(data.quality * 100).toFixed(1)}%</span>
        </div>
      )}
      
      {data.size !== undefined && (
        <div className="flex justify-between items-center text-xs">
          <span className="text-slate-500">Context Size</span>
          <span className="text-indigo-400 font-mono">{data.size} chars</span>
        </div>
      )}
    </div>
  );
};

const nodeTypes = {
  viewNode: ViewNode,
};

export default function ViewExplorerConsole() {
  const { data: viewsData, isLoading } = useQuery({
    queryKey: ['cachedViews'],
    queryFn: api.console.getCachedViews,
    refetchInterval: 5000,
  });

  const { nodes, edges } = useMemo(() => {
    if (!viewsData || !viewsData.context_bus) {
      return { nodes: [], edges: [] };
    }

    const flowNodes: Node[] = [];
    const flowEdges: Edge[] = [];
    
    let yPos = 50;
    const xPosStart = 100;
    
    // context_bus is a dict of cached state keys
    // We will just draw them sequentially or in a star graph if they share a workspace
    let idx = 0;
    Object.entries(viewsData.context_bus).forEach(([key, viewInfo]: [string, any]) => {
        // key is something like workspace_id:view_type:provider
        const parts = key.split(':');
        const viewType = parts.length > 1 ? parts[1] : 'unknown';
        const provider = parts.length > 2 ? parts[2] : 'unknown';
        
        flowNodes.push({
            id: `v_${idx}`,
            type: 'viewNode',
            position: { x: xPosStart + (idx % 3) * 300, y: yPos + Math.floor(idx / 3) * 150 },
            data: {
              label: `View Node`,
              view_type: viewType,
              provider: provider,
              quality: viewInfo.quality_score || 0.9,
              size: viewInfo.context_length || 0,
            }
        });
        idx++;
    });

    return { nodes: flowNodes, edges: flowEdges };
  }, [viewsData]);

  if (isLoading) return <div className="p-8 text-slate-400">Loading View Engine Explorer...</div>;

  return (
    <div className="flex flex-col h-full w-full">
      <div className="p-6 border-b border-slate-800 bg-slate-900 shrink-0">
        <h1 className="text-2xl font-bold text-white mb-2">View Engine Explorer</h1>
        <p className="text-sm text-slate-400">Visualize semantic projections and provider shaping.</p>
        
        {nodes.length === 0 && (
          <div className="mt-4 p-3 bg-indigo-950/30 border border-indigo-900 rounded text-sm text-indigo-300">
            No active views cached. Run a coordination query to generate and cache semantic projections.
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
