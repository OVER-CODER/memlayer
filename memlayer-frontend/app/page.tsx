'use client';

import { useEffect, useState } from 'react';
import { workspacesAPI } from '@/lib/api';
import { Workspace } from '@/types';
import Link from 'next/link';

export default function WorkspacesPage() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [loading, setLoading] = useState(true);
  const [newName, setNewName] = useState('');
  const [newDescription, setNewDescription] = useState('');

  useEffect(() => {
    loadWorkspaces();
  }, []);

  const loadWorkspaces = async () => {
    try {
      setLoading(true);
      const response = await workspacesAPI.list();
      setWorkspaces(response.data);
    } catch (error) {
      console.error('Failed to load workspaces:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateWorkspace = async () => {
    if (!newName.trim()) return;
    
    try {
      await workspacesAPI.create(newName, newDescription);
      setNewName('');
      setNewDescription('');
      loadWorkspaces();
    } catch (error) {
      console.error('Failed to create workspace:', error);
    }
  };

  const handleDeleteWorkspace = async (id: string) => {
    if (!window.confirm('Delete this workspace?')) return;
    
    try {
      await workspacesAPI.delete(id);
      loadWorkspaces();
    } catch (error) {
      console.error('Failed to delete workspace:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-6xl mx-auto p-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">MemLayer</h1>
          <p className="text-gray-600">Persistent semantic memory for AI workspaces</p>
        </div>

        {/* Create Workspace Form */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">Create New Workspace</h2>
          <div className="space-y-4">
            <input
              type="text"
              placeholder="Workspace name"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <textarea
              placeholder="Description (optional)"
              value={newDescription}
              onChange={(e) => setNewDescription(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 h-24"
            />
            <button
              onClick={handleCreateWorkspace}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition"
            >
              Create Workspace
            </button>
          </div>
        </div>

        {/* Workspaces List */}
        <div>
          <h2 className="text-2xl font-semibold mb-4">Your Workspaces</h2>
          {loading ? (
            <div className="text-center py-8">
              <p className="text-gray-600">Loading workspaces...</p>
            </div>
          ) : workspaces.length === 0 ? (
            <div className="text-center py-8 bg-white rounded-lg">
              <p className="text-gray-600">No workspaces yet. Create one to get started!</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {workspaces.map((ws) => (
                <Link
                  key={ws.id}
                  href={`/workspace/${ws.id}`}
                >
                  <div className="bg-white rounded-lg shadow-md hover:shadow-lg transition p-6 cursor-pointer h-full">
                    <h3 className="text-lg font-semibold mb-2">{ws.name}</h3>
                    <p className="text-gray-600 text-sm mb-4">{ws.description || 'No description'}</p>
                    <div className="text-xs text-gray-500">
                      Created {new Date(ws.created_at).toLocaleDateString()}
                    </div>
                    <button
                      onClick={(e) => {
                        e.preventDefault();
                        handleDeleteWorkspace(ws.id);
                      }}
                      className="mt-4 text-red-600 hover:text-red-700 text-sm font-medium"
                    >
                      Delete
                    </button>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
