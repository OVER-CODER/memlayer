'use client';

import { ArrowDown } from 'lucide-react';

export default function CompilerConsole() {
  // Mock data for visualization until we hook it up to a specific coordination trace
  const pipeline = [
    { step: 'Raw Memory Input', tokens: 12500, metric: '100 memories' },
    { step: 'Semantic Deduplication', tokens: 8400, metric: '32.8% reduction' },
    { step: 'Semantic Chunking', tokens: 8600, metric: '24 chunks generated' },
    { step: 'Context Compression', tokens: 3200, metric: '62.7% compression ratio' },
    { step: 'Adaptive Assembly', tokens: 3450, metric: 'Fit to 4000 budget' },
    { step: 'Compiled Semantic State', tokens: 3450, metric: 'Ready for projection' },
  ];

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-white mb-2">Context Compiler Pipeline</h1>
        <p className="text-slate-400">Deterministic semantic reduction and context assembly.</p>
      </div>

      <div className="space-y-2 py-8">
        {pipeline.map((stage, i) => (
          <div key={stage.step} className="flex flex-col items-center">
            <div className="w-full max-w-2xl bg-slate-950 border border-slate-800 rounded-lg p-6 flex justify-between items-center relative overflow-hidden group hover:border-indigo-500 transition-colors">
              <div className="absolute left-0 top-0 bottom-0 w-1 bg-indigo-500/20 group-hover:bg-indigo-500 transition-colors"></div>
              <div>
                <h3 className="text-lg font-semibold text-white">{stage.step}</h3>
                <p className="text-sm text-slate-400">{stage.metric}</p>
              </div>
              <div className="text-right">
                <div className="text-2xl font-mono text-indigo-400">{stage.tokens}</div>
                <div className="text-xs text-slate-500 uppercase tracking-wider">Tokens</div>
              </div>
            </div>
            
            {i < pipeline.length - 1 && (
              <div className="h-8 flex items-center justify-center text-slate-700">
                <ArrowDown className="h-5 w-5" />
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
