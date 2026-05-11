'use client';

import { RetrievedMemory } from '@/types';

interface MemoryVisualizerProps {
  memories: RetrievedMemory[];
  isOpen: boolean;
  onClose: () => void;
}

export function MemoryVisualizer({ memories, isOpen, onClose }: MemoryVisualizerProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-end">
      <div className="bg-white w-full max-h-96 rounded-t-lg shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-600 to-blue-600 p-4 flex justify-between items-center">
          <h3 className="text-white font-semibold">
            Retrieved Memories ({memories.length})
          </h3>
          <button
            onClick={onClose}
            className="text-white hover:bg-white hover:bg-opacity-20 p-1 rounded"
          >
            ✕
          </button>
        </div>

        {/* Memories Grid */}
        <div className="overflow-y-auto max-h-80 p-4">
          {memories.length === 0 ? (
            <p className="text-gray-600 text-center py-8">No memories retrieved</p>
          ) : (
            <div className="space-y-3">
              {memories.map((memory, index) => (
                <div
                  key={memory.id}
                  className="bg-gray-50 rounded-lg p-3 border-l-4 border-purple-600"
                >
                  {/* Header */}
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex-1">
                      <div className="text-sm font-medium text-gray-900">
                        #{index + 1} • {memory.source_type}
                      </div>
                      <div className="text-xs text-gray-600 mt-1">
                        {new Date(memory.timestamp).toLocaleString()}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs font-semibold text-purple-600">
                        {(memory.similarity_score * 100).toFixed(1)}% match
                      </div>
                      <div className="w-24 bg-gray-200 rounded-full h-1.5 mt-1">
                        <div
                          className="bg-purple-600 h-1.5 rounded-full"
                          style={{ width: `${memory.similarity_score * 100}%` }}
                        />
                      </div>
                    </div>
                  </div>

                  {/* Summary */}
                  {memory.summary && (
                    <div className="text-sm text-gray-900 bg-white p-2 rounded mb-2">
                      <span className="font-medium">Summary:</span> {memory.summary}
                    </div>
                  )}

                  {/* Content Preview */}
                  <div className="text-xs text-gray-600 bg-white p-2 rounded line-clamp-2">
                    {memory.content.substring(0, 150)}
                    {memory.content.length > 150 ? '...' : ''}
                  </div>

                  {/* Scores */}
                  <div className="flex gap-4 mt-2 text-xs text-gray-600">
                    <div>
                      <span className="font-medium">Similarity:</span>{' '}
                      {(memory.similarity_score * 100).toFixed(1)}%
                    </div>
                    <div>
                      <span className="font-medium">Importance:</span>{' '}
                      {(memory.importance_score * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
