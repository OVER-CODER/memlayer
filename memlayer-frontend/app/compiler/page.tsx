'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '../../lib/api';
import ReactFlow, { Background, Controls, Edge, Node, MarkerType } from 'reactflow';
import 'reactflow/dist/style.css';
import { useMemo } from 'react';

// Custom node component for the DAG
const CompilerNode = ({ data }: { data: any }) => {
  return (
    <div className="bg-slate-950 border border-slate-700 rounded-lg p-4 min-w-[250px] shadow-lg">
      <div className="font-bold text-white mb-1">{data.label}</div>
      <div className="text-xs text-slate-400 mb-3">{data.description}</div>
      
      {data.duration_ms !== undefined && (
        <div className="flex justify-between items-center text-xs mb-1">
          <span className="text-slate-500">Duration</span>
          <span className="text-emerald-400 font-mono">{data.duration_ms.toFixed(1)}ms</span>
        </div>
      )}
      
      {data.input_count !== undefined && (
        <div className="flex justify-between items-center text-xs mb-1">
          <span className="text-slate-500">Input</span>
          <span className="text-indigo-400 font-mono">{data.input_count} items</span>
        </div>
      )}

      {data.output_count !== undefined && (
        <div className="flex justify-between items-center text-xs">
          <span className="text-slate-500">Output</span>
          <span className="text-indigo-400 font-mono">{data.output_count} items</span>
        </div>
      )}
    </div>
  );
};

const nodeTypes = {
  compilerNode: CompilerNode,
};

export default function CompilerConsole() {
  const { data, isLoading } = useQuery({
    queryKey: ['compilerPipeline'],
    queryFn: api.console.getCompilerPipeline,
    refetchInterval: 5000,
  });

  const { nodes, edges } = useMemo(() => {
    if (!data || !data.history || data.history.length === 0) {
      return { nodes: [], edges: [] };
    }

    // Get latest execution
    const latest = data.history[data.history.length - 1];
    const metrics = latest.stage_metrics || [];

    const flowNodes: Node[] = [];
    const flowEdges: Edge[] = [];
    
    let yPos = 50;
    const xPos = 250;

    // Initial Node
    flowNodes.push({
      id: 'raw_memory',
      type: 'compilerNode',
      position: { x: xPos, y: yPos },
      data: { 
        label: 'Raw Workspace Memory',
        description: `Query: "${latest.query}"`,
      }
    });

    let prevId = 'raw_memory';

    metrics.forEach((m: any, idx: number) => {
      yPos += 150;
      const id = `stage_${m.stage}`;
      
      flowNodes.push({
        id,
        type: 'compilerNode',
        position: { x: xPos, y: yPos },
        data: {
          label: m.stage.toUpperCase(),
          description: m.notes || `Pipeline stage execution`,
          duration_ms: m.duration_ms,
          input_count: m.input_count,
          output_count: m.output_count,
        }
      });

      flowEdges.push({
        id: `e_${prevId}_${id}`,
        source: prevId,
        target: id,
        animated: true,
        style: { stroke: '#6366f1', strokeWidth: 2 },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: '#6366f1',
        },
      });

      prevId = id;
    });

    // Final state node
    yPos += 150;
    flowNodes.push({
      id: 'compiled_state',
      type: 'compilerNode',
      position: { x: xPos, y: yPos },
      data: {
        label: 'Compiled Semantic State',
        description: `Provider: ${latest.provider} | Efficiency: ${(latest.token_efficiency * 100).toFixed(1)}%`,
      }
    });

    flowEdges.push({
      id: `e_${prevId}_compiled_state`,
      source: prevId,
      target: 'compiled_state',
      animated: true,
      style: { stroke: '#10b981', strokeWidth: 2 },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: '#10b981',
      },
    });

    return { nodes: flowNodes, edges: flowEdges };
  }, [data]);

  if (isLoading) return <div className="p-8 text-slate-400">Loading Compiler Telemetry...</div>;

  return (
    <div className="flex flex-col h-full w-full">
      <div className="p-6 border-b border-slate-800 bg-slate-900 shrink-0">
        <h1 className="text-2xl font-bold text-white mb-2">Context Compiler Pipeline</h1>
        <p className="text-sm text-slate-400">Deterministic semantic reduction and context assembly DAG.</p>
        
        {data?.history?.length === 0 && (
          <div className="mt-4 p-3 bg-indigo-950/30 border border-indigo-900 rounded text-sm text-indigo-300">
            No pipeline executions recorded yet. Trigger a coordination in a workspace to view the compiler DAG.
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
