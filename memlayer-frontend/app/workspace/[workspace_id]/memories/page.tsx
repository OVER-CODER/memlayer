'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { memoriesAPI } from '@/lib/api';
import { Memory, MemoryStats } from '@/types';
import Link from 'next/link';

export default function MemoryInspectorPage() {
  const params = useParams();
  const workspaceId = params.workspace_id as string;

  const [memories, setMemories] = useState<Memory[]>([]);
  const [stats, setStats] = useState<MemoryStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Memory[]>([]);
  const [selectedMemory, setSelectedMemory] = useState<Memory | null>(null);
  const [filterSource, setFilterSource] = useState<string>('all');

  useEffect(() => {
    loadMemories();
    loadStats();
  }, [workspaceId]);

  const loadMemories = async () => {
    try {
      setLoading(true);
      const response = await memoriesAPI.list(workspaceId, 100, 0);
      setMemories(response.data);
    } catch (error) {
      console.error('Failed to load memories:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const response = await memoriesAPI.getStats(workspaceId);
      setStats(response.data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }

    try {
      const response = await memoriesAPI.search(workspaceId, searchQuery, 10);
      setSearchResults(response.data);
    } catch (error) {
      console.error('Failed to search memories:', error);
    }
  };

  const handleDeleteMemory = async (memoryId: string) => {
    if (!window.confirm('Delete this memory?')) return;

    try {
      await memoriesAPI.delete(workspaceId, memoryId);
      setMemories(memories.filter(m => m.id !== memoryId));
      setSelectedMemory(null);
      loadStats();
    } catch (error) {
      console.error('Failed to delete memory:', error);
    }
  };

  const filteredMemories = memories.filter(m => {
    if (filterSource !== 'all' && m.source_type !== filterSource) {
      return false;
    }
    return true;
  });

  const sourceTypes = stats
    ? Object.keys(stats.by_source).sort()
    : [];

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="max-w-7xl mx-auto p-6">
        {/* Header */}
        <div className="mb-6">
          <Link href={`/workspace/${workspaceId}`} className="text-blue-600 hover:text-blue-700 text-sm">
            ← Back to Chat
          </Link>
          <h1 className="text-3xl font-bold text-gray-900 mt-2">Memory Inspector</h1>
          <p className="text-gray-600">Visualize and manage semantic memories</p>
        </div>

        {/* Stats */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-3xl font-bold text-blue-600">{stats.total_memories}</div>
              <div className="text-gray-600 text-sm">Total Memories</div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-3xl font-bold text-purple-600">{(stats.avg_importance * 100).toFixed(0)}%</div>
              <div className="text-gray-600 text-sm">Avg Importance</div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-lg font-semibold text-gray-900">Sources</div>
              <div className="text-sm text-gray-600 mt-2">
                {sourceTypes.map((type, i) => (
                  <div key={type}>{type}: {stats.by_source[type]}</div>
                ))}
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-sm font-semibold text-gray-900">Memory Span</div>
              <div className="text-xs text-gray-600 mt-2">
                {stats.oldest_memory && (
                  <div>From: {new Date(stats.oldest_memory).toLocaleDateString()}</div>
                )}
                {stats.newest_memory && (
                  <div>To: {new Date(stats.newest_memory).toLocaleDateString()}</div>
                )}
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: Search and Filtering */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">Search & Filter</h2>

              {/* Search */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Semantic Search
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="Search memories..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') handleSearch();
                    }}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                  />
                  <button
                    onClick={handleSearch}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm"
                  >
                    Search
                  </button>
                </div>
              </div>

              {/* Filter by Source */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Filter by Source
                </label>
                <select
                  value={filterSource}
                  onChange={(e) => setFilterSource(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                >
                  <option value="all">All Sources</option>
                  {sourceTypes.map((type) => (
                    <option key={type} value={type}>
                      {type}
                    </option>
                  ))}
                </select>
              </div>

              {/* Search Results */}
              {searchResults.length > 0 && (
                <div className="mt-6">
                  <h3 className="text-sm font-semibold mb-3">Search Results ({searchResults.length})</h3>
                  <div className="space-y-2">
                    {searchResults.map((memory) => (
                      <button
                        key={memory.id}
                        onClick={() => setSelectedMemory(memory)}
                        className={`w-full text-left p-3 rounded-lg transition text-sm ${
                          selectedMemory?.id === memory.id
                            ? 'bg-blue-100 border-l-4 border-blue-600'
                            : 'bg-gray-50 hover:bg-gray-100'
                        }`}
                      >
                        <div className="font-medium truncate">{memory.summary || memory.raw_content.substring(0, 50)}</div>
                        <div className="text-xs text-gray-600 mt-1">{memory.source_type}</div>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Middle: Memory List */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">
                Memories ({filteredMemories.length})
              </h2>

              {loading ? (
                <p className="text-gray-600 text-sm">Loading...</p>
              ) : filteredMemories.length === 0 ? (
                <p className="text-gray-600 text-sm">No memories found</p>
              ) : (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {filteredMemories.map((memory) => (
                    <button
                      key={memory.id}
                      onClick={() => setSelectedMemory(memory)}
                      className={`w-full text-left p-3 rounded-lg transition text-sm ${
                        selectedMemory?.id === memory.id
                          ? 'bg-blue-100 border-l-4 border-blue-600'
                          : 'bg-gray-50 hover:bg-gray-100'
                      }`}
                    >
                      <div className="font-medium truncate">
                        {memory.summary || memory.raw_content.substring(0, 50)}
                      </div>
                      <div className="text-xs text-gray-600 mt-1">
                        {memory.source_type} • {(memory.importance_score * 100).toFixed(0)}% importance
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Right: Memory Details */}
          <div className="lg:col-span-1">
            {selectedMemory ? (
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex justify-between items-start mb-4">
                  <h2 className="text-lg font-semibold">Memory Details</h2>
                  <button
                    onClick={() => handleDeleteMemory(selectedMemory.id)}
                    className="text-red-600 hover:text-red-700 text-sm font-medium"
                  >
                    Delete
                  </button>
                </div>

                <div className="space-y-4">
                  {/* ID */}
                  <div>
                    <div className="text-xs font-semibold text-gray-600 uppercase">ID</div>
                    <div className="text-sm font-mono text-gray-900 truncate">{selectedMemory.id}</div>
                  </div>

                  {/* Source */}
                  <div>
                    <div className="text-xs font-semibold text-gray-600 uppercase">Source Type</div>
                    <div className="text-sm text-gray-900">{selectedMemory.source_type}</div>
                  </div>

                  {/* Timestamp */}
                  <div>
                    <div className="text-xs font-semibold text-gray-600 uppercase">Timestamp</div>
                    <div className="text-sm text-gray-900">
                      {new Date(selectedMemory.timestamp).toLocaleString()}
                    </div>
                  </div>

                  {/* Importance Score */}
                  <div>
                    <div className="text-xs font-semibold text-gray-600 uppercase">Importance Score</div>
                    <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{ width: `${selectedMemory.importance_score * 100}%` }}
                      />
                    </div>
                    <div className="text-sm text-gray-900 mt-1">
                      {(selectedMemory.importance_score * 100).toFixed(1)}%
                    </div>
                  </div>

                  {/* Summary */}
                  <div>
                    <div className="text-xs font-semibold text-gray-600 uppercase mb-2">Summary</div>
                    <div className="text-sm text-gray-900 bg-gray-50 p-3 rounded max-h-24 overflow-y-auto">
                      {selectedMemory.summary || '(No summary)'}
                    </div>
                  </div>

                  {/* Content */}
                  <div>
                    <div className="text-xs font-semibold text-gray-600 uppercase mb-2">Raw Content</div>
                    <div className="text-sm text-gray-900 bg-gray-50 p-3 rounded max-h-40 overflow-y-auto whitespace-pre-wrap">
                      {selectedMemory.raw_content}
                    </div>
                  </div>

                  {/* Metadata */}
                  {selectedMemory.metadata && Object.keys(selectedMemory.metadata).length > 0 && (
                    <div>
                      <div className="text-xs font-semibold text-gray-600 uppercase mb-2">Metadata</div>
                      <div className="text-sm text-gray-900 bg-gray-50 p-3 rounded font-mono max-h-24 overflow-y-auto">
                        {JSON.stringify(selectedMemory.metadata, null, 2)}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow p-6 text-center">
                <p className="text-gray-600">Select a memory to view details</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
